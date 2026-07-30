#!/usr/bin/env python3
"""
Deploy-time bootstrap for Aurora pgvector schema.

Creates extension / table / index once via the RDS Data API. Safe to re-run:
already-exists errors (including SQLSTATE 23505 catalog races) are treated
as success. Does not run inside Lambda request handlers.

Usage (env vars, typically injected by Terraform local-exec or DEPLOY.md):

  AWS_REGION=sa-east-1 \\
  AURORA_CLUSTER_ARN=... \\
  AURORA_SECRET_ARN=... \\
  AURORA_DATABASE_NAME=ragagent \\
  AURORA_TABLE_NAME=document_chunks_openai \\
  EMBEDDING_DIMENSIONS=1536 \\
  python rag-core/scripts/bootstrap_pgvector_schema.py
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import boto3

# Allow `python scripts/bootstrap_pgvector_schema.py` from repo / rag-core.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.vector_db.pgvector_schema import (  # noqa: E402
    call_with_resume_retry,
    ensure_pgvector_schema,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("bootstrap_pgvector_schema")


def _require(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


def main() -> None:
    region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
    if not region:
        raise SystemExit("Missing AWS_REGION (or AWS_DEFAULT_REGION)")

    cluster_arn = _require("AURORA_CLUSTER_ARN")
    secret_arn = _require("AURORA_SECRET_ARN")
    database = _require("AURORA_DATABASE_NAME")
    table_name = _require("AURORA_TABLE_NAME")
    dimensions = int(os.environ.get("EMBEDDING_DIMENSIONS", "1536"))

    client = boto3.client("rds-data", region_name=region)

    def execute_sql(sql: str):
        return call_with_resume_retry(
            client.execute_statement,
            resourceArn=cluster_arn,
            secretArn=secret_arn,
            database=database,
            sql=sql,
        )

    logger.info(
        "Bootstrapping pgvector schema (db=%s table=%s dims=%s)",
        database,
        table_name,
        dimensions,
    )
    ensure_pgvector_schema(
        execute_sql=execute_sql,
        table_name=table_name,
        embedding_dimensions=dimensions,
    )
    logger.info("Bootstrap complete.")


if __name__ == "__main__":
    main()
