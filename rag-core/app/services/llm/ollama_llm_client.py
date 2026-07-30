from langchain_ollama import ChatOllama

from app.core.config import settings


def _content_to_text(content) -> str:
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and "text" in block:
                parts.append(block["text"])
        return "".join(parts)
    return str(content)


class OllamaLLMClient:
    """
    LLM client backed by LangChain ChatOllama.
    Implements the shared `generate(prompt) -> str` contract.

    Note: ChatOllama lives in `langchain-ollama` (moved out of
    langchain-community). Embeddings/health remain on the httpx
    OllamaClient under app.services.ollama.
    """

    def __init__(self):
        self._llm = ChatOllama(
            model=settings.resolve_llm_model(),
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0,
            # RAG prompts with retrieved context can exceed short timeouts.
            timeout=120.0,
        )

    async def generate(self, prompt: str) -> str:
        response = await self._llm.ainvoke(prompt)
        return _content_to_text(response.content)
