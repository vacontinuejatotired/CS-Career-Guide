# Docker 镜像

> 状态：基线提交 `3480b91` 的两个 Dockerfile 已在 [Actions 39540701547](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39540701547) 完成构建和容器冒烟，未推送 ACR；开发机未运行 Docker。服务器部署尚未验证。

前端镜像的 `/var/www/backend-static`、`/var/www/media` 与后端写入进程统一使用 UID/GID `10001:10001`，避免空共享卷由前端先初始化后，后端无法写入。Nginx 仍只读挂载这些卷；此镜像修改不会自动修正已有卷的属主，已有数据需另行评估。

## 镜像地址

```text
crpi-gbihc3e57h3o3f2l.cn-hangzhou.personal.cr.aliyuncs.com/tencent-ubutun22/cs-career-guide-backend
crpi-gbihc3e57h3o3f2l.cn-hangzhou.personal.cr.aliyuncs.com/tencent-ubutun22/cs-career-guide-frontend
```

标签规则：

- `latest`：演示环境跟踪标签，Watchtower 默认关注它。
- `sha-<7位提交>`：不可变回滚标签。
- 手动触发时可额外指定一个 tag。

## 后端镜像

- 使用多阶段 `python:3.11-slim-bookworm`。
- builder 阶段安装编译工具和 `default-libmysqlclient-dev`，根据 `requirements-runtime.txt` 预构建 wheel。
- runtime 阶段只安装 MariaDB 客户端运行库，复制后端源码，并以非 root 用户运行。
- 启动时依次执行 `collectstatic`、`migrate`、Gunicorn；任一步失败就让容器退出，避免 Watchtower 认为不健康版本已发布。
- Gunicorn worker 默认 `min(2*CPU+1, 4)`，可通过 `GUNICORN_WORKERS` 覆盖；超时默认 300 秒。
- 进程级健康检查只检查本机 8000 端口，不是业务健康接口。

### 运行时依赖边界

`requirements-runtime.txt` 有意排除：

- `torch`、`torchaudio`、`torchvision`
- `sentence-transformers`
- `transformers`

LanceDB、PyArrow、NumPy 仍保留。语义模型包缺失时应降级为空结果，不能阻止 Django 加载或登录、业务页面启动。`langgraph` 仍是启动必需依赖，CI 会安装完整测试依赖。

## 前端镜像

- 构建阶段使用 `node:24-bookworm-slim`。
- 运行阶段使用 `nginx:1.27-alpine`。
- 保留 `frontend/public/models` 中的 GLB 和 VAD 资源，因为它们是运行时资源。
- Nginx 提供 Vite 构建产物，支持 Vue history 路由回退，并把 `/api` 反向代理到后端。
- `/company-api` 在未配置外部企业服务时返回 503。
- 请求体上限为 20 MiB。流式聊天关闭代理缓冲并使用 300 秒超时。

## 构建上下文与缓存

根目录 `.dockerignore` 排除 Git 元数据、虚拟环境、运行时数据、文档、媒体、旧 LanceDB、Python 缓存和 Nginx 配置；前端 GLB 与 VAD 资源通过例外规则保留。

GitHub Actions 使用 `type=gha` 分层缓存，前后端 scope 分别为：

```text
cs-career-guide-backend
cs-career-guide-frontend
```

不要用 registry cache 作为 ACR 个人版的兜底；不支持的 cache manifest 会导致构建失败。

## CI 验证

本项目的 Docker build 和容器启动检查在 GitHub Actions 的 PR/build-only 流程执行，不在开发机运行 Docker。后端检查容器启动、静态文件收集、SQLite 迁移和 Gunicorn 健康状态；前端检查 Nginx 启动、首页、history 路由、API 代理路由、企业服务 503 响应以及 GLB/VAD 资源。

这些 build-only 检查不登录 ACR、不推送镜像，也不能替代真实服务器验证。
