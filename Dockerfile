# FIRST-AID OCR Service
# RapidOCR (ONNX Runtime) + FastAPI, single-worker CPU inference.
#
# Build:
#   docker build -t firstaid-ocr-service .
#
# Run (auto-download models on first start):
#   docker run -d -p 8898:8898 --name ocr firstaid-ocr-service
#
# Persist models across restarts:
#   docker run -d -p 8898:8898 -v ocr-models:/home/ocruser/.cache/rapidocr firstaid-ocr-service

FROM python:3.11-slim-bookworm

# ONNX Runtime CPU needs libgomp1 for parallel inference
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY requirements-common.txt requirements-cpu.txt ./
RUN pip install --no-cache-dir -r requirements-cpu.txt \
    && rm requirements-common.txt requirements-cpu.txt

# Copy application code
COPY app/ ./app/

# Create non-root user for running the service
RUN useradd --create-home --home-dir /home/ocruser ocruser \
    && chown -R ocruser:ocruser /app /home/ocruser

USER ocruser

# Production defaults (override via -e or env_file)
ENV OCR_HOST=0.0.0.0
ENV OCR_PORT=8898
ENV OCR_AUTO_LOAD=true
ENV OCR_LOG_LEVEL=info

EXPOSE 8898

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; f=urllib.request.urlopen('http://127.0.0.1:8898/v1/ocr/health'); exit(0 if f.status==200 else 1)"

# Single worker — model is a process-level singleton
CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8898", \
     "--workers", "1"]
