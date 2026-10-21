# 服务器拉取部署

> 状态：草案。尚未连接服务器、启动容器，也未迁移任何数据。

## 部署拓扑

```text
浏览器 -> 宿主机 :48080 -> frontend（Nginx）
                              |-- /api/ -> backend :8000
                              `-- /static、/media -> 共享卷

backend -> sqlite-data:/data
backend -> backend-static:/data/staticfiles
backend -> media:/data/media
watchtower -> Docker socket + 服务器本地 Docker 凭据
```

宿主机只开放前端端口；后端、SQLite 和 Watchtower 不直接暴露业务端口。

## 低资源演示默认值

- 数据库：SQLite，保存到 `sqlite-data` 持久卷。
- Django 配置：`cs_career_guide.settings_sqlite`。
- 向量模式：LanceDB 目录存在，但默认关闭嵌入模型；语义检索可能返回空结果。
- 媒体：空持久卷，现有上传文件不会自动复制。
- 静态文件：后端 `collectstatic` 写入共享卷，Nginx 只读提供。
- MySQL：只通过可选 `mysql` Compose profile 和显式 settings 切换启用。

SQLite 只适合低并发演示，不是正式生产数据库方案。

## ACR 登录

GitHub Actions 使用公网 Registry：

```text
crpi-gbihc3e57h3o3f2l.cn-hangzhou.personal.cr.aliyuncs.com
```

服务器如果位于同一 VPC，可以使用 VPC 地址：

```text
crpi-gbihc3e57h3o3f2l-vpc.cn-hangzhou.personal.cr.aliyuncs.com
```

公网和 VPC 地址指向同一组仓库，按服务器实际网络选择；不要假设 GitHub Actions 能访问 VPC 地址。

首次启动 Watchtower 前先手动登录：

```bash
docker login --username=<ACR_USERNAME> crpi-gbihc3e57h3o3f2l.cn-hangzhou.personal.cr.aliyuncs.com
```

不要把 Registry 密码写入 Compose 或 `.env`。

## 准备服务器

要求：

- Docker Engine 与 Compose v2。
- 能访问 ACR。
- 可写的部署目录。
- 生成的 Django `SECRET_KEY`。

把部署文件放到服务器后，从样例创建环境文件：

```bash
cd deploy
cp .env.example .env
# 在服务器本地编辑 .env，不能提交。
docker compose config
```

如果服务器使用 VPC 地址，请只修改 `.env` 中的 Registry 主机名。设置 `SECRET_KEY`，并让 `ALLOWED_HOSTS` 与演示地址一致；IP 访问只适合临时演示，不能宣称已具备公网生产条件。

## 启动与验证

```bash
cd deploy
docker compose pull
docker compose up -d --no-build
docker compose ps
docker compose logs --tail=100 backend
docker compose logs --tail=100 frontend
```

检查项：

1. `http://<服务器IP>:48080/` 能显示 Vue 页面。
2. `/login` 和 `/register` 可以打开。
3. 没有 Token 访问业务页面会跳转登录。
4. 注册、登录后能拿到 Token 并返回原业务路径。
5. `/api/` 由 Nginx 代理，后端端口不对宿主机公开。
6. `/static/` 和 `/media/` 能通过 Nginx 访问。
7. 容器日志中不出现密钥。

应用使用进程级检查，不是业务健康接口；端口可连不等于数据库、AI 或外部企业服务都健康。

## 数据持久化与备份

默认卷：

```text
sqlite-data
backend-static
media
mysql-data   # 只有启用 MySQL profile 时使用
```

SQLite 建议在应用停止时冷备份：

```bash
docker compose stop backend
docker run --rm -v <PROJECT>_sqlite-data:/data -v "$PWD/backups:/backup" alpine \
  sh -c 'cp /data/cs-career-guide.sqlite3 /backup/cs-career-guide.sqlite3'
docker compose start backend
```

先用 `docker volume ls` 确认真实卷名，不要直接使用占位符。媒体卷和静态卷有用户内容时也要分别备份。

## 以后切换 MySQL

先启动可选服务：

```bash
docker compose --profile mysql up -d mysql
```

然后在 `.env` 中显式切换到原有 MySQL settings，并提供完整数据库变量：

```text
DJANGO_SETTINGS_MODULE=cs_career_guide.settings
DATABASE_NAME=cs_career_guide
DATABASE_USER=cs_career_guide
DATABASE_PASSWORD=<服务器密钥>
DATABASE_HOST=mysql
DATABASE_PORT=3306
MYSQL_ROOT_PASSWORD=<服务器密钥>
```

只加 `--profile mysql` 不会让 Django 自动改用 MySQL。不要自动迁移现有 SQLite 数据；迁移必须单独设计、备份和验证。

## 更新与回滚

Watchtower 负责演示环境更新，详见 [Watchtower 与回滚](watchtower-rollback.md)。手动拉取：

```bash
cd deploy
docker compose pull
docker compose up -d --no-build
```

按 SHA 回滚时，把 `BACKEND_TAG` 和/或 `FRONTEND_TAG` 改成已验证的不可变 tag，先暂停 Watchtower，再重建受影响服务，避免它自动把容器拉回 `latest`。

## 当前限制

- 没有 HTTPS 和域名证书。
- 没有自动迁移已有媒体或 SQLite 数据。
- 没有真实 MySQL 迁移验证。
- 没有真实 AI 费用验证。
- 不能宣称已完成公网上线。