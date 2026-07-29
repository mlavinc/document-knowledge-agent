variable "aws_region" {
  # sa-east-1 (São Paulo): amazon.nova-micro-v1:0 no está disponible ahí,
  # de ahí el cambio de bedrock_llm_model_id más abajo. Aurora PostgreSQL
  # Serverless v2 (16.13) y Titan Text Embeddings V2 sí están disponibles
  # en esta región.
  description = "Región de AWS para los recursos de producción."
  type        = string
  default     = "sa-east-1"
}

variable "image_tag" {
  description = "Tag de las imágenes de rag-core y api-gateway en ECR. Debe existir en ECR antes de aplicar (ver README de infra para el flujo de build+push)."
  type        = string
  default     = "latest"
}

variable "bedrock_llm_model_id" {
  # amazon.nova-micro-v1:0 (usado en us-east-1) no está disponible en
  # sa-east-1. mistral.mistral-7b-instruct-v0:2 es el equivalente más
  # cercano disponible ahí en el mismo nivel de costo/tamaño, y usa la
  # misma Converse API sin cambios de código (bedrock_client.py es
  # agnóstico al modelo). Los modelos de Anthropic (Claude) requieren
  # además un formulario de "use case details" aparte antes de poder
  # invocarse, por lo que se evitan aquí a propósito.
  description = "Modelo de Bedrock usado para generación de respuestas."
  type        = string
  default     = "mistral.mistral-7b-instruct-v0:2"
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

variable "frontend_origin" {
  # El frontend de portafolio corre en Vercel (dominio distinto al de la
  # API pública), por lo que el navegador hace peticiones cross-origin y
  # el CORS de Express sí entra en juego aquí (a diferencia del frontend
  # servido desde el mismo CloudFront, que es same-origin). "*" es
  # razonable para esta demo pública de solo lectura/ingestión sin
  # autenticación; se puede acotar al dominio exacto de Vercel si se
  # prefiere.
  description = "Origen permitido por CORS en api-gateway (dominio del frontend en Vercel, o \"*\")."
  type        = string
  default     = "*"
}
