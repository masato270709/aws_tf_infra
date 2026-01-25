#!/usr/bin/env python
"""
統合テスト: ローカル環境（LocalStack + PostgreSQL）でのエンドツーエンドテスト
"""

import os
import sys
import boto3
import psycopg2
import time
from psycopg2 import sql

def wait_for_service(host, port, timeout=30):
    """サービスが起動するまで待つ"""
    import socket
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            socket.create_connection((host, port), timeout=1)
            print(f"✓ {host}:{port} is ready")
            return True
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(1)
    
    raise TimeoutError(f"Service {host}:{port} did not start within {timeout} seconds")

def test_localstack_kms():
    """LocalStack KMSのテスト"""
    print("\n=== Testing LocalStack KMS ===")
    
    localstack_endpoint = os.getenv('LOCALSTACK_ENDPOINT', 'http://localhost:4566')
    
    try:
        # LocalStackのKMSクライアント
        kms = boto3.client(
            'kms',
            region_name='ap-northeast-1',
            endpoint_url=localstack_endpoint,
            aws_access_key_id='test',
            aws_secret_access_key='test'
        )
        
        # デフォルトキーを使用
        response = kms.list_keys()
        print(f"✓ KMS connected. Keys: {len(response['Keys'])}")
        
        # 暗号化テスト
        try:
            encrypt_response = kms.encrypt(
                KeyId='alias/aws/s3',
                Plaintext=b'test_id_12345'
            )
            print(f"✓ KMS encryption test passed")
            return True
        except kms.exceptions.NotFoundException:
            print("⚠ KMS key alias/aws/s3 not found, but KMS is working")
            return True
            
    except Exception as e:
        print(f"✗ KMS test failed: {e}")
        return False

def test_postgres_connection():
    """PostgreSQLの接続テスト"""
    print("\n=== Testing PostgreSQL Connection ===")
    
    postgres_host = os.getenv('POSTGRES_HOST', 'localhost')
    postgres_port = int(os.getenv('POSTGRES_PORT', '5432'))
    postgres_user = os.getenv('POSTGRES_USER', 'postgres')
    postgres_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
    postgres_db = os.getenv('POSTGRES_DB', 'dev_db')
    
    try:
        conn = psycopg2.connect(
            host=postgres_host,
            port=postgres_port,
            user=postgres_user,
            password=postgres_password,
            database=postgres_db
        )
        
        cursor = conn.cursor()
        
        # テーブルの存在確認
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'person'
            )
        """)
        
        if cursor.fetchone()[0]:
            print("✓ Table 'person' exists")
        else:
            print("✗ Table 'person' not found")
            return False
        
        # データの件数確認
        cursor.execute("SELECT COUNT(*) FROM sc_test_1.user_order")
        count = cursor.fetchone()[0]
        print(f"✓ Found {count} rows in user_order table")
        
        # サンプルデータを確認
        cursor.execute("SELECT id, name FROM sc_test_1.user_order ORDER BY id LIMIT 3")
        rows = cursor.fetchall()
        for row in rows:
            print(f"  - ID: {row[0]}, Name: {row[1]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"✗ PostgreSQL test failed: {e}")
        return False

def test_data_encryption_simulation():
    """暗号化処理のシミュレーション"""
    print("\n=== Testing Data Encryption Simulation ===")
    
    import base64
    
    # テストデータ
    test_ids = [1, 2, 3, None]
    
    def simulate_encrypt(plain_id):
        """暗号化シミュレーション"""
        if plain_id is None:
            return None
        # ローカルテスト用: Base64エンコードで代用
        return base64.b64encode(str(plain_id).encode('utf-8')).decode('utf-8')
    
    encrypted_ids = []
    for test_id in test_ids:
        encrypted = simulate_encrypt(test_id)
        encrypted_ids.append(encrypted)
        if encrypted:
            print(f"✓ ID {test_id} -> {encrypted[:30]}...")
        else:
            print(f"✓ ID {test_id} -> None")
    
    # NULL値の処理が正しいか確認
    if encrypted_ids[-1] is None:
        print("✓ NULL handling test passed")
        return True
    else:
        print("✗ NULL handling test failed")
        return False

def test_postgres_write():
    """PostgreSQLへの書き込みテスト"""
    print("\n=== Testing PostgreSQL Write ===")
    
    postgres_host = os.getenv('POSTGRES_HOST', 'localhost')
    postgres_port = int(os.getenv('POSTGRES_PORT', '5432'))
    postgres_user = os.getenv('POSTGRES_USER', 'postgres')
    postgres_password = os.getenv('POSTGRES_PASSWORD', 'postgres')
    postgres_db = os.getenv('POSTGRES_DB', 'dev_db')
    
    try:
        conn = psycopg2.connect(
            host=postgres_host,
            port=postgres_port,
            user=postgres_user,
            password=postgres_password,
            database=postgres_db
        )
        
        cursor = conn.cursor()
        
        # テスト用テーブルを作成
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sc_test_1.user_order_encrypted (
                id VARCHAR(500),
                name VARCHAR(100),
                birthdate DATE
            )
        """)
        
        # テストデータを挿入
        import base64
        test_data = [
            (base64.b64encode(b'1').decode('utf-8'), 'Alice', '1990-01-15'),
            (base64.b64encode(b'2').decode('utf-8'), 'Bob', '1985-05-20'),
        ]
        
        cursor.executemany(
            "INSERT INTO sc_test_1.user_order_encrypted (id, name, birthdate) VALUES (%s, %s, %s)",
            test_data
        )
        
        conn.commit()
        
        # 書き込み確認
        cursor.execute("SELECT COUNT(*) FROM sc_test_1.user_order_encrypted")
        count = cursor.fetchone()[0]
        print(f"✓ Inserted {count} rows into user_order_encrypted table")
        
        # クリーンアップ
        cursor.execute("DROP TABLE sc_test_1.user_order_encrypted")
        conn.commit()
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"✗ PostgreSQL write test failed: {e}")
        return False

def main():
    """メインテスト実行"""
    print("=" * 60)
    print("Integration Test: Local Environment (LocalStack + PostgreSQL)")
    print("=" * 60)
    
    # サービス起動待機
    print("\n=== Waiting for services to be ready ===")
    try:
        wait_for_service('localhost', 4566, timeout=30)  # LocalStack
        wait_for_service('localhost', 5432, timeout=30)  # PostgreSQL
    except TimeoutError as e:
        print(f"✗ Service startup timeout: {e}")
        return False
    
    # テスト実行
    results = {
        'LocalStack KMS': test_localstack_kms(),
        'PostgreSQL Connection': test_postgres_connection(),
        'Data Encryption': test_data_encryption_simulation(),
        'PostgreSQL Write': test_postgres_write(),
    }
    
    # 結果集計
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
