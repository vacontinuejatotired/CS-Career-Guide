# 部署与运维总览

> 状态：演示部署实施中。基线提交 `3480b91` 已通过 [Actions 构建与容器冒烟](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39540701547)；ACR 推送、服务器启动及 Watchtower 自动更新尚未验证。

## 发布链路

```text
功能分支 / PR
  -> 后端测试 + 前端测试 + Docker build-only
  -> 合入 master
  -> 自动推送 ACR：latest、sha-<7位提交>
  -> 演示机 Watchtower 每 30 秒检查
  -> 拉取并重建 backend / frontend 容器
```

默认演示环境使用 SQLite 持久卷，前后端各自一个镜像。正式数据阶段仍保留原 MySQL settings 和可选 Compose profile。

## 镜像坐标

```text
crpi-gbihc3e57h3o3f2l.cn-hangzhou.personal.cr.aliyuncs.com/tencent-ubutun22/cs-career-guide-backend
crpi-gbihc3e57h3o3f2l.cn-hangzhou.personal.cr.aliyuncs.com/tencent-ubutun22/cs-career-guide-frontend
```

两个镜像的 `latest` 是演示更新入口；`sha-<7位提交>` 是不可变回滚入口。ECR/ACR 密码、Django `SECRET_KEY`、LLM key、数据库密码都不得写入仓库。

## 前置条件

1. 在 ACR `tencent-ubutun22` 命名空间下创建 `cs-career-guide-backend` 与 `cs-career-guide-frontend` 两个私有仓库。
2. 在 GitHub Actions Variables 配置：
   - `ACR_REGISTRY=crpi-gbihc3e57h3o3f2l.cn-hangzhou.personal.cr.aliyuncs.com`
   - `ACR_NAMESPACE=tencent-ubutun22`
3. 确认 Action Secrets 已有 `ALIYUN_ACR_USERNAME`、`ALIYUN_ACR_PASSWORD`。
4. 服务器先手动执行 `docker login`，让 Watchtower 复用 Docker 登录配置。
5. 服务器 `.env` 使用 `deploy/.env.example` 建立，真实值只在服务器保存。

## 文档索引

| 主题 | 文档 |
| --- | --- |
| CI 触发、Job、变量与排障 | [CI/CD 流水线](ci-cd.md) |
| 前后端镜像、依赖和构建上下文 | [Docker 镜像](docker-images.md) |
| 服务器登录 ACR、Compose、SQLite 与持久卷 | [服务器拉取部署](server-pull.md) |
| Watchtower 更新、SHA 回滚和故障排查 | [Watchtower 与回滚](watchtower-rollback.md) |

环境变量基础规则仍见 [环境变量配置](environment.md)；统一登录行为和验证边界见 [统一登录门槛](authentication-gate.md)。

## 当前状态与边界

- workflow、Dockerfile、Nginx、Compose 和 SQLite settings 已提交到 fork 的 `codex/ci-cd-images` 分支。
- 基线 `3480b91` 的前后端测试、双镜像构建和容器冒烟已由 Actions 39540701547 验证，包含容器内 SQLite 首次迁移。
- 本轮只允许功能分支 build-only，不合并、不发布镜像、不连接服务器或执行部署。
- build-only 工作流新增真实 Django/Nginx 注册登录、资料读写和 SQLite 卷重建校验，使用 runner 临时数据；结果以对应提交的 Actions 为准。
- CI 不覆盖浏览器交互、私有 ACR 拉取、Watchtower 自动更新或真实服务器部署。
- 不包含生产数据库迁移、已有媒体迁移、真实 AI 付费调用或公网 HTTPS。
