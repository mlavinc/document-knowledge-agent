variable "aws_region" {
  description = "Región de AWS para los recursos de bootstrap."
  type        = string
  default     = "us-east-1"
}

variable "state_bucket_name" {
  description = "Nombre del bucket S3 para el estado remoto de Terraform. Si se deja como null, se genera automáticamente a partir del Account ID."
  type        = string
  default     = null
}

variable "budget_limit_usd" {
  description = "Límite mensual de costo (USD) que dispara las alertas de AWS Budgets."
  type        = number
  default     = 5
}

variable "budget_alert_email" {
  description = "Correo que recibe las alertas de AWS Budgets."
  type        = string
}
