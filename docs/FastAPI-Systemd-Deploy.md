# FastAPI 服务 systemd 部署文档

## 1. 部署说明

使用 systemd 管理 FastAPI 服务，实现：

- 服务后台运行
- SSH退出不中断
- 开机自动启动
- 异常自动重启
- 统一日志管理


部署结构：

```
Nginx

  |

FastAPI OCR Service

  |

Uvicorn

  |

Python Virtual Environment
```

---

# 2. 项目目录


示例：

```
/opt/CQUT/ocr-service/firstaid-ocr-service-main

├── app
│   └── main.py
│
├── .venv
│
├── requirements.txt
│
└── logs
```

---

# 3. 创建systemd服务


创建：

```bash
sudo vim /etc/systemd/system/ocr-service.service
```


写入：

```ini
[Unit]

Description=First Aid OCR FastAPI Service

After=network.target



[Service]

Type=simple


User=sysadmin


WorkingDirectory=/opt/CQUT/ocr-service/firstaid-ocr-service-main


ExecStart=/opt/CQUT/ocr-service/firstaid-ocr-service-main/.venv/bin/python \
-m uvicorn app.main:app \
--host 127.0.0.1 \
--port 8898 \
--workers 1


Restart=always

RestartSec=5



[Install]

WantedBy=multi-user.target
```

---

# 4. 加载配置


```bash
sudo systemctl daemon-reload
```

---

# 5. 启动服务


```bash
sudo systemctl start ocr-service
```


查看状态：

```bash
systemctl status ocr-service
```


正常：

```
Active: active (running)
```

---

# 6. 设置开机启动


```bash
sudo systemctl enable ocr-service
```


查看：

```bash
systemctl is-enabled ocr-service
```

---

# 7. 查看日志


实时日志：

```bash
journalctl -u ocr-service -f
```


查看最近日志：

```bash
journalctl -u ocr-service -n 100
```

---

# 8. 服务管理


启动：

```bash
systemctl start ocr-service
```


停止：

```bash
systemctl stop ocr-service
```


重启：

```bash
systemctl restart ocr-service
```


状态：

```bash
systemctl status ocr-service
```

---

# 9. 测试服务


服务器内部：

```bash
curl http://127.0.0.1:8898
```


查看端口：

```bash
netstat -tunlp | grep 8898
```

---

# 10. Nginx代理


配置：

```nginx
server {

    listen 80;

    server_name example.com;


    location /ocr/ {


        proxy_pass http://127.0.0.1:8898/;


        proxy_set_header Host $host;

        proxy_set_header X-Real-IP $remote_addr;

    }

}
```


检查：

```bash
nginx -t
```


重启：

```bash
systemctl restart nginx
```

---

# 11. 更新部署


进入目录：

```bash
cd /opt/CQUT/ocr-service/firstaid-ocr-service-main
```


更新代码：

```bash
git pull
```


更新依赖：

```bash
.venv/bin/pip install -r requirements.txt
```


重启：

```bash
systemctl restart ocr-service
```

---

# 12. 优点


优点：

- 配置简单
- 性能损耗低
- 不需要Docker环境
- 适合单服务部署


缺点：

- 环境依赖服务器
- 多服务管理复杂


适合：

- 单个Python服务
- 内网服务
- 小型生产环境