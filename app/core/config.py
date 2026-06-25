from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "FIRST-AID OCR Service"
    app_version: str = "0.1.0"

    host: str = Field(default="127.0.0.1", alias="OCR_HOST")
    port: int = Field(default=8898, alias="OCR_PORT")
    log_level: str = Field(default="info", alias="OCR_LOG_LEVEL")
    lang: str = Field(default="ch", alias="OCR_LANG")
    auto_load: bool = Field(default=False, alias="OCR_AUTO_LOAD")
    max_upload_size_mb: int = Field(default=20, alias="OCR_MAX_UPLOAD_SIZE_MB")
    allowed_image_extensions: str = Field(
        default=".jpg,.jpeg,.png,.bmp,.webp",
        alias="OCR_ALLOWED_IMAGE_EXTENSIONS",
    )
    model_cache_dir: Path = Field(
        default=Path("model_cache"),
        alias="OCR_MODEL_CACHE_DIR",
    )
    temp_dir: Path = Field(default=Path("tmp"), alias="OCR_TEMP_DIR")

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def allowed_image_suffixes(self) -> set[str]:
        return {
            extension.strip().lower()
            for extension in self.allowed_image_extensions.split(",")
            if extension.strip()
        }

    @property
    def resolved_model_cache_dir(self) -> Path:
        return _resolve_project_path(self.model_cache_dir)

    @property
    def resolved_temp_dir(self) -> Path:
        return _resolve_project_path(self.temp_dir)


def _resolve_project_path(path: Path) -> Path:
    return path if path.is_absolute() else PROJECT_ROOT / path


settings = Settings()
