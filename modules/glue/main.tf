resource "aws_glue_job" "redshift_encrypt_job" {
  name              = "redshift-id-encryption-job"
  role_arn          = var.glue_role_arn
  glue_version      = "5.0"
  worker_type       = "G.1X"
  number_of_workers = 2

  command {
    # 汎用ソースバケット内の特定のパスを指定
    script_location = "s3://${var.source_bucket}/glue/scripts/redshift_encryption.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"             = "python"
    "--KMS_KEY_ID"               = var.kms_key_id
    "--REDSHIFT_CONNECTION_NAME" = var.redshift_connection_name
    "--TEMP_S3_DIR"              = "s3://${var.temp_bucket}/temp/"
    "--DB_SCHEMA"                = var.db_schema
    "--DB_TABLE"                 = var.db_table
    # ログ出力設定
    "--enable-continuous-cloudwatch-log" = "true"
    "--job-bookmark-option"              = "job-bookmark-disable"
  }
}