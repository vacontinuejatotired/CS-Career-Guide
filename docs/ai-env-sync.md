# 发布后同步 AI 配置

镜像发布成功后，通过 SSH 更新服务器已有 `.env` 中的 AI 配置，再拉取服务器 Compose 所选镜像并重建 `backend`、`frontend`。默认关闭；设置 Actions Variable `DEPLOY_ENV_SYNC_ENABLED=true` 后，只有本 fork 的 master 成功发布才执行。PR 和其他分支不接触服务器凭据。

> 2026-10-23 状态：实现仍在本地 `codex/sync-ai-env` 工作区，未提交、未推送、未发布；上述同步未实际执行。Actions 已配置三个模型 Secrets、六个 SSH Secrets 和十个模型 Variables；启用变量尚未设置。服务器 `csdeploy` 的密钥登录、目录访问和 Docker 调用已验证，私有 ACR 拉取尚未验证。完整交接见 [当前验收状态](deployment-status.md)。

## 配置归属与安全边界

GitHub 管理 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`、`CAREER_REPORT_MODEL`、`ASR_API_KEY`、`ASR_WSS_URL`、`ASR_MODEL`、`ENABLE_TTS`、`TTS_API_KEY`、`TTS_WSS_URL`、`TTS_MODEL`、`TTS_VOICE`。

这些字段在服务器已有的值将被 GitHub 非空值更新。GitHub 空值跳过，不删除服务器值；前三个 LLM 字段必须完整。白名单之外的行保留，包括数据库、`SECRET_KEY`、域名、端口、资源限制、镜像 tag/digest、ACR 和自定义设置。如某个 AI 字段也要由服务器独立维护，应从同步白名单中移除，不能由两端同时管理。

严格核验主机密钥的 SSH 传输中，API Key 只走加密 stdin，不进入参数、镜像、Artifact、日志或 `$GITHUB_ENV`。临时 SSH 凭据权限 600，用完删除。服务器候选 `.env` 权限 600，通过校验和镜像拉取后原子替换；文件锁避免两个 CI 同时写入。

目标必须是部署用户拥有的现存普通 `.env` 文件，权限 600，无符号链接和硬链接；父目录归部署用户且不可由其他用户写入。不支持多行 dotenv 值、重复受管字段或模糊语法，遇到时拒绝修改。发送值含换行、单引号、反斜杠或控制字符也会拒绝，避免配置注入。

GitHub 仓库及可修改发布 workflow 的人员将纳入服务器信任边界。使用专用部署账号；known_hosts 必须经可信渠道核验，不能每次 CI 直接信任 ssh-keyscan 的结果。拥有 Docker socket 权限的账号实际上具有很高的宿主机权限，不代表完全隔离。

## GitHub 配置

模型使用已有 Secrets：`LLM_API_KEY`、`ASR_API_KEY`、`TTS_API_KEY`。模型名、URL 和开关继续使用同名 Variables。

2026-10-23 已保存的十个 Variables：

| Variable | 已选配置／填写规则 |
| --- | --- |
| `LLM_MODEL` | `qwen3.8-flash` |
| `CAREER_REPORT_MODEL` | `qwen3.7-plus` |
| `LLM_BASE_URL` | 业务空间的 HTTPS OpenAI 兼容地址，结尾 `/compatible-mode/v1` |
| `ASR_MODEL` | `fun-asr-realtime`；当前调用协议仍待适配验收 |
| `ASR_WSS_URL` | 同一业务空间的 WSS 地址，结尾 `/api-ws/v1/inference` |
| `TTS_MODEL` | `cosyvoice-v3-flash` |
| `TTS_WSS_URL` | 对应业务空间的 WSS 地址，结尾同上 |
| `TTS_VOICE` | `longanyang` |
| `ENABLE_TTS` | `True`，后端运行时开关 |
| `VITE_ENABLE_TTS` | `True`，前端构建时开关 |

模型与地址已在本会话选定并保存，未执行真实模型成功验证。具体业务空间地址从 Actions 查看，此处不固化到代码或示例。

服务器连接信息全部使用 repository Secrets：

| Secret | 内容 |
| --- | --- |
| `DEPLOY_SSH_HOST` | 服务器主机名或 IPv4，不带协议 |
| `DEPLOY_SSH_PORT` | 端口，空值默认 22 |
| `DEPLOY_SSH_USER` | 专用部署用户名 |
| `DEPLOY_ENV_PATH` | `.env` 的绝对路径，如 `/srv/cs-career-guide/.env` |
| `DEPLOY_SSH_KEY` | 专用、可非交互使用的 SSH 私钥完整内容 |
| `DEPLOY_SSH_KNOWN_HOSTS` | 已核验的 OpenSSH known_hosts 内容；非 22 端口应匹配 `[主机]:端口` |

最后设置 Variable `DEPLOY_ENV_SYNC_ENABLED=true`。只改配置不会触发发布，需后续 master 发布或在 master 手动运行 workflow。

## 服务器前提与生效流程

- Linux 已有 Python 3、Docker、支持 JSON config 和 `up --wait` 的 Compose v2；部署用户可非交互运行 Docker，并须先以该用户完成 ACR 登录。`csdeploy` 已验证前三项，ACR 登录/拉取仍待验证。
- `.env` 同目录有 `docker-compose.yml`。脚本不覆盖服务器 Compose。启用前先逐项合并仓库 `deploy/docker-compose.yml` 的 AI environment 映射，保留服务器定制设置。
- 脚本只加载基础 `docker-compose.yml`，拉取其中选定的镜像；仓库基础文件通过 `BACKEND_TAG`、`FRONTEND_TAG` 选择版本。不会修改这些字段，但也不会自动使用本次发布的成对 digest，成功同步不等于部署了本次发布的版本。
- **脚本不会加载 `docker-compose.digest.yml`。** 通过该 override 固定 digest 的部署或回滚期间，必须关闭 `DEPLOY_ENV_SYNC_ENABLED`，否则之后的自动重建可能按基础 Compose 切回其他版本。若自行在基础 Compose 的 image 中固定 digest，则以该基础文件为准。
- 脚本使用部署账号默认的 Docker CLI 凭据配置。`.env` 中的 `DOCKER_CONFIG_DIR` 用于 Watchtower 挂载，不会自动变成 CLI 的 `DOCKER_CONFIG`；管理员能拉取镜像，也不代表 `csdeploy` 能拉取。
- `VITE_ENABLE_TTS` 作为公开构建参数传给前端构建，不写服务器 `.env`，也不包含任何 Key；变更需重建并发布前端。

先生成候选 `.env`，运行 `docker compose config --format json`，核验 backend 中每个受管值与输入一致；缺字段或服务器 Shell 冲突时停止。校验结果、SSH 和 Compose 原始输出不打印，避免泄露密钥。随后拉取 backend/frontend，这些步骤失败时原 `.env` 不变。

然后原子替换 `.env`，执行 `up -d --no-deps --force-recreate --wait --wait-timeout 180 backend frontend`，等待健康检查。不会启动依赖服务、删除卷或管理 Watchtower。重建有短暂中断，镜像现有入口可能执行数据库迁移。若重建或健康检查失败，Actions 报错并保留新 `.env`，不自动回滚文件、容器或数据库；需在服务器私下诊断，不能输出含密钥的 config。

本会话观察到服务器已有 Watchtower 容器运行。启用新的 Actions 自动重建前，需明确选择一种更新入口，并安排停止旧 Watchtower，避免两个控制器同时重建。前面没有停止或重启该容器；仓库 profile 默认关闭不代表它已经停止。

同步和健康检查通过只证明配置传递与容器状态，不能替代真实模型、语音效果、浏览器验收。现有 ASR 使用 Gummy 消息格式，更换 fun-asr-realtime 名称仍需单独适配验证。

## 离线检查

`python -m unittest discover -s ci -p 'test_*.py' -v`

测试使用虚构凭据和模拟 SSH/Compose，不联网、不启动 Docker。Linux 额外验证权限、原子替换和失败保留；Windows 跳过 fcntl 相关测试。
