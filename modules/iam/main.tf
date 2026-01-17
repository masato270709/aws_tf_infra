# 1. カスタムポリシーの定義
resource "aws_iam_policy" "glue_redshift_allow_policy" {
  name        = "Glue_Redshift_Allow_Policy"
  description = "Policy for Glue to access Redshift, CloudWatch, and KMS"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "GluePolicy"
        Effect   = "Allow"
        Action   = ["glue:*"]
        Resource = "*"
      },
      {
        Sid    = "RedshiftPolicy"
        Effect = "Allow"
        Action = [
          "redshift-serverless:*",
          "redshift-data:*"
        ]
        Resource = "*"
      },
      {
        Sid      = "logPolicy"
        Effect   = "Allow"
        Action   = ["cloudwatch:*"]
        Resource = "*"
      },
      {
        Sid      = "kmsPolicy"
        Effect   = "Allow"
        Action   = ["kms:*"]
        Resource = "*"
      }
    ]
  })
}

# 2. IAMロールの作成と信頼関係の設定
resource "aws_iam_role" "glue_redshift_role" {
  name = "SR_Glue_Redshift_TF"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = [
            "redshift-serverless.amazonaws.com",
            "redshift.amazonaws.com",
            "glue.amazonaws.com"
          ]
        }
      }
    ]
  })
}

# 3. AWS管理ポリシー (AmazonS3FullAccess) のアタッチ
resource "aws_iam_role_policy_attachment" "s3_full_access" {
  role       = aws_iam_role.glue_redshift_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# 4. 作成したカスタムポリシーのアタッチ
resource "aws_iam_role_policy_attachment" "custom_policy_attach" {
  role       = aws_iam_role.glue_redshift_role.name
  policy_arn = aws_iam_policy.glue_redshift_allow_policy.arn
}

# 後続のGlueジョブ等で利用するために、ロールのARNを出力に設定しておく
output "role_arn" {
  value = aws_iam_role.glue_redshift_role.arn
}