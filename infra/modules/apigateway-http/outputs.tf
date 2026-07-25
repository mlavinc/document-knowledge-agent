output "api_endpoint" {
  value = aws_apigatewayv2_api.this.api_endpoint
}

output "api_domain" {
  description = "Dominio (sin protocolo) de la API, usable como origin de CloudFront."
  value       = replace(aws_apigatewayv2_api.this.api_endpoint, "https://", "")
}

output "api_id" {
  value = aws_apigatewayv2_api.this.id
}
