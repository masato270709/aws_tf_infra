# --- 1. ソース管理用バケット ---
resource "aws_s3_bucket" "source_bucket" {
  # 固定値ではなく変数を使う
  bucket = var.source_bucket_name

  tags = {
    Environment = "dev"
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
  bucket = var.temp_bucket_name
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

moved {
  from = aws_s3_bucket.this
  to   = aws_s3_bucket.source_bucket
}