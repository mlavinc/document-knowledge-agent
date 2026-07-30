from langchain_openai import ChatOpenAI

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


class OpenAILLMClient:
    """
    LLM client backed by LangChain ChatOpenAI.
    Implements the shared `generate(prompt) -> str` contract.
    """

    def __init__(self):
        api_key = settings.resolve_openai_api_key()
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY or OPENAI_API_KEY_SSM_PARAMETER is required "
                "when LLM_PROVIDER=openai"
            )

        self._llm = ChatOpenAI(
            model=settings.resolve_llm_model(),
            api_key=api_key,
            temperature=0,
        )

    async def generate(self, prompt: str) -> str:
        response = await self._llm.ainvoke(prompt)
        return _content_to_text(response.content)
