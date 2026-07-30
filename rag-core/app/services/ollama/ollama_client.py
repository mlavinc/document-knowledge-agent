import httpx

from app.core.config import settings


class OllamaClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=settings.OLLAMA_BASE_URL,
            timeout=30.0,
        )

    async def list_models(self):
        response = await self.client.get("/api/tags")
        response.raise_for_status()
        return response.json()

    async def health_check(self):
        try:
            await self.list_models()
            return True
        except Exception:
            return False         
    async def generate_embedding(self, text: str) -> list[float]:
        response = await self.client.post(
            "/api/embed",
            json={
                "model": settings.OLLAMA_EMBEDDING_MODEL,
                "input": text,
            },
        )
        response.raise_for_status()
        return response.json()["embeddings"][0]

    # LLM generation moved to app.services.llm.ollama_llm_client
    # (LangChain ChatOllama). This client remains responsible for
    # embeddings and health/model listing only.