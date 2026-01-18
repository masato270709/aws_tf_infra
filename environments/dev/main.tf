# 環境名を指定
locals {
  env = "dev"
}

terraform {
  required_version = ">= 1.0.0"

  backend "s3" {
    bucket = "dev-tfstate-bucket-20250111" # 以前作成したState保存用バケット名
    key    = "dev/terraform.tfstate"
    region = "ap-northeast-1"
  }
}


# S3モジュールの呼び出し
module "dev_s3_bucket" {
  source = "../../modules/s3"

  # 変数名をモジュール側に合わせる
  source_bucket_name = "my-glue-project-dev-data"
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

# kmsモジュール呼び出し
module "dev_kms" {
  source        = "../../modules/kms"
  env           = local.env
  glue_role_arn = module.dev_iam.role_arn # IAMモジュールの出力を渡す
}