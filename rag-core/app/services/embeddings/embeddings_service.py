from typing import Literal

from app.core.config import settings
from app.services.ollama.ollama_client import OllamaClient

EmbeddingPurpose = Literal["query", "ingestion"]


class EmbeddingsService:
    """
    Handles embedding generation. Provider is selected via
    EMBEDDING_PROVIDER (ollama | openai). Callers never depend on a
    specific vendor SDK.

    `purpose` is forwarded for providers that distinguish query vs
    ingestion retry budgets; OpenAI ignores it.
    """

    def __init__(self):
        provider = settings.EMBEDDING_PROVIDER.lower()

        if provider == "openai":
            from app.services.embeddings.openai_embeddings_client import (
                OpenAIEmbeddingsClient,
            )

            self._client = OpenAIEmbeddingsClient()
        else:
            self._client = OllamaClient()

    async def embed(
        self,
        text: str,
        *,
        purpose: EmbeddingPurpose = "ingestion",
    ) -> list[float]:
        return await self._client.generate_embedding(text, purpose=purpose)


embeddings_service = EmbeddingsService()
