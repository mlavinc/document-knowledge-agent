# Presupuesto mensual de costos con alertas por correo.
#
# Se usan notificaciones directas por email (subscriber_email_addresses)
# en lugar de un tópico SNS intermedio: para un proyecto de portafolio
# con este objetivo (protegerse de costos inesperados) un tópico SNS
# agrega un recurso más sin aportar valor adicional.
resource "aws_budgets_budget" "monthly_cost" {
  name         = var.budget_name
  budget_type  = "COST"
  limit_amount = tostring(var.limit_amount)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  dynamic "notification" {
    for_each = var.actual_alert_thresholds

    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = notification.value
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = var.alert_emails
    }
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = var.forecasted_alert_threshold
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = var.alert_emails
  }
}
