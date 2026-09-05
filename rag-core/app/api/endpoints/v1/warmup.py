import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.services.vector_db.vector_db_service import vector_db_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/warmup",
    summary="Warm the RAG runtime and resume the vector database",
)
async def warmup():
    """
    Wait for Aurora to resume using a lightweight SELECT 1.

    This endpoint is intended for asynchronous Lambda invocation. It never
    creates an embedding or invokes the LLM.
    """
    logger.info("Starting RAG Core warmup.")
    await vector_db_service.warmup()
    logger.info("RAG Core warmup completed.")
    return {"status": "ready"}


@router.get(
    "/warmup",
    summary="Check whether the vector database is ready",
)
async def warmup_status():
    """Perform one lightweight readiness probe without long retries."""
    if await vector_db_service.is_ready():
        return {"status": "ready"}
    return JSONResponse(
        status_code=202,
        content={"status": "initializing"},
    )
