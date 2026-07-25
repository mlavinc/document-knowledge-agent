variable "repository_name" {
  description = "Nombre del repositorio ECR."
  type        = string
}

variable "max_image_count" {
  description = "Cantidad máxima de imágenes a conservar (las más antiguas se eliminan automáticamente para minimizar costo de almacenamiento)."
  type        = number
  default     = 5
}
