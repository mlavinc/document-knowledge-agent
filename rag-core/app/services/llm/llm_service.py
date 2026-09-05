from app.core.config import settings
from app.services.prompt_builder import prompt_builder


class LLMService:
    """
    Handles answer generation. Provider is selected via LLM_PROVIDER
    (ollama | openai). Callers never depend on a specific LangChain
    chat model or vendor SDK.
    """

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client

        provider = settings.LLM_PROVIDER.lower()

        if provider == "openai":
            from app.services.llm.openai_client import OpenAILLMClient

            self._client = OpenAILLMClient()
        else:
            from app.services.llm.ollama_llm_client import OllamaLLMClient

            self._client = OllamaLLMClient()
        return self._client

    async def generate(self, question: str, context: list[dict]) -> str:
        prompt = prompt_builder.build(question, context)
        return await self._get_client().generate(prompt)


llm_service = LLMService()
