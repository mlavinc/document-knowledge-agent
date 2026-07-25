terraform {
  required_version = ">= 1.11"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # bucket, key, region y use_lockfile se completan con
  # -backend-config=backend.hcl en `terraform init`, para no hardcodear
  # valores dependientes del entorno en el código versionado.
  backend "s3" {}
}
