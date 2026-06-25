from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

from fastapi import UploadFile


class ImageUploadError(ValueError):
    code = "image_upload_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class EmptyImageUploadError(ImageUploadError):
    code = "image_empty"


class ImageUploadTooLargeError(ImageUploadError):
    code = "image_too_large"


async def save_image_upload_to_temp_file(
    upload: UploadFile,
    temp_dir: Optional[Path],
    max_bytes: int,
) -> Path:
    suffix = _suffix_from_filename(upload.filename or "")
    kwargs = {"delete": False, "suffix": suffix}
    if temp_dir:
        temp_dir.mkdir(parents=True, exist_ok=True)
        kwargs["dir"] = str(temp_dir)

    path: Optional[Path] = None
    total_bytes = 0
    try:
        with NamedTemporaryFile(**kwargs) as temp_file:
            path = Path(temp_file.name)
            while chunk := await upload.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    raise ImageUploadTooLargeError(
                        f"image file exceeds {max_bytes // 1024 // 1024} MB"
                    )
                temp_file.write(chunk)
    except ImageUploadError:
        if path:
            path.unlink(missing_ok=True)
        raise

    if total_bytes == 0:
        if path:
            path.unlink(missing_ok=True)
        raise EmptyImageUploadError("image file is empty")

    return path


def _suffix_from_filename(filename: str) -> str:
    suffix = Path(filename).suffix
    return suffix if suffix else ".image"
