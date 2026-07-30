from app.core.config import settings
from app.services.storage.filesystem_storage_client import (
    FilesystemStorageClient,
)


def _ingest_status_key(document_id: str) -> str:
    # Keep a stable, filesystem/S3-safe key derived from the upload name.
    safe = document_id.replace("/", "_").replace("\\", "_")
    return f"ingest-status/{safe}.json"


class StorageService:
    """
    Handles persisting uploaded PDFs (and ingest status markers). Uses
    the local filesystem in development and S3 in production.
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

    async def write_ingest_status(
        self,
        document_id: str,
        status: str,
        *,
        chunks: int | None = None,
        error: str | None = None,
    ) -> None:
        payload: dict = {
            "document_id": document_id,
            "filename": document_id,
            "status": status,
        }
        if chunks is not None:
            payload["chunks"] = chunks
        if error is not None:
            payload["error"] = error
        await self._client.put_json(_ingest_status_key(document_id), payload)

    async def read_ingest_status(self, document_id: str) -> dict | None:
        return await self._client.get_json(_ingest_status_key(document_id))


storage_service = StorageService()
