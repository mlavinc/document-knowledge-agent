variable "bucket_name" {
  description = "Nombre del bucket S3."
  type        = string
}

variable "versioning_enabled" {
  description = "Habilita versionado de objetos."
  type        = bool
  default     = false
}

variable "force_destroy" {
  description = "Permite eliminar el bucket aunque contenga objetos (útil para un proyecto de demo)."
  type        = bool
  default     = true
}

variable "cors_allowed_origins" {
  description = "Orígenes permitidos por CORS (vacío = sin regla CORS). Usado por el bucket de PDFs si se sube directo desde el navegador; no se usa en este proyecto pero queda disponible."
  type        = list(string)
  default     = []
}
