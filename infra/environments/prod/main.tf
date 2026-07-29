data "aws_caller_identity" "current" {}

locals {
  account_id           = data.aws_caller_identity.current.account_id
  frontend_bucket      = "rag-agent-frontend-${local.account_id}"
  documents_bucket     = "rag-agent-documents-${local.account_id}"
  rag_core_ecr_name    = "rag-agent-rag-core"
  api_gateway_ecr_name = "rag-agent-api-gateway"
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
data "aws_iam_policy_document" "rag_core_permissions" {
  statement {
    sid       = "BedrockInvoke"
    actions   = ["bedrock:InvokeModel"]
    resources = ["*"]
  }

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
  # 300s (vs. los 30s por defecto del módulo): la ingestión ahora genera
  # embeddings de Bedrock estrictamente secuenciales (sin concurrencia)
  # con pacing mínimo entre llamadas y reintentos exponenciales ante
  # ThrottlingException (hasta 1+2+4+8+16 = 31s de backoff por chunk en
  # el peor caso). Para documentos con muchos chunks, ese margen debe
  # cubrir el pipeline completo, no solo un chunk aislado; 120s se
  # quedaba corto para documentos grandes con throttling sostenido.
  # NOTA: la llamada pública POST /api/documents/ingest sigue acotada
  # por el timeout de api-gateway_lambda (30s) y por el límite fijo de
  # ~29s de integración de API Gateway HTTP API (no configurable). Este
  # cambio evita que rag-core se corte a mitad de los reintentos cuando
  # se invoca directamente vía su Function URL; para destrabar también
  # el flujo público de punta a punta haría falta subir el timeout de
  # api-gateway_lambda (fuera de alcance de este fix puntual).
  timeout                = 300
  additional_policy_json = data.aws_iam_policy_document.rag_core_permissions.json

  environment_variables = {
    LLM_PROVIDER       = "bedrock"
    EMBEDDING_PROVIDER = "bedrock"
    VECTOR_DB_PROVIDER = "pgvector"
    STORAGE_PROVIDER   = "s3"
    # AWS_REGION no se define aquí: es una variable reservada que Lambda
    # inyecta automáticamente en el entorno de ejecución.
    BEDROCK_LLM_MODEL_ID         = var.bedrock_llm_model_id
    BEDROCK_EMBEDDING_MODEL_ID   = var.bedrock_embedding_model_id
    BEDROCK_EMBEDDING_DIMENSIONS = tostring(var.bedrock_embedding_dimensions)
    AURORA_CLUSTER_ARN           = module.aurora.cluster_arn
    AURORA_SECRET_ARN            = module.aurora.secret_arn
    AURORA_DATABASE_NAME         = module.aurora.database_name
    AURORA_TABLE_NAME            = "document_chunks"
    S3_DOCUMENTS_BUCKET          = module.documents_bucket.id
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
    # La ingestión de documentos usa invocación asíncrona nativa de Lambda
    # (InvocationType="Event") en lugar de esperar la respuesta HTTP de
    # rag-core: la generación de embeddings de Bedrock con pacing/retries
    # puede tardar minutos, muy por encima del límite fijo de ~29s de
    # integración de API Gateway HTTP API (no configurable). Con
    # INGESTION_MODE=async, api-gateway dispara rag-core y responde 202 de
    # inmediato; rag-core sigue procesando en su propia invocación Lambda
    # (hasta su propio timeout de 300s), sin infraestructura adicional.
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
