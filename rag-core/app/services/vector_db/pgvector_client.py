import asyncio
import json
import logging

import boto3

from app.core.collection import resolve_aurora_table
from app.core.config import settings
from app.services.vector_db.pgvector_schema import call_with_resume_retry


logger = logging.getLogger(__name__)


def _embedding_literal(embedding: list[float]) -> str:
    """Formats an embedding as a pgvector input literal, e.g. '[0.1,0.2]'."""
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


class PgVectorClient:
    """
    Vector storage backed by Aurora PostgreSQL Serverless v2 + pgvector,
    accessed exclusively through the RDS Data API.

    Table is resolved per request from X-RAG-Collection (default vs portfolio).
    Schema is NOT created on the request path — bootstrap at deploy time.
    """

    def __init__(self):
        self._client = boto3.client("rds-data", region_name=settings.AWS_REGION)

    @property
    def _table(self) -> str:
        return resolve_aurora_table()

    def _execute(self, sql: str, parameters: list[dict] | None = None):
        kwargs = {
            "resourceArn": settings.AURORA_CLUSTER_ARN,
            "secretArn": settings.AURORA_SECRET_ARN,
            "database": settings.AURORA_DATABASE_NAME,
            "sql": sql,
        }
        if parameters:
            kwargs["parameters"] = parameters
        return call_with_resume_retry(self._client.execute_statement, **kwargs)

    def _batch_execute(self, sql: str, parameter_sets: list[list[dict]]):
        return call_with_resume_retry(
            self._client.batch_execute_statement,
            resourceArn=settings.AURORA_CLUSTER_ARN,
            secretArn=settings.AURORA_SECRET_ARN,
            database=settings.AURORA_DATABASE_NAME,
            sql=sql,
            parameterSets=parameter_sets,
        )

    async def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, str]],
    ) -> None:
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
        response = await asyncio.to_thread(
            self._execute, f"SELECT COUNT(*) FROM {self._table}"
        )
        return int(_field_value(response["records"][0][0]))

    async def reset(self) -> None:
        await asyncio.to_thread(self._execute, f"TRUNCATE TABLE {self._table}")

    async def peek(self):
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
