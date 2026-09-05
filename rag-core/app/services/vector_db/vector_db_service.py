from app.core.config import settings


class VectorDBService:
    """
    Vector storage facade. Uses ChromaDB for local development and
    Aurora PostgreSQL Serverless v2 + pgvector (via the RDS Data API) in
    production. The provider is selected via VECTOR_DB_PROVIDER, so
    callers (ingestion_service, rag_service) never depend on a specific
    backend.
    """

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client

        if settings.VECTOR_DB_PROVIDER == "pgvector":
            from app.services.vector_db.pgvector_client import PgVectorClient

            self._client = PgVectorClient()
        else:
            from app.services.vector_db.chroma_client import ChromaVectorDBClient

            self._client = ChromaVectorDBClient()
        return self._client

    async def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, str]],
    ) -> None:
        await self._get_client().add_documents(
            ids, documents, embeddings, metadatas
        )

    async def search(
        self,
        embedding: list[float],
        n_results: int = 3,
    ) -> list[dict]:
        return await self._get_client().search(embedding, n_results)

    async def warmup(self) -> None:
        if settings.VECTOR_DB_PROVIDER != "pgvector":
            return
        await self._get_client().warmup()

    async def is_ready(self) -> bool:
        if settings.VECTOR_DB_PROVIDER != "pgvector":
            return True
        return await self._get_client().is_ready()

    async def count(self) -> int:
        return await self._get_client().count()

    async def reset(self) -> None:
        await self._get_client().reset()

    async def peek(self):
        return await self._get_client().peek()


vector_db_service = VectorDBService()
