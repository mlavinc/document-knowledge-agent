from langchain_openai import OpenAIEmbeddings

from app.core.config import settings


class OpenAIEmbeddingsClient:
    """
    Embeddings client backed by LangChain OpenAIEmbeddings.
    Implements the shared `generate_embedding(text, *, purpose) -> list[float]`
    contract used by EmbeddingsService.
    """

    def __init__(self):
        api_key = settings.resolve_openai_api_key()
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY or OPENAI_API_KEY_SSM_PARAMETER is required "
                "when EMBEDDING_PROVIDER=openai"
            )

        self._embeddings = OpenAIEmbeddings(
            model=settings.resolve_embedding_model(),
            api_key=api_key,
            dimensions=settings.EMBEDDING_DIMENSIONS,
        )

    async def generate_embedding(
        self,
        text: str,
        *,
        purpose: str = "ingestion",
    ) -> list[float]:
        # `purpose` kept for interface parity with other providers
        # (query vs ingestion retry budgets). OpenAI does not use it.
        _ = purpose
        return await self._embeddings.aembed_query(text)
