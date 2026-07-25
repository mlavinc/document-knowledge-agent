output "cluster_arn" {
  value = aws_rds_cluster.this.arn
}

output "secret_arn" {
  description = "ARN del secreto en Secrets Manager con las credenciales del master user, generado automáticamente (manage_master_user_password)."
  value       = aws_rds_cluster.this.master_user_secret[0].secret_arn
}

output "database_name" {
  value = aws_rds_cluster.this.database_name
}
