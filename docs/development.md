# 开发指南

先读根目录 [agent.md](../agent.md) 选择任务文档。主分支为 master，日常使用 codex/personal；分支和 PR 规则见 [Git 规范](git-workflow.md)。

## 代码定位

| 位置 | 当前职责 |
| --- | --- |
| `frontend/src/views/` | Vue 页面；模拟面试在 interview/Index.vue |
| `frontend/src/api/` | Axios/fetch、登录凭据与共享 API 入口 |
| `frontend/src/features/interview/` | 面试服务契约、legacy 适配器、SSE 解码及实现组装 |
| `frontend/src/config.js` | 公开前端配置与 URL/超时设置 |
| `backend/cs_career_guide/` | Django 配置、总路由、鉴权中间件及向量存储契约 |
| `backend/users/`、`resumes/` | 用户、资料和简历接口 |
| `backend/career_paths/`、`career_evaluation/`、`company_reviews/` | 职业路径、评估、企业相关业务 |
| `backend/ai_integration/` | 共享模型接口、会话/复盘记录、职业报告、检索和 LangGraph 实现 |
| `backend/ai_integration/interview/` | 网页面试当前使用的提示词策略与复盘解析 |
| `backend/asr/` | Fun-ASR 协议和真实短音频上传已验证；浏览器录音权限与完整语音流程另行验收 |
| `ci/`、`.github/workflows/` | 离线脚本测试、runner 联调、镜像发布及可选 AI 配置同步 |
| `deploy/` | Compose、部署配置样例与 digest override |

总路由在 backend/cs_career_guide/urls.py，前端路由在 frontend/src/router/index.js。新增接口前先核对两端实际路径与鉴权，不只按文件名判断实现是否被页面调用。

## 本地环境

后端使用 Python 3.11，前端/CI 使用 Node 24。遵循 [README 环境步骤](../README.md) 与 [配置说明](environment.md)，只复制 `.env.example` 创建自己的配置，不覆盖已有环境文件。真实秘密不入库。

低资源开发可使用 SQLite 演示配置 `cs_career_guide.settings_sqlite`，MySQL 是另一种显式选择。SQLite 不要求 MySQL 凭据；应用仍需有效 SECRET_KEY。嵌入模型关闭时走关键词检索，不下载或伪造向量。

前端开发代理目标由 DEV_* 配置；VITE_* 会进入浏览器。独立企业查询服务不由 Django 自动提供，默认生产 Nginx 对 company-api 返回 503；不要把前后端启动等同于全部功能可用。

requirements.txt 是现有 UTF-16 文件，CI 会转换临时副本；不要顺手整文件转码或升级依赖。镜像使用 requirements-runtime.txt，缺少本地 Embedding 的可选重依赖是当前演示方案的一部分。

## 选择与改动相关的验证

纯文档检查链接和命令即可；业务/协议重构跑对应测试，公共鉴权、配置或 API 变化补相关回归。下面是可在仓库根目录运行的 Windows 命令，使用已有 `.venv`；测试均为隔离数据或虚构模型，不需要真实 Key。

```powershell
node --test frontend/tests/auth.test.mjs frontend/tests/config.test.mjs frontend/tests/api-contract.test.mjs frontend/tests/interview.test.mjs
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -p test_interview.py
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -p test_env_config.py
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -p test_deploy_runtime.py
.\.venv\Scripts\python.exe -m unittest discover -s ci -p test_*.py
```

鉴权测试使用 Django runner，不要直接用普通 unittest discover 导入它：

```powershell
Push-Location backend
..\.venv\Scripts\python.exe -m django test tests.test_auth --settings=tests.auth_settings
Pop-Location
```

Linux/macOS 对应 Python 路径通常为 `.venv/bin/python`。ci/sync_runtime_env 的 POSIX 权限测试在 Windows 跳过、Linux 执行；跳过不能写成已验证 Linux 文件行为。

前端生产编译在 frontend 目录运行 `npm run build`；确认已有环境配置符合本次验证目的，输出写忽略目录。构建通过不能替代浏览器和模型验收。Docker 构建、真实容器冒烟、Nginx/Django 联调、SQLite 持久化在 Actions runner 验证，不为完成本地测试启动 Docker。

2026-10-26 补齐 `career_paths` 初始迁移，修复新部署只运行 `migrate` 时职业路径、题目和结果表没有创建的问题。新库按原流程执行 `migrate`；历史数据库若已手动建齐这三张表，先备份并核对模型与表结构，再使用 `migrate career_paths --fake-initial` 登记初始迁移，不能直接对部分存在或结构不一致的表使用 fake。本次迁移只建表，不导入题库、职业或招聘数据。`test_career_path_migrations.py` 在内存 SQLite 中执行真实迁移并验证三类记录读写与模型无漂移。

真实模型/语音、浏览器账号和服务器检查按实际授权执行，记录时间、环境、输入范围及结果；保留失败证据，不把模拟通过写成真实服务成功。相关接口与验收见 [面试重构](interview-refactor.md)。

## 增量维护文档

修改功能时优先补对应文档中的行为、使用方法和验证，不扩写无关内容；新主题文档加入 agent.md 索引。配置、接口、迁移和部署变化的具体要求见 [文档更新表](git-workflow.md#开发时补多少文档)。历史接手记录提供线索，实际开发仍以当前代码和查询结果为准。
