provider "aws" {
  region = "ap-northeast-1"
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # ステート管理用のバケット（手動で作成した名前を入れてください）
  backend "s3" {
    bucket = "dev-tfstate-bucket-20250111 " # ← ここを書き換え
    key    = "dev/terraform.tfstate"
    region = "ap-northeast-1"
  }
}

# S3モジュールの呼び出し
module "dev_s3_bucket" {
  source      = "../../modules/s3"
  bucket_name = "my-glue-project-dev-data-2026" # ← 世界で一意の名前に書き換え
}