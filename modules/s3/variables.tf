# modules/s3/variables.tf

variable "source_bucket_name" {
  description = "コード資材を置くバケット名"
}

variable "temp_bucket_name" {
  description = "Glueの一時ファイル用バケット名"
}