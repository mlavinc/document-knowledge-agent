import asyncio
import tempfile
from pathlib import Path

import boto3

from app.core.config import settings


class S3StorageClient:
    """
    Stores uploaded PDFs in S3. Downloads the object to a temp file on
    `save`, so callers (pdf_parser_service, which uses PyMuPDF and needs
    a local file path) don't need to change between providers.
    """

    def __init__(self):
        self._client = boto3.client("s3", region_name=settings.AWS_REGION)
        self._bucket = settings.S3_DOCUMENTS_BUCKET

    def _save_sync(self, filename: str, content: bytes) -> str:
        self._client.put_object(
            Bucket=self._bucket,
            Key=filename,
            Body=content,
            ContentType="application/pdf",
        )

        suffix = Path(filename).suffix or ".pdf"
        tmp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        tmp_file.write(content)
        tmp_file.close()
        return tmp_file.name

    async def save(self, filename: str, content: bytes) -> str:
        return await asyncio.to_thread(self._save_sync, filename, content)
