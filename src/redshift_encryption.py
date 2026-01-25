import sys
import os
import boto3
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import udf, col
from pyspark.sql.types import StringType

# 引数の取得（KMSキーIDや接続名などをジョブ設定から受け取る）
try:
    args = getResolvedOptions(sys.argv, [
        'JOB_NAME',
        'KMS_KEY_ID',
        'REDSHIFT_CONNECTION_NAME',
        'TEMP_S3_DIR',
        'DB_SCHEMA',
        'DB_TABLE'
    ])
    # 出力テーブル名を動的に生成（元テーブル名 + _encrypted）
    args['DB_TABLE_OUTPUT'] = f"{args['DB_TABLE']}_encrypted"
    print("[SUCCESS] Job arguments loaded successfully")
    print(f"[DEBUG] Input table: {args['DB_SCHEMA']}.{args['DB_TABLE']}")
    print(f"[DEBUG] Output table: {args['DB_SCHEMA']}.{args['DB_TABLE_OUTPUT']}")
except Exception as e:
    print(f"[ERROR] Failed to load job arguments: {e}")
    sys.exit(1)

# ローカル環境判定
IS_LOCAL = os.getenv('LOCALSTACK_ENDPOINT') is not None

#glueコンテキストとSparkセッションの初期化
try:
    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session
    job = Job(glueContext)
    job.init(args['JOB_NAME'], args)
    print("[SUCCESS] Spark and Glue context initialized")
except Exception as e:
    print(f"[ERROR] Failed to initialize Spark/Glue context: {e}")
    sys.exit(1)

# --- KMS クライアント初期化 ---
try:
    if IS_LOCAL:
        # ローカル環境: LocalStackに接続
        kms_client = boto3.client(
            'kms',
            region_name='ap-northeast-1',
            endpoint_url=os.getenv('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
        )
        print("[INFO] Initialized KMS client for LocalStack environment")
    else:
        # AWS環境: 通常のKMSに接続
        kms_client = boto3.client('kms', region_name='ap-northeast-1')
        print("[INFO] Initialized KMS client for AWS environment")
except Exception as e:
    print(f"[ERROR] Failed to initialize KMS client: {e}")
    sys.exit(1)

def encrypt_id(plain_id):
    """
    ID列を暗号化する関数
    - AWS環境: KMS + AES256で暗号化
    - ローカル環境: KMS + AES256で暗号化（推奨）、失敗時はBase64にフォールバック
    """
    if plain_id is None:
        return None
    
    try:
        plain_id_str = str(plain_id)
        plain_text = plain_id_str.encode('utf-8')
        
        try:
            # Step 1: KMS から データキーを生成（AWS・ローカル共通）
            print(f"[DEBUG] Generating data key from KMS for ID: {plain_id_str[:10]}...")
            data_key_response = kms_client.generate_data_key(
                KeyId=args['KMS_KEY_ID'],
                KeySpec='AES_256'
            )
            plaintext_key = data_key_response['Plaintext']
            encrypted_data_key = data_key_response['CiphertextBlob']
            print("[DEBUG] Data key generated successfully")
            
            # Step 2: AES256でデータを暗号化（AWS・ローカル共通）
            print(f"[DEBUG] Encrypting data with AES256...")
            iv = os.urandom(16)  # 初期化ベクトル
            cipher = Cipher(
                algorithms.AES(plaintext_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # パディング処理
            padding_length = 16 - (len(plain_text) % 16)
            padded_text = plain_text + bytes([padding_length] * padding_length)
            
            ciphertext = encryptor.update(padded_text) + encryptor.finalize()
            print("[DEBUG] Data encrypted with AES256 successfully")
            
            # Step 3: 暗号化されたデータキー + IV + 暗号化されたデータを結合
            # フォーマット: [encrypted_data_key_length(4bytes)][encrypted_data_key][iv(16bytes)][ciphertext]
            encrypted_data_key_len = len(encrypted_data_key).to_bytes(4, 'big')
            combined = encrypted_data_key_len + encrypted_data_key + iv + ciphertext
            
            # Base64エンコードして返す
            return base64.b64encode(combined).decode('utf-8')
            
        except kms_client.exceptions.InvalidKeyId as e:
            print(f"[ERROR] Invalid KMS key ID '{args['KMS_KEY_ID']}': {e}")
            if IS_LOCAL:
                print(f"[WARNING] LocalStack KMS key not found, falling back to Base64 encoding")
                return base64.b64encode(plain_text).decode('utf-8')
            raise
        except kms_client.exceptions.KMSInvalidStateException as e:
            print(f"[ERROR] KMS key is in invalid state: {e}")
            if IS_LOCAL:
                print(f"[WARNING] LocalStack KMS key is invalid, falling back to Base64 encoding")
                return base64.b64encode(plain_text).decode('utf-8')
            raise
        except Exception as e:
            print(f"[ERROR] Failed to encrypt data with KMS/AES256: {e}")
            if IS_LOCAL:
                print(f"[WARNING] LocalStack KMS failed, falling back to Base64 encoding")
                return base64.b64encode(plain_text).decode('utf-8')
            raise
                
    except Exception as e:
        print(f"[ERROR] Encryption failed for ID {plain_id}: {e}")
        raise

# Spark UDFとして登録
encrypt_udf = udf(encrypt_id, StringType())

# --- 1. Redshiftからデータをロード ---
try:
    print("[INFO] Starting data load phase...")
    
    if IS_LOCAL:
        # ローカル環境: PostgreSQLから直接読み込み
        print("[INFO] Loading data from PostgreSQL (Local environment)")
        
        try:
            postgres_host = os.getenv('POSTGRES_HOST', 'localhost')
            postgres_port = os.getenv('POSTGRES_PORT', '5432')
            postgres_db = os.getenv('POSTGRES_DB', 'dev_db')
            postgres_user = os.getenv('POSTGRES_USER', 'postgres')
            postgres_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
            
            print(f"[DEBUG] Connecting to PostgreSQL: {postgres_host}:{postgres_port}/{postgres_db}")
            
            df = spark.read \
                .format("jdbc") \
                .option("url", f"jdbc:postgresql://{postgres_host}:{postgres_port}/{postgres_db}") \
                .option("dbtable", f"{args['DB_SCHEMA']}.{args['DB_TABLE']}") \
                .option("user", postgres_user) \
                .option("password", postgres_password) \
                .option("driver", "org.postgresql.Driver") \
                .load()
            
            print("[SUCCESS] Data loaded from PostgreSQL")
        except Exception as e:
            print(f"[ERROR] Failed to load data from PostgreSQL: {e}")
            raise
    else:
        # AWS環境: Glue Data Catalogの接続（Connection）を使用
        print("[INFO] Loading data from Redshift (AWS environment)")
        
        try:
            datasource = glueContext.create_dynamic_frame.from_options(
                connection_type="redshift",
                connection_options={
                    "useConnectionProperties": "true",
                    "dbtable": f"{args['DB_SCHEMA']}.{args['DB_TABLE']}",
                    "connectionName": args['REDSHIFT_CONNECTION_NAME'],
                }
            )
            df = datasource.toDF()
            print("[SUCCESS] Data loaded from Redshift")
        except Exception as e:
            print(f"[ERROR] Failed to load data from Redshift: {e}")
            raise
    
    row_count = df.count()
    print(f"[SUCCESS] Total rows loaded from {args['DB_SCHEMA']}.{args['DB_TABLE']}: {row_count} rows")
    
except Exception as e:
    print(f"[CRITICAL] Data load phase failed: {e}")
    sys.exit(1)

# --- 2. ID列の暗号化処理 ---
try:
    print("[INFO] Starting encryption phase...")
    print(f"[DEBUG] Adding 'encrypted_id' column for output table: {args['DB_SCHEMA']}.{args['DB_TABLE_OUTPUT']}")
    
    encrypted_df = df.withColumn("encrypted_id", encrypt_udf(col("id")))
    
    print("[SUCCESS] Encryption completed successfully")
    encrypted_row_count = encrypted_df.count()
    print(f"[INFO] Encrypted rows: {encrypted_row_count}")
    
except Exception as e:
    print(f"[CRITICAL] Encryption phase failed: {e}")
    sys.exit(1)

# --- 3. Redshiftへ書き戻し（全件更新） ---
try:
    print("[INFO] Starting write-back phase...")
    
    if IS_LOCAL:
        # ローカル環境: PostgreSQLに書き戻し
        print(f"[INFO] Writing encrypted data to PostgreSQL (Local environment): {args['DB_SCHEMA']}.{args['DB_TABLE_OUTPUT']}")
        
        try:
            encrypted_df.write \
                .format("jdbc") \
                .mode("overwrite") \
                .option("url", f"jdbc:postgresql://{postgres_host}:{postgres_port}/{postgres_db}") \
                .option("dbtable", f"{args['DB_SCHEMA']}.{args['DB_TABLE_OUTPUT']}") \
                .option("user", postgres_user) \
                .option("password", postgres_password) \
                .option("driver", "org.postgresql.Driver") \
                .save()
            
            print(f"[SUCCESS] Data written to {args['DB_SCHEMA']}.{args['DB_TABLE_OUTPUT']} successfully")
        except Exception as e:
            print(f"[ERROR] Failed to write data to PostgreSQL: {e}")
            raise
    else:
        # AWS環境: Glue + Redshiftに書き戻し
        print(f"[INFO] Writing encrypted data to Redshift (AWS environment): {args['DB_SCHEMA']}.{args['DB_TABLE_OUTPUT']}")
        
        try:
            output_dynamic_frame = DynamicFrame.fromDF(encrypted_df, glueContext, "output_dynamic_frame")
            print("[DEBUG] DynamicFrame created")
            
            # 全件更新を実現するため、事前にテーブルをTRUNCATEする
            truncate_sql = f"TRUNCATE TABLE {args['DB_SCHEMA']}.{args['DB_TABLE_OUTPUT']};"
            print(f"[DEBUG] Preparing TRUNCATE operation: {truncate_sql}")
            
            glueContext.write_dynamic_frame.from_options(
                frame=output_dynamic_frame,
                connection_type="redshift",
                connection_options={
                    "useConnectionProperties": "true",
                    "dbtable": f"{args['DB_SCHEMA']}.{args['DB_TABLE_OUTPUT']}",
                    "connectionName": args['REDSHIFT_CONNECTION_NAME'],
                    "preactions": truncate_sql,
                    "tempdir": args['TEMP_S3_DIR']
                }
            )
            
            print(f"[SUCCESS] Data written to {args['DB_SCHEMA']}.{args['DB_TABLE_OUTPUT']} successfully")
        except Exception as e:
            print(f"[ERROR] Failed to write data to Redshift: {e}")
            raise
    
    print("[SUCCESS] Write-back phase completed successfully")
    
except Exception as e:
    print(f"[CRITICAL] Write-back phase failed: {e}")
    sys.exit(1)

# --- 4. ジョブ完了 ---
try:
    print("[INFO] Finalizing job...")
    job.commit()
    print("[SUCCESS] Job completed successfully!")
except Exception as e:
    print(f"[ERROR] Failed to commit job: {e}")
    sys.exit(1)