variable "bucket_name" {
  description = "S3バケットの名前"
  type        = string
}

resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name

  tags = {
    Environment = "dev" # 本来はここも変数にすべきですが、まずは固定で
  }
}

# 意図しない公開を防ぐ設定（実務では必須）
resource "aws_s3_bucket_public_access_block" "this" {
  bucket                  = aws_s3_bucket.this.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}