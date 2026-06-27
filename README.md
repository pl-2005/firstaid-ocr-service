# FIRST-AID OCR Service

FIRST-AID 的独立本地 OCR 推理服务。使用 **RapidOCR（ONNX Runtime）** 搭配 PP-OCR 模型权重，通过稳定的 HTTP 协议向 Java 后端提供图像文字识别。不再依赖 `funasr-asr-service` 进程。

RapidOCR 通过 ONNX Runtime 进行 CPU 推理，相比 PaddleOCR 速度提升 2~5 倍，内存占用更低。

## 服务边界

- 本仓库只负责 OCR 模型加载、图片识别和文字坐标输出。
- Java 后端继续负责 ECG、SpO2、RESP、NIBP 等生命体征匹配。
- HTTP 地址和响应结构保持不变，Java 后端无需修改调用协议。
- 默认监听 `127.0.0.1:8898`，生产环境建议保持单 worker。

## 目录

```text
ocr-service/
  app/
    api/            # OCR 路由和错误响应
    core/           # 环境变量配置
    services/       # RapidOCR 推理封装
    utils/          # 图片上传和临时文件
    main.py         # FastAPI 入口
    schemas.py      # HTTP 响应结构
  scripts/
    create/         # 创建虚拟环境
    delete/         # 删除虚拟环境
    start/          # 启动服务
  tests/
  docs/
```

## Windows 快速启动

```powershell
Copy-Item .env.example .env
.\scripts\create\create-cpu.ps1 -WithDev
.\scripts\start\run-cpu.ps1
```

首次启动时 RapidOCR 会自动下载 ONNX 模型，后续从缓存加载。

生产启动关闭 reload：

```powershell
.\scripts\start\run-cpu.ps1 -NoReload
```

## HTTP 接口

```text
GET  /v1/ocr/health
POST /v1/ocr/warmup
POST /v1/ocr/recognize   multipart field: image
```

验证：

```powershell
curl.exe http://127.0.0.1:8898/v1/ocr/health
curl.exe -X POST http://127.0.0.1:8898/v1/ocr/warmup
curl.exe -X POST http://127.0.0.1:8898/v1/ocr/recognize -F "image=@C:\path\monitor.jpg"
```

`/v1/ocr/health` 的 `model_loaded` 字段可以判断模型是否就绪。

## Java 后端配置

```yaml
ocr:
  provider: paddleocr
  local:
    base-url: http://127.0.0.1:8898
    connect-timeout-ms: 3000
    read-timeout-ms: 120000
```

## 测试

```powershell
python -m pytest tests
```

## Docker 部署

```bash
# docker compose（推荐）
docker compose up -d
docker compose logs -f
docker compose down

# 或手动构建运行
docker build -t firstaid-ocr-service .
docker run -d -p 8898:8898 -v ocr-models:/home/ocruser/.cache/rapidocr --name ocr firstaid-ocr-service

# 健康检查
curl http://127.0.0.1:8898/v1/ocr/health
```

部署细节见 [docs/部署运维说明.md](docs/部署运维说明.md)。
