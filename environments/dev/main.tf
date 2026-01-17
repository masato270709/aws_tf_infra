# S3モジュールの呼び出し
module "dev_s3_bucket" {
  source = "../../modules/s3"

  # 変数名をモジュール側に合わせる
  source_bucket_name = "my-glue-project-dev-data-2026"
  temp_bucket_name   = "my-project-glue-temp-bucket"
}

# IAMモジュールの呼び出し
module "dev_iam" {
  source = "../../modules/iam"
}

# Glueモジュールの呼び出し
module "dev_glue" {
  source = "../../modules/glue"

  # S3モジュールの出力をGlueに渡す
  source_bucket = module.dev_s3_bucket.source_bucket_id
  temp_bucket   = module.dev_s3_bucket.temp_bucket_id

  # IAMの出力をGlueに渡す
  glue_role_arn = module.dev_iam.role_arn

  # KMSや接続名はご自身の環境に合わせて指定
  kms_key_id               = "arn:aws:kms:ap-northeast-1:xxx:key/xxx"
  redshift_connection_name = "your-redshift-connection"
}

###一時追加
# --- IAMロールのインポート (これが必要です) ---
import {
  to = module.dev_iam.aws_iam_role.glue_redshift_role
  id = "SR_Glue_Redshift_TF"
}

# --- IAMポリシーのインポート ---
import {
  to = module.dev_iam.aws_iam_policy.glue_redshift_allow_policy
  id = "arn:aws:iam::910520206137:policy/Glue_Redshift_Allow_Policy"
}

# --- ソース用S3バケットのインポート ---
import {
  to = module.dev_s3_bucket.aws_s3_bucket.source_bucket
  id = "my-glue-project-dev-data-2026"
}

# --- 一時用S3バケットのインポート ---
import {
  to = module.dev_s3_bucket.aws_s3_bucket.glue_temp_bucket
  id = "my-project-glue-temp-bucket"
}