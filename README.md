# Document Knowledge Agent

A Retrieval-Augmented Generation (RAG) system for PDF knowledge bases. Upload a document, ask questions in natural language, and get answers grounded in retrieved chunks — with source metadata so you can see which document backed the response.

The same backend powers a second surface: an “Ask me anything” portfolio assistant that queries an isolated corpus (CV, experience, projects) instead of user-uploaded papers.

## Features

- PDF upload, text extraction (PyMuPDF), and fixed-size chunking with overlap
- Semantic search over embeddings, then LLM generation with retrieved context
- Source metadata on answers (`document_id`, title, chunk index, score)
- Async document ingestion in production (gateway returns `202`, client polls status)
- Isolated vector collections for the demo corpus vs the portfolio assistant
- Local stack (Ollama + Chroma) and cloud stack (OpenAI + Aurora pgvector) behind the same service interfaces

## Architecture

```text
Browser (React / Vite)
        │
        ▼
API Gateway (Node.js / Express / TypeScript)
  · validates requests
  · proxies search & ingest
  · optional IAM SigV4 → rag-core
  · sync or async ingest mode
        │
        ▼
RAG Core (Python / FastAPI)
  · parse → chunk → embed → store
  · retrieve → generate
        │
        ├── Vector store: Chroma (local) | Aurora PostgreSQL + pgvector (prod)
        ├── Models:       Ollama (local) | OpenAI (prod)
        └── Storage:      filesystem (local) | S3 (prod)
```

Public edge routes (API Gateway):

| Method | Path | Role |
| --- | --- | --- |
| `GET` | `/health` | Liveness |
| `POST` | `/api/search` | Question → grounded answer + sources |
| `POST` | `/api/documents/ingest` | Upload PDF |
| `GET` | `/api/documents/status/:documentId` | Ingest job status |

Collection routing uses the `X-RAG-Collection` header (`default` \| `portfolio`).

Production infra (Terraform under `infra/`): container Lambdas (ECR + Lambda Web Adapter), HTTP API, CloudFront + S3 for the SPA, S3 for PDFs, Aurora Serverless v2 with pgvector, and the OpenAI API key in SSM SecureString.

## Technical Highlights

- **Provider facades.** LLM, embeddings, vector DB, and storage are selected via env (`LLM_PROVIDER`, `EMBEDDING_PROVIDER`, `VECTOR_DB_PROVIDER`, `STORAGE_PROVIDER`). Application code does not hardcode Ollama vs OpenAI.
- **Thin gateway, fat core.** Express owns validation, CORS, upload handling, and auth to rag-core. All RAG logic stays in FastAPI.
- **Async ingest vs sync search.** Local ingest waits for completion. In production the gateway invokes rag-core with Lambda `InvocationType=Event`, returns `202`, and the UI polls status — so long PDF jobs do not hit the HTTP API timeout.
- **IAM between services.** rag-core’s Function URL uses `AWS_IAM`; the gateway signs outbound calls with SigV4 when `RAG_CORE_AUTH_MODE=iam`.
- **Corpus isolation.** Demo uploads and the portfolio knowledge base use separate Chroma collections / pgvector tables, selected per request.
- **Same image, two runtimes.** Docker multi-stage builds (`dev` / `lambda`) share application code; Lambda Web Adapter exposes the normal HTTP servers without Mangum or custom handlers.

## Tech Stack

**Backend**
Python 3.11 · FastAPI · LangChain · PyMuPDF · Node.js · Express · TypeScript · Zod

**AI / data**
Ollama (local) · OpenAI (prod) · ChromaDB (local) · Aurora PostgreSQL + pgvector (prod)

**Frontend**
React 18 · TypeScript · Vite · Tailwind CSS

**Infrastructure**
Docker Compose (local) · Terraform · AWS Lambda · API Gateway · CloudFront · S3 · ECR · SSM · Vercel (demo / portfolio UIs)

## Getting Started

### Prerequisites

- Docker and Docker Compose
- ~5 GB disk for Ollama models (first pull)

### Configure env files

```bash
git clone https://github.com/mlavinc/document-knowledge-agent.git
cd document-knowledge-agent

cp rag-core/.env.example rag-core/.env
cp api-gateway/.env.example api-gateway/.env
cp frontend/.env.example frontend/.env
```

In `rag-core/.env`, set the Ollama URL to the Compose service name:

```env
OLLAMA_BASE_URL=http://ollama:11434
```

(`rag-core/.env.example` defaults to `localhost`, which is correct for host-side runs but wrong inside the container.)

### Run

```bash
docker compose up --build
```

Pull the models used by the default config (once):

```bash
docker compose exec ollama ollama pull qwen2.5:3b
docker compose exec ollama ollama pull nomic-embed-text
```

| Service | URL |
| --- | --- |
| Frontend | http://localhost:5173 |
| API Gateway | http://localhost:3000 |
| RAG Core | http://localhost:8000 |

Upload a PDF in the UI, wait for ingest to finish, then ask a question.

### Tests

```bash
cd api-gateway && npm test
```

Gateway tests use Vitest + Supertest (validation, proxy behavior, async ingest).

### Production deploy

See [`infra/environments/prod/DEPLOY.md`](infra/environments/prod/DEPLOY.md) for Terraform apply, SSM key setup, and Lambda image push.

## Demo

Live UI: [document-knowledge-agent-tau.vercel.app](https://document-knowledge-agent-tau.vercel.app/)

Upload a PDF and ask questions; answers include source metadata from the retrieved chunks.

## Case Study

Architecture decisions, trade-offs, and product framing:

[mlavinc-portfolio.vercel.app/projects/document-knowledge-agent](https://mlavinc-portfolio.vercel.app/projects/document-knowledge-agent)

## Repository layout

```text
frontend/              Demo SPA (upload + chat)
frontend-portfolio/    Portfolio “Ask me anything” SPA
api-gateway/           Express edge API
rag-core/              FastAPI RAG pipeline
infra/                 Terraform (bootstrap + prod)
portfolio_documents/   Corpus for the portfolio assistant
scripts/               Portfolio ingest / regression helpers
```
