import json
from pathlib import Path


class FilesystemStorageClient:
    """
    Stores uploaded PDFs (and small JSON side-car files) on the local
    filesystem. Used in local development.
    """

    def __init__(self, base_dir: str = "data/uploads"):
        self._base_dir = Path(base_dir)

    async def save(self, filename: str, content: bytes) -> str:
        file_path = self._base_dir / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)
        return str(file_path)

    async def put_json(self, key: str, payload: dict) -> None:
        path = self._base_dir / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    async def get_json(self, key: str) -> dict | None:
        path = self._base_dir / key
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))
