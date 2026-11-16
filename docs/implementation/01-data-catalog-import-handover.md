# 成员1：授权题库导入交接

日期：2026-11-15

状态（2026-11-16 更新）：**943 道题已导入现有演示服务的 SQLite 数据库**；重复导入、真实网关目录查询、正式检索与练习会话创建已通过。原 2026-11-15 交接内容保留为操作说明；实际执行证据见下文，不以 CI 通过代替数据验收。

## 2026-11-16 导入签收

以下是北京时间09:22首次导入时的证据快照；后端镜像、源文件hash、检索算法和验收范围均以当时执行为界。后续PR #54已调整来源显示并上线BM25与关键词知识点兜底，自由面试技术追问也已接入题库；当前接口和部署以[App接入文档](../app-api.md)及[运维记录](../deployment-status.md)为准。原始导入文件hash为下文的d5b4d083，新显示文件hash为 `5c41c2a85e812e11529d5023db7598da2351ff50c4e229b099c88256e0d89fab`，显示调整不改变题目ID、题干或许可。此次处理PR只补文档，不重新执行导入。

- 授权：项目用户在本次会话明确确认，已核实允许用于本项目线上题库和面试检索，按 `allowed` 导入。凭证由项目方保管，本仓库不附原件；不将会话确认写成助手已独立审阅原件。
- 执行：Codex 按用户授权，通过既有严格主机密钥核验 SSH 通道，在运行中的 `cs-career-guide-backend` 调用 `import_catalog --kind questions`。没有 staff 用户，沿用命令已有 `management-command` 系统 actor；未创建管理员、读取已有 Token 或修改账号权限。
- 环境：现有演示服务器 `123.207.252.243`，后端健康；SQLite 文件 `/data/cs-career-guide.sqlite3`，导入前题库 0 条。后端镜像 ID 为 `sha256:6d739130e365c9f08319418caccb3c0af1a0c5281250286d15a1b84ff8deb656`；包含导入命令，不为本次导入重新部署或切换数据库。
- 备份：2026-11-16 09:22:28（北京时间），使用 SQLite backup API 创建 `/data/catalog-backups/before-xiaolincoding-20261116T012228Z.sqlite3`，1,454,080 字节，权限 `0600`，`PRAGMA quick_check=ok`；SHA-256 为 `8b77a79f00de115353e86240bc33be81dd83a4f1f2a3332e7ec4cd2274672b41`。备份留在服务器持久卷，不下载或入库；完整库恢复会覆盖后续数据，不能默认用备份整体替换当前库。
- 数据文件 SHA-256：`d5b4d0834c70558d933367f71afe13453506c5499fc56819d2f463660b0f507c`。本地离线校验 943/943 通过，重复去重键与重复题干均为 0；服务器接收后再次校验同一 hash，数据临时文件随命令结束清理。
- 线上 dry-run：`created=943 updated=0 unchanged=0`，前后计数均为 0；正式导入：`created=943 updated=0 unchanged=0`；第二次正式执行：`created=0 updated=0 unchanged=943`。最终 `xl-` 前缀记录与全表计数均为 943，全部 `allowed`、`is_demo=false`，来源、来源链接和采集时间完整。
- 索引：首次 `index_notification=not_configured`，重复执行 `not_required`；这是既有 ORM 检索架构的预期行为，不代表已建立向量索引。
- 实际 HTTP 验收：后端容器通过 `gateway:8080` 访问现有网关与 Gunicorn，匿名目录查询返回 401；带临时验收 Token 的 `catalog/questions/?role=Java后端&topic=集合&page_size=1` 返回 200、`count=69` 且来源/采集时间完整。正式 `questions/retrieve/` 使用 `ArrayList` 与集合主题返回 200、1 条 `origin=catalog` 且带来源链接；底层 `DjangoQuestionRetriever` 同样命中。
- 练习验收：使用本次正式检索回执和题目 ID 创建练习会话，返回 200、1 条目录题快照；重复同一请求返回同一会话。临时普通用户、临时 Token 与其练习记录已删除并核对不存在；没有提交答案或调用反馈/总结模型。
- 范围限制：未做浏览器页面点击、真实模型、MySQL 或成员2评估基线重跑；不代表所有16主题/全部难度的检索质量已验收。自由模拟面试继续使用 legacy 主链路，本次没有将其改接题库。

原第9节为首次导入前的交接模板，不是当前待办状态：该次已完成授权确认、备份、dry-run、正式导入、幂等与API/练习创建验证，未代发通知。以下第1至9节保留原操作说明及当时限制；其中“尚未验证”的陈述只描述首次导入范围，后续评估、模型、浏览器与发布证据见对应实施文档和运维记录。

## 1. 已完成

- PR [#37](https://github.com/vacontinuejatotired/CS-Career-Guide/pull/37)：943 道小林coding Java 后端面试题，文件为 `data/career-platform/xiaolincoding-questions.json`，记录带 `source`、`source_url`、`collected_at`、`dedupe_key`，当前标记 `permission_status=allowed`、`is_demo=false`。
- PR [#38](https://github.com/vacontinuejatotired/CS-Career-Guide/pull/38)：幂等导入入口与测试。
  - `backend/company_reviews/management/commands/import_catalog.py`
  - `data/career-platform/import_catalog_via_api.py`
  - `backend/tests/test_catalog_import.py` 新增 943 条导入、二次幂等、目录查询和 `DjangoQuestionRetriever` 检索断言
- 主项目 `master` 合并提交：`1c7c816`。
- CI：PR #37、#38 全绿；本地 catalog 固定验收 4 项 + 导入测试 7 项通过。
- 合并后的 master 流水线 `43722555711` 检查已通过，镜像发布/部署进行中；截至本文撰写时未确认线上运行版本。实际线上版本以 Actions 和部署记录为准。

## 2. 数据会进入哪些功能

- **目录题库查询**：`GET /api/career-platform/catalog/questions/`，role/difficulty不区分大小写精确匹配，topic优先规范分类、无对应分类时按内容关键词兜底；前端 `/career-platform/catalog` 展示来源和采集时间。正式BM25检索和目录包含查询不同，详见App接入文档。
- **练习页** `/career-platform/practice`：正式检索由 `DjangoQuestionRetriever` 读取 `allowed` 的 `InterviewQuestion`，选中后创建练习会话。
- **成员4 RAG**：逐题检索、参考要点和来源证据使用同一批数据库记录。
- **成员2评估**：评估和检索基线需在导入后重跑，不能沿用旧 Top-K/分数。
- **App 端**：复用同一套 API，见 `docs/app-api.md`。
- **索引说明**：当前题库不使用 LanceDB 向量索引；`career_platform_questions_v1` 只是契约索引名，`index_notifier` 未配置，ORM 是检索权威来源。导入结果中的 `index_notification=not_configured` 是预期值。

## 3. 交接前必须确认

- [ ] **授权**：943 条题标记 `allowed` 的依据是成员1声明已获原作者授权；书面凭证不在仓库。导入前请核对授权范围与凭证。
  - 若授权未落实：先把 `permission_status` 改为 `pending`（JSON 或数据库），或只做 dry-run；`pending` 不会进入正式查询和 RAG。
- [ ] **目标环境**：确认 base URL/数据库连接，避免误导入本地或他人环境。
- [ ] **备份**：线上 SQLite/MySQL 先备份。导入本身幂等，但回滚删除仍需要备份。
- [ ] **权限**：执行人需要 `is_staff=true` 账号的 Token，或服务器/数据库访问权限。

## 4. 导入方式 A：HTTP API（推荐，不依赖新镜像）

要求：已部署后端可达，持有 staff Token。现有 `catalog/imports/` 接口已支持本数据集，不需要等待新镜像。

```bash
export CATALOG_IMPORT_TOKEN='<staff-token>'
python data/career-platform/import_catalog_via_api.py \
  data/career-platform/xiaolincoding-questions.json --dry-run
python data/career-platform/import_catalog_via_api.py \
  data/career-platform/xiaolincoding-questions.json --commit
```

- 默认 base URL 为 `http://123.207.252.243/api`，可用 `--base-url` 覆盖。
- HTTP 明文仅用于当前演示环境；正式环境应使用 HTTPS。
- Token 只从环境变量读取，脚本不回显、不跟随重定向；不要提交到仓库。
- 预期：第一次 `created=943`；再次执行 `created=0 unchanged=943`；`index_notification=not_configured`。

## 5. 导入方式 B：服务器管理命令（需要新镜像和数据库访问）

```bash
docker cp data/career-platform/xiaolincoding-questions.json <backend-container>:/tmp/
docker compose exec -T backend python manage.py import_catalog /tmp/xiaolincoding-questions.json --dry-run
docker compose exec -T backend python manage.py import_catalog /tmp/xiaolincoding-questions.json --commit
```

- 默认 dry-run；`--commit` 才写库；可用 `--kind questions` 只导入题库。
- 命令复用 `CatalogService`，按 `dedupe_key` 幂等，单批最多 1000 条。
- 优先使用第一个 staff 用户；没有 staff 用户时使用管理命令系统 actor，并打印警告。

## 6. 导入后验收

```bash
# 方式 A：API 查询（替换 Token）
curl -H "Authorization: Token $CATALOG_IMPORT_TOKEN" \
  "http://123.207.252.243/api/career-platform/catalog/questions/?role=Java后端&topic=集合&page_size=1"

# 服务器/Django shell
python manage.py shell -c \
"from career_platform.models import InterviewQuestion; \
 print(InterviewQuestion.objects.filter(dedupe_key__startswith='xl-').count()); \
 print(InterviewQuestion.objects.filter(permission_status='allowed', topic='集合').count())"
```

- `dedupe_key` 前缀 `xl-` 的数量应为 **943**。
- `catalog/questions/` 返回 `count > 0`，结果含 `source`、`source_url`、`collected_at`。
- 练习页用 `role=Java后端`、`topic=集合` 和任意难度发起检索，应能选到题目并创建会话。
- 成员4 `DjangoQuestionRetriever` 查询 `ArrayList` 应返回结果，`origin=catalog`。
- 成员2需重跑评估/检索基线；旧 Top-K 或分数不能复用。

## 7. 回滚

仅在确认需要撤销时执行，先备份：

```bash
python manage.py shell -c \
"from career_platform.models import InterviewQuestion; \
 qs=InterviewQuestion.objects.filter(dedupe_key__startswith='xl-'); \
 print('to delete', qs.count()); qs.delete()"
```

- 只删除本数据集（`xl-` 前缀）；不要按题目文本或其他来源批量删除。
- 已创建的练习会话使用快照；删除题目不会改写历史快照，但会影响后续检索。
- 回滚后把实际数量、执行人、时间和原因追加到 `docs/deployment-status.md` 或对应发布记录。

## 8. 已知限制

- 难度和主题为 `rule-based-v1` 自动分类，未逐题人审；建议抽检后再扩大使用。
- 未执行真实 MySQL、浏览器、真实模型或 RAG/评估基线重跑。
- `java2top.cn` 未采集（本机不可达且其源仓库无许可证）。
- 导入是否成功以数据库计数和实际接口结果为准，不以 CI 通过代替。

## 9. 交接清单

- [ ] 核对授权凭证；未落实则先把数据改为 `pending` 或只做 dry-run。
- [ ] dry-run 结果为 943。
- [ ] `--commit` 后 `dedupe_key` 前缀 `xl-` 计数为 943。
- [ ] 目录查询、练习页检索、成员4文本检索各验证一次。
- [ ] 通知成员2重跑评估基线、成员4重跑检索验收。
- [ ] 在 `docs/deployment-status.md` 或发布记录登记导入时间、执行人、环境、结果和限制。
