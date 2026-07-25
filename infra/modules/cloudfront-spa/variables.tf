variable "name" {
  description = "Nombre/etiqueta descriptiva de la distribución."
  type        = string
}

variable "s3_bucket_id" {
  description = "ID del bucket S3 que sirve el frontend."
  type        = string
}

variable "s3_bucket_regional_domain_name" {
  description = "Dominio regional del bucket S3 (origen de CloudFront)."
  type        = string
}

variable "api_domain_name" {
  description = "Dominio (sin protocolo) de la API Gateway HTTP API a la que se enrutan las rutas /api/*."
  type        = string
}
