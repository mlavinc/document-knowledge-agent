import logging

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

router = APIRouter()
logger = logging.getLogger(__name__)


class StagedDocumentRequest(BaseModel):
    document_id: str = Field(min_length=1, max_length=255)
    object_key: str = Field(pattern=r"^staging/")


async def _ingest_content(document_id: str, content: bytes):
    from app.services.ingestion.ingestion_service import ingestion_service
    from app.services.storage.storage_service import storage_service

    await storage_service.write_ingest_status(document_id, "processing")

    try:
        file_path = await storage_service.save(document_id, content)
        result = await ingestion_service.ingest_pdf(
            file_path,
            {
                "document_id": document_id,
                "title": document_id,
                "source": "upload",
            },
        )
        await storage_service.write_ingest_status(
            document_id,
            "completed",
            chunks=result.get("chunks"),
            suggestions=result.get("suggestions"),
        )
        return {"filename": document_id, **result}
    except Exception as exc:
        await storage_service.write_ingest_status(
            document_id,
            "failed",
            error=str(exc),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Ingestion failed: {exc}",
        ) from exc


@router.get(
    "/documents/extract",
    summary="Extract text from PDF",
)
async def extract_pdf(file_path: str):
    from app.services.document.pdf_parser_service import pdf_parser_service

    return pdf_parser_service.extract_text(file_path)


@router.get(
    "/documents/chunks",
    summary="Extract PDF text and split into chunks",
)
async def get_chunks(file_path: str):
    from app.services.chunking_service import chunking_service
    from app.services.document.pdf_parser_service import pdf_parser_service

    parsed = pdf_parser_service.extract_text(file_path)
    chunks = chunking_service.split(parsed["pages"])
    return {
        "pages": parsed["pages"],
        "chunks": len(chunks),
        "first_chunk": chunks[0] if chunks else None,
    }


@router.get(
    "/documents/status/{document_id}",
    summary="Get async ingestion status for a document",
)
async def get_ingest_status(document_id: str):
    from app.services.storage.storage_service import storage_service

    status = await storage_service.read_ingest_status(document_id)
    if status is None:
        # Job accepted but marker not written yet (or unknown id).
        return {
            "document_id": document_id,
            "filename": document_id,
            "status": "processing",
        }
    return status


@router.post(
    "/documents/ingest",
    summary="Upload and ingest PDF document",
)
async def ingest_document(file: UploadFile = File(...)):
    document_id = file.filename or "upload.pdf"
    content = await file.read()
    return await _ingest_content(document_id, content)


@router.post(
    "/documents/ingest-staged",
    summary="Ingest a PDF previously staged in private storage",
)
async def ingest_staged_document(request: StagedDocumentRequest):
    from app.services.storage.storage_service import storage_service

    try:
        content = await storage_service.read_staged(request.object_key)
        return await _ingest_content(request.document_id, content)
    except HTTPException:
        raise
    except Exception as exc:
        await storage_service.write_ingest_status(
            request.document_id,
            "failed",
            error=str(exc),
        )
        raise HTTPException(
            status_code=500,
            detail=f"Could not read staged document: {exc}",
        ) from exc
    finally:
        try:
            await storage_service.delete_staged(request.object_key)
        except Exception:
            logger.exception("Could not delete staged object %s", request.object_key)
