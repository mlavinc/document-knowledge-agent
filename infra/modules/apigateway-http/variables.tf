variable "api_name" {
  description = "Nombre de la API Gateway HTTP API."
  type        = string
}

variable "lambda_function_name" {
  description = "Nombre de la función Lambda a integrar (proxy)."
  type        = string
}

variable "lambda_invoke_arn" {
  description = "Invoke ARN de la función Lambda."
  type        = string
}

variable "lambda_function_arn" {
  description = "ARN (no invoke) de la función Lambda, para el permiso de invocación."
  type        = string
}
