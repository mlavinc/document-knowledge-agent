import logging

import chromadb

from app.core.config import settings


logger = logging.getLogger(__name__)


class ChromaVectorDBClient:
    """
    Vector storage backed by an embedded ChromaDB instance
    (chromadb.PersistentClient). Used in local development.
    """

    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PATH,
        )

        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )

    async def add_documents(
        self,
        ids: list[str],
        documents: list[str],
        embeddings: list[list[float]],
        metadatas: list[dict[str, str]],
    ) -> None:
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
        )

    async def search(
        self,
        embedding: list[float],
        n_results: int = 3,
    ) -> list[dict]:
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=settings.RAG_TOP_K,
        )

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        logger.info(
            "Retrieved %s candidate chunks from ChromaDB",
            len(documents),
        )

        chunks = []

        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances,
        ):
            accepted = distance <= settings.RAG_MIN_SCORE

            logger.debug(
                "Chunk distance: %.4f | Accepted: %s",
                distance,
                accepted,
            )

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
        return self.collection.count()

    async def reset(self) -> None:
        """
        Deletes and recreates the vector collection.
        Useful for development/testing.
        """
        try:
            self.client.delete_collection(
                name=settings.CHROMA_COLLECTION
            )
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )

    async def peek(self):
        results = self.collection.peek()

        return {
            "ids": results["ids"],
            "documents": results["documents"],
            "metadatas": results["metadatas"],
        }
