# Document Knowledge Agent

Document Knowledge Agent is a Retrieval-Augmented Generation (RAG) system for PDF knowledge bases. Users upload a document, ask questions in natural language, and receive answers grounded in retrieved chunks, with source metadata pointing back to the documents that supported the response.

The same backend also powers a second surface: an “Ask me anything” portfolio assistant that queries an isolated corpus (profile, experience, projects) instead of user-uploaded papers.

Live demo: https://document-knowledge-agent-tau.vercel.app/

`[Screenshot: demo UI with PDF upload and grounded Q&A]`

## Motivation / Problem

I built this project to learn how a full RAG pipeline works in practice, not only as a notebook experiment. The starting point was an ArXiv-oriented agent: search papers, ingest PDFs, embed them locally with Ollama and Chroma, and answer questions over that corpus. Sprint scaffolding in the repo still reflects that path.

As the system matured, the interesting problem shifted. I wanted a document Q&A product that could run fully offline for development, then deploy to AWS without rewriting the application for each environment. Keyword search is a poor fit for long technical PDFs; semantic retrieval plus grounded generation is a better match, but only if the architecture can survive real cloud constraints (timeouts, secrets, cold starts, cost).

The portfolio assistant came later as a productization test: reuse the same search API against a curated knowledge base, keep the demo corpus isolated, and expose the result as a chat experience visitors can try.

## Architecture

The system is split into three application layers plus infrastructure defined in Terraform.

```text
Browser (React / Vite)
        │
        ▼
API Gateway (Express / TypeScript)
  validates input, handles uploads, proxies to rag-core
  production: IAM SigV4, async ingest via Lambda Event invoke
        │
        ▼
RAG Core (FastAPI / Python)
  parse → chunk → embed → store
  retrieve → generate
        │
        ├── Local:  Ollama + Chroma + filesystem
        └── Prod:   OpenAI + Aurora pgvector (Data API) + S3
```

`[Architecture diagram: local Compose stack vs AWS serverless path]`

The gateway stays thin on purpose. It owns HTTP concerns (CORS, Helmet, Zod validation, multipart upload, response status codes). RAG Core owns the pipeline: PyMuPDF extraction, fixed-size chunking (1000 characters, 200 overlap), embeddings, vector search, and LLM generation through LangChain-backed providers.

Collection routing uses the `X-RAG-Collection` header (`default` or `portfolio`). FastAPI stores that choice in a request-scoped context and resolves separate Chroma collections or Aurora tables (`document_chunks_openai` vs `document_chunks_portfolio` in production).

Both Lambdas run container images with AWS Lambda Web Adapter, so the same FastAPI and Express apps listen on HTTP without Mangum or custom handlers. CloudFront serves the SPA from S3 and can forward `/api/*` to the HTTP API.

## Engineering Decisions

**Thin Node gateway, Python RAG core.**  
Sprint 1 locked this boundary early. Python is the natural home for PDF parsing, embeddings, and vector clients. Express is a better fit for a typed public edge with middleware and upload handling. The trade-off is an extra network hop and two deployable units, in exchange for independent scaling and clearer ownership.

**Provider facades instead of environment-specific branches.**  
`LLM_PROVIDER`, `EMBEDDING_PROVIDER`, `VECTOR_DB_PROVIDER`, and `STORAGE_PROVIDER` select implementations at runtime. Local development defaults to Ollama (`qwen2.5:3b`, `nomic-embed-text`), Chroma, and filesystem storage. Production Terraform sets OpenAI (`gpt-4.1-mini`, `text-embedding-3-small`), Aurora pgvector, and S3. Switching providers is configuration, not a rewrite of the RAG orchestration layer.

**OpenAI in production after Bedrock.**  
An earlier production path used Bedrock. Commit history records throttling workarounds (backoff, bounded concurrency) and a later migration to OpenAI. The current codebase and `DEPLOY.md` have no Bedrock dependency; the API key lives in SSM SecureString and is loaded at runtime by name only.

**Async ingest only where the timeout forces it.**  
Locally, ingest is synchronous because Compose has no API Gateway 29-second limit and Ollama is on the same network. In production, the gateway returns `202`, invokes rag-core with `InvocationType=Event` using a synthetic Function URL-shaped payload (so Lambda Web Adapter still works), and the frontend polls status. Search stays synchronous. Gateway Lambda timeout is 30 seconds; rag-core is allowed up to 300 seconds.

**IAM on the rag-core Function URL.**  
rag-core is not a public endpoint. The gateway signs outbound calls with SigV4 when `RAG_CORE_AUTH_MODE=iam`. Resource-based Lambda permissions were required in addition to the caller’s IAM policy; without them, invokes failed with 403.

**Aurora Serverless v2 + RDS Data API.**  
pgvector runs on Aurora with HTTP Data API access so Lambdas stay out of the VPC (no NAT/ENI tax for a portfolio workload). Schema bootstrap runs once at `terraform apply` via a local Python script, not on every request. Minimum capacity is 0; the client retries on `DatabaseResumingException` when the cluster wakes up.

**Isolated portfolio corpus on the same API.**  
Rather than standing up a second backend, the portfolio frontend only calls `POST /api/search` with `X-RAG-Collection: portfolio`. Query expansion rewrites deictic “you/your” questions for embedding only, while the original question still goes to the LLM. That keeps retrieval useful for first-person portfolio chat without changing the demo path.

## Challenges

**API Gateway hard timeout vs long PDF ingest.**  
Parse, chunk, embed, and store can exceed ~29 seconds. The fix was not “make ingest faster”; it was decoupling acknowledgment from work. Status markers in storage (`processing` → `completed`/`failed`) let the UI poll safely, including a `processing` fallback when the marker has not appeared yet.

**Production reliability under serverless cost constraints.**  
Aurora at min capacity 0 means resume latency on cold clusters. Embedding calls needed separate retry policies for query vs ingestion. Lambda container images had to be built with `docker buildx` using `--provenance=false --sbom=false` because Lambda rejects some BuildKit OCI manifests.

**Local and production vector spaces are not interchangeable.**  
Local embeddings are 768-dimensional (`nomic-embed-text`); production uses 1536 (`text-embedding-3-small`). Tables and bootstrap scripts take `EMBEDDING_DIMENSIONS` explicitly so schema width matches the active model.

**Keeping two product surfaces from contaminating each other.**  
Demo uploads and portfolio documents share infrastructure but not indexes. Collection-aware table names, S3 key prefixes, and header validation prevent a paper upload from answering a “tell me about your Nestlé internship” question (and the reverse).

## Results

- End-to-end local stack via Docker Compose (Ollama, rag-core, api-gateway, frontend).
- Production path defined in Terraform: ECR, two container Lambdas, HTTP API, CloudFront, S3, Aurora pgvector, SSM parameter, and a $5/month AWS Budgets alert in bootstrap.
- Live demo UI on Vercel backed by the AWS API.
- API Gateway covered by Vitest + Supertest (health, search validation/proxy, documents validation/proxy, async ingest `202` behavior).
- Portfolio assistant reuses the same search contract against a curated corpus under `portfolio_documents/`.

No latency or retrieval-quality benchmarks are claimed here; those were not established as measured project results.

`[Deployment flow: terraform apply → image push → Lambda update → frontend sync]`

## What I Learned

- Cloud timeouts shape API design more than model choice. Sync search and async ingest are different contracts for a reason.
- Provider abstractions pay off only when local and production stay honest about their differences (dimensions, storage, auth mode).
- Serverless RAG is less about “putting FastAPI on Lambda” and more about secrets, resume behavior, image packaging, and which service is allowed to talk to which endpoint.
- A second product surface (portfolio chat) is a strong test of whether boundaries like collections and prompts are actually isolated.

## Future Improvements

- End-user authentication and per-user document spaces (the public API currently has no auth beyond edge validation and IAM between services).
- A real evaluation harness for retrieval and answer quality (today there is only a portfolio regression helper script).
- Wire or remove `packages/rag-ui-shared`; both frontends are currently self-contained.
- Decide the fate of leftover ArXiv routes on rag-core, which are not exposed through the public gateway.
