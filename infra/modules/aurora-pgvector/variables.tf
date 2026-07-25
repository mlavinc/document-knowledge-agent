variable "cluster_identifier" {
  description = "Identificador del cluster Aurora."
  type        = string
}

variable "database_name" {
  description = "Nombre de la base de datos inicial."
  type        = string
  default     = "ragagent"
}

variable "engine_version" {
  description = "Versión de Aurora PostgreSQL (debe soportar pgvector y RDS Data API)."
  type        = string
  default     = "16.13"
}

variable "min_capacity" {
  description = "ACUs mínimas de Aurora Serverless v2. 0 permite escalar a cero cuando no hay tráfico (clave para costo casi nulo)."
  type        = number
  default     = 0
}

variable "max_capacity" {
  description = "ACUs máximas de Aurora Serverless v2."
  type        = number
  default     = 1
}
