from fastapi import APIRouter, Body


router = APIRouter()


@router.post(
    "/ingestion/pdf",
    summary="Ingest a PDF into vector database"
)
async def ingest_pdf(
    file_path: str,
    metadata: dict = Body(default={}),
):
    from app.services.ingestion.ingestion_service import ingestion_service

    result = await ingestion_service.ingest_pdf(
        file_path=file_path,
        metadata=metadata,
    )

    return result