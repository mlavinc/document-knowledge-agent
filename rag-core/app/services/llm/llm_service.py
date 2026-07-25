from app.core.config import settings
from app.services.ollama.ollama_client import OllamaClient
from app.services.prompt_builder import prompt_builder


class LLMService:
    """
    Handles answer generation. Uses Ollama for local development and
    Amazon Bedrock in production. The provider is selected via
    LLM_PROVIDER, so callers never depend on a specific provider.
    """

    def __init__(self):
        if settings.LLM_PROVIDER == "bedrock":
            from app.services.llm.bedrock_client import BedrockLLMClient

            self._client = BedrockLLMClient()
        else:
            self._client = OllamaClient()

    async def generate(self, question: str, context: list[dict]) -> str:
        # Step 1: Build the prompt
        prompt = prompt_builder.build(question, context)

        # Step 2: Generate the answer with the configured provider
        answer = await self._client.generate(prompt)

        return answer


llm_service = LLMService()
