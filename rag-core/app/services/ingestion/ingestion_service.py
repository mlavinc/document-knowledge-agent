import asyncio
import logging

from app.services.document.pdf_parser_service import pdf_parser_service
from app.services.chunking_service import chunking_service
from app.services.embeddings.embeddings_service import embeddings_service
from app.services.vector_db.vector_db_service import vector_db_service

logger = logging.getLogger(__name__)

# Bounds how many embedding requests are in flight at once across the
# whole pipeline. This protects providers with tight rate limits (e.g.
# a new AWS account's Bedrock quota) without serializing everything.
# Ollama has no such constraint locally, so this is a no-op in practice
# for the local dev mode besides capping concurrency to 2.
EMBEDDING_CONCURRENCY = 2


class IngestionService:
    """
    Orchestrates the document ingestion pipeline.

    Flow:
    PDF
      -> Text extraction
      -> Chunking
      -> Embeddings
      -> Vector database
    """

    def __init__(self):
        self._embedding_semaphore = asyncio.Semaphore(EMBEDDING_CONCURRENCY)

    async def _embed_chunk(self, chunk: dict) -> list[float]:
        async with self._embedding_semaphore:
            return await embeddings_service.embed(chunk["text"])

    async def ingest_pdf(
        self,
        file_path: str,
        metadata: dict,
    ) -> dict:

        # 1. Extract text from document
        parsed = pdf_parser_service.extract_text(
            file_path
        )

        # 2. Split document into chunks
        chunks = chunking_service.split(
            parsed["pages"]
        )

        # 3. Generate embeddings (at most EMBEDDING_CONCURRENCY in flight)
        logger.info(
            "Generating embeddings for %s chunks (max %s concurrent requests).",
            len(chunks),
            EMBEDDING_CONCURRENCY,
        )

        embeddings = await asyncio.gather(
            *(self._embed_chunk(chunk) for chunk in chunks)
        )

        document_id = metadata.get(
            "document_id",
            "unknown",
        )

        # 4. Prepare Chroma documents
        ids = [
            f"{document_id}_chunk_{chunk['chunk_id']}"
            for chunk in chunks
        ]

        metadatas = [
            {
                **metadata,
                "chunk_index": chunk["chunk_id"],
                "page_number": chunk["page_number"],
            }
            for chunk in chunks
        ]

        # 5. Store vectors
        await vector_db_service.add_documents(
            ids=ids,
            documents=[chunk["text"] for chunk in chunks],
            embeddings=embeddings,
            metadatas=metadatas,
        )

        return {
            "chunks": len(chunks),
            "status": "completed",
        }


ingestion_service = IngestionService()