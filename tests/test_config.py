from app.core.config import PROJECT_ROOT, Settings


def test_model_cache_dir_resolves_relative_to_project_root() -> None:
    settings = Settings(OCR_MODEL_CACHE_DIR="model_cache")

    assert settings.resolved_model_cache_dir == PROJECT_ROOT / "model_cache"


def test_temp_dir_resolves_relative_to_project_root() -> None:
    settings = Settings(OCR_TEMP_DIR="tmp")

    assert settings.resolved_temp_dir == PROJECT_ROOT / "tmp"


def test_allowed_image_suffixes_are_normalized() -> None:
    settings = Settings(OCR_ALLOWED_IMAGE_EXTENSIONS=".JPG, .png,,.webp")

    assert settings.allowed_image_suffixes == {".jpg", ".png", ".webp"}
