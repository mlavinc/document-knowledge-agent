from fastapi import FastAPI, Request

from app.api.endpoints.v1.arxiv import router as arxiv_router
from app.api.endpoints.v1.documents import router as documents_router
from app.api.endpoints.v1.health import router as health_router
from app.api.endpoints.v1.ingestion import router as ingestion_router
from app.api.endpoints.v1.ollama import router as ollama_router
from app.api.endpoints.v1.search import router as search_router
from app.api.endpoints.v1.vector_db import router as vector_db_router
from app.core.collection import reset_collection, set_collection
from app.core.config import settings


def create_app() -> FastAPI:
    """Create a FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="An agentic RAG system for querying knowledge documents.",
    )

    @app.middleware("http")
    async def collection_context_middleware(request: Request, call_next):
        token = set_collection(request.headers.get("x-rag-collection"))
        try:
            return await call_next(request)
        finally:
            reset_collection(token)

    app.include_router(health_router, prefix=settings.API_PREFIX, tags=["health"])
    app.include_router(search_router, prefix=settings.API_PREFIX, tags=["search"])
    app.include_router(ollama_router, prefix=settings.API_PREFIX, tags=["ollama"])
    app.include_router(vector_db_router, prefix=settings.API_PREFIX, tags=["vector-db"])
    app.include_router(arxiv_router, prefix=settings.API_PREFIX, tags=["arxiv"])
    app.include_router(documents_router, prefix=settings.API_PREFIX, tags=["documents"])
    app.include_router(ingestion_router, prefix=settings.API_PREFIX, tags=["ingestion"])

    @app.get("/")
    async def root():
        return {
            "service": "rag-core",
            "version": settings.VERSION,
            "status": "healthy",
        }

    return app


app = create_app()