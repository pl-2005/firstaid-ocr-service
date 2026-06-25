from pathlib import Path

from fastapi import APIRouter, File, UploadFile, status

from app.api.errors import api_error
from app.core.config import settings
from app.schemas import OcrHealthResponse, OcrRecognizeResponse, OcrWordResponse
from app.services.ocr import OcrEngineError, ocr_engine
from app.utils.image import (
    ImageUploadError,
    save_image_upload_to_temp_file,
)

router = APIRouter()


@router.get("/v1/ocr/health", response_model=OcrHealthResponse)
async def ocr_health() -> OcrHealthResponse:
    return OcrHealthResponse(
        status="ok",
        engine="rapidocr",
        model="PP-OCR-v4",
        device="cpu",
        model_loaded=ocr_engine.is_loaded,
        version=settings.app_version,
    )


@router.post("/v1/ocr/warmup", response_model=OcrHealthResponse)
async def ocr_warmup() -> OcrHealthResponse:
    try:
        ocr_engine.load()
    except OcrEngineError as exc:
        raise api_error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "ocr_model_load_failed",
            str(exc),
        ) from exc

    return await ocr_health()


@router.post("/v1/ocr/recognize", response_model=OcrRecognizeResponse)
async def recognize(image: UploadFile = File(...)) -> OcrRecognizeResponse:
    _validate_image_file(image)

    try:
        temp_path = await save_image_upload_to_temp_file(
            image,
            settings.resolved_temp_dir,
            settings.max_upload_bytes,
        )
    except ImageUploadError as exc:
        status_code = (
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
            if exc.code == "image_too_large"
            else status.HTTP_400_BAD_REQUEST
        )
        raise api_error(status_code, exc.code, exc.message) from exc

    try:
        result = ocr_engine.recognize(temp_path)
        return OcrRecognizeResponse(
            engine="rapidocr",
            model="PP-OCR-v4",
            device="cpu",
            duration_ms=result.duration_ms,
            words_result=[
                OcrWordResponse.from_ocr_word(word)
                for word in result.words
            ],
        )
    except OcrEngineError as exc:
        raise api_error(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "ocr_recognize_failed",
            str(exc),
        ) from exc
    finally:
        temp_path.unlink(missing_ok=True)


def _validate_image_file(image: UploadFile) -> None:
    if not image.filename:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "image_filename_required",
            "image filename is required",
        )

    suffix = Path(image.filename).suffix.lower()
    if suffix not in settings.allowed_image_suffixes:
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "unsupported_image_type",
            (
                f"unsupported image extension: {suffix or '<none>'}; "
                f"allowed: {', '.join(sorted(settings.allowed_image_suffixes))}"
            ),
        )
