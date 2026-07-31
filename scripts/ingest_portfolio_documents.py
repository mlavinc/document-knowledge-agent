#!/usr/bin/env python3
"""
One-shot ingest of portfolio_documents/ into the isolated portfolio corpus.

Always sends header:
  X-RAG-Collection: portfolio

Ingest path (avoids API Gateway async Event 1MB payload limit):
  boto3 lambda.invoke → rag-agent-rag-core (RequestResponse)

Status polling (optional) still uses API_GATEWAY_URL when needed.

Usage:
  set API_GATEWAY_URL=https://xxxx.execute-api.sa-east-1.amazonaws.com
  set AWS_REGION=sa-east-1
  python scripts/ingest_portfolio_documents.py

Optional:
  PORTFOLIO_DOCS_DIR=portfolio_documents
  RAG_CORE_FUNCTION_NAME=rag-agent-rag-core
  WAIT_SECONDS=1
"""

from __future__ import annotations

import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = Path(
    os.environ.get("PORTFOLIO_DOCS_DIR", ROOT / "portfolio_documents")
).resolve()
API_BASE = os.environ.get("API_GATEWAY_URL", "").rstrip("/")
FUNCTION_NAME = os.environ.get("RAG_CORE_FUNCTION_NAME", "rag-agent-rag-core")
AWS_REGION = os.environ.get("AWS_REGION") or os.environ.get(
    "AWS_DEFAULT_REGION", "sa-east-1"
)
WAIT_SECONDS = float(os.environ.get("WAIT_SECONDS", "1"))
COLLECTION_HEADER = "X-RAG-Collection"
COLLECTION_PORTFOLIO = "portfolio"


def _ensure_fitz() -> None:
    try:
        import fitz  # noqa: F401
    except ImportError:
        import subprocess

        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "pymupdf", "-q"]
        )


def _resolve_unicode_font() -> str | None:
    candidates = [
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "arial.ttf",
        Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts" / "calibri.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
    ]
    for path in candidates:
        if path.is_file():
            return str(path)
    return None


def text_to_pdf(src: Path, dest: Path) -> None:
    _ensure_fitz()
    import fitz

    text = src.read_text(encoding="utf-8", errors="replace")
    fontfile = _resolve_unicode_font()
    font = fitz.Font(fontfile=fontfile) if fontfile else None
    if font is None:
        import unicodedata

        text = (
            unicodedata.normalize("NFKD", text)
            .encode("ascii", "ignore")
            .decode("ascii")
        )

    doc = fitz.open()
    text_chunks = [
        text[i : i + 3500] for i in range(0, max(len(text), 1), 3500)
    ] or [text]
    for chunk in text_chunks:
        page = doc.new_page(width=595, height=842)
        rect = fitz.Rect(48, 48, 547, 794)
        if font is not None:
            writer = fitz.TextWriter(page.rect)
            writer.fill_textbox(rect, chunk, font=font, fontsize=10, align=0)
            writer.write_text(page)
        else:
            page.insert_textbox(
                rect, chunk, fontsize=10, fontname="helv", align=0
            )

    dest.parent.mkdir(parents=True, exist_ok=True)
    doc.save(dest, garbage=4, deflate=True)
    doc.close()

    check = fitz.open(dest)
    extracted = "".join(page.get_text() for page in check).strip()
    check.close()
    if not extracted:
        dest.unlink(missing_ok=True)
        raise RuntimeError(f"Converted PDF has no extractable text: {src.name}")


def multipart_body(filename: str, content: bytes) -> tuple[bytes, dict[str, str]]:
    boundary = f"----ragportfolio{int(time.time() * 1000)}"
    lines = [
        f"--{boundary}".encode(),
        (
            f'Content-Disposition: form-data; name="file"; filename="{filename}"'
        ).encode(),
        b"Content-Type: application/pdf",
        b"",
        content,
        f"--{boundary}--".encode(),
        b"",
    ]
    body = b"\r\n".join(lines)
    headers = {
        "content-type": f"multipart/form-data; boundary={boundary}",
        COLLECTION_HEADER.lower(): COLLECTION_PORTFOLIO,
    }
    return body, headers


def build_lambda_url_event(
    method: str, path: str, headers: dict[str, str], body: bytes
) -> dict:
    now = time.time()
    return {
        "version": "2.0",
        "routeKey": "$default",
        "rawPath": path,
        "rawQueryString": "",
        "headers": headers,
        "requestContext": {
            "accountId": "anonymous",
            "apiId": "portfolio-ingest",
            "domainName": "portfolio-ingest",
            "domainPrefix": "portfolio-ingest",
            "http": {
                "method": method,
                "path": path,
                "protocol": "HTTP/1.1",
                "sourceIp": "127.0.0.1",
                "userAgent": "ingest-portfolio-documents",
            },
            "requestId": f"portfolio-{int(now * 1000)}",
            "routeKey": "$default",
            "stage": "$default",
            "time": time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(now)),
            "timeEpoch": int(now * 1000),
        },
        "body": base64.b64encode(body).decode("ascii"),
        "isBase64Encoded": True,
    }


def ingest_via_lambda(pdf_path: Path, display_name: str) -> dict:
    import boto3

    body, headers = multipart_body(display_name, pdf_path.read_bytes())
    event = build_lambda_url_event(
        "POST", "/api/v1/documents/ingest", headers, body
    )
    client = boto3.client("lambda", region_name=AWS_REGION)
    response = client.invoke(
        FunctionName=FUNCTION_NAME,
        InvocationType="RequestResponse",
        Payload=json.dumps(event).encode("utf-8"),
    )
    raw = response["Payload"].read()
    if response.get("FunctionError"):
        raise SystemExit(f"Lambda error for {display_name}: {raw.decode()}")

    payload = json.loads(raw.decode())
    status_code = int(payload.get("statusCode", 500))
    body_raw = payload.get("body", "{}")
    if payload.get("isBase64Encoded"):
        body_raw = base64.b64decode(body_raw).decode("utf-8", errors="replace")
    try:
        parsed = json.loads(body_raw) if isinstance(body_raw, str) else body_raw
    except json.JSONDecodeError:
        parsed = {"raw": body_raw}

    if status_code >= 400:
        raise SystemExit(
            f"Ingest failed for {display_name}: {status_code} {parsed}"
        )
    return parsed if isinstance(parsed, dict) else {"result": parsed}


def collect_pdf_jobs() -> list[tuple[Path, str]]:
    """
    Prefer RAG-optimized numbered docs (01_*.md → 01_*.pdf).

    When any 0N_*.md/pdf files exist, only those are ingested. Legacy CVs /
    READMEs remain in the folder for reference but are not re-ingested into
    the portfolio table (keeps retrieval focused and maintainable).

    Override with PORTFOLIO_INGEST_ALL=1 to ingest every PDF in the folder.
    """
    ingest_all = os.environ.get("PORTFOLIO_INGEST_ALL", "").strip() in {
        "1",
        "true",
        "yes",
    }

    sources = sorted(list(DOCS_DIR.glob("*.txt")) + list(DOCS_DIR.glob("*.md")))
    numbered_sources = [
        src
        for src in sources
        if src.name[:2].isdigit() and src.name[2:3] == "_"
    ]
    convert_sources = (
        sources
        if ingest_all
        else (numbered_sources or [s for s in sources if s.name.lower() != "readme.md"])
    )

    for src in convert_sources:
        if src.name.lower() == "readme.md":
            continue
        pdf = src.with_suffix(".pdf")
        if not pdf.exists() or pdf.stat().st_mtime < src.stat().st_mtime:
            print(f"Converting {src.name} -> {pdf.name}")
            text_to_pdf(src, pdf)

    jobs: list[tuple[Path, str]] = []
    seen: set[str] = set()
    pdfs = sorted(DOCS_DIR.glob("*.pdf"))
    numbered_pdfs = [
        pdf for pdf in pdfs if pdf.name[:2].isdigit() and pdf.name[2:3] == "_"
    ]
    selected = pdfs if ingest_all else (numbered_pdfs or pdfs)

    for pdf in selected:
        key = pdf.name.lower()
        if key in seen:
            continue
        seen.add(key)
        jobs.append((pdf, pdf.name))

    return jobs


def main() -> None:
    if not DOCS_DIR.is_dir():
        raise SystemExit(f"Documents directory not found: {DOCS_DIR}")

    jobs = collect_pdf_jobs()
    if not jobs:
        raise SystemExit(f"No PDF/text documents found in {DOCS_DIR}")

    print(
        f"Ingesting {len(jobs)} document(s) via Lambda {FUNCTION_NAME} "
        f"(collection={COLLECTION_PORTFOLIO}, region={AWS_REGION})"
    )
    for pdf_path, name in jobs:
        print(f"-> {name} ({pdf_path.stat().st_size / 1024:.1f} KB)")
        result = ingest_via_lambda(pdf_path, name)
        status = result.get("status")
        document_id = result.get("document_id") or result.get("filename") or name
        chunks = result.get("chunks")
        print(f"   done: status={status} id={document_id} chunks={chunks}")
        if status == "failed":
            raise SystemExit(result.get("error") or "ingest failed")
        time.sleep(WAIT_SECONDS)

    print("Portfolio corpus ingest complete.")
    if API_BASE:
        print(f"(API Gateway still available for search: {API_BASE})")


if __name__ == "__main__":
    main()
