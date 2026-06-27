# FIRST-AID OCR Service
# RapidOCR (ONNX Runtime) + FastAPI，单 worker CPU 推理。
#
# 构建：
#   docker build -t firstaid-ocr-service .
#
# 运行（首次启动自动下载模型）：
#   docker run -d -p 8898:8898 --name ocr firstaid-ocr-service
#
# 持久化模型缓存，避免重启后重新下载：
#   docker run -d -p 8898:8898 -v ocr-models:/home/ocruser/.cache/rapidocr firstaid-ocr-service

FROM python:3.11-slim-bookworm

# ONNX Runtime CPU 需要 libgomp1 进行并行推理
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先安装 Python 依赖（利用 Docker 层缓存）
COPY requirements-common.txt requirements-cpu.txt ./
RUN pip install --no-cache-dir -r requirements-cpu.txt \
    && rm requirements-common.txt requirements-cpu.txt

# 复制应用代码
COPY app/ ./app/

# 创建非 root 用户运行服务
RUN useradd --create-home --home-dir /home/ocruser ocruser \
    && chown -R ocruser:ocruser /app /home/ocruser

USER ocruser

# 生产环境默认值（可通过 -e 或 env_file 覆盖）
ENV OCR_HOST=0.0.0.0
ENV OCR_PORT=8898
ENV OCR_AUTO_LOAD=true
ENV OCR_LOG_LEVEL=info

EXPOSE 8898

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; f=urllib.request.urlopen('http://127.0.0.1:8898/v1/ocr/health'); exit(0 if f.status==200 else 1)"

# 单 worker —— 模型是进程级单例，多 worker 会重复加载
CMD ["python", "-m", "uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8898", \
     "--workers", "1"]
