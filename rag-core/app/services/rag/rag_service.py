from app.schemas.search import SearchResponse, Source
from app.services.embeddings.embeddings_service import embeddings_service
from app.services.llm.llm_service import llm_service
from app.services.rag.query_expansion import expand_query_for_embedding
from app.services.vector_db.vector_db_service import vector_db_service


class RAGService:
    """
    Handles the RAG pipeline orchestration.
    """

    async def search(self, question: str) -> SearchResponse:
        # Step 1: Embed (portfolio may expand deictic "you/your" for retrieval only)
        embed_text = expand_query_for_embedding(question)
        embedding = await embeddings_service.embed(embed_text, purpose="query")

        # Step 2: Search relevant documents
        context = await vector_db_service.search(embedding)

        # Si no hay contexto, no llamamos al LLM
        if not context:
            return SearchResponse(
                answer="No relevant documents were found in the knowledge base.",
                sources=[],
            )

        # Step 3: Generate final answer (original question + prompt rules)
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