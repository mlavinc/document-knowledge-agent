class EmbeddingProviderError(Exception):
    """Raised when the embeddings provider cannot fulfill a request.

    Used to surface a controlled failure from the embeddings provider
    on the interactive search path instead of waiting until an upstream
    gateway timeout.
    """
