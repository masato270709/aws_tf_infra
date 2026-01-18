# KMSキーの定義
resource "aws_kms_key" "glue_key" {
  description              = "KMS key for Glue Redshift ID encryption"
  is_enabled               = true              # 暗号化後の値が都度変わってしまうと不整合が起きてしまうため。
  customer_master_key_spec = SYMMETRIC_DEFAULT # AES256を宣言
  enable_key_rotation      = false             # 後述の理由により有効を推奨

  # キーポリシー（Glueロールに権限を付与）
  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "glue-key-policy"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow Glue Service Role to use the key"
        Effect = "Allow"
        Principal = {
          AWS = var.glue_role_arn
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:ReEncrypt*",
          "kms:GenerateDataKey*",
          "kms:DescribeKey"
        ]
        Resource = "*"
      }
    ]
  })
}

# キーのエイリアス（人間が分かりやすい名前を付ける）
resource "aws_kms_alias" "glue_key_alias" {
  name          = "alias/glue-redshift-encryption-key-${var.env}"
  target_key_id = aws_kms_key.glue_key.key_id
}

# 自分のアカウントIDを取得するためのデータソース
data "aws_caller_identity" "current" {}