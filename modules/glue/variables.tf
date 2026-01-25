# --- IAM関連 ---
variable "glue_role_arn" {
  description = "IAMロールのARN（IAMモジュールから渡される）"
  type        = string
}

# --- S3関連 ---
variable "source_bucket" {
  description = "ソースコードを管理するS3バケット名（S3モジュールから渡される）"
  type        = string
}

variable "temp_bucket" {
  description = "Glueの一時保存用S3バケット名（S3モジュールから渡される）"
  type        = string
}

# --- KMS関連 ---
variable "kms_key_id" {
  description = "ID列の暗号化に使用するKMSキーのIDまたはARN"
  type        = string
}

# --- Redshift関連 ---
variable "redshift_connection_name" {
  description = "AWSコンソール等で作成済みのGlue Connection名"
  type        = string
}

variable "db_schema" {
  description = "読み込み対象のスキーマ名"
  type        = string
  default     = "sc_test_1"
}

variable "db_table" {
  description = "読み込み対象のテーブル名"
  type        = string
  default     = "user_order"
}