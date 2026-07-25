import asyncio
import json
import logging

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

# New/low-volume AWS accounts get very tight Bedrock TPS quotas, so
# InvokeModel calls for embeddings can be throttled even without real
# concurrency. Retry a handful of times with exponential backoff before
# giving up; any other error is re-raised immediately (not swallowed).
MAX_THROTTLE_RETRIES = 5
BASE_BACKOFF_SECONDS = 1.0


class BedrockEmbeddingsClient:
    """
    Embeddings client backed by Amazon Bedrock (Titan Embeddings Text
    v2). Implements the same `generate_embedding` interface as
    OllamaClient.
    """

    def __init__(self):
        self._client = boto3.client(
            "bedrock-runtime", region_name=settings.AWS_REGION
        )

    def _invoke(self, text: str) -> list[float]:
        body = json.dumps(
            {
                "inputText": text,
                "dimensions": settings.BEDROCK_EMBEDDING_DIMENSIONS,
                "normalize": True,
            }
        )
        response = self._client.invoke_model(
            modelId=settings.BEDROCK_EMBEDDING_MODEL_ID,
            body=body,
            contentType="application/json",
            accept="application/json",
        )
        payload = json.loads(response["body"].read())
        return payload["embedding"]

    async def generate_embedding(self, text: str) -> list[float]:
        attempt = 0
        while True:
            try:
                return await asyncio.to_thread(self._invoke, text)
            except ClientError as error:
                error_code = error.response.get("Error", {}).get("Code", "")
                if error_code != "ThrottlingException":
                    raise

                attempt += 1
                if attempt > MAX_THROTTLE_RETRIES:
                    logger.error(
                        "Bedrock embeddings throttled and exhausted all "
                        "%s retries; giving up.",
                        MAX_THROTTLE_RETRIES,
                    )
                    raise

                backoff_seconds = BASE_BACKOFF_SECONDS * (2 ** (attempt - 1))
                logger.warning(
                    "Bedrock embeddings throttled (attempt %s/%s); "
                    "retrying in %.1fs.",
                    attempt,
                    MAX_THROTTLE_RETRIES,
                    backoff_seconds,
                )
                await asyncio.sleep(backoff_seconds)
