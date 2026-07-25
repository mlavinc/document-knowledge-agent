from pathlib import Path


class FilesystemStorageClient:
    """
    Stores uploaded PDFs on the local filesystem. Used in local
    development, matching the previous behavior of the ingest endpoint.
    """

    def __init__(self, base_dir: str = "data/uploads"):
        self._base_dir = Path(base_dir)

    async def save(self, filename: str, content: bytes) -> str:
        self._base_dir.mkdir(parents=True, exist_ok=True)
        file_path = self._base_dir / filename
        file_path.write_bytes(content)
        return str(file_path)
