import uuid
from pathlib import Path

from fastapi import UploadFile

MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


async def save_upload(file: UploadFile, directory: Path) -> tuple[Path, int]:
    """Stream an upload to disk under a random filename (never trust the
    original name for the path) and return (path, size_in_bytes)."""

    directory.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "").suffix[:10]
    destination = directory / f"{uuid.uuid4()}{suffix}"

    size = 0
    with open(destination, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                out.close()
                destination.unlink(missing_ok=True)
                raise ValueError("File exceeds maximum upload size (20 MB)")
            out.write(chunk)

    return destination, size
