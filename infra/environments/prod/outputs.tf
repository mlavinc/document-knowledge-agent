output "cloudfront_domain_name" {
  description = "Dominio público de la aplicación (frontend + /api/*)."
  value       = "https://${module.cdn.domain_name}"
}

output "rag_core_ecr_repository_url" {
  value = module.rag_core_ecr.repository_url
}

output "api_gateway_ecr_repository_url" {
  value = module.api_gateway_ecr.repository_url
}

output "frontend_bucket_name" {
  value = module.frontend_bucket.id
}

output "documents_bucket_name" {
  value = module.documents_bucket.id
}

output "aurora_cluster_arn" {
  value = module.aurora.cluster_arn
}

output "aurora_secret_arn" {
  value = module.aurora.secret_arn
}

output "rag_core_function_url" {
  value = module.rag_core_lambda.function_url
}

output "api_gateway_endpoint" {
  value = module.http_api.api_endpoint
}
