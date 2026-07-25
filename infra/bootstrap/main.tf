# Bootstrap: backend remoto de Terraform (S3) + protección de costos
# (AWS Budgets) desde el primer despliegue de infraestructura.
#
# Se aplica UNA sola vez, con estado local, antes de que exista cualquier
# otro recurso del proyecto. A partir de aquí, `environments/prod` usa
# el bucket creado aquí como su backend remoto.

data "aws_caller_identity" "current" {}

locals {
  state_bucket_name = coalesce(
    var.state_bucket_name,
    "rag-agent-tfstate-${data.aws_caller_identity.current.account_id}"
  )
}

resource "aws_s3_bucket" "terraform_state" {
  bucket = local.state_bucket_name

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
