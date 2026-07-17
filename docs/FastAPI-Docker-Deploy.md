# FastAPI Docker生产部署文档


## 1. 部署架构


```
Nginx

 |

FastAPI Container

 |

Python Runtime

 |

OCR Model
```



---

# 2. 项目结构


调整：

```
firstaid-ocr-service-main

├── app

│   └── main.py


├── requirements.txt


├── Dockerfile


└── docker-compose.yml

```

---

# 3. Dockerfile


创建：

```
Dockerfile
```


内容：

```dockerfile
FROM python:3.12-slim


WORKDIR /app


COPY requirements.txt .


RUN pip install --no-cache-dir \
    -r requirements.txt


COPY . .


EXPOSE 8898


CMD [
"uvicorn",
"app.main:app",
"--host",
"0.0.0.0",
"--port",
"8898",
"--workers",
"1"
]
```

---

# 4. 创建docker-compose


docker-compose.yml


```yaml
services:


  ocr-service:


    build: .


    container_name: firstaid-ocr


    restart: always


    ports:

      - "127.0.0.1:8898:8898"


    volumes:

      - ./logs:/app/logs


    environment:

      TZ: Asia/Shanghai

```

---

# 5. 构建镜像


```bash
docker compose build
```


查看：

```bash
docker images
```

---

# 6. 启动服务


后台启动：

```bash
docker compose up -d
```


查看：

```bash
docker ps
```

---

# 7. 查看日志


实时：

```bash
docker logs -f firstaid-ocr
```


最近：

```bash
docker logs --tail 100 firstaid-ocr
```

---

# 8. 服务管理


停止：

```bash
docker compose down
```


启动：

```bash
docker compose up -d
```


重启：

```bash
docker restart firstaid-ocr
```

---

# 9. 更新部署


拉取代码：

```bash
git pull
```


重新构建：

```bash
docker compose build
```


重新启动：

```bash
docker compose up -d
```

---

# 10. Nginx代理


```
用户

 |

Nginx

 |

127.0.0.1:8898

 |

Docker FastAPI

```


配置：

```nginx
location /ocr/ {


proxy_pass http://127.0.0.1:8898/;


}

```

---

# 11. 健康检查


增加：

```yaml
healthcheck:

  test:
    [
      "CMD",
      "curl",
      "-f",
      "http://localhost:8898"
    ]

  interval:30s

  timeout:5s

  retries:3
```

---

# 12. 优点


优点：

- 环境隔离
- 部署一致
- 易迁移
- 方便扩容
- 适合微服务


缺点：

- 需要维护镜像
- 初始配置复杂


适合：

- 多服务系统

- AI服务

- 微服务架构

- 云服务器部署

  