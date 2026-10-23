# Docker 镜像

> 状态核对：2026-10-23。最新已查询的 master [Actions 39897322500](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39897322500)（`9837e71`）成功；首次发布 digest 仍保留在 [历史记录](releases/2026-10-21-c1d7b6a.json)。本会话观察到服务器前后端健康，但未将运行 digest 与发布记录逐项对应。新增 TTS 构建参数、配置同步和面试重构尚未生成新的已验证镜像。开发机未运行 Docker。

前端镜像的 `/var/www/backend-static`、`/var/www/media` 与后端写入进程统一使用 UID/GID `10001:10001`，避免空共享卷由前端先初始化后，后端无法写入。Nginx 仍只读挂载这些卷；此镜像修改不会自动修正已有卷的属主，已有数据需另行评估。

当前本地 `Dockerfile.frontend` 新增公开参数 `VITE_ENABLE_TTS`，workflow 从同名 Variable 传入，缺省 False。参数在构建时写入静态资源，不能用于传 Key；运行时只更新 `.env` 不会改变已构建页面。模型与 SSH Secrets 只在可选同步 Job 中使用，不进入镜像。

面试 legacy 重构随应用代码进入镜像，不新增服务、数据表或迁移；通过编译和离线测试不等于模型/语音已可用，详见 [重构说明](interview-refactor.md)。当前后端演示依赖仍未包含 `sentence-transformers`，本地向量模型未随此次改动启用。

## 镜像地址

```text
crpi-gbihc3e57h3o3f2l.cn-hangzhou.personal.cr.aliyuncs.com/tencent-ubutun22/cs-career-guide-backend
crpi-gbihc3e57h3o3f2l.cn-hangzhou.personal.cr.aliyuncs.com/tencent-ubutun22/cs-career-guide-frontend
```

标签规则：

- `latest`：演示环境跟踪标签，Watchtower 默认关注它。
- `sha-<7位提交>`：源码追踪标签，可能被覆盖；精确回滚使用发布记录中的 `repository@sha256:<digest>`。
- 手动触发时可额外指定一个 tag。

## 后端镜像

- 使用多阶段 `python:3.11-slim-bookworm`。
- builder 阶段安装编译工具和 `default-libmysqlclient-dev`，根据 `requirements-runtime.txt` 预构建 wheel。
- runtime 阶段只安装 MariaDB 客户端运行库，复制后端源码，并以非 root 用户运行。
- 启动时依次执行 `collectstatic`、`migrate`、Gunicorn；任一步失败就让容器退出，避免 Watchtower 认为不健康版本已发布。
- 演示 Compose 默认 `GUNICORN_WORKERS=1`；独立运行镜像且未指定该值时，入口脚本仍使用 `min(2*CPU+1, 4)`。超时默认 300 秒。
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
- 当前功能分支使用 UID/GID `10001:10001` 运行 Nginx，监听容器内 `8080`；PID 放在 `/tmp`，缓存目录由有限大小的 tmpfs 提供。旧发布 `c1d7b6a` 的前端仍监听 `80`，部署文件和镜像必须配套更新。
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

Compose 的非 root、只读根目录、无额外 capability、CPU/内存/进程数及日志上限，还会在真实联调启动后通过 Docker inspect 核对。检查不读取容器环境变量，详见 [宿主机保护边界](host-protection.md)。
