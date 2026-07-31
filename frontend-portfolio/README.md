# frontend-portfolio

Chat-only **Ask me anything** UI for Martín Lavín’s professional portfolio.

- Same API Gateway + RAG Core as `frontend/`
- **Only** calls `POST /api/search`
- Sends `X-RAG-Collection: portfolio` so retrieval uses an **isolated**
  vector table (`document_chunks_portfolio`), never the demo corpus
- Never calls `/api/documents/*`
- Shared search/chat logic: `packages/rag-ui-shared` (demo frontend untouched)

## Local development

```bash
cd frontend-portfolio
cp .env.example .env
npm install
npm run dev   # http://localhost:5174
```

## Deploy on Vercel

1. Root Directory: `frontend-portfolio`
2. Env: `VITE_API_GATEWAY_URL=<API Gateway URL>`
3. Deploy

Allow the Vercel origin in API Gateway CORS if not using `*`.

## Knowledge base (portfolio only)

```bash
set API_GATEWAY_URL=https://xxxx.execute-api.sa-east-1.amazonaws.com
python scripts/ingest_portfolio_documents.py
```

The script always sets `X-RAG-Collection: portfolio`.
See `portfolio_documents/README.md`.
