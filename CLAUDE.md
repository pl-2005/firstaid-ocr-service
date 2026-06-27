# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

FIRST-AID OCR Service — a standalone local OCR inference service that uses FastAPI + RapidOCR (ONNX Runtime with PP-OCR model weights) to extract text with bounding boxes and confidence scores from medical monitor screenshots. It exposes a stable HTTP API consumed by a Java backend for vital-signs matching (ECG, SpO2, RESP, NIBP). The service replaces a previous dependency on `funasr-asr-service`.

**Boundary**: this repo handles OCR model loading, image recognition, and text-coordinate output only. Vitals matching happens in the Java backend.

## Commands

```powershell
# First-time setup
Copy-Item .env.example .env
.\scripts\create\create-cpu.ps1 -WithDev

# Start dev server (with hot reload)
.\scripts\start\run-cpu.ps1

# Production start (single worker, no reload)
.\scripts\start\run-cpu.ps1 -NoReload

# Run all tests
python -m pytest tests

# Run a single test file
python -m pytest tests/test_routes.py

# Run a specific test function
python -m pytest tests/test_engine.py::test_parse_result_converts_box_to_bounds -v

# Verify the service is healthy
curl http://127.0.0.1:8898/v1/ocr/health
curl -X POST http://127.0.0.1:8898/v1/ocr/warmup
```

```bash
# Docker compose
docker compose up -d
docker compose logs -f

# 使用测试图片验证
curl -X POST http://127.0.0.1:8898/v1/ocr/recognize -F "image=@tests/test1.jpg"
```

## Architecture

```
app/
  main.py            # FastAPI app factory with lifespan (auto-load on startup)
  api/routes.py      # 3 endpoints: health, warmup, recognize
  api/errors.py      # Structured error helpers (api_error + exception handler)
  core/config.py     # pydantic-settings from .env
  services/ocr.py    # RapidOcrEngine — ONNX Runtime inference wrapper
  utils/image.py     # Upload validation, temp file saving, size enforcement
  schemas.py         # Pydantic request/response models
```

### Key design decisions

**RapidOCR + ONNX Runtime** (`services/ocr.py:RapidOcrEngine`): uses the same PP-OCR model weights as PaddleOCR but runs inference through ONNX Runtime, which is 2–5× faster on CPU and uses less memory. The engine downloads ONNX models automatically on first use and caches them locally. Engine lifetime is managed as a module-level singleton — loaded once at warmup or on first request.

**Bounding box conversion** (`services/ocr.py:_box_to_bounds`): RapidOCR returns four-corner polygons `[[x1,y1], …, [x4,y4]]`. The helper computes axis-aligned `{left, top, width, height}` from min/max coordinates. It also handles flat `[x1, y1, x2, y2]` rectangles for forward compatibility.

**Error response convention**: every error response has `{"success": false, "code": "<machine_readable>", "message": "<human_readable>"}`. The `api_error()` helper in `errors.py` creates `HTTPException` with this shape; the exception handler passes it through as JSON. Unrecognized HTTPExceptions get wrapped in this shape too.

**Single-worker design**: the model is loaded once into process memory via the module-level `ocr_engine` singleton. Running multiple uvicorn workers would duplicate the model (heavy memory cost). Production should use `--workers 1`.

### Test patterns

Tests live in `tests/`. Route tests use `fastapi.testclient.TestClient` + `monkeypatch` to inject a `FakeOcrEngine` in place of `routes.ocr_engine`. Engine tests instantiate `RapidOcrEngine` directly and call private methods via the `_` prefix convention. Config tests create `Settings` instances with specific env overrides via constructor kwargs.

### Environment and requirements

- **Python 3.11** required
- `requirements-common.txt` — FastAPI, uvicorn, pydantic-settings
- `requirements-cpu.txt` — `rapidocr-onnxruntime>=1.3.0`, opencv-python-headless, Pillow
- `requirements-dev.txt` — pytest, httpx
- `.env` is `.gitignore`d; `.env.example` is the template
