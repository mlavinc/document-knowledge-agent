from fastapi import APIRouter

router = APIRouter()


@router.get("/ollama/health")
async def ollama_health():
    from app.services.ollama.ollama_client import OllamaClient

    client = OllamaClient()
    healthy = await client.health_check()

    return {
        "service": "ollama",
        "healthy": healthy,
    }


@router.get("/ollama/models")
async def list_models():
    from app.services.ollama.ollama_client import OllamaClient

    client = OllamaClient()
    return await client.list_models()