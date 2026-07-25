# RAG Agent

**Ask questions about your PDFs, in natural language, backed by a retrieval-augmented generation pipeline you fully own and control.**

Upload a paper or document, and the system chunks it, embeds it, indexes it in a vector store, and lets you have a grounded conversation with it — every answer comes with the exact source passages it was built from.

The project is built as a **dual-mode system**: the exact same application code runs entirely offline on your laptop (Docker Compose + Ollama + ChromaDB, zero cloud dependency) *or* on a real, serverless, pay-per-use AWS deployment (Bedrock + Aurora Serverless v2/pgvector + S3 + Lambda + CloudFront) — selected purely through environment variables and Terraform, with no forks and no duplicated business logic.

<p align="center">
  <img alt="React" src="https://img.shields.io/badge/Frontend-React%2018%20%2B%20TypeScript-61DAFB?logo=react&logoColor=white&labelColor=20232a">
  <img alt="Express" src="https://img.shields.io/badge/API%20Gateway-Node.js%20%2B%20Express%205-339933?logo=node.js&logoColor=white&labelColor=20232a">
  <img alt="FastAPI" src="https://img.shields.io/badge/RAG%20Core-Python%20%2B%20FastAPI-009688?logo=fastapi&logoColor=white&labelColor=20232a">
  <img alt="Terraform" src="https://img.shields.io/badge/IaC-Terraform-7B42BC?logo=terraform&logoColor=white&labelColor=20232a">
  <img alt="AWS" src="https://img.shields.io/badge/Cloud-AWS%20Serverless-FF9900?logo=amazonaws&logoColor=white&labelColor=20232a">
</p>

---

## Table of contents

- [Why this project exists](#why-this-project-exists)
- [Architecture](#architecture)
- [Features](#features)
- [Tech stack](#tech-stack)
- [Repository layout](#repository-layout)
- [Quick start (local, offline)](#quick-start-local-offline)
- [Environment variables](#environment-variables)
- [API reference](#api-reference)
- [Testing](#testing)
- [AWS deployment](#aws-deployment)
- [Cost model — will this cost me anything?](#cost-model--will-this-cost-me-anything)
- [Known limitations & roadmap](#known-limitations--roadmap)
- [License](#license)

---

## Why this project exists

Most personal RAG projects stop at "it works on my machine." This one is built as a small, honest showcase of **production-minded engineering**:

- A **decoupled, three-tier architecture** (React → Express API Gateway → FastAPI RAG Core) that mirrors what you'd actually find guarding a real backend, instead of calling the LLM straight from the browser.
- A **provider abstraction layer** so the exact same RAG pipeline code can run against Ollama/ChromaDB locally or Bedrock/Aurora in the cloud — no `if AWS` branches sprinkled through business logic.
- **100% of the AWS infrastructure defined as Terraform**, module by module, with a remote state backend and a budget guardrail created *before* anything billable.
- A serverless deployment that is deliberately **not over-engineered**: no EC2, no ECS/Fargate, no NAT Gateway, no ALB, no VPC-bound Lambdas — because none of those are needed to serve a low-traffic public demo well.

## Architecture

### Request flow (identical in both modes)

```
┌───────────┐      ┌──────────────────────┐      ┌───────────────────┐
│  React    │ ───► │  API Gateway         │ ───► │  RAG Core         │
│  (Vite)   │      │  Node.js + Express   │      │  Python + FastAPI │
└───────────┘      └──────────────────────┘      └───────────────────┘
                    validates, proxies,            chunking · embeddings
                    never contains RAG logic        vector search · LLM
```

The API Gateway **never** talks to the LLM or the vector store directly — it only validates and forwards. All retrieval-augmented-generation logic (chunking, embeddings, similarity search, prompting) lives exclusively in the RAG Core service.

### Local development mode

```
React (Vite)  →  Express (Docker)  →  FastAPI (Docker)  →  Ollama (LLM + embeddings)
                                                          →  ChromaDB (vector store)
                                                          →  local filesystem (PDFs)
```

Fully offline. No AWS account, no API keys, no cost — just Docker.

### AWS production mode

```
                 ┌─────────────────────────── CloudFront (single public entry point) ───────────────────────────┐
                 │                                                                                                │
  Browser  ──►   │  S3 (static React build)              /api/*  ──►  API Gateway (HTTP API)  ──►  Express Lambda│
                 │                                                                                       │        │
                 └───────────────────────────────────────────────────────────────────────────────────────┼────────┘
                                                                                                           │
                                                          async  lambda:Invoke (Event)   ┌────────────────┘
                                                     ┌───────────────────────────────────┘
                                                     ▼
                                          FastAPI Lambda (container image, Lambda Web Adapter)
                                                     │
                            ┌────────────────────────┼─────────────────────────┐
                            ▼                        ▼                         ▼
                  Amazon Bedrock             Aurora PostgreSQL              S3 bucket
              (LLM + Titan Embeddings)    Serverless v2 + pgvector      (original PDFs)
                                          (RDS Data API, MinCapacity=0)
```

Key production decisions, and why:

| Decision | Why |
|---|---|
| **Lambda (container images) instead of ECS/Fargate/App Runner** | Scales to zero automatically, no idle compute cost, and no cluster/service to babysit for a low-traffic demo. |
| **Lambda Web Adapter** on both Lambdas | Runs the *unmodified* Express and FastAPI apps inside Lambda — no `serverless-http`, no rewritten handlers. |
| **Aurora Serverless v2 + pgvector via RDS Data API** | `MinCapacity=0` lets the cluster scale to zero when idle. The Data API is HTTPS-based, so Lambdas never need to join a VPC — no NAT Gateway, no ENIs. |
| **Document ingestion via native async Lambda invocation** (`InvocationType=Event`) | API Gateway HTTP API has a hard, non-configurable ~29s integration timeout. Ingesting a PDF (chunking + sequential, rate-limited Bedrock embedding calls) can take minutes. The gateway fires the RAG Core Lambda asynchronously and returns `202 Accepted` immediately; the RAG Core Lambda keeps processing in its own execution environment, bound only by its own (300s) timeout. Zero extra infrastructure — this is a native Lambda feature. |
| **CloudFront as the single public entry point** | Serves the SPA from S3 *and* proxies `/api/*` to the HTTP API under one domain, which eliminates CORS in production entirely. |
| **No EC2 / ECS / Fargate / App Runner / NAT Gateway / ALB** | None of them are needed here, and each one adds either idle cost, operational surface, or both. |

## Features

- **PDF ingestion** — upload a document, it gets parsed, chunked, embedded and indexed automatically.
- **Grounded Q&A** — ask questions in natural language and get answers generated strictly from the ingested content.
- **Source transparency** — every answer links back to the exact chunks (with similarity scores) it was generated from.
- **In-session history** — revisit previous questions and answers during the session.
- **Markdown export** — export a conversation for later reference.
- **Deliberately un-"AI-chatbot"-looking UI** — light, paper-and-sage palette, built for reading, not for looking like a ChatGPT clone.

## Tech stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18 · TypeScript · Vite · Tailwind CSS |
| **API Gateway** | Node.js · Express 5 · TypeScript · Zod · Helmet · Vitest/Supertest |
| **RAG Core** | Python · FastAPI · PyMuPDF (PDF parsing) |
| **LLM / Embeddings (local)** | Ollama (Llama/Qwen + `nomic-embed-text`) |
| **LLM / Embeddings (AWS)** | Amazon Bedrock (Nova Micro + Titan Text Embeddings V2) |
| **Vector store (local)** | ChromaDB |
| **Vector store (AWS)** | Aurora PostgreSQL Serverless v2 + `pgvector`, via RDS Data API |
| **Document storage** | Local filesystem (dev) · S3 (AWS) |
| **Compute (AWS)** | Lambda (container images) + Lambda Web Adapter |
| **Edge / CDN (AWS)** | CloudFront + API Gateway (HTTP API) |
| **Infrastructure as Code** | Terraform (modular, remote S3 state backend) |
| **Cost guardrail** | AWS Budgets (monthly limit + email alerts) |

## Repository layout

```
RAG-Agent/
├── frontend/                    React + TypeScript + Vite SPA
├── api-gateway/                 Node.js + Express API Gateway
│   └── src/
│       ├── clients/             HTTP + native async Lambda invocation to RAG Core
│       ├── controllers/         Route handlers
│       ├── services/            Orchestration (sync vs. async ingestion)
│       ├── middleware/          Error handling, logging, validation
│       └── utils/                SigV4 signing, synthetic Lambda event builder
├── rag-core/                     Python + FastAPI RAG engine
│   └── app/
│       ├── api/endpoints/v1/     /search, /documents/ingest
│       └── services/
│           ├── llm/               ollama_client.py · bedrock_client.py
│           ├── embeddings/        ollama · bedrock (with throttling backoff + pacing)
│           ├── vector_db/         chroma_client.py · pgvector_client.py
│           ├── storage/           filesystem_storage_client.py · s3_storage_client.py
│           └── ingestion/         chunking → embeddings → vector store orchestration
├── infra/                        Terraform (all AWS infrastructure)
│   ├── bootstrap/                 Remote state bucket + AWS Budgets (applied once, first)
│   ├── modules/                   s3-bucket · ecr-repository · aurora-pgvector ·
│   │                              lambda-container · apigateway-http · cloudfront-spa ·
│   │                              aws-budgets
│   └── environments/prod/         Wires every module together for the live deployment
└── docker-compose.yml             Full local stack: Ollama + RAG Core + API Gateway + Frontend
```

Each service also has its own README with service-specific details: [`frontend/`](./frontend/README.md) · [`api-gateway/`](./api-gateway/README.md) · [`rag-core/`](./rag-core/README.md).

## Quick start (local, offline)

**Requirements:** Docker & Docker Compose. Nothing else — Node.js/Python are only needed if you want to run a service outside its container.

```bash
git clone <this-repo>
cd RAG-Agent
docker compose up
```

This starts, in dependency order:

| Service | URL | Notes |
|---|---|---|
| Ollama | `http://localhost:11434` | Pulls/serves the local LLM + embedding models |
| RAG Core (FastAPI) | `http://localhost:8000` | Swagger docs at `/docs` |
| API Gateway (Express) | `http://localhost:3000` | Public-facing surface |
| Frontend (Vite) | `http://localhost:5173` | Open this in your browser |

First run will take a few minutes while Ollama pulls the LLM/embedding models. Everything after that is instant and fully offline — no external API calls, no AWS account required.

## Environment variables

Every service ships a `.env.example`. The provider selection pattern is consistent throughout: unset (or `ollama`/`chroma`/`filesystem`) means local, anything else means AWS.

**`rag-core/.env`** (see `app/core/config.py` for the full list):

| Variable | Local value | AWS value |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `bedrock` |
| `EMBEDDING_PROVIDER` | `ollama` | `bedrock` |
| `VECTOR_DB_PROVIDER` | `chroma` | `pgvector` |
| `STORAGE_PROVIDER` | `filesystem` | `s3` |

**`api-gateway/.env`**:

| Variable | Local value | AWS value |
|---|---|---|
| `RAG_CORE_AUTH_MODE` | `none` | `iam` (SigV4-signs requests to the RAG Core Function URL) |
| `INGESTION_MODE` | `sync` (waits for the full result) | `async` (fires the RAG Core Lambda natively and responds `202` immediately) |
| `RAG_CORE_FUNCTION_NAME` | *(unused)* | RAG Core Lambda's function name (required for async invocation) |

## API reference

Public surface, exposed exclusively by the API Gateway:

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check |
| `POST` | `/api/search` | `{ "question": "..." }` → grounded answer + sources |
| `POST` | `/api/documents/ingest` | `multipart/form-data` PDF upload → ingestion result (see below) |

`POST /api/documents/ingest` response shape depends on `INGESTION_MODE`:

- **`sync`** (local): waits for the full pipeline and returns `{ "filename", "chunks", "status": "completed" }`.
- **`async`** (AWS): returns immediately with `202 Accepted` and `{ "document_id", "filename", "status": "processing" }`. The document becomes queryable once RAG Core finishes processing in the background.

## Testing

```bash
# API Gateway
cd api-gateway && npm test

# Frontend build (type-checking + bundling)
cd frontend && npm run build

# RAG Core
cd rag-core && pytest
```

## AWS deployment

All infrastructure lives in [`infra/`](./infra) and is applied in two stages.

### 1. Bootstrap (once, before anything else)

Creates the remote Terraform state bucket and the AWS Budgets guardrail, so cost monitoring exists *before* any billable project resource does.

```bash
cd infra/bootstrap
terraform init
terraform apply -var="budget_alert_email=you@example.com"
```

### 2. Build & push the container images

Lambda (container image) deployments require the image to already exist in ECR before Terraform can reference it.

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# rag-core
docker build --provenance=false --platform linux/amd64 --target lambda \
  -t <account-id>.dkr.ecr.us-east-1.amazonaws.com/rag-agent-rag-core:latest ./rag-core
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/rag-agent-rag-core:latest

# api-gateway
docker build --provenance=false --platform linux/amd64 --target lambda \
  -t <account-id>.dkr.ecr.us-east-1.amazonaws.com/rag-agent-api-gateway:latest ./api-gateway
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/rag-agent-api-gateway:latest
```

> `--provenance=false` is required: Lambda does not support the OCI attestation manifest Docker adds by default.

### 3. Provision everything else

```bash
cd infra/environments/prod
terraform init
terraform apply
```

This provisions, in order: ECR repos, S3 buckets (frontend + documents), Aurora Serverless v2 + pgvector, both Lambdas + their IAM roles, the HTTP API, and the CloudFront distribution.

### 4. Ship the frontend

```bash
cd frontend
npm run build
aws s3 sync dist/ s3://<frontend-bucket-name> --delete
aws cloudfront create-invalidation --distribution-id <distribution-id> --paths "/*"
```

### Redeploying after a code change

Terraform doesn't re-pull a `:latest` image tag on its own once it's already pointing at it — after pushing a new image, force the Lambda to pick it up:

```bash
aws lambda update-function-code --function-name rag-agent-rag-core \
  --image-uri <account-id>.dkr.ecr.us-east-1.amazonaws.com/rag-agent-rag-core:latest
```

## Cost model — will this cost me anything?

**Short, honest answer: not literally $0, but designed to stay in the single-digit-dollars-per-month range for a low/no-traffic demo — and there's a hard budget alarm watching it from the very first `terraform apply`.**

Almost every component here scales to zero *compute* cost when idle:

| Component | Idle cost | Why |
|---|---|---|
| Lambda (both functions) | **$0** | AWS's "always free" tier includes 1M requests + 400,000 GB-seconds/month, forever, not just for 12 months. A low-traffic demo won't get close. |
| Aurora Serverless v2 compute | **$0** | `MinCapacity = 0` — the cluster suspends compute entirely with no queries. |
| API Gateway (HTTP API) | **~$0** | Pay-per-request, no idle charge. |
| Bedrock | **$0** | Pay-per-token, only when the model is actually invoked. |
| S3 | **~$0** | A handful of PDFs + a static SPA build; storage cost is fractions of a cent. |

However, a few things are **not** truly $0 even with zero traffic, because AWS bills them independently of usage:

| Component | Approx. cost | Why it's not zero |
|---|---|---|
| **Secrets Manager** (Aurora's managed master password) | **~$0.40/month** | Terraform's `manage_master_user_password = true` creates one secret, and Secrets Manager charges per secret regardless of how often it's read. |
| **Aurora storage** | **~$0.10–1/month** | Storage (and automated backups) is billed even at 0 ACU — only *compute* scales to zero, not the data on disk. Negligible for a demo-sized dataset. |
| **ECR image storage** | **~$0.05–0.20/month** | Two repositories with container image layers; a lifecycle policy already prunes old images to limit this. |
| **CloudWatch Logs** | **~$0–0.10/month** | 14-day retention is configured to cap this; without it, logs would accumulate indefinitely. |

Realistically, **total baseline cost sits around $1–3/month even with zero visitors**, almost entirely from Secrets Manager + Aurora storage — both fixed, tiny, and independent of traffic. Real usage (search queries, ingestions) adds Bedrock token cost and Lambda GB-seconds on top, but for a portfolio-demo traffic level that's still expected to be cents.

Two things exist specifically so this never turns into a surprise:

1. **AWS Budgets**, deployed in the bootstrap stage *before* anything else — a monthly cost threshold (default `$5`, configurable via `budget_limit_usd`) with email alerts at forecast and actual-spend thresholds.
2. **You can `terraform destroy` the `prod` environment at any time** (keeping only the cheap `bootstrap` stage) between demos, and everything — Lambdas, Aurora, CloudFront, S3 content — comes back with `terraform apply` + a fresh image push. There is no persistent expensive resource that only makes sense to leave running 24/7.

If you want the closest thing to a hard guarantee, set `budget_limit_usd` low (e.g. `$3`) and treat the AWS Budgets email alert as your safety net — it's exactly what it's there for.

## Known limitations & roadmap

- **New AWS accounts can have a `0` on-demand throughput quota for Bedrock embedding models** (account-level, not a code issue) — ingestion will fail until AWS Support grants throughput for the model in use. Search/chat (LLM-only) is unaffected.
- No authentication — this is an open public demo by design, not a multi-tenant product.
- No persistent chat history across sessions/devices (in-memory only, by design, per the original scope).

## License

Personal portfolio project. No license file yet — treat as all-rights-reserved unless stated otherwise.
