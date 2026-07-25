output "state_bucket_name" {
  description = "Nombre del bucket S3 que almacena el estado remoto de Terraform."
  value       = aws_s3_bucket.terraform_state.id
}

output "state_bucket_arn" {
  description = "ARN del bucket S3 de estado remoto."
  value       = aws_s3_bucket.terraform_state.arn
}

output "budget_name" {
  description = "Nombre del presupuesto de AWS Budgets creado."
  value       = module.aws_budgets.budget_name
}
