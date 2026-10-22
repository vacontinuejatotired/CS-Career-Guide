# 演示部署验收状态与接手记录

核对日期：2026-10-22（Asia/Shanghai）。本页依据当前 Git、fork 的 GitHub Actions、PR 和发布 Artifact 核对，区分代码验证、镜像发布与服务器部署。

## 当前代码与分支

- 仓库：`vacontinuejatotired/CS-Career-Guide`；只在此 fork 开发，不向 `ccccczhang/CS-Career-Guide` 提 PR。
- 应用代码的功能分支基线：`acad2c8120ea5216765c5f3bc7edba264bff72d1`，提交说明为 `fix(ci): publish only verified image artifacts`。本次接手前，本地与远端 `codex/ci-cd-images` 一致，工作区干净。
- fork 内的 [PR #1](https://github.com/vacontinuejatotired/CS-Career-Guide/pull/1) 已于 **2026-10-21 15:43:07（北京时间）** 合并到 fork 的 `master`；合并提交为 `c1d7b6ab0ff3c48d732fea55cb88899a33c77e9b`。
- “HEAD 是 `3480b91`、Actions 39540701547 仍运行中、尚未合并或发布”的旧交接信息已经过时。本次接手没有再次合并或发布。

## GitHub Actions 验收证据

| 运行 | 提交 / 事件 | 已确认的结果 |
| --- | --- | --- |
| [39540701547](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39540701547) | `3480b91` / 功能分支 push | 已成功完成；包含 SQLite 首次迁移的镜像冒烟，不再是运行中 |
| [39561641720](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39561641720) | `acad2c8` / 功能分支 push | 前后端测试、双镜像、真实联调、SQLite 持久化、待发布归档身份验证均通过；publisher 跳过 |
| [39562842520](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39562842520) | `acad2c8` / PR | 完整 build-only 验证通过；publisher 跳过 |
| [39563943035](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39563943035) | `acad2c8` / PR | 前后端测试通过；镜像与发布任务跳过，不能将这次绿色状态单独当作镜像验证证据 |
| [39563957000](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39563957000) | `c1d7b6a` / master push | 全部 7 个 Job 成功，包含独立 publisher；2026-10-21 16:01:29（北京时间）完成 |

master 运行的后端日志明确记录：

- 真实 Nginx/Django 注册、登录、鉴权拒绝、资料更新和共享静态文件验证通过。
- 删除并重新创建后端容器后，用户、原密码、原 Token 和资料标记均保留，SQLite 命名卷持久化验证通过。
- 两份待发布归档的提交、镜像 ID 与 `linux/amd64` 平台匹配；publisher 使用相同归档发布，没有重新构建。

## 首次 ACR 发布记录

来源为 master 运行的 `published-images-39563957000` Artifact，其中的 `published-images.json` 已核对：完整源码提交为 `c1d7b6ab0ff3c48d732fea55cb88899a33c77e9b`，`complete` 为 `true`，两个组件均记录了 `sha-c1d7b6a` 和 `latest`。

不含凭据的原始 JSON 已保存至 [2026-10-21-c1d7b6a.json](releases/2026-10-21-c1d7b6a.json)，保留镜像 ID、manifest digest、完整仓库引用和已推送标签，避免只依赖有保留期限的 Artifact。

| 组件 | 发布时的 manifest digest |
| --- | --- |
| backend | `sha256:a88b86560d20e879b3228f1373d0b33ec22a691fd083189d9f9fdb4dc680b8ec` |
| frontend | `sha256:0596c35212f18fd221aff79ad28a9bd998ca4fc2d528e38c36f6e5b3b1150b2f` |

这是该次发布的历史记录。此次没有登录 ACR 或查询当前标签；不能据此断言 `latest` 仍指向这些 digest，也不能证明演示服务器已拉取或启动镜像。

## 尚未验证

- 真实服务器的 ACR 登录、私有镜像拉取、Compose 启动和浏览器交互。
- Watchtower 的每 30 秒轮询、带标签容器更新，以及成对 digest 回滚演练。
- 公网 HTTPS、真实 MySQL 运行与数据迁移、已有媒体迁移、付费 AI 功能。

现有证据说明演示链路的 **CI 验证与首次镜像发布已完成**；服务器部署仍待单独验收，不能称为生产完成。

## 后续执行边界

2026-10-22 的接手工作仅同步上述验收状态与发布记录。文档改动只提交并推送到 `origin/codex/ci-cd-images`；纯 README/docs 改动预期只运行测试，镜像及 publisher 均跳过。新运行只验证本次文档提交，不替代上述镜像证据。

后续接手仍先查 Git 与最新 Actions，避免依据本页快照重复修复。默认 MySQL settings 保持不变，SQLite 通过独立的 `settings_sqlite` 模块启用；Docker 构建和容器验证只允许在 Actions runner 执行。

当前授权不包含再次合并、推送 master、发布镜像、连接服务器或部署；不读取真实 `.env`、凭据、私钥或进程环境变量，不调用付费 AI，不迁移真实数据。下一阶段应在取得服务器操作授权后，按 [服务器拉取部署](server-pull.md) 与 [Watchtower 与回滚](watchtower-rollback.md) 分别验收。
