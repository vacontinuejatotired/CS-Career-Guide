# CI/CD 流水线

> 状态：草案。工作流文件已在工作区，但尚未提交、推送，也尚未在 GitHub Actions 实际运行。

## 触发规则

| 事件 | 目标分支 | 测试 | 构建镜像 | 推送 ACR |
| --- | --- | --- | --- | --- |
| PR 到 `master` | 任意分支 | 是 | 是，仅构建不推送 | 否 |
| push 到 `master`，有代码变更 | `master` | 是 | 是 | 是 |
| push 到 `master`，只有 README/docs | `master` | 是 | 否 | 否 |
| push 到其他分支 | 任意 ref | 是 | 是，仅构建不推送 | 否 |
| `workflow_dispatch` 手动触发 | 任意选择的分支 | 是 | 是 | 仅 `master` |

纯文档判定只匹配 `README.md` 和 `docs/`。`.github/workflows/**`、`deploy/**`、Dockerfile 和 Nginx 配置都属于代码或部署配置，会触发镜像构建。

## Job 结构

```text
changes
  |-- backend-test  --> backend-image  --|
  `-- frontend-test --> frontend-image --+--> release-summary
```

- **backend-test**：把 UTF-16 的 `requirements.txt` 转成临时 UTF-8 文件，安装 `default-libmysqlclient-dev`，运行 `tests.test_auth`、`test_env_config.py`、`test_deploy_runtime.py`，并执行隔离 Django check。
- **frontend-test**：使用 Node 24，依次执行 `npm ci`、鉴权和配置测试、Vite 构建，并检查 `dist/index.html`、GLB 和 VAD ONNX 是否存在。
- **backend-image / frontend-image**：并行构建 `linux/amd64` 镜像。PR 和非 master 分支（包括从非 master 手动触发）只做 build-only 冒烟；后端容器实际执行静态收集、SQLite 迁移并等待 Gunicorn 健康，前端检查首页、history 路由、GLB/VAD 资源和未配置企业服务时的 503。只有 master 才登录 ACR 并推送。
- **release-summary**：只有两个镜像 Job 都成功时才通过。

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
- CI 禁止回显 Secrets，禁止上传 `.env`。Artifact 只包含测试日志、前端构建产物和发布摘要。
- 镜像构建使用 `type=gha` 缓存，并关闭 provenance/SBOM，避免个人版 ACR 拒绝不支持的 manifest 附件。
- 手动触发可以附加一个合法 tag；标准标签仍是 `latest` 和 `sha-<7位SHA>`。

## 首次 PR 验证

```bash
git switch -c codex/ci-cd-images
# 完成实现与本地检查后
git push -u origin codex/ci-cd-images
gh pr create --base master --head codex/ci-cd-images
gh run list --workflow CI/CD
```

合并前确认：

1. 后端和前端测试 Job 都通过。
2. build-only 镜像可以启动，且没有执行 ACR 登录或推送。
3. 纯文档改动不会触发镜像 Job。
4. 失败时可以下载测试日志，日志中没有凭据。

## 常见失败

| 现象 | 检查项 |
| --- | --- |
| `requirements.txt` 编码失败 | 确认原文件仍是 UTF-16 BOM；CI 只转换临时副本为 UTF-8 |
| `mysqlclient` 编译失败 | 检查 `default-libmysqlclient-dev` 和 `pkg-config` |
| ACR 登录失败 | 使用 Registry 访问凭证，不是阿里云账号登录密码 |
| `unknown manifest class` | 确认 `provenance: false` 和 `sbom: false` |
| Variables 缺失 | 在 Settings → Secrets and variables → Actions 配置两个 Repository Variables |
