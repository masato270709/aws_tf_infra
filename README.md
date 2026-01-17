AWS Glue 5.0 Local Development & Terraform Project
このプロジェクトは、AWS Glue 5.0 のジョブ開発をローカル環境（VS Code Dev Containers）で行い、実行に必要なインフラ（IAM, S3, Glue Job）を Terraform で管理・デプロイするためのテンプレートです。

プロジェクト構造
Plaintext

.
├── .devcontainer/
│   └── devcontainer.json    # Glue 5.0 ローカル開発環境の定義
├── environments/
│   └── dev/
│       └── main.tf          # 開発環境用のルート設定（モジュールの結合）
├── modules/                 # 再利用可能なインフラ定義
│   ├── glue/                # Glue Job, Variables
│   ├── iam/                 # Service Role, Policies
│   └── s3/                  # Source & Temp Buckets
├── src/
│   └── glue_jobs/           # Glue 処理本編 (Python)
│       └── redshift_encryption.py
└── README.md
1. ローカル開発環境のセットアップ
前提条件
Docker Desktop

VS Code

VS Code Extension: Dev Containers

起動手順
VS Code で本プロジェクトを開く。

左下の緑色のアイコン（または Ctrl+Shift+P -> Dev Containers: Reopen in Container）をクリック。

コンテナ起動後、ターミナルで以下を確認。

python3 --version -> 3.11.x

pyspark --version -> 3.5.x

2. インフラ構成 (Terraform)
本プロジェクトでは以下のリソースをモジュール化して管理しています。

構成図
モジュール詳細
S3 (modules/s3):

source_bucket: Glue スクリプトや Lambda 資材の格納用。

temp_bucket: Glue の一時ファイル・ログ出力用。

IAM (modules/iam):

SR_Glue_Redshift_TF: Glue が S3, Redshift, CloudWatch, KMS にアクセスするためのサービスロール。

Glue (modules/glue):

Glue 5.0 ジョブの定義。KMS キー ID や Redshift 接続名を引数として受け取ります。

3. 開発フロー
運用ルール
main ブランチ: 保護ブランチ。直接の Push は禁止。

feature ブランチ: 作業ごとに feature/xxx ブランチを作成し、Pull Request を経由してマージします。

手順
ブランチ作成: git checkout -b feature/your-update

インフラ変更: environments/dev/ で修正を行い、GitHub Actions で terraform plan を確認。

コード修正: src/glue_jobs/ 配下の Python スクリプトを編集。

デプロイ: マージ後、GitHub Actions により S3 へスクリプトが同期され、Terraform が実行されます。

4. Glue ジョブ仕様 (Redshift Encryption)
処理概要
Redshift Serverless から person テーブルをロード。

id 列（DECIMAL型）を AWS KMS を使用して暗号化（Base64文字列化）。

加工後のデータを person_encrypted テーブルへ書き出し。

主要な引数 (Default Arguments)
--KMS_KEY_ID: 暗号化に使用するキーの ARN。

--REDSHIFT_CONNECTION_NAME: AWS 上で設定済みの接続名。

5. トラブルシューティング
S3 バケット名変更時の衝突
リソース名を this から変更した際に BucketAlreadyOwnedByYou エラーが出た場合は、modules/s3/main.tf 内の moved ブロックを使用してステートを移行してください。

Terraform

moved {
  from = aws_s3_bucket.this
  to   = aws_s3_bucket.source_bucket
}