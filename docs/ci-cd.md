# CI/CD 流水线

> 状态：演示部署实施中。基线提交 `8c12688` 已通过 [Actions 39557869697](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/39557869697) 的双镜像、真实联调和 SQLite 持久化验证。本轮将验证与发布拆成独立 Job；改动以新提交的 Actions 为准。ACR 首次发布和服务器部署仍未验证。

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
frontend-test --> frontend-image (归档) --|
backend-test ---------------------------+--> backend-image + 真实联调 (归档)
全部测试与镜像验证 ----------------------> publish (仅 fork/master)
验证与发布结果 --------------------------> release-summary
```

- **backend-test**：安装完整测试依赖，运行鉴权、配置、部署运行时、烟测脚本及发布脚本回归测试，并执行隔离 Django check。脚本测试使用合成数据和模拟 Docker，不访问 Registry 或真实凭据。
- **frontend-test**：使用 Node 24，依次执行 `npm ci`、鉴权和配置测试、Vite 构建，并检查 `dist/index.html`、GLB 和 VAD ONNX 是否存在。
- **backend-image / frontend-image**：所有触发路径均使用 `push: false`、`load: true`，执行单镜像冒烟；master 也执行真实联调、SQLite 持久化和归档身份检查。验证 Job 不读取 Registry Secrets、不登录或推送 ACR。
- **publish**：只在 `vacontinuejatotired/CS-Career-Guide` 的 master 发布事件运行，等待前后端测试及两个镜像 Job 成功。下载本次运行的两份归档，核对完整提交 SHA、镜像 ID 和平台；直接推送已验证的同一份镜像，不重新构建。
- **release-summary**：检查验证结果，以及本次发布是否按预期成功或跳过；不能把部分发布报告为成功。

## 真实联调与持久化校验

所有镜像验证路径均在 Actions runner 执行 `ci/demo_smoke.py`，不在开发机运行 Docker：

1. 通过短期 Artifact 传递已通过前端冒烟的镜像和身份元数据，后端复用当前 Job 已加载的镜像，不重新构建、不拉取 ACR。
2. 使用 `deploy/docker-compose.yml` 加 `ci/docker-compose.smoke.yml`，指定唯一 `ci-demo-<run-id>-<attempt>` 项目，只启动真实 Django 和 Nginx。Watchtower 和 MySQL 均不启动。
3. 使用 `--env-file /dev/null`、虚构密钥和全新命名卷；只监听 runner 的 `127.0.0.1:18080`，关闭嵌入下载和 TTS，不调用 AI 接口。
4. 从 Nginx 入口检查 Vue 路由、后端收集的静态文件、未授权/无效 Token 的 401，以及注册、登录、资料读写。
5. 删除并重新创建后端容器，确认容器 ID 变化；使用原 Token 和原密码重新验证相同用户 ID、资料标记，确认 SQLite 卷持久化。
6. 成功或失败均采集容器日志并清理本次项目的容器、网络和卷；日志不输出测试密码或 Token。通过后导出后端镜像，并真实加载核对两份待发布归档的身份。

新增检查是否通过，以对应提交的 Actions 结果为准；本地脚本单元测试不能替代容器验证。

## 变量与 Secrets

以下两项支持 Repository Variables 或同名 Secrets，Variables 优先；已有 Secrets 无需移动或重填：

```text
ACR_REGISTRY=crpi-gbihc3e57h3o3f2l.cn-hangzhou.personal.cr.aliyuncs.com
ACR_NAMESPACE=tencent-ubutun22
```

Actions Secrets：

```text
ALIYUN_ACR_USERNAME
ALIYUN_ACR_PASSWORD
```

仅 publisher 通过 `${{ vars.ACR_REGISTRY || secrets.ACR_REGISTRY }}` 及对应 namespace 表达式读取镜像坐标。配置缺失或格式非法时，在登录前失败。`ACR_REGISTRY` 必须是不带 `https://` 和路径的主机名；`ACR_NAMESPACE` 只能使用小写字母、数字和连字符。

## 发布顺序与回滚记录

`ci/release_images.py` 先加载归档并核对镜像 ID，然后先推送两个镜像的 `sha-<7位提交>` 和可选版本标签，最后更新两个 `latest`。每次推送都解析并校验 manifest digest；版本标签与 latest 的 digest 必须一致。

发布摘要及 `published-images-<run-id>` Artifact 中的 `published-images.json` 记录完整源码提交、镜像 ID、已推送标签和成对的 `repository@sha256:<digest>` 引用。`complete: true` 才代表全部推送完成；失败时尽可能保留 `complete: false` 的部分发布记录。回滚使用已完成发布的两份 digest 引用，详见 [Watchtower 与回滚](watchtower-rollback.md)。

两个仓库的更新不是原子操作，后半段失败仍可能留下部分标签更新；不会自动回退 Registry 或服务器。演示环境需人工检查部分发布记录，不能据此宣称零中断或原子部署。

## 权限、并发与日志

- 权限限制为 `contents: read`、`packages: write`。
- 同一个 ref 使用同一并发组；PR 可以取消旧运行，push 和手动发布不取消。
- CI 禁止回显 Secrets，禁止上传 `.env` 或 Docker 登录配置。两份镜像归档和身份元数据保留 1 天；测试与容器日志保留 7 天；不含凭据的发布记录保留 30 天。
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

单镜像冒烟不能替代真实联调与持久化步骤。功能分支的 publisher 必须跳过；即使全部验证通过，也不等于实际 ACR 认证、推送、Watchtower 更新、真实 MySQL、服务器部署或浏览器交互测试通过。

## 常见失败

| 现象 | 检查项 |
| --- | --- |
| `requirements.txt` 编码失败 | 确认原文件仍是 UTF-16 BOM；CI 只转换临时副本为 UTF-8 |
| `mysqlclient` 编译失败 | 检查 `default-libmysqlclient-dev` 和 `pkg-config` |
| ACR 登录失败 | 使用 Registry 访问凭证，不是阿里云账号登录密码 |
| `unknown manifest class` | 确认 `provenance: false` 和 `sbom: false` |
| 镜像坐标配置缺失 | 检查同名 Repository Variables 或 Secrets；仅存在于 Secrets 也可使用 |
