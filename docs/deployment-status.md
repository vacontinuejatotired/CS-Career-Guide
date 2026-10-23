# 演示部署验收状态与接手记录

核对日期：2026-10-23（Asia/Shanghai）。Git/Actions/配置名称在本次文档维护时重新查询；服务器状态依据本会话前面实际 SSH 检查和账号配置结果，没有为更新文档重启或重新部署服务。区分本地实现、CI、发布、运行状态与业务验收。

## 当前主分支与个人开发分支

本会话先按 main 名称推送了三个提交，用户随后纠正：主分支继续使用 master。本轮将它们整合进 master，并从最终主分支建立长期个人分支 `codex/personal`，以后从该分支提 PR 到本 fork 的 master。`codex/ci-cd-images` 的全部提交已包含在 master，本地 `codex/sync-ai-env` 也没有额外提交，不需要重复 cherry-pick。已有 luochen 分支不改写。

代码提交 `33cbc57` 已通过 [Actions 39979362642](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39979362642)，publisher 和服务器同步按非 master 规则跳过。master 的后续完整验证与发布查看 [当前 Actions](https://github.com/vacontinuejatotired/CS-Career-Guide/actions?query=branch%3Amaster)，不能将 build-only 成功写成 master 镜像已发布。

下文的 `codex/sync-ai-env`、dirty tree、“未提交”以及旧 HEAD 描述保留为提交前的实施快照。当前代码已通过提交保留；未提交的课程资料、`.gitignore` 和 output 仍在工作区，不自动混入主分支。新的 Git/PR/commit 与文档更新规则见 [Git 规范](git-workflow.md)，导航入口见 [agent.md](../agent.md)。

仓库默认关闭 Watchtower、限制容器权限和资源、仅绑定回环地址，详见 [宿主机保护边界](host-protection.md)。服务器已有旧 Watchtower 运行，仓库 profile 不能自动停止它。以下首次发布记录仅作为历史证据。

## 提交前的代码与分支快照

- 仓库：`vacontinuejatotired/CS-Career-Guide`；只在此 fork 开发，不向 `ccccczhang/CS-Career-Guide` 提 PR。
- 本地分支：`codex/sync-ai-env`；HEAD 为 `9837e71ff1d86d7ecfb88f60c49702094a645a84`。工作区包含未提交的 AI 配置同步、Compose 映射、前端 TTS 构建参数、模拟面试重构和文档更新。
- 原有 `.gitignore` 修改、课程需求文档、Typst 文件和 `output/` 已保留，不属于此次部署实现的提交范围。后续应显式分组暂存，不能 `git add .`。
- 最新查询的 master [Actions 39897322500](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39897322500) 对应 `9837e71`，结果成功；该运行没有包含当前未提交改动。
- fork 内的 [PR #1](https://github.com/vacontinuejatotired/CS-Career-Guide/pull/1) 已于 **2026-10-21 15:43:07（北京时间）** 合并到 fork 的 `master`；合并提交为 `c1d7b6ab0ff3c48d732fea55cb88899a33c77e9b`。
- `acad2c8`、`c1d7b6a`、`codex/ci-cd-images` 属于首次发布历史。旧文档的“工作区干净”“从未连接服务器”已不适用于本次快照。

## 2026-10-23 提交前实施状态（历史快照）

| 项目 | 已确认的状态 | 不能据此推断 |
| --- | --- | --- |
| 现有应用容器 | 本会话 SSH 查看时 backend/frontend healthy，旧 Watchtower 运行 | 未核对运行镜像 digest、全部宿主机限制或真实业务效果 |
| 专用部署账号 | `csdeploy` 密钥登录成功；密码锁定，无 sudo，有 Docker 组权限；目录及 `.env` 权限已配置 | Docker 组权限不是受限沙箱；未验证私有 ACR 拉取 |
| Actions 配置 | 三个模型 Secrets、六个 SSH Secrets、十个模型 Variables 已保存并核对名称；Variables 也核对了值 | GitHub 不可回读 Secret 值，不能宣称已验证模型 Key 有效 |
| 服务器 AI 配置 | `.env` 字段元数据检查显示三个 LLM 字段为空；完整 ASR/TTS 字段未配置 | Key 已存 GitHub 不代表运行中的容器已拿到 Key |
| AI 环境同步 | `ci/sync_runtime_env.py`、发布后 Job、白名单合并、健康等待已在本地实现 | 未提交、未推送、未触发新 CI、未同步服务器、未重建 |
| 自动同步开关 | `DEPLOY_ENV_SYNC_ENABLED` 尚不存在，因此关闭 | 不会因为保存 Secret 自动发布 |
| 面试重构 | legacy 适配器、服务契约、后端策略已实现；前端 32 项、面试 6 项、鉴权 16 项测试和前端构建通过 | 无真实模型调用、语音或浏览器全流程验收 |

同步脚本离线 CI 工具测试在 Linux 上 36 项通过，使用模拟 SSH/Compose；后续在 Windows 运行时，4 项 POSIX 测试按平台跳过。上述本地测试不能替代新提交的 Actions 镜像验证。

账号配置仅改变目标目录/`.env` 的所有权和权限，并安装专用公钥；环境文件内容未修改，应用未重启。服务器地址、端口和私钥不写入此文档，实际值由 `DEPLOY_*` Secrets 管理。

## 首次发布的 GitHub Actions 历史证据

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

## 当前仍待验证

- `csdeploy` 的 ACR 登录/私有镜像拉取；服务器 Compose 补齐 AI 映射后的候选配置校验；新的自动同步、拉取和重建流程。
- 当前运行镜像与发布 digest 对应关系、运行时宿主机防护参数及浏览器业务交互。观察到 healthy 不等于这些项目均已验收。
- Watchtower 的每 30 秒轮询、带标签容器更新，以及成对 digest 回滚演练。
- 公网 HTTPS、真实 MySQL 运行与数据迁移、已有媒体迁移、付费 AI 功能。

已存在的基础容器运行与新增自动部署链路必须分开验收。不能再写“服务器完全未部署”，也不能据此宣称新配置已经上线或所有 AI 功能可用。

## 后续执行边界

2026-10-22 文档提交 `3289bec` 的 Actions 39706415076 等为历史记录。分支整合后的开发从 `codex/personal` 继续，保留工作区无关草稿，不能切回旧分支重做，也不能用旧镜像证据代替新配置验证。

后续接手仍先查 Git 与最新 Actions，避免依据本页快照重复修复。默认 MySQL settings 保持不变，SQLite 通过独立的 `settings_sqlite` 模块启用；Docker 构建和容器验证只允许在 Actions runner 执行。

本会话已明确授权并完成服务器部署账号创建和相关 Secrets 配置；后来工作范围调整为现有面试实现的结构重构，本次再补运维文档。没有执行应用重建、模型调用或数据迁移。后续提交、推送、发布和服务器操作按当时明确授权执行，不能将历史文档中的临时授权限制当作当前事实，也不能将账号创建授权扩展为任意服务器变更。

上线顺序：先整理并验证改动，再以部署账号验证 ACR，逐项补服务器 Compose 映射，协调停止旧 Watchtower，最后才启用同步并执行已获授权的发布。回滚前关闭同步开关；自动脚本不加载 digest override，见 [AI 环境同步](ai-env-sync.md) 与 [回滚手册](watchtower-rollback.md)。模拟面试实现与验收边界见 [重构说明](interview-refactor.md)。
