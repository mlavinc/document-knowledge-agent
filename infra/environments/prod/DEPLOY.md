# Deploy producción — RAG Agent

## Secretos (OpenAI)

La API key **no** va en `terraform.tfvars` ni como env plaintext de Lambda.

1. Terraform crea el parámetro SSM SecureString `/rag-agent/openai-api-key` (placeholder).
2. Lambda recibe solo `OPENAI_API_KEY_SSM_PARAMETER` (nombre del parámetro).
3. `rag-core` lee el valor en runtime con `ssm:GetParameter` + decrypt.

Escribir / rotar la key:

```bash
aws ssm put-parameter \
  --region sa-east-1 \
  --name "/rag-agent/openai-api-key" \
  --type SecureString \
  --value "sk-..." \
  --overwrite
```

## Terraform

```bash
cd infra/environments\prod
cp terraform.tfvars.example terraform.tfvars   # sin secretos
terraform init -backend-config=backend.hcl
terraform apply
```

`terraform apply` also runs **`null_resource.pgvector_schema_bootstrap`**: a local
Python script that creates the pgvector extension/table/index **once** via the
RDS Data API (idempotent; ignores SQLSTATE 23505 / already-exists).

Schema is **not** created inside Lambda on each search/ingest request.

Manual re-bootstrap (optional):

```bash
cd rag-core
# Set AURORA_* / EMBEDDING_DIMENSIONS from terraform output / Lambda env
python scripts/bootstrap_pgvector_schema.py
```

## Imágenes Lambda (tag `latest` mutable)

Tras `terraform apply`, hay que **forzar** el pull de imagen nueva:

```bash
# rag-core
cd rag-core
aws ecr get-login-password --region sa-east-1 \
  | docker login --username AWS --password-stdin <ACCOUNT>.dkr.ecr.sa-east-1.amazonaws.com
# Usar buildx sin provenance/SBOM: Lambda no acepta manifiestos OCI de BuildKit.
docker buildx build --platform linux/amd64 --provenance=false --sbom=false \
  --target lambda \
  -t <ACCOUNT>.dkr.ecr.sa-east-1.amazonaws.com/rag-agent-rag-core:latest \
  --push .
aws lambda update-function-code --region sa-east-1 \
  --function-name rag-agent-rag-core \
  --image-uri <ACCOUNT>.dkr.ecr.sa-east-1.amazonaws.com/rag-agent-rag-core:latest
aws lambda wait function-updated --region sa-east-1 --function-name rag-agent-rag-core

# api-gateway (mismo patrón)
cd ../api-gateway
docker buildx build --platform linux/amd64 --provenance=false --sbom=false \
  --target lambda \
  -t <ACCOUNT>.dkr.ecr.sa-east-1.amazonaws.com/rag-agent-api-gateway:latest \
  --push .
aws lambda update-function-code --region sa-east-1 \
  --function-name rag-agent-api-gateway \
  --image-uri <ACCOUNT>.dkr.ecr.sa-east-1.amazonaws.com/rag-agent-api-gateway:latest
aws lambda wait function-updated --region sa-east-1 --function-name rag-agent-api-gateway
```


## Providers esperados en prod

| Variable | Valor |
|---|---|
| `LLM_PROVIDER` | `openai` |
| `EMBEDDING_PROVIDER` | `openai` |
| `LLM_MODEL` | `gpt-4.1-mini` |
| `EMBEDDING_MODEL` | `text-embedding-3-small` |
| `OPENAI_API_KEY_SSM_PARAMETER` | `/rag-agent/openai-api-key` |

Sin Bedrock en el flujo RAG.
