output "budget_name" {
  description = "Nombre del presupuesto creado."
  value       = aws_budgets_budget.monthly_cost.name
}

output "budget_arn" {
  description = "ARN del presupuesto creado."
  value       = aws_budgets_budget.monthly_cost.arn
}
