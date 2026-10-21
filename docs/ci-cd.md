# CI/CD 流水线

> 状态：演示部署实施中。基线提交 `3480b91` 已于 2026-10-21 通过 [Actions 39540701547](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39540701547)：前后端测试、双镜像构建和容器冒烟通过，两个镜像均为 `push: false`。ACR 发布和服务器部署尚未验证。

## 触发规则

| 事件 | 目标分支 | 测试 | 构建镜像 | 推送 ACR |
| --- | --- | --- | --- | --- |
| PR 到 `master` | 任意分支 | 是 | 有代码变更时，仅构建不推送 | 否 |
| push 到 `master`，有代码变更 | `master` | 是 | 是 | 是 |
| push 到 `master`，只有 README/docs | `master` | 是 | 否 | 否 |
| push 到其他分支 | 任意 ref | 是 | 有代码变更时，仅构建不推送 | 否 |
| `workflow_dispatch` 手动触发 | 任意选择的分支 | 是 | 是 | 仅 `master` |

纯文档判定只匹配 `README.md` 和 `docs/`。`.github/workflows/**`、`deploy/**`、Dockerfile 和 Nginx 配置都属于代码或部署配置，会触发镜像构建。

## Job 结构

```text
changes
  |-- backend-test ---------------------> backend-image --> release-summary
  `-- frontend-test --> frontend-image ---^
                           (build-only image artifact)
```

- **backend-test**：把 UTF-16 的 `requirements.txt` 转成临时 UTF-8 文件，安装 `default-libmysqlclient-dev`，运行 `tests.test_auth`、`test_env_config.py`、`test_deploy_runtime.py` 和不启动 Docker 的烟测脚本单元测试，并执行隔离 Django check。
- **frontend-test**：使用 Node 24，依次执行 `npm ci`、鉴权和配置测试、Vite 构建，并检查 `dist/index.html`、GLB 和 VAD ONNX 是否存在。
- **backend-image / frontend-image**：构建 `linux/amd64` 镜像，后端 Job 等待前端镜像通过。后端构建前使用虚构配置校验 Compose 默认 SQLite、可选 MySQL 及 Watchtower 的出站网络和凭据目录。PR 和非 master 分支（包括从非 master 手动触发）只做 build-only；原有单镜像冒烟保留。随后前端 Job 导出已测镜像，后端 Job 复用它执行真实联调和 SQLite 持久化校验。只有 master 才登录 ACR 并推送。
- **release-summary**：只有两个镜像 Job 都成功时才通过。

## 真实联调与持久化校验

仅在 Actions runner 的 build-only 路径执行 `ci/demo_smoke.py`，不在开发机运行 Docker：

1. 通过短期 Artifact 传递已通过前端冒烟的镜像，后端复用当前 Job 已加载的镜像，不重新构建、不拉取 ACR。
2. 使用 `deploy/docker-compose.yml` 加 `ci/docker-compose.smoke.yml`，指定唯一 `ci-demo-<run-id>-<attempt>` 项目，只启动真实 Django 和 Nginx。Watchtower 和 MySQL 均不启动。
3. 使用 `--env-file /dev/null`、虚构密钥和全新命名卷；只监听 runner 的 `127.0.0.1:18080`，关闭嵌入下载和 TTS，不调用 AI 接口。
4. 从 Nginx 入口检查 Vue 路由、后端收集的静态文件、未授权/无效 Token 的 401，以及注册、登录、资料读写。
5. 删除并重新创建后端容器，确认容器 ID 变化；使用原 Token 和原密码重新验证相同用户 ID、资料标记，确认 SQLite 卷持久化。
6. 成功或失败均采集容器日志并清理本次项目的容器、网络和卷；日志不输出测试密码或 Token。

新增检查是否通过，以对应提交的 Actions 结果为准；本地脚本单元测试不能替代容器验证。

## 变量与 Secrets

Repository Variables：

```text
ACR_REGISTRY=crpi-gbihc3e57h3o3f2l.cn-hangzhou.personal.cr.aliyuncs.com
ACR_NAMESPACE=tencent-ubutun22
```

Actions Secrets：

```text
ALIYUN_ACR_USERNAME
ALIYUN_ACR_PASSWORD
```

变量缺失或格式非法时，发布 Job 必须失败，不能静默跳过。`ACR_REGISTRY` 必须是不带 `https://` 和路径的主机名；`ACR_NAMESPACE` 只能使用小写字母、数字和连字符。

## 权限、并发与日志

- 权限限制为 `contents: read`、`packages: write`。
- 同一个 ref 使用同一并发组；PR 可以取消旧运行，push 和手动发布不取消。
- CI 禁止回显 Secrets，禁止上传 `.env`。Artifact 包含测试日志、前端构建产物和 build-only 前端镜像归档；镜像归档保留 1 天，真实联调容器日志保留 7 天，不保存测试密码或 Token。
- 镜像构建使用 `type=gha` 缓存，并关闭 provenance/SBOM，避免个人版 ACR 拒绝不支持的 manifest 附件。
- 手动触发可以附加一个合法 tag；标准标签仍是 `latest` 和 `sha-<7位SHA>`。

## 功能分支验证与边界

本轮只在 `vacontinuejatotired/CS-Career-Guide` 的 `codex/ci-cd-images` 分支开发；不创建上游 PR、不合并、不发布镜像，也不连接服务器。

```bash
git switch codex/ci-cd-images
# 完成实现与本地检查后
git push -u origin codex/ci-cd-images
gh run list --repo vacontinuejatotired/CS-Career-Guide --branch codex/ci-cd-images --workflow ci-cd.yml
```

检查结果时确认：

1. 后端和前端测试 Job 都通过。
2. build-only 镜像可以启动，且没有执行 ACR 登录或推送。
3. 纯文档改动不会触发镜像 Job。
4. 失败时可以下载测试日志，日志中没有凭据。

单镜像冒烟不能替代新增的真实联调与持久化步骤。即使新增步骤通过，也不等于 Watchtower 拉取私有 ACR、真实服务器部署或浏览器交互测试通过。

## 常见失败

| 现象 | 检查项 |
| --- | --- |
| `requirements.txt` 编码失败 | 确认原文件仍是 UTF-16 BOM；CI 只转换临时副本为 UTF-8 |
| `mysqlclient` 编译失败 | 检查 `default-libmysqlclient-dev` 和 `pkg-config` |
| ACR 登录失败 | 使用 Registry 访问凭证，不是阿里云账号登录密码 |
| `unknown manifest class` | 确认 `provenance: false` 和 `sbom: false` |
| Variables 缺失 | 在 Settings → Secrets and variables → Actions 配置两个 Repository Variables |
