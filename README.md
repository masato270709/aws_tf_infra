# AWS Glue 5.0 Local Development & Terraform Project

AWS Glue 5.0 を使用して Redshift/PostgreSQL の ID カラムを KMS キーで暗号化するジョブを開発・テストするプロジェクトです。VS Code Dev Containers とローカル Docker 環境でのテスト、Terraform によるインフラストラクチャ管理に対応しています。

---

## 1. プロジェクト構造

```
.
├── .devcontainer/
│   ├── Dockerfile           # Glue 5.0 開発環境のコンテナイメージ定義
│   └── devcontainer.json    # VS Code DevContainer 設定（docker-compose.yml 参照）
│
├── .github/                 # GitHub 関連の設定（CI/CD など）
│
├── docker-compose.yml       # ローカル開発環境のオーケストレーション
│                             # - LocalStack（KMS, S3 エミュレーション）
│                             # - PostgreSQL 15（Redshift の代替）
│                             # - Glue-dev（Glue 開発環境コンテナ）
│
├── environments/
│   └── dev/
│       └── main.tf          # 開発環境の Terraform ルート設定
│                             # (モジュール呼び出しとリソース定義)
│
├── modules/                 # 再利用可能な Terraform モジュール
│   ├── glue/                # AWS Glue Job の定義
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── iam/                 # IAM Role とポリシーの定義
│   │   └── main.tf
│   ├── kms/                 # AWS KMS キーの定義
│   │   └── main.tf
│   └── s3/                  # S3 バケットの定義
│       └── main.tf
│
├── src/
│   └── redshift_encryption.py  # メイン Glue ジョブスクリプト
│                                 # - KMS で生成したデータキーで AES256 暗号化
│                                 # - LocalStack/AWS の環境検出
│                                 # - PostgreSQL/Redshift への読み書き対応
│
├── test/
│   ├── init_db.sql             # PostgreSQL 初期化スクリプト
│   │                             # - sc_test_1 スキーマ作成
│   │                             # - user_order（元データ）テーブル
│   │                             # - user_order_encrypted（暗号化済み）テーブル
│   │                             # - サンプルデータ挿入
│   │
│   ├── test_redshift_encryption.py   # 単体テスト
│   │   └── 暗号化関数、NULL処理などの検証
│   │
│   └── test_integration.py      # 統合テスト
│       └── LocalStack KMS, PostgreSQL との連携確認
│
├── requirements.txt         # Python 依存パッケージ
│   └── boto3, psycopg2, pytest, pandas, pyarrow, jupyter 等
│
├── TEST_GUIDE.md            # テスト実行ガイド（詳細）
├── README.md                # このファイル
└── .git/                    # Git リポジトリ

```

---

## 2. 技術スタック

| 項目 | 技術 |
|------|------|
| **ETL エンジン** | AWS Glue 5.0 (PySpark) |
| **暗号化** | AWS KMS + AES256-CBC |
| **データベース** | AWS Redshift / PostgreSQL 15 |
| **ローカルテスト** | LocalStack, Docker Compose |
| **開発環境** | VS Code Dev Containers |
| **インフラストラクチャ** | Terraform |
| **Python** | 3.11 |

---

## 3. 機能概要

### 3.1 Glue ジョブの処理フロー

```
user_order (元テーブル)
    ↓
[Step 1] データロード
    - ローカル環境：PostgreSQL から読み込み
    - AWS環境：Redshift から読み込み
    ↓
[Step 2] ID カラムの暗号化
    - KMS で AES256 データキーを生成
    - AES256-CBC で ID を暗号化
    - encrypted_id カラムに格納
    ↓
[Step 3] 暗号化済みデータ書き込み
    - ローカル環境：PostgreSQL に overwrite
    - AWS環境：Redshift に truncate → insert
    ↓
user_order_encrypted (暗号化済みテーブル)
```

### 3.2 環境検出メカニズム

```python
IS_LOCAL = os.getenv('LOCALSTACK_ENDPOINT') is not None
```

環境変数 `LOCALSTACK_ENDPOINT` が存在するかで、ローカル/AWS 環境を自動判別：

- **ローカル環境（docker-compose）**
  - KMS: `http://localstack:4566` に接続
  - DB: PostgreSQL に直接接続
  - エラー時のフォールバック：Base64 エンコード

- **AWS 環境**
  - KMS: AWS KMS サービスに接続
  - DB: Glue Connection 経由で Redshift に接続
  - エラーは即座に報告

---

## 4. セットアップ

### 4.1 前提条件

- Docker & Docker Compose がインストール済み
- VS Code + Dev Containers 拡張機能
- Terraform （AWS へのデプロイ時）
- AWS CLI （AWS へのデプロイ時）

### 4.2 ローカル環境のセットアップ

#### Step 1: リポジトリのクローン

```bash
git clone <repository-url>
cd aws_tf_infra
```

#### Step 2: Dev Container を開く

VS Code で このフォルダを開き、コマンドパレット（Ctrl+Shift+P）から：

```
Dev Containers: Reopen in Container
```

#### Step 3: Docker Compose 起動

```bash
docker-compose up -d
```

コンテナの起動確認：

```bash
docker-compose ps
```

出力例：
```
NAME                    STATUS
localstack              Up (healthy)
postgres                Up (healthy)
glue-dev                Up
```

---

## 5. テスト実行

### 5.1 単体テスト

```bash
docker-compose exec glue-dev python -m pytest test/test_redshift_encryption.py -v
```

### 5.2 統合テスト

```bash
docker-compose exec glue-dev python -m pytest test/test_integration.py -v
```

### 5.3 全テスト実行

```bash
docker-compose exec glue-dev python -m pytest test/ -v
```

### 5.4 カバレッジ付きテスト

```bash
docker-compose exec glue-dev python -m pytest test/ -v --cov=src
```

---

## 6. Glue ジョブの実行

### 6.1 ローカル環境でのテスト実行

```bash
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

### 6.2 データ確認（ローカル）

```bash
docker-compose exec postgres psql -U postgres -d dev_db -c \
    "SELECT COUNT(*) FROM sc_test_1.user_order_encrypted;"
```

---

## 7. AWS へのデプロイ

### 7.1 Terraform 初期化

```bash
cd environments/dev
terraform init
```

### 7.2 リソースの確認

```bash
terraform plan
```

### 7.3 リソースの作成

```bash
terraform apply
```

デプロイ時に必要な設定：

- **AWS Redshift Cluster**：事前に作成が必要
- **Glue Connection**：Redshift への接続設定
- **KMS キー**：暗号化用キーの ARN
- **S3 バケット**：Glue ジョブスクリプトと一時ディレクトリ用

---

## 8. トラブルシューティング

### 8.1 Docker コンテナが起動しない

```bash
docker-compose logs glue-dev
```

### 8.2 PostgreSQL への接続エラー

```bash
docker-compose exec postgres psql -U postgres -d dev_db
```

### 8.3 KMS キーが見つからない

```bash
docker-compose exec glue-dev aws kms list-keys --endpoint-url http://localstack:4566
```

### 8.4 テスト失敗時のログ確認

```bash
docker-compose exec glue-dev python -m pytest test/ -v --tb=long
```

---

## 9. その他のドキュメント

- [TEST_GUIDE.md](TEST_GUIDE.md) - 詳細なテスト実行ガイド
- [modules/glue](modules/glue) - Glue モジュールの変数設定
- [modules/iam](modules/iam) - IAM ポリシーの詳細

---

## 10. ライセンス

このプロジェクトはMITライセンスの下で提供されています。
