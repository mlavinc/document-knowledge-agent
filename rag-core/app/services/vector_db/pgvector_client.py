import asyncio
import json
import logging
import time

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings


logger = logging.getLogger(__name__)

# Aurora Serverless v2 with min_capacity=0 auto-pauses. The first Data API
# call after pause raises DatabaseResumingException until the instance is
# ready. Retry briefly so search/ingestion recover without raising
# min_capacity (cost). Other DB errors are re-raised immediately.
MAX_RESUME_RETRIES = 3
RESUME_BACKOFF_SECONDS = (2.0, 4.0, 8.0)


def _embedding_literal(embedding: list[float]) -> str:
    """Formats an embedding as a pgvector input literal, e.g. "[0.1,0.2]"."""
    return "[" + ",".join(repr(float(value)) for value in embedding) + "]"


def _field_value(field: dict):
    """Extracts the Python value from an RDS Data API result field."""
    if field.get("isNull"):
        return None
    for key in (
        "stringValue",
        "longValue",
        "doubleValue",
        "booleanValue",
        "blobValue",
    ):
        if key in field:
            return field[key]
    return None


def _is_database_resuming(error: ClientError) -> bool:
    return (
        error.response.get("Error", {}).get("Code") == "DatabaseResumingException"
    )


class PgVectorClient:
    """
    Vector storage backed by Aurora PostgreSQL Serverless v2 + pgvector,
    accessed exclusively through the RDS Data API. This keeps Lambda out
    of the VPC (no NAT Gateway/ENIs needed) since Data API calls are
    plain HTTPS requests to the RDS control plane.

    Implements the same interface as ChromaVectorDBClient so that
    VectorDBService can swap providers transparently.
    """

    def __init__(self):
        self._client = boto3.client("rds-data", region_name=settings.AWS_REGION)
        self._table = settings.AURORA_TABLE_NAME
        self._ensured = False

    def _call_with_resume_retry(self, operation, *args, **kwargs):
        """Runs an RDS Data API call, retrying only on Aurora resume."""
        attempt = 0
        while True:
            try:
                return operation(*args, **kwargs)
            except ClientError as error:
                if not _is_database_resuming(error):
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

    def _execute(self, sql: str, parameters: list[dict] | None = None):
        kwargs = {
            "resourceArn": settings.AURORA_CLUSTER_ARN,
            "secretArn": settings.AURORA_SECRET_ARN,
            "database": settings.AURORA_DATABASE_NAME,
            "sql": sql,
        }
        if parameters:
            kwargs["parameters"] = parameters
        return self._call_with_resume_retry(
            self._client.execute_statement, **kwargs
        )

    def _batch_execute(self, sql: str, parameter_sets: list[list[dict]]):
        return self._call_with_resume_retry(
            self._client.batch_execute_statement,
            resourceArn=settings.AURORA_CLUSTER_ARN,
            secretArn=settings.AURORA_SECRET_ARN,
            database=settings.AURORA_DATABASE_NAME,
            sql=sql,
            parameterSets=parameter_sets,
        )

    def _ensure_schema_sync(self) -> None:
        if self._ensured:
            return

        self._execute("CREATE EXTENSION IF NOT EXISTS vector")
        self._execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self._table} (
                id TEXT PRIMARY KEY,
                document TEXT NOT NULL,
                embedding vector({settings.BEDROCK_EMBEDDING_DIMENSIONS}) NOT NULL,
                metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb
            )
            """
        )
        self._execute(
            f"""
            CREATE INDEX IF NOT EXISTS {self._table}_embedding_idx
            ON {self._table}
            USING hnsw (embedding vector_cosine_ops)
            """
        )
        self._ensured = True

    async def _ensure_schema(self) -> None:
        await asyncio.to_thread(self._ensure_schema_sync)

    async def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, str]],
    ) -> None:
        await self._ensure_schema()

        parameter_sets = []
        for doc_id, document, embedding, metadata in zip(
            ids, documents, embeddings, metadatas
        ):
            parameter_sets.append(
                [
                    {"name": "id", "value": {"stringValue": doc_id}},
                    {"name": "document", "value": {"stringValue": document}},
                    {
                        "name": "embedding",
                        "value": {"stringValue": _embedding_literal(embedding)},
                    },
                    {
                        "name": "metadata",
                        "value": {"stringValue": json.dumps(metadata)},
                    },
                ]
            )

        sql = f"""
            INSERT INTO {self._table} (id, document, embedding, metadata)
            VALUES (:id, :document, :embedding::vector, :metadata::jsonb)
            ON CONFLICT (id) DO UPDATE SET
                document = EXCLUDED.document,
                embedding = EXCLUDED.embedding,
                metadata = EXCLUDED.metadata
        """

        await asyncio.to_thread(self._batch_execute, sql, parameter_sets)

    async def search(
        self,
        embedding: list[float],
        n_results: int = 3,
    ) -> list[dict]:
        await self._ensure_schema()

        sql = f"""
            SELECT document, metadata, embedding <=> :embedding::vector AS distance
            FROM {self._table}
            ORDER BY distance ASC
            LIMIT :limit
        """
        parameters = [
            {
                "name": "embedding",
                "value": {"stringValue": _embedding_literal(embedding)},
            },
            {"name": "limit", "value": {"longValue": settings.RAG_TOP_K}},
        ]

        response = await asyncio.to_thread(self._execute, sql, parameters)

        logger.info(
            "Retrieved %s candidate chunks from pgvector",
            len(response.get("records", [])),
        )

        chunks = []
        for record in response.get("records", []):
            document = _field_value(record[0])
            metadata = json.loads(_field_value(record[1]) or "{}")
            distance = _field_value(record[2])

            accepted = distance <= settings.RAG_MIN_SCORE

            if accepted:
                chunks.append(
                    {
                        "document": document,
                        "metadata": metadata,
                        "score": distance,
                    }
                )

        logger.info(
            "Returning %s relevant chunks after filtering",
            len(chunks),
        )

        return chunks

    async def count(self) -> int:
        await self._ensure_schema()

        response = await asyncio.to_thread(
            self._execute, f"SELECT COUNT(*) FROM {self._table}"
        )
        return int(_field_value(response["records"][0][0]))

    async def reset(self) -> None:
        await self._ensure_schema()
        await asyncio.to_thread(self._execute, f"TRUNCATE TABLE {self._table}")

    async def peek(self):
        await self._ensure_schema()

        response = await asyncio.to_thread(
            self._execute,
            f"SELECT id, document, metadata FROM {self._table} LIMIT 10",
        )

        ids, documents, metadatas = [], [], []
        for record in response.get("records", []):
            ids.append(_field_value(record[0]))
            documents.append(_field_value(record[1]))
            metadatas.append(json.loads(_field_value(record[2]) or "{}"))

        return {"ids": ids, "documents": documents, "metadatas": metadatas}
