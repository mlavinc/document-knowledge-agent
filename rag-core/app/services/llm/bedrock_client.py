import asyncio

import boto3

from app.core.config import settings


class BedrockLLMClient:
    """
    LLM client backed by Amazon Bedrock's Converse API. Implements the
    same `generate` interface as OllamaClient.
    """

    def __init__(self):
        self._client = boto3.client(
            "bedrock-runtime", region_name=settings.AWS_REGION
        )

    def _invoke(self, prompt: str) -> str:
        response = self._client.converse(
            modelId=settings.BEDROCK_LLM_MODEL_ID,
            messages=[{"role": "user", "content": [{"text": prompt}]}],
        )
        return response["output"]["message"]["content"][0]["text"]

    async def generate(self, prompt: str) -> str:
        return await asyncio.to_thread(self._invoke, prompt)
