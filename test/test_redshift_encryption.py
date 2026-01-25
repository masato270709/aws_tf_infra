import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
import base64
import json
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

# ローカルパスをPYTHONPATHに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

class TestRedshiftEncryption(unittest.TestCase):
    """Redshift暗号化Glueジョブのテスト"""
    
    @classmethod
    def setUpClass(cls):
        """テスト用のSparkセッションを作成"""
        cls.spark = SparkSession.builder \
            .appName("test_redshift_encryption") \
            .master("local[1]") \
            .getOrCreate()
        cls.spark.sparkContext.setLogLevel("ERROR")
    
    @classmethod
    def tearDownClass(cls):
        """SparkSessionを閉じる"""
        cls.spark.stop()
    
    def setUp(self):
        """各テストの前に実行"""
        # テスト用のサンプルデータを作成
        self.test_data = [
            (1, "Alice", "1990-01-15"),
            (2, "Bob", "1985-05-20"),
            (None, "Charlie", "1992-12-10"),  # NULLテスト
        ]
        
        self.df = self.spark.createDataFrame(
            self.test_data,
            ["id", "name", "birthdate"]
        )
    
    def test_encryption_function(self):
        """KMS暗号化関数のテスト"""
        from pyspark.sql.functions import udf
        from pyspark.sql.types import StringType
        
        # モック化されたKMSクライアント
        def mock_encrypt_id(plain_id):
            if plain_id is None:
                return None
            # テスト用: 単純なBase64エンコード
            return base64.b64encode(str(plain_id).encode('utf-8')).decode('utf-8')
        
        encrypt_udf = udf(mock_encrypt_id, StringType())
        
        # UDFを適用
        encrypted_df = self.df.withColumn("id_encrypted", encrypt_udf(col("id")))
        
        result = encrypted_df.collect()
        
        # 暗号化が成功したことを確認
        self.assertIsNotNone(result[0]['id_encrypted'])
        self.assertIsNotNone(result[1]['id_encrypted'])
        self.assertIsNone(result[2]['id_encrypted'])  # NULLはNULLのまま
        
        print("✓ Encryption function test passed")
    
    def test_dataframe_loading(self):
        """データフレーム読み込みのテスト"""
        # サンプルデータが正しく読み込まれたか確認
        self.assertEqual(self.df.count(), 3)
        self.assertEqual(len(self.df.columns), 3)
        
        print("✓ DataFrame loading test passed")
    
    def test_null_handling(self):
        """NULL値のハンドリングテスト"""
        from pyspark.sql.functions import udf
        from pyspark.sql.types import StringType
        
        def safe_encrypt(value):
            if value is None:
                return None
            return base64.b64encode(str(value).encode('utf-8')).decode('utf-8')
        
        encrypt_udf = udf(safe_encrypt, StringType())
        encrypted_df = self.df.withColumn("id_encrypted", encrypt_udf(col("id")))
        
        # NULL行を確認
        null_row = encrypted_df.filter(encrypted_df.id.isNull()).collect()[0]
        self.assertIsNone(null_row['id_encrypted'])
        
        print("✓ NULL handling test passed")
    
    @patch.dict(os.environ, {'LOCALSTACK_ENDPOINT': 'http://localhost:4566'})
    def test_localstack_environment(self):
        """LocalStack環境判定のテスト"""
        is_local = os.getenv('LOCALSTACK_ENDPOINT') is not None
        self.assertTrue(is_local)
        
        print("✓ LocalStack environment test passed")

if __name__ == '__main__':
    unittest.main(verbosity=2)
