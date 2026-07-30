from fastapi import APIRouter
from app.services.vector_db.vector_db_service import vector_db_service
from app.services.embeddings.embeddings_service import embeddings_service

router = APIRouter()


@router.get(
    "/vector-db/count",
    summary="Get document count in vector database"
)
async def get_vector_db_count():
    count = await vector_db_service.count()
    return {"documents": count}
@router.get(
    "/vector-db/peek",
    summary="Inspect stored vectors metadata"
)
async def peek_vector_db():
    return await vector_db_service.peek()
    
@router.post(
    "/vector-db/populate",
    summary="Insert demo documents into the vector database"
)
async def populate_vector_db():
    documents = [
        "Linkin Park is a rock band from the United States.",
        "Los Tres is a Chilean rock band.",
        "Poppy is an Australian singer-songwriter.",
    ]
    ids = []
    embeddings = []
    metadatas = []

    for idx, document in enumerate(documents, start=1):
        ids.append(f"demo_{idx}")
        embedding = await embeddings_service.embed(
            document, purpose="ingestion"
        )
        embeddings.append(embedding)
        metadatas.append(
            {
                "source": "demo",
                "topic": "music",
            }
        )
    await vector_db_service.add_documents(
    ids=ids,
    documents=documents,
    embeddings=embeddings,
    metadatas=metadatas,
    )

    return {
    "message": "Demo documents inserted successfully.",
    "documents": len(documents),
    }