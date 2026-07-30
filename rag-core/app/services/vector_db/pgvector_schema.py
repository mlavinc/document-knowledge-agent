"""Idempotent pgvector DDL shared by deploy-time bootstrap (not request path)."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

MAX_RESUME_RETRIES = 3
RESUME_BACKOFF_SECONDS = (2.0, 4.0, 8.0)


def schema_statements(table_name: str, embedding_dimensions: int) -> list[str]:
    """Return ordered DDL statements for the pgvector knowledge-base table."""
    return [
        "CREATE EXTENSION IF NOT EXISTS vector",
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id TEXT PRIMARY KEY,
            document TEXT NOT NULL,
            embedding vector({embedding_dimensions}) NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb
        )
        """.strip(),
        f"""
        CREATE INDEX IF NOT EXISTS {table_name}_embedding_idx
        ON {table_name}
        USING hnsw (embedding vector_cosine_ops)
        """.strip(),
    ]


def is_database_resuming(error: ClientError) -> bool:
    return error.response.get("Error", {}).get("Code") == "DatabaseResumingException"


def is_already_exists_error(error: ClientError) -> bool:
    """
    True only for PostgreSQL 'object already exists' / unique race on catalog
    types (common with concurrent CREATE EXTENSION vector). Other DB errors
    must not be swallowed.
    """
    payload = error.response.get("Error", {})
    code = payload.get("Code", "")
    message = payload.get("Message", "") or ""
    message_lower = message.lower()

    if "sqlstate: 23505" in message_lower:  # unique_violation (catalog race)
        return True
    if "sqlstate: 42710" in message_lower:  # duplicate_object
        return True
    if "sqlstate: 42p07" in message_lower:  # duplicate_table
        return True
    if code == "DatabaseErrorException" and (
        "already exists" in message_lower
        or "duplicate key value violates unique constraint" in message_lower
    ):
        return True
    return False


def call_with_resume_retry(operation: Callable[..., Any], *args: Any, **kwargs: Any):
    """Retry RDS Data API calls only while Aurora is resuming from auto-pause."""
    attempt = 0
    while True:
        try:
            return operation(*args, **kwargs)
        except ClientError as error:
            if not is_database_resuming(error):
                raise

            if attempt >= MAX_RESUME_RETRIES:
                logger.error(
                    "Aurora still resuming after %s retries; giving up.",
                    MAX_RESUME_RETRIES,
                )
                raise

            backoff = RESUME_BACKOFF_SECONDS[
                min(attempt, len(RESUME_BACKOFF_SECONDS) - 1)
            ]
            attempt += 1
            logger.warning(
                "Aurora is resuming after auto-pause "
                "(attempt %s/%s); retrying in %.1fs.",
                attempt,
                MAX_RESUME_RETRIES,
                backoff,
            )
            time.sleep(backoff)


def execute_ddl_idempotent(execute_sql: Callable[[str], Any], sql: str) -> None:
    """Run DDL; treat already-exists / catalog unique races as success."""
    try:
        execute_sql(sql)
    except ClientError as error:
        if is_already_exists_error(error):
            logger.info(
                "Schema object already present (idempotent success): %s",
                " ".join(sql.split())[:120],
            )
            return
        raise


def ensure_pgvector_schema(
    *,
    execute_sql: Callable[[str], Any],
    table_name: str,
    embedding_dimensions: int,
) -> None:
    """Apply full pgvector schema once, idempotently."""
    for statement in schema_statements(table_name, embedding_dimensions):
        execute_ddl_idempotent(execute_sql, statement)
    logger.info(
        "pgvector schema ready (table=%s, dimensions=%s)",
        table_name,
        embedding_dimensions,
    )
