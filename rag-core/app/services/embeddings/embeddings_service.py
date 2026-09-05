from typing import Literal

from app.core.config import settings

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
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client

        provider = settings.EMBEDDING_PROVIDER.lower()

        if provider == "openai":
            from app.services.embeddings.openai_embeddings_client import (
                OpenAIEmbeddingsClient,
            )

            self._client = OpenAIEmbeddingsClient()
        else:
            from app.services.ollama.ollama_client import OllamaClient

            self._client = OllamaClient()
        return self._client

    async def embed(
        self,
        text: str,
        *,
        purpose: EmbeddingPurpose = "ingestion",
    ) -> list[float]:
        return await self._get_client().generate_embedding(
            text, purpose=purpose
        )


embeddings_service = EmbeddingsService()
