import asyncio
import json
import logging
import time
from typing import Literal

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.utils.exceptions import EmbeddingProviderError

logger = logging.getLogger(__name__)

EmbeddingPurpose = Literal["query", "ingestion"]

# Ingestion runs as a fire-and-forget async Lambda invocation (see
# api-gateway's ingestDocumentAsync), decoupled from API Gateway's ~29s
# hard timeout. It can wait out a tight Bedrock quota within this
# Lambda's own 300s timeout.
INGESTION_MAX_THROTTLE_RETRIES = 7
INGESTION_BASE_BACKOFF_SECONDS = 1.0
INGESTION_MAX_BACKOFF_SECONDS = 20.0

# Interactive search is synchronous end-to-end and must stay well under
# API Gateway's ~29s limit. Fail fast so the frontend gets a controlled
# error instead of hanging until the connection is cut.
# Worst-case sleep budget: 1s + 2s = 3s (+ invoke latency) ≪ 15s.
QUERY_MAX_THROTTLE_RETRIES = 2
QUERY_BASE_BACKOFF_SECONDS = 1.0
QUERY_MAX_BACKOFF_SECONDS = 2.0

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
    OllamaClient, with purpose-specific throttle retry budgets.
    """

    def __init__(self):
        self._client = boto3.client(
            "bedrock-runtime", region_name=settings.AWS_REGION
        )
        self._pacing_lock = asyncio.Lock()
        self._last_call_at: float | None = None

    def _retry_profile(self, purpose: EmbeddingPurpose) -> tuple[int, float, float]:
        if purpose == "query":
            return (
                QUERY_MAX_THROTTLE_RETRIES,
                QUERY_BASE_BACKOFF_SECONDS,
                QUERY_MAX_BACKOFF_SECONDS,
            )
        return (
            INGESTION_MAX_THROTTLE_RETRIES,
            INGESTION_BASE_BACKOFF_SECONDS,
            INGESTION_MAX_BACKOFF_SECONDS,
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

    async def generate_embedding(
        self,
        text: str,
        *,
        purpose: EmbeddingPurpose = "ingestion",
    ) -> list[float]:
        max_retries, base_backoff, max_backoff = self._retry_profile(purpose)
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
                if attempt > max_retries:
                    logger.error(
                        "Bedrock embeddings throttled and exhausted all "
                        "%s retries (purpose=%s); giving up.",
                        max_retries,
                        purpose,
                    )
                    raise EmbeddingProviderError(
                        "The embeddings service is temporarily overloaded. "
                        "Please try again in a moment."
                    ) from error

                backoff_seconds = min(
                    base_backoff * (2 ** (attempt - 1)),
                    max_backoff,
                )
                logger.warning(
                    "Bedrock embeddings throttled (attempt %s/%s, "
                    "purpose=%s); retrying in %.1fs.",
                    attempt,
                    max_retries,
                    purpose,
                    backoff_seconds,
                )
                await asyncio.sleep(backoff_seconds)
