from fastapi import APIRouter, HTTPException

from app.schemas.search import SearchRequest, SearchResponse
from app.services.rag.rag_service import rag_service
from app.utils.exceptions import EmbeddingProviderError

router = APIRouter()


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Search indexed ArXiv papers"
)
async def search(request: SearchRequest) -> SearchResponse:
    try:
        return await rag_service.search(request.question)
    except EmbeddingProviderError as exc:
        # Fail fast with a controlled 503 so API Gateway / the frontend
        # can clear loading state instead of waiting for a gateway timeout.
        raise HTTPException(status_code=503, detail=str(exc)) from exc
