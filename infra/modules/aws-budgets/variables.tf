variable "budget_name" {
  description = "Nombre del presupuesto de costos de AWS Budgets."
  type        = string
}

variable "limit_amount" {
  description = "Límite mensual de costo, en USD, a partir del cual se disparan alertas."
  type        = number
}

variable "alert_emails" {
  description = "Direcciones de correo que reciben las notificaciones del presupuesto."
  type        = list(string)
}

variable "actual_alert_thresholds" {
  description = "Porcentajes del presupuesto (gasto ACTUAL) en los que se envía una alerta."
  type        = list(number)
  default     = [80, 100]
}

variable "forecasted_alert_threshold" {
  description = "Porcentaje del presupuesto (gasto PROYECTADO) en el que se envía una alerta temprana."
  type        = number
  default     = 100
}
