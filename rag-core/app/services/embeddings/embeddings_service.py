from app.core.config import settings
from app.services.ollama.ollama_client import OllamaClient


class EmbeddingsService:
    """
    Handles embedding generation. Uses Ollama for local development and
    Amazon Bedrock in production. The provider is selected via
    EMBEDDING_PROVIDER, so callers never depend on a specific provider.
    """

    def __init__(self):
        if settings.EMBEDDING_PROVIDER == "bedrock":
            from app.services.embeddings.bedrock_embeddings_client import (
                BedrockEmbeddingsClient,
            )

            self._client = BedrockEmbeddingsClient()
        else:
            self._client = OllamaClient()

    async def embed(self, text: str) -> list[float]:
        return await self._client.generate_embedding(text)


embeddings_service = EmbeddingsService()
