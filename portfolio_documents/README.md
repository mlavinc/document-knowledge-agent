# Portfolio knowledge base

Documents in this folder power the **Ask me anything** portfolio frontend
(`frontend-portfolio/`). They are ingested once at deploy time via
`scripts/ingest_portfolio_documents.py` — there is no upload UI.

They are stored in an **isolated** vector table/collection
(`document_chunks_portfolio` / `portfolio_documents`), selected with the
`X-RAG-Collection: portfolio` header. Demo papers (PyramidTNT, uploads,
etc.) live in a separate table and are never retrieved by this chat.

## What to put here

| Kind | Examples | Notes |
| --- | --- | --- |
| CV / resume | `*.pdf` | Preferred. Ingested as-is. |
| About / bio | `.txt`, `.md` | Converted to PDF automatically by the ingest script. |
| Project write-ups | `README *.md` | Project case studies the chat should know. |

## Current corpus

- `CV Martin Lavin Jul2026.pdf`
- `CV Martin Lavin July 2026.pdf`
- `About Me.txt` (+ generated `About Me.pdf`)
- Project READMEs: Portafolio, DAG, Cloud, ECG, skill tracker (+ generated PDFs)

The API Gateway ingest endpoint accepts **PDF only**. Non-PDF sources are
converted on ingest; keep the originals for editing.
