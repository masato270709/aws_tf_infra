#!/usr/bin/env python
"""
暗号化されたデータをホスト側（Windows）から確認
"""

import psycopg2
import sys

def check_encrypted_data():
    """PostgreSQLから暗号化データを確認"""
    
    try:
        # ホスト側から接続（localhost）
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            user='postgres',
            password='postgres',
            database='db_test_1'
        )
        
        cursor = conn.cursor()
        
        print("=" * 80)
        print("暗号化データの確認 (ホスト側から接続)")
        print("=" * 80)
        
        # 元データを確認
        print("\n【元データ】 sc_test_1.user_order")
        print("-" * 80)
        cursor.execute("""
            SELECT id, name, birthdate 
            FROM sc_test_1.user_order 
            ORDER BY id
        """)
        
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                print(f"  ID: {row[0]}, Name: {row[1]}, Birthdate: {row[2]}")
        else:
            print("  (データなし)")
        
        # 暗号化データを確認
        print("\n【暗号化データ】 sc_test_1.user_order_encrypted")
        print("-" * 80)
        cursor.execute("""
            SELECT encrypted_id, name, birthdate 
            FROM sc_test_1.user_order_encrypted 
            ORDER BY encrypted_id
            LIMIT 10
        """)
        
        rows = cursor.fetchall()
        if rows:
            print(f"合計 {len(rows)} 件のレコード\n")
            for i, row in enumerate(rows, 1):
                encrypted_id = row[0]
                # 長すぎる場合は省略
                display_id = encrypted_id[:50] + "..." if len(encrypted_id) > 50 else encrypted_id
                print(f"  [{i}] encrypted_id: {display_id}")
                print(f"      name: {row[1]}, birthdate: {row[2]}\n")
        else:
            print("  (データなし - テストがまだ実行されていない可能性があります)")
        
        # 統計情報
        print("\n【統計情報】")
        print("-" * 80)
        cursor.execute("SELECT COUNT(*) FROM sc_test_1.user_order_encrypted")
        count = cursor.fetchone()[0]
        print(f"  暗号化テーブルのレコード数: {count}")
        
        cursor.close()
        conn.close()
        
        print("\n✓ データベース接続成功")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"✗ 接続エラー: {e}")
        print("\n  確認事項:")
        print("  1. docker-compose ps で PostgreSQL が Running か確認")
        print("  2. ホスト側から: docker ps で postgres コンテナを確認")
        return False
    except psycopg2.ProgrammingError as e:
        print(f"✗ SQL実行エラー: {e}")
        print("\n  テーブルが存在しないか、スキーマが異なる可能性があります")
        return False
    except Exception as e:
        print(f"✗ エラーが発生しました: {e}")
        return False

if __name__ == '__main__':
    success = check_encrypted_data()
    sys.exit(0 if success else 1)
