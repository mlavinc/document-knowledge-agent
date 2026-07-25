variable "aws_region" {
  description = "Región de AWS para los recursos de producción."
  type        = string
  default     = "us-east-1"
}

variable "image_tag" {
  description = "Tag de las imágenes de rag-core y api-gateway en ECR. Debe existir en ECR antes de aplicar (ver README de infra para el flujo de build+push)."
  type        = string
  default     = "latest"
}

variable "bedrock_llm_model_id" {
  description = "Modelo de Bedrock usado para generación de respuestas."
  type        = string
  default     = "amazon.nova-micro-v1:0"
}

variable "bedrock_embedding_model_id" {
  description = "Modelo de Bedrock usado para embeddings."
  type        = string
  default     = "amazon.titan-embed-text-v2:0"
}

variable "bedrock_embedding_dimensions" {
  description = "Dimensiones del vector de embeddings de Bedrock Titan v2."
  type        = number
  default     = 1024
}
