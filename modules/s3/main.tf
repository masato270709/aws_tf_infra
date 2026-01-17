# --- 1. ソース管理用バケット ---
resource "aws_s3_bucket" "source_bucket" {
  bucket = "my-project-apps-source-bucket"
  tags = {
    Environment = "dev"
    Role        = "source-assets"
  }
}

# 既存の設定（パブリックアクセスブロック）を適用
resource "aws_s3_bucket_public_access_block" "source_bucket_block" {
  bucket                  = aws_s3_bucket.source_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 暗号化設定
resource "aws_s3_bucket_server_side_encryption_configuration" "source_crypto" {
  bucket = aws_s3_bucket.source_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# --- 2. Glue一時ファイル用バケット ---
resource "aws_s3_bucket" "glue_temp_bucket" {
  bucket = "my-project-glue-temp-bucket"
  tags = {
    Environment = "dev"
    Role        = "glue-temp"
  }
}

# 一時バケットにもパブリックアクセスブロックを適用
resource "aws_s3_bucket_public_access_block" "temp_bucket_block" {
  bucket                  = aws_s3_bucket.glue_temp_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 暗号化設定
resource "aws_s3_bucket_server_side_encryption_configuration" "temp_crypto" {
  bucket = aws_s3_bucket.glue_temp_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# --- 出力 (他モジュール用) ---
output "source_bucket_id" {
  value = aws_s3_bucket.source_bucket.id
}

output "temp_bucket_id" {
  value = aws_s3_bucket.glue_temp_bucket.id
}