import asyncio

from app.services.embeddings.embeddings_service import embeddings_service
from app.services.vector_db.vector_db_service import vector_db_service


QUESTION = "How many stages does PyramidTNT have?"


async def main():
    print(f"Question: {QUESTION}\n")

    embedding = await embeddings_service.embed(QUESTION, purpose="query")

    chunks = await vector_db_service.search(embedding)

    print(f"Retrieved {len(chunks)} relevant chunk(s):\n")

    for i, chunk in enumerate(chunks, start=1):
        print(f"--- Chunk {i} ---")
        print("Score (distance):", chunk["score"])
        print("Metadata:", chunk["metadata"])
        preview = chunk["document"][:200].replace("\n", " ")
        preview = preview.encode("ascii", errors="replace").decode("ascii")
        print("Document (preview):", preview)
        print()

    assert len(chunks) > 0, "Expected at least one relevant chunk to be retrieved"

    print("Retrieval validation PASSED")


asyncio.run(main())
