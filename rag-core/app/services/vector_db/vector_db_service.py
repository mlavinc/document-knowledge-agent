from app.core.config import settings
from app.services.vector_db.chroma_client import ChromaVectorDBClient


class VectorDBService:
    """
    Vector storage facade. Uses ChromaDB for local development and
    Aurora PostgreSQL Serverless v2 + pgvector (via the RDS Data API) in
    production. The provider is selected via VECTOR_DB_PROVIDER, so
    callers (ingestion_service, rag_service) never depend on a specific
    backend.
    """

    def __init__(self):
        if settings.VECTOR_DB_PROVIDER == "pgvector":
            from app.services.vector_db.pgvector_client import PgVectorClient

            self._client = PgVectorClient()
        else:
            self._client = ChromaVectorDBClient()

    async def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, str]],
    ) -> None:
        await self._client.add_documents(ids, documents, embeddings, metadatas)

    async def search(
        self,
        embedding: list[float],
        n_results: int = 3,
    ) -> list[dict]:
        return await self._client.search(embedding, n_results)

    async def count(self) -> int:
        return await self._client.count()

    async def reset(self) -> None:
        await self._client.reset()

    async def peek(self):
        return await self._client.peek()


vector_db_service = VectorDBService()
