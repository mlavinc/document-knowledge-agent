class EmbeddingProviderError(Exception):
    """Raised when the embeddings provider cannot fulfill a request.

    Used to surface a controlled failure (e.g. Bedrock throttling after
    fail-fast retries on the interactive search path) instead of letting
    the request wait until an upstream gateway timeout.
    """
