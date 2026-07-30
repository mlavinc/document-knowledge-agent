data "aws_caller_identity" "current" {}

locals {
  account_id           = data.aws_caller_identity.current.account_id
  frontend_bucket      = "rag-agent-frontend-${local.account_id}"
  documents_bucket     = "rag-agent-documents-${local.account_id}"
  rag_core_ecr_name    = "rag-agent-rag-core"
  api_gateway_ecr_name = "rag-agent-api-gateway"
  # OpenAI embedding width (1536). Kept out of the Lambda request path:
  # schema is bootstrapped once via null_resource below.
  aurora_table_name = "document_chunks_openai"
}

# ---------------------------------------------------------------------------
# ECR: repositorios de imágenes para las dos Lambdas basadas en contenedor
# ---------------------------------------------------------------------------
module "rag_core_ecr" {
  source          = "../../modules/ecr-repository"
  repository_name = local.rag_core_ecr_name
}

module "api_gateway_ecr" {
  source          = "../../modules/ecr-repository"
  repository_name = local.api_gateway_ecr_name
}

# ---------------------------------------------------------------------------
# S3: frontend estático + almacenamiento de PDFs
# ---------------------------------------------------------------------------
module "frontend_bucket" {
  source      = "../../modules/s3-bucket"
  bucket_name = local.frontend_bucket
}

module "documents_bucket" {
  source             = "../../modules/s3-bucket"
  bucket_name        = local.documents_bucket
  versioning_enabled = true
}

# ---------------------------------------------------------------------------
# Aurora PostgreSQL Serverless v2 + pgvector (Data API, MinCapacity = 0)
# ---------------------------------------------------------------------------
module "aurora" {
  source             = "../../modules/aurora-pgvector"
  cluster_identifier = "rag-agent-aurora"
  database_name      = "ragagent"
  min_capacity       = 0
  max_capacity       = 1
}

# ---------------------------------------------------------------------------
# IAM: permisos mínimos de cada Lambda, encapsulados fuera del módulo
# genérico lambda-container para mantenerlo reutilizable.
# ---------------------------------------------------------------------------
# OpenAI API key lives in SSM Parameter Store (SecureString). Terraform
# only stores the parameter *name* on the Lambda; the secret value is set
# out-of-band via CLI (see DEPLOY.md) and never enters tfvars / TF state
# as a managed secret after the initial placeholder.
resource "aws_ssm_parameter" "openai_api_key" {
  name        = var.openai_api_key_ssm_parameter_name
  description = "OpenAI API key for rag-core (LLM + embeddings). Set value with aws ssm put-parameter --overwrite."
  type  = "SecureString"
  value = "REPLACE_ME_VIA_AWS_CLI"

  lifecycle {
    ignore_changes = [value]
  }

  tags = {
    Project = "rag-agent"
  }
}

data "aws_iam_policy_document" "rag_core_permissions" {
  statement {
    sid = "AuroraDataApi"
    actions = [
      "rds-data:ExecuteStatement",
      "rds-data:BatchExecuteStatement",
      "rds-data:BeginTransaction",
      "rds-data:CommitTransaction",
      "rds-data:RollbackTransaction",
    ]
    resources = [module.aurora.cluster_arn]
  }

  statement {
    sid       = "AuroraSecret"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = [module.aurora.secret_arn]
  }

  statement {
    sid       = "DocumentsBucketAccess"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${module.documents_bucket.arn}/*"]
  }

  statement {
    sid       = "ReadOpenAIApiKeyFromSsm"
    actions   = ["ssm:GetParameter"]
    resources = [aws_ssm_parameter.openai_api_key.arn]
  }
}

# ---------------------------------------------------------------------------
# Lambda: RAG Core (FastAPI). Solo accesible internamente vía Function
# URL con autenticación IAM (nunca expuesta directamente al público).
# ---------------------------------------------------------------------------
module "rag_core_lambda" {
  source              = "../../modules/lambda-container"
  function_name       = "rag-agent-rag-core"
  image_uri           = "${module.rag_core_ecr.repository_url}:${var.image_tag}"
  create_function_url = true
  memory_size         = 512
  # 300s: ingestión async (InvocationType=Event) puede embeber muchos
  # chunks con OpenAI de forma secuencial; el timeout público de API
  # Gateway (~29s) no aplica a esa invocación de fondo.
  timeout                = 300
  additional_policy_json = data.aws_iam_policy_document.rag_core_permissions.json

  environment_variables = {
    LLM_PROVIDER                   = "openai"
    EMBEDDING_PROVIDER             = "openai"
    VECTOR_DB_PROVIDER             = "pgvector"
    STORAGE_PROVIDER               = "s3"
    LLM_MODEL                      = var.openai_llm_model
    EMBEDDING_MODEL                = var.openai_embedding_model
    EMBEDDING_DIMENSIONS           = tostring(var.openai_embedding_dimensions)
    # Parameter *name* only — secret value is loaded at runtime from SSM.
    OPENAI_API_KEY_SSM_PARAMETER   = aws_ssm_parameter.openai_api_key.name
    # AWS_REGION no se define aquí: es una variable reservada que Lambda
    # inyecta automáticamente en el entorno de ejecución.
    AURORA_CLUSTER_ARN             = module.aurora.cluster_arn
    AURORA_SECRET_ARN              = module.aurora.secret_arn
    AURORA_DATABASE_NAME           = module.aurora.database_name
    AURORA_TABLE_NAME              = local.aurora_table_name
    S3_DOCUMENTS_BUCKET            = module.documents_bucket.id
  }
}

# ---------------------------------------------------------------------------
# One-time (or on-trigger) pgvector schema bootstrap. Runs on the machine
# executing terraform apply — no extra AWS resources / cost. Idempotent:
# safe if the table already exists or two applies race on CREATE EXTENSION.
# ---------------------------------------------------------------------------
resource "null_resource" "pgvector_schema_bootstrap" {
  depends_on = [module.aurora]

  triggers = {
    cluster_arn = module.aurora.cluster_arn
    secret_arn  = module.aurora.secret_arn
    database    = module.aurora.database_name
    table_name  = local.aurora_table_name
    dimensions  = tostring(var.openai_embedding_dimensions)
  }

  provisioner "local-exec" {
    interpreter = ["python"]
    command     = abspath("${path.module}/../../../rag-core/scripts/bootstrap_pgvector_schema.py")

    environment = {
      AWS_REGION           = var.aws_region
      AURORA_CLUSTER_ARN   = module.aurora.cluster_arn
      AURORA_SECRET_ARN    = module.aurora.secret_arn
      AURORA_DATABASE_NAME = module.aurora.database_name
      AURORA_TABLE_NAME    = local.aurora_table_name
      EMBEDDING_DIMENSIONS = tostring(var.openai_embedding_dimensions)
    }
  }
}

# ---------------------------------------------------------------------------
# Lambda: API Gateway (Express). Único componente público (vía HTTP API
# + CloudFront). Invoca rag-core firmando con SigV4 (IAM) su Function URL.
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "api_gateway_permissions" {
  statement {
    sid       = "InvokeRagCoreFunctionUrl"
    actions   = ["lambda:InvokeFunctionUrl", "lambda:InvokeFunction"]
    resources = [module.rag_core_lambda.function_arn]
  }
}

module "api_gateway_lambda" {
  source                 = "../../modules/lambda-container"
  function_name          = "rag-agent-api-gateway"
  image_uri              = "${module.api_gateway_ecr.repository_url}:${var.image_tag}"
  create_function_url    = false
  memory_size            = 256
  timeout                = 30
  additional_policy_json = data.aws_iam_policy_document.api_gateway_permissions.json

  # AWS_REGION no se define aquí: es una variable reservada que Lambda
  # inyecta automáticamente en el entorno de ejecución.
  environment_variables = {
    NODE_ENV           = "production"
    RAG_CORE_URL       = module.rag_core_lambda.function_url
    RAG_CORE_AUTH_MODE = "iam"
    # El frontend de portafolio se despliega en Vercel (origen distinto
    # al de esta API pública), de ahí que CORS_ORIGIN sí se configure en
    # producción -ver variable "frontend_origin".
    CORS_ORIGIN = var.frontend_origin
    # Ingestión async (InvocationType=Event): responde 202 de inmediato y
    # rag-core indexa en segundo plano (hasta su timeout de 300s), por
    # encima del límite ~29s de API Gateway HTTP API.
    INGESTION_MODE         = "async"
    RAG_CORE_FUNCTION_NAME = module.rag_core_lambda.function_name
  }
}

# ---------------------------------------------------------------------------
# API Gateway HTTP API: único punto público de entrada a la Lambda de
# api-gateway (además del frontend, servido directo desde S3).
# ---------------------------------------------------------------------------
# Además del permiso identity-based en el rol de api-gateway_lambda,
# una Function URL con AWS_IAM requiere una política resource-based
# explícita que autorice al invocador (si no, la firma es válida pero
# la invocación se rechaza con 403 Forbidden).
resource "aws_lambda_permission" "allow_api_gateway_invoke_function_url" {
  statement_id           = "AllowApiGatewayInvokeFunctionUrl"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = module.rag_core_lambda.function_name
  principal              = module.api_gateway_lambda.role_arn
  function_url_auth_type = "AWS_IAM"
}

resource "aws_lambda_permission" "allow_api_gateway_invoke_function" {
  statement_id  = "AllowApiGatewayInvokeFunction"
  action        = "lambda:InvokeFunction"
  function_name = module.rag_core_lambda.function_name
  principal     = module.api_gateway_lambda.role_arn
}

module "http_api" {
  source               = "../../modules/apigateway-http"
  api_name             = "rag-agent-api"
  lambda_function_name = module.api_gateway_lambda.function_name
  lambda_function_arn  = module.api_gateway_lambda.function_arn
  lambda_invoke_arn    = module.api_gateway_lambda.invoke_arn
}

# ---------------------------------------------------------------------------
# CloudFront: entrada única (frontend + /api/*), sin CORS en producción.
# ---------------------------------------------------------------------------
module "cdn" {
  source                         = "../../modules/cloudfront-spa"
  name                           = "rag-agent"
  s3_bucket_id                   = module.frontend_bucket.id
  s3_bucket_regional_domain_name = module.frontend_bucket.bucket_regional_domain_name
  api_domain_name                = module.http_api.api_domain
}

# La bucket policy vive en el root (no en los módulos) porque necesita
# combinar outputs de dos módulos distintos (bucket + distribución).
data "aws_iam_policy_document" "frontend_bucket_policy" {
  statement {
    sid       = "AllowCloudFrontOAC"
    actions   = ["s3:GetObject"]
    resources = ["${module.frontend_bucket.arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [module.cdn.distribution_arn]
    }
  }
}

resource "aws_s3_bucket_policy" "frontend" {
  bucket = module.frontend_bucket.id
  policy = data.aws_iam_policy_document.frontend_bucket_policy.json
}
