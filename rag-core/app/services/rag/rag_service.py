from app.schemas.search import SearchResponse, Source
from app.services.embeddings.embeddings_service import embeddings_service
from app.services.vector_db.vector_db_service import vector_db_service
from app.services.llm.llm_service import llm_service


class RAGService:
    """
    Handles the RAG pipeline orchestration.
    """

    async def search(self, question: str) -> SearchResponse:
        # Step 1: Generate embedding (fail-fast retry budget for interactive search)
        embedding = await embeddings_service.embed(question, purpose="query")

        # Step 2: Search relevant documents
        context = await vector_db_service.search(embedding)

        # Si no hay contexto, no llamamos al LLM
        if not context:
            return SearchResponse(
                answer="No relevant documents were found in the knowledge base.",
                sources=[],
            )

        # Step 3: Generate final answer
        answer = await llm_service.generate(question, context)

        # Step 4: Build sources (one per document)
        sources = []
        seen_documents = set()

        for chunk in context:
            metadata = chunk["metadata"]
            document_id = metadata["document_id"]

            if document_id in seen_documents:
                continue

            seen_documents.add(document_id)

            sources.append(
                Source(
                    document_id=document_id,
                    title=metadata["title"],
                    chunk_index=metadata["chunk_index"],
                    score=chunk["score"],
                )
            )

        return SearchResponse(
            answer=answer,
            sources=sources,
        )


rag_service = RAGService()