# Watchtower 与回滚

> 状态：草案。Compose 定义已在工作区，但尚未在服务器实际启动 Watchtower。

## 适用范围

Watchtower 只用于演示环境，每 30 秒轮询一次，只更新带以下标签的容器：

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

## Watchtower 前置条件

- 挂载 Docker socket：`/var/run/docker.sock`。
- 服务器本地保存 Docker 登录凭据，目录只读挂载到容器 `/config`，通过 `DOCKER_CONFIG=/config` 读取其中的 `config.json`。
- 启动前已对实际使用的 ACR 地址执行过 `docker login`。
- 与业务容器处于同一 Compose 项目，并尽量避免不必要的网络暴露。

Compose 给 Watchtower 使用 `network_mode: bridge`，允许它访问 ACR Registry API 检查镜像。`network_mode: none` 会阻断这类出站请求。Watchtower 不映射宿主机端口，通过 Docker socket 管理带标签的容器，通过只读凭据目录完成仓库鉴权。

## 回滚到不可变 SHA

1. 从 Actions Summary 或 ACR 找到已验证的 `sha-<7位SHA>`。
2. 在服务器 `.env` 设置 `BACKEND_TAG` 和/或 `FRONTEND_TAG`。
3. 重建前先停止 Watchtower，否则它可能再把容器切回 `latest`。

```bash
cd deploy
docker compose stop watchtower
docker compose pull backend frontend
docker compose up -d --no-build backend frontend
docker compose ps
```

回滚验证完成后，在合适时机把 tag 恢复成 `latest` 并重新启动 Watchtower：

```bash
docker compose start watchtower
```

不要只通过改镜像 tag 回滚数据库 schema。SQLite/MySQL schema 变更需要单独制定恢复方案。

## 查看状态与日志

```bash
cd deploy
docker compose ps
docker compose logs --tail=200 watchtower
docker compose logs --tail=200 backend
docker compose logs --tail=200 frontend
```

确认实际运行的镜像 digest：

```bash
docker inspect cs-career-guide-backend --format '{{.Config.Image}} {{.Image}}'
docker inspect cs-career-guide-frontend --format '{{.Config.Image}} {{.Image}}'
```

## 停止自动更新

```bash
cd deploy
docker compose stop watchtower
```

停止 Watchtower 不会停止应用，也不会删除数据卷。恢复时执行 `docker compose start watchtower`。

## 常见故障

| 现象 | 处理 |
| --- | --- |
| Watchtower 报未授权 | 在服务器重新执行 `docker login`，并检查 `DOCKER_CONFIG_DIR` 指向正确的凭据目录 |
| 更新后容器反复重启 | 查看后端日志；迁移、collectstatic 或 Gunicorn 失败会让容器退出 |
| 新前端看起来没更新 | 强制刷新；确认 `index.html` 未缓存且 `latest` digest 已变化 |
| 回滚后仍是错误镜像 | 先停止 Watchtower，再核对 tag 和 digest，最后重新启动 |
| MySQL 被意外升级 | 基础设施服务不要加 Watchtower 标签，数据库始终手动升级 |
