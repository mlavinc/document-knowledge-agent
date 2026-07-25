provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "rag-agent"
      ManagedBy   = "terraform"
      Environment = "prod"
    }
  }
}
