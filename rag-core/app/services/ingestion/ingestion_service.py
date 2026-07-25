import logging

from app.services.document.pdf_parser_service import pdf_parser_service
from app.services.chunking_service import chunking_service
from app.services.embeddings.embeddings_service import embeddings_service
from app.services.vector_db.vector_db_service import vector_db_service

logger = logging.getLogger(__name__)


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

        # 3. Generate embeddings one chunk at a time. This used to run
        # up to 2 embedding requests concurrently (asyncio.Semaphore),
        # but even that was enough to exceed a low-quota AWS account's
        # Bedrock throughput and trigger sustained ThrottlingException.
        # Embeddings providers have no batch API we can use here (see
        # BedrockEmbeddingsClient), so strictly sequential is the
        # simplest correct strategy: it minimizes request rate without
        # touching EmbeddingsService.embed()'s interface, and Ollama
        # (no rate limits locally) is unaffected other than running
        # one request at a time instead of two.
        logger.info(
            "Generating embeddings for %s chunks (sequential).",
            len(chunks),
        )

        embeddings = [
            await embeddings_service.embed(chunk["text"])
            for chunk in chunks
        ]

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