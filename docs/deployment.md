# 部署与运维总览

> 状态核对：2026-10-22。演示部署的 CI 验证和首次 ACR 双镜像发布已由提交 `c1d7b6a` 的 [Actions 39563957000](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39563957000) 完成；服务器启动及 Watchtower 自动更新仍未验证。详见 [验收状态与接手记录](deployment-status.md)，不能据此宣称生产完成。

## 发布链路

```text
功能分支 / PR
  -> 后端测试 + 前端测试 + 双镜像构建、联调、持久化验证
  -> 合入 master
  -> master 再次完整验证，独立 publisher 推送同一份已验收镜像
  -> 记录前后端 digest，再更新 ACR latest
  -> 演示机 Watchtower 每 30 秒检查
  -> 拉取并重建 backend / frontend 容器
```

默认演示环境使用 SQLite 持久卷，前后端各自一个镜像。正式数据阶段仍保留原 MySQL settings 和可选 Compose profile。

## 镜像坐标

```text
crpi-gbihc3e57h3o3f2l.cn-hangzhou.personal.cr.aliyuncs.com/tencent-ubutun22/cs-career-guide-backend
crpi-gbihc3e57h3o3f2l.cn-hangzhou.personal.cr.aliyuncs.com/tencent-ubutun22/cs-career-guide-frontend
```

两个镜像的 `latest` 是演示更新入口，`sha-<7位提交>` 用于追踪源码但可以被覆盖。精确回滚使用一次完整发布记录中的前后端 `repository@sha256:<digest>` 引用，不能把 SHA tag 当作不可变保证。ACR 密码、Django `SECRET_KEY`、LLM key、数据库密码都不得写入仓库。

## 前置条件

1. 在 ACR `tencent-ubutun22` 命名空间下创建 `cs-career-guide-backend` 与 `cs-career-guide-frontend` 两个私有仓库。
2. 在 GitHub Actions Variables 或同名 Secrets 配置以下坐标；Variables 优先，现有 Secrets 可直接使用：
   - `ACR_REGISTRY=crpi-gbihc3e57h3o3f2l.cn-hangzhou.personal.cr.aliyuncs.com`
   - `ACR_NAMESPACE=tencent-ubutun22`
3. 确认 Action Secrets 已有 `ALIYUN_ACR_USERNAME`、`ALIYUN_ACR_PASSWORD`。
4. 服务器先手动执行 `docker login`，让 Watchtower 复用 Docker 登录配置。
5. 服务器 `.env` 使用 `deploy/.env.example` 建立，真实值只在服务器保存。

## 文档索引

| 主题 | 文档 |
| --- | --- |
| 已验证结果、发布记录与接手边界 | [验收状态与接手记录](deployment-status.md) |
| CI 触发、Job、变量与排障 | [CI/CD 流水线](ci-cd.md) |
| 前后端镜像、依赖和构建上下文 | [Docker 镜像](docker-images.md) |
| 服务器登录 ACR、Compose、SQLite 与持久卷 | [服务器拉取部署](server-pull.md) |
| Watchtower 更新、SHA 回滚和故障排查 | [Watchtower 与回滚](watchtower-rollback.md) |

环境变量基础规则仍见 [环境变量配置](environment.md)；统一登录行为和验证边界见 [统一登录门槛](authentication-gate.md)。

## 当前状态与边界

- workflow、Dockerfile、Nginx、Compose 和 SQLite settings 已随 fork 的 PR #1 合入 `master`，合并提交为 `c1d7b6ab0ff3c48d732fea55cb88899a33c77e9b`。
- 功能分支 `acad2c8` 的 Actions 39561641720 已通过 build-only；master 的 Actions 39563957000 再次通过完整测试、双镜像冒烟、真实联调、SQLite 卷重建持久化和归档身份验证，并成功推送 ACR。
- 首次发布记录 `complete: true`，镜像标签为 `sha-c1d7b6a` 和 `latest`；成对 digest 记录已归档到 [发布记录 JSON](releases/2026-10-21-c1d7b6a.json)。这只能证明该次发布成功，不能证明标签此后未改变或服务器已拉取。
- 2026-10-22 的接手工作只同步验收文档；不再次合并、不发布镜像、不连接服务器或执行部署。
- 所有镜像构建路径均执行真实 Django/Nginx 注册登录、资料读写、SQLite 卷重建和待发布归档身份校验，使用 runner 临时数据；结果以对应提交的 Actions 为准。
- CI 不覆盖浏览器交互、私有 ACR 拉取、Watchtower 自动更新或真实服务器部署。
- 不包含生产数据库迁移、已有媒体迁移、真实 AI 付费调用或公网 HTTPS。
