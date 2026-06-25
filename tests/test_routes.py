from pathlib import Path

from fastapi.testclient import TestClient

from app.api import routes
from app.core.config import settings
from app.main import app
from app.services.ocr import OcrResult, OcrWord


class FakeOcrEngine:
    def __init__(self) -> None:
        self.loaded = False

    @property
    def is_loaded(self) -> bool:
        return self.loaded

    def load(self) -> None:
        self.loaded = True

    def recognize(self, image_path: Path) -> OcrResult:
        assert image_path.exists()
        self.loaded = True
        return OcrResult(
            duration_ms=8,
            words=[
                OcrWord(
                    words="ECG",
                    left=20,
                    top=30,
                    width=60,
                    height=24,
                    score=0.97,
                ),
                OcrWord(
                    words="86",
                    left=95,
                    top=30,
                    width=38,
                    height=24,
                    score=0.99,
                ),
            ],
        )


def test_v1_ocr_health() -> None:
    response = TestClient(app).get("/v1/ocr/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["engine"] == "rapidocr"


def test_v1_ocr_warmup_loads_model(monkeypatch) -> None:
    fake_engine = FakeOcrEngine()
    monkeypatch.setattr(routes, "ocr_engine", fake_engine)

    response = TestClient(app).post("/v1/ocr/warmup")

    assert response.status_code == 200
    assert response.json()["model_loaded"] is True


def test_v1_ocr_recognize_returns_stable_response(monkeypatch) -> None:
    monkeypatch.setattr(routes, "ocr_engine", FakeOcrEngine())

    response = TestClient(app).post(
        "/v1/ocr/recognize",
        files={"image": ("monitor.jpg", b"fake-jpg", "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "engine": "rapidocr",
        "model": "PP-OCR-v4",
        "device": "cpu",
        "duration_ms": 8,
        "words_result": [
            {
                "words": "ECG",
                "location": {
                    "left": 20,
                    "top": 30,
                    "width": 60,
                    "height": 24,
                },
                "score": 0.97,
            },
            {
                "words": "86",
                "location": {
                    "left": 95,
                    "top": 30,
                    "width": 38,
                    "height": 24,
                },
                "score": 0.99,
            },
        ],
    }


def test_v1_ocr_recognize_rejects_unsupported_extension() -> None:
    response = TestClient(app).post(
        "/v1/ocr/recognize",
        files={"image": ("monitor.txt", b"not-image", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["success"] is False
    assert response.json()["code"] == "unsupported_image_type"


def test_v1_ocr_recognize_rejects_empty_image() -> None:
    response = TestClient(app).post(
        "/v1/ocr/recognize",
        files={"image": ("monitor.jpg", b"", "image/jpeg")},
    )

    assert response.status_code == 400
    assert response.json() == {
        "success": False,
        "code": "image_empty",
        "message": "image file is empty",
    }


def test_v1_ocr_recognize_rejects_oversized_image(monkeypatch) -> None:
    monkeypatch.setattr(settings, "max_upload_size_mb", 0)

    response = TestClient(app).post(
        "/v1/ocr/recognize",
        files={"image": ("monitor.jpg", b"x", "image/jpeg")},
    )

    assert response.status_code == 413
    assert response.json()["success"] is False
    assert response.json()["code"] == "image_too_large"
