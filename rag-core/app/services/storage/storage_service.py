from app.core.config import settings
from app.services.storage.filesystem_storage_client import (
    FilesystemStorageClient,
)


class StorageService:
    """
    Handles persisting uploaded PDFs. Uses the local filesystem in
    development and S3 in production. The provider is selected via
    STORAGE_PROVIDER.
    """

    def __init__(self):
        if settings.STORAGE_PROVIDER == "s3":
            from app.services.storage.s3_storage_client import S3StorageClient

            self._client = S3StorageClient()
        else:
            self._client = FilesystemStorageClient()

    async def save(self, filename: str, content: bytes) -> str:
        """Persists the file and returns a local path usable by
        pdf_parser_service (which reads PDFs from disk)."""
        return await self._client.save(filename, content)


storage_service = StorageService()
