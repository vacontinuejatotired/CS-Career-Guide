# Watchtower 与回滚

> 2026-10-23 状态：仓库默认关闭 Watchtower，仅放在 `updates` profile；但本会话已观察到服务器旧 Watchtower 运行。本次没有停止它，也没有验证其更新效果或演练回滚。新增 Actions 自动重建仍为本地代码且开关关闭，启用前必须协调两种更新入口。

## 适用范围

只有显式启用时，Watchtower 才每 30 秒轮询一次，只更新带以下标签的容器：

```yaml
com.centurylinklabs.watchtower.enable: "true"
```

本次只有 `backend` 和 `frontend` 带这个标签。MySQL、本 Compose 之外的 Nginx，以及宿主机上无关服务都不能自动升级。

## 为什么使用两个仓库

后端和前端是两个镜像、两个 ACR 仓库，因此可以各自跟踪 `latest`。这样可以避免单仓库 tag 方案里，前端推送覆盖后端所用镜像的问题。

## 预期更新流程

```text
master push
  -> CI 通过
  -> 推送 backend/frontend 的 latest 和 sha-<短SHA>
  -> Watchtower 检测到新 digest
  -> 拉取镜像
  -> 重建带标签容器
  -> 容器重启期间短暂中断
```

演示环境接受短暂中断，不采用蓝绿部署或零停机方案。

## 默认关闭与显式启用

默认的 `docker compose up -d` 不启动 Watchtower。它挂载 Docker socket，具备宿主机容器管理权限；`--label-enable` 只限制正常更新的选择范围，不能把 socket 变成受限的管理接口。只读挂载 socket 也不能阻止有写入效果的 Docker API 请求。

如明确选择自动更新，先准备只包含本项目 ACR 登录的 `/etc/cs-career-guide/acr`，再显式执行：

```bash
docker compose --profile updates up -d watchtower
```

配置中将服务移入 profile 不会自动停止服务器上已经运行的 Watchtower；改用 Actions 自动重建前，应在维护操作中明确停止旧 Watchtower，不能让两个入口同时重建。本会话仅查看其运行状态，没有执行停止操作。其余容器权限与资源限制见 [宿主机保护边界](host-protection.md)。

## Watchtower 前置条件

- 挂载 Docker socket：`/var/run/docker.sock`。
- 使用只包含本项目 ACR 登录的独立目录，默认 `/etc/cs-career-guide/acr`；该目录只读挂载到容器 `/config`，通过 `DOCKER_CONFIG=/config` 读取其中的 `config.json`。不挂载 `/root/.docker` 等通用凭据目录。
- 启动前已对实际使用的 ACR 地址执行过 `docker login`。
- 与业务容器处于同一 Compose 项目，并尽量避免不必要的网络暴露。

Compose 给 Watchtower 使用 `network_mode: bridge`，允许它访问 ACR Registry API 检查镜像。`network_mode: none` 会阻断这类出站请求。Watchtower 不映射宿主机端口，通过 Docker socket 管理带标签的容器，通过只读凭据目录完成仓库鉴权。

## 按 digest 精确回滚

**先停自动更新入口，再操作版本。** 如果已启用 Actions 同步，先将 Variable `DEPLOY_ENV_SYNC_ENABLED` 改为 `false`，并确认没有同步 Job 正在执行，再停止 Watchtower。修改变量不会中断已经启动的 Job，服务器文件锁也不能替代人工回滚协调。经授权可在管理机执行：

```bash
gh variable set DEPLOY_ENV_SYNC_ENABLED --body false --repo vacontinuejatotired/CS-Career-Guide
```

当前同步脚本只读取基础 `docker-compose.yml`，不加载 `docker-compose.digest.yml`。因此使用 digest override 的回滚期间必须保持同步关闭，否则之后的发布可能按基础文件重建成其他版本。它也不会自动恢复旧 `.env` 或数据库；完整失败行为见 [AI 环境同步](ai-env-sync.md)。

从一次成功发布的 `published-images.json` 获取两个 `images.<组件>.reference`，确认 `complete` 为 `true`，并核对完整源码提交。将这两个 `repository@sha256:<64位digest>` 引用分别填入服务器部署 `.env` 的 `BACKEND_IMAGE`、`FRONTEND_IMAGE`。

使用同一份发布记录中的一对镜像，不自行拼接不同版本。先暂停 Watchtower，确认数据库备份与目标代码的 schema 兼容后再操作：

当前防护配置要求前端支持非 root 用户与容器端口 `8080`。旧 `c1d7b6a` 前端仍使用 `80`，不能直接套用以下新 Compose 回滚；跨部署配置版本需要单独评估，不能为恢复旧镜像自动放宽宿主机限制。

```bash
cd deploy
docker compose stop watchtower
docker --config /etc/cs-career-guide/acr compose -f docker-compose.yml -f docker-compose.digest.yml pull backend frontend
docker compose -f docker-compose.yml -f docker-compose.digest.yml up -d --no-build backend frontend
docker compose -f docker-compose.yml -f docker-compose.digest.yml ps
```

保持 Watchtower 停止，验证登录、受保护 API、静态/媒体资源和已有数据。该流程不包含数据卷删除或数据库降级；本项目尚未在真实服务器演练。

## 按源码标签选择版本

1. 从成功发布记录或 ACR 找到已验证的 `sha-<7位SHA>`；这种 tag 可以被重新推送，不能代替 digest 固定。
2. 在服务器 `.env` 设置 `BACKEND_TAG` 和/或 `FRONTEND_TAG`。
3. 重建前先停止 Watchtower，否则它可能再把容器切回 `latest`。

```bash
cd deploy
docker compose stop watchtower
docker --config /etc/cs-career-guide/acr compose pull backend frontend
docker compose up -d --no-build backend frontend
docker compose ps
```

## 恢复 latest 自动更新

在服务器部署 `.env` 中把 `BACKEND_TAG`、`FRONTEND_TAG` 都恢复为 `latest`。使用基础 Compose 文件，停止加载 digest override；先拉取并重建应用容器、检查运行状态，再启动 Watchtower：

```bash
cd deploy
docker compose stop watchtower
docker --config /etc/cs-career-guide/acr compose -f docker-compose.yml pull backend frontend
docker compose -f docker-compose.yml up -d --no-build backend frontend
docker compose -f docker-compose.yml ps
# 完成业务验证后，再执行：
docker compose -f docker-compose.yml start watchtower
```

只编辑 `.env` 或启动 Watchtower 不会改变现有应用容器的镜像引用，必须重建。不要只通过改镜像 tag/digest 回滚数据库 schema；SQLite/MySQL schema 变更需要单独制定恢复方案。

## 查看状态与日志

```bash
cd deploy
docker compose ps
docker compose logs --tail=200 watchtower
docker compose logs --tail=200 backend
docker compose logs --tail=200 frontend
```

确认运行容器的镜像引用和本地镜像 ID（镜像 ID 不是 Registry manifest digest）：

```bash
docker inspect cs-career-guide-backend --format '{{.Config.Image}} {{.Image}}'
docker inspect cs-career-guide-frontend --format '{{.Config.Image}} {{.Image}}'
```

Registry manifest digest 以成功发布记录中的 `digest`/`reference` 为准；也可检查对应镜像的 RepoDigests。不要把容器 `.Image` 字段当作发布 digest。

## 停止自动更新

```bash
cd deploy
docker compose stop watchtower
```

停止 Watchtower 不会停止应用，也不会删除数据卷。恢复已存在且已启用的服务时执行 `docker compose --profile updates start watchtower`。

## 常见故障

| 现象 | 处理 |
| --- | --- |
| Watchtower 报未授权 | 在服务器重新执行 `docker login`，并检查 `DOCKER_CONFIG_DIR` 指向正确的凭据目录 |
| 更新后容器反复重启 | 查看后端日志；迁移、collectstatic 或 Gunicorn 失败会让容器退出 |
| 新前端看起来没更新 | 强制刷新；确认 `index.html` 未缓存且 `latest` digest 已变化 |
| 回滚后仍是错误镜像 | 先停止 Watchtower，再核对 tag 和 digest，最后重新启动 |
| MySQL 被意外升级 | 基础设施服务不要加 Watchtower 标签，数据库始终手动升级 |
