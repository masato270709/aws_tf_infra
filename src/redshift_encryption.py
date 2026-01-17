import sys
import boto3
import base64
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import udf, col
from pyspark.sql.types import StringType

# 引数の取得（KMSキーIDや接続名などをジョブ設定から受け取る）
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'KMS_KEY_ID',
    'REDSHIFT_CONNECTION_NAME',
    'TEMP_S3_DIR',
    'DB_SCHEMA',
    'DB_TABLE'
])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# --- KMS暗号化用の関数定義 ---
kms_client = boto3.client('kms', region_name='ap-northeast-1')

def encrypt_id(plain_id):
    if plain_id is None:
        return None
    # DECIMAL(32,0)を文字列として扱い暗号化
    response = kms_client.encrypt(
        KeyId=args['KMS_KEY_ID'],
        Plaintext=str(plain_id).encode('utf-8')
    )
    # バイナリをBase64文字列に変換して保存可能にする
    return base64.b64encode(response['CiphertextBlob']).decode('utf-8')

# Spark UDFとして登録
encrypt_udf = udf(encrypt_id, StringType())

# --- 1. Redshiftからデータをロード ---
# Glue Data Catalogの接続（Connection）を使用
datasource = glueContext.create_dynamic_frame.from_options(
    connection_type="redshift",
    connection_options={
        "useConnectionProperties": "true",
        "dbtable": f"{args['DB_SCHEMA']}.{args['DB_TABLE']}",
        "connectionName": args['REDSHIFT_CONNECTION_NAME'],
        "aws_iam_user": "arn:aws:iam::xxxxxxxxxxxx:role/service-role/your-glue-role" # 適宜変更
    }
)

df = datasource.toDF()

# --- 2. ID列の暗号化処理 ---
# id列に対してUDFを適用
encrypted_df = df.withColumn("id", encrypt_udf(col("id")))

# --- 3. Redshiftへ書き戻し ---
# 書き込み用のDynamicFrameに変換
output_dynamic_frame = DynamicFrame.fromDF(encrypted_df, glueContext, "output_dynamic_frame")

glueContext.write_dynamic_frame.from_options(
    frame=output_dynamic_frame,
    connection_type="redshift",
    connection_options={
        "useConnectionProperties": "true",
        "dbtable": f"{args['DB_SCHEMA']}.{args['DB_TABLE']}_encrypted", # 別テーブルにする例
        "connectionName": args['REDSHIFT_CONNECTION_NAME'],
        "preactions": f"CREATE TABLE IF NOT EXISTS {args['DB_SCHEMA']}.{args['DB_TABLE']}_encrypted (id VARCHAR(500), name VARCHAR(100), birthdate DATE);",
        "tempdir": args['TEMP_S3_DIR']
    }
)

job.commit()