# Portfolio knowledge base

Documents in this folder power the **Ask me anything** portfolio frontend
(`frontend-portfolio/`). They are ingested via
`scripts/ingest_portfolio_documents.py` — there is no upload UI.

They are stored in an **isolated** vector table
(`document_chunks_portfolio`), selected with the
`X-RAG-Collection: portfolio` header. Demo papers live in a separate table.

## RAG-optimized corpus (default ingest)

Edit the markdown sources; the ingest script converts them to PDF.

| File | Purpose |
| --- | --- |
| `01_Profile.md` | Identity, education, goals, skills, short Q&A |
| `02_Experience_Nestle.md` | Nestlé / Nestle internship facts + tech |
| `03_Document_Knowledge_Agent.md` | RAG / Document Knowledge Agent project |
| `04_Cloud_Operations_Lab.md` | Cloud Operations Lab project |
| `05_ECG_AI_Serverless.md` | ECG AI Serverless project |
| `06_Skill_Tracker.md` | Skill Tracker project |

Default ingest only uploads these numbered `0N_*.pdf` files so retrieval stays
focused. Set `PORTFOLIO_INGEST_ALL=1` to also ingest legacy CVs / READMEs.

## Legacy / source materials (not ingested by default)

CV PDFs, About Me, and project README exports remain here for human editing
and as source material for the optimized docs above.

## Regression checks

```bash
set AWS_REGION=sa-east-1
set API_GATEWAY_URL=https://6cwjcmekm6.execute-api.sa-east-1.amazonaws.com
python scripts/regression_portfolio_search.py
```
