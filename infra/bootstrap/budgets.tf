# Presupuesto de costos aplicado desde el inicio de la infraestructura,
# antes de crear ningún recurso facturable del proyecto en sí.
module "aws_budgets" {
  source = "../modules/aws-budgets"

  budget_name  = "rag-agent-monthly-cost"
  limit_amount = var.budget_limit_usd
  alert_emails = [var.budget_alert_email]
}
