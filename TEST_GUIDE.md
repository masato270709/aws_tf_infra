# ローカル環境テスト実行ガイド

セキュリティ条件下（AWS環境にアクセスできない）でのテスト実行方法です。

## セットアップ

### 1. Docker Compose で環境を起動

```bash
# ワークスペースのルートディレクトリで実行
docker-compose up -d
```

これにより以下が起動します：
- **LocalStack**: KMS、S3をエミュレート
- **PostgreSQL**: Redshiftの代替（RedshiftはPostgreSQL互換）
  - Database: `db_test_1`
  - Schema: `sc_test_1`
  - Table: `user_order`
- **Glue Dev環境**: PySpark + Glueライブラリ

### 2. テストのセットアップ確認

```bash
# コンテナ内でテストを実行
docker-compose exec glue-dev bash

# PostgreSQLの接続確認
psql -h postgres -U postgres -d db_test_1 -c "SELECT * FROM sc_test_1.user_order;"
```

## テスト実行方法

### ユニットテストの実行

```bash
docker-compose exec glue-dev python -m pytest test/test_redshift_encryption.py -v
```

### 統合テストの実行

```bash
# LocalStack環境でのテスト実行
docker-compose exec glue-dev python test/test_integration.py
```

### Glueジョブの実行

```bash
# ローカルモード（LocalStack + PostgreSQL）での実行
docker-compose exec glue-dev spark-submit \
    --master local[2] \
    src/redshift_encryption.py \
    --JOB_NAME test_job \
    --KMS_KEY_ID alias/aws/s3 \
    --REDSHIFT_CONNECTION_NAME local \
    --TEMP_S3_DIR s3://local-bucket/temp/ \
    --DB_SCHEMA sc_test_1 \
    --DB_TABLE user_order
```

## 環境変数

ローカル環境での実行時、以下の環境変数が自動設定されます：

| 変数名 | 説明 | ローカル値 |
|--------|------|----------|
| `LOCALSTACK_ENDPOINT` | LocalStackのエンドポイント | http://localstack:4566 |
| `POSTGRES_HOST` | PostgreSQLホスト | postgres |
| `POSTGRES_PORT` | PostgreSQLポート | 5432 |
| `POSTGRES_DB` | データベース名 | db_test_1 |
| `POSTGRES_USER` | ユーザー名 | postgres |
| `POSTGRES_PASSWORD` | パスワード | postgres |
| `DB_SCHEMA` | スキーマ名 | sc_test_1 |
| `DB_TABLE` | テーブル名 | user_order |

## テスト中のデータベース確認

```bash
# PostgreSQLに接続
docker-compose exec postgres psql -U postgres -d db_test_1

# テーブルの内容を確認
SELECT * FROM sc_test_1.user_order;

# スキーマ/テーブル情報を確認
\dn sc_test_1
\dt sc_test_1.*
```

## LocalStackでのKMS操作

```bash
# KMSキーの作成（オプション）
docker-compose exec localstack awslocal kms create-key --region ap-northeast-1

# キーのリスト確認
docker-compose exec localstack awslocal kms list-keys --region ap-northeast-1
```

## トラブルシューティング

### PostgreSQLの接続エラー
```bash
# コンテナのログを確認
docker-compose logs postgres

# 接続テスト
docker-compose exec postgres pg_isready -U postgres
```

### LocalStackの接続エラー
```bash
# LocalStackのログを確認
docker-compose logs localstack

# ヘルスチェック
curl http://localhost:4566/_localstack/health
```

### テスト実行エラー
```bash
# Python依存パッケージを再インストール
docker-compose exec glue-dev pip install -r requirements.txt

# テストのログレベルを上げる
docker-compose exec glue-dev python -m pytest test/test_redshift_encryption.py -v -s
```

## クリーンアップ

```bash
# コンテナを停止
docker-compose down

# ボリュームも削除（データをリセット）
docker-compose down -v
```

## 本番環境への移行

コード上で `IS_LOCAL` フラグで環境を判定しているため、本番環境では：
1. `LOCALSTACK_ENDPOINT` 環境変数を設定しない
2. Glue Connectionを正しく設定
3. KMS_KEY_IDを実際のキーARNに変更
4. Redshiftの接続情報を設定

で自動的にAWS環境に接続されます。
