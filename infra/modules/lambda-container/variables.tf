variable "function_name" {
  description = "Nombre de la función Lambda."
  type        = string
}

variable "image_uri" {
  description = "URI completa de la imagen de contenedor en ECR (repo:tag)."
  type        = string
}

variable "memory_size" {
  description = "Memoria asignada, en MB."
  type        = number
  default     = 512
}

variable "timeout" {
  description = "Timeout, en segundos."
  type        = number
  default     = 30
}

variable "environment_variables" {
  description = "Variables de entorno para la función."
  type        = map(string)
  default     = {}
}

variable "create_function_url" {
  description = "Crea una Function URL con autenticación IAM (para invocación interna entre Lambdas, p. ej. api-gateway -> rag-core)."
  type        = bool
  default     = false
}

variable "additional_policy_json" {
  description = "Documento de política IAM adicional (JSON) a adjuntar al rol de ejecución, además de logging básico."
  type        = string
}

variable "log_retention_days" {
  description = "Días de retención de logs en CloudWatch (para minimizar costo de almacenamiento)."
  type        = number
  default     = 14
}
