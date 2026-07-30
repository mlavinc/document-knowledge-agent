import asyncio
import json
import tempfile
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

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

    def _put_json_sync(self, key: str, payload: dict) -> None:
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=json.dumps(payload).encode("utf-8"),
            ContentType="application/json",
        )

    def _get_json_sync(self, key: str) -> dict | None:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") in {
                "NoSuchKey",
                "404",
                "NotFound",
            }:
                return None
            raise
        body = response["Body"].read().decode("utf-8")
        return json.loads(body)

    async def put_json(self, key: str, payload: dict) -> None:
        await asyncio.to_thread(self._put_json_sync, key, payload)

    async def get_json(self, key: str) -> dict | None:
        return await asyncio.to_thread(self._get_json_sync, key)
