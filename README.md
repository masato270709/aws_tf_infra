# AWS Glue 5.0 Local Development & Terraform Project

AWS Glue 5.0 のジョブ開発をローカル環境（VS Code Dev Containers）で行い、実行に必要なインフラ（IAM, S3, Glue Job）を Terraform で管理・デプロイするためのテンプレートリポジトリです。

---

## 1. プロジェクト構造

リポジトリ内の主要なディレクトリとファイルの役割は以下の通りです。

```text
.
├── .devcontainer/
│   └── devcontainer.json    # Glue 5.0 ローカル開発環境の定義
├── environments/
│   └── dev/
│       └── main.tf          # 開発環境用のルート設定（モジュールの結合）
├── modules/                 # 再利用可能なインフラ定義（部品）
│   ├── glue/                # Glue Job, Variables の定義
│   ├── iam/                 # Service Role, カスタムポリシーの定義
│   └── s3/                  # ソース資材用・一時ファイル用バケットの定義
├── src/
│   └── glue_jobs/           # Glue 処理本編 (Python/PySpark)
│       └── redshift_encryption.py
└── README.md

