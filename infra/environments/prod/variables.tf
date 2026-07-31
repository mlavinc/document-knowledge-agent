variable "aws_region" {
  description = "Región de AWS para los recursos de producción."
  type        = string
  default     = "sa-east-1"
}

variable "image_tag" {
  description = "Tag de las imágenes de rag-core y api-gateway en ECR. Debe existir en ECR antes de aplicar (ver README de infra para el flujo de build+push)."
  type        = string
  default     = "latest"
}

variable "openai_api_key_ssm_parameter_name" {
  description = "Nombre del parámetro SSM SecureString con la OpenAI API key. El valor se escribe con AWS CLI, nunca en tfvars."
  type        = string
  default     = "/rag-agent/openai-api-key"
}

variable "openai_llm_model" {
  description = "Modelo OpenAI usado para generación de respuestas."
  type        = string
  default     = "gpt-4.1-mini"
}

variable "openai_embedding_model" {
  description = "Modelo OpenAI usado para embeddings."
  type        = string
  default     = "text-embedding-3-small"
}

variable "openai_embedding_dimensions" {
  description = "Dimensiones del vector de embeddings (text-embedding-3-small default = 1536)."
  type        = number
  default     = 1536
}

variable "frontend_origin" {
  # El frontend de portafolio corre en Vercel (dominio distinto al de la
  # API pública), por lo que el navegador hace peticiones cross-origin y
  # el CORS de Express sí entra en juego aquí.
  description = "Origen(es) CORS en api-gateway: un dominio Vercel, lista separada por comas (demo + portfolio), o \"*\"."
  type        = string
  default     = "*"
}
