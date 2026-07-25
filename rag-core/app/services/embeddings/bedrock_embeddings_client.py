import asyncio
import json
import logging
import time

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)

# New/low-volume AWS accounts get very tight Bedrock TPS quotas, so
# InvokeModel calls for embeddings can be throttled even without real
# concurrency. Retry a handful of times with exponential backoff before
# giving up; any other error is re-raised immediately (not swallowed).
# Ingestion now runs as a fire-and-forget async Lambda invocation (see
# api-gateway's ingestDocumentAsync), decoupled from API Gateway's ~29s
# hard timeout, so there is much more headroom (up to this Lambda's own
# 300s timeout) to wait out a persistently tight quota. Backoff is capped
# per attempt so retries stay predictable even with more attempts.
MAX_THROTTLE_RETRIES = 7
BASE_BACKOFF_SECONDS = 1.0
MAX_BACKOFF_SECONDS = 20.0

# Titan Embeddings v2 only accepts one `inputText` per InvokeModel call
# (no batch parameter), so there is no way to reduce the number of
# Bedrock requests for a given set of chunks. Instead, pace requests
# proactively: even with no concurrency, back-to-back calls can still
# outrun a tight account quota. Enforcing a minimum interval between
# calls smooths out bursts before they get throttled, so the reactive
# retry above becomes a safety net rather than the primary defense.
MIN_INTERVAL_SECONDS = 1.5


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
        self._pacing_lock = asyncio.Lock()
        self._last_call_at: float | None = None

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

    async def _wait_for_pacing_slot(self) -> None:
        """Enforces MIN_INTERVAL_SECONDS between the start of any two
        InvokeModel calls made through this client, regardless of how
        many coroutines are calling generate_embedding()."""
        async with self._pacing_lock:
            if self._last_call_at is not None:
                elapsed = time.monotonic() - self._last_call_at
                remaining = MIN_INTERVAL_SECONDS - elapsed
                if remaining > 0:
                    await asyncio.sleep(remaining)
            self._last_call_at = time.monotonic()

    async def generate_embedding(self, text: str) -> list[float]:
        attempt = 0
        while True:
            await self._wait_for_pacing_slot()
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

                backoff_seconds = min(
                    BASE_BACKOFF_SECONDS * (2 ** (attempt - 1)),
                    MAX_BACKOFF_SECONDS,
                )
                logger.warning(
                    "Bedrock embeddings throttled (attempt %s/%s); "
                    "retrying in %.1fs.",
                    attempt,
                    MAX_THROTTLE_RETRIES,
                    backoff_seconds,
                )
                await asyncio.sleep(backoff_seconds)
