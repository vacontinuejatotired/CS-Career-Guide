# 成员3：简历 NLP 与有依据的建议

> 2026-11-16 通用优化与岗位定向优化均已部署，发布证据及真实模型限制见 deployment-status.md。下文早期501、候选和未部署记录为历史快照；不填JD的通用优化及本次线上验收见文末。

## 2026-11-15 优化入口并入简历工作台

- `/resume` 新增“编辑与预览 / 岗位对照与优化”切换；优化URL为 `/resume?tab=optimize`。编辑区使用v-show保留未保存内容，切换不重新创建编辑器。
- 旧 `/career-platform/resume` 兼容重定向，保留其他query/hash；课程导航移除重复入口。
- `views/resume/OptimizationPanel.vue` 提供JD输入与真实服务状态；分析前读取已保存简历的edit_revision，不让用户手填版本或建议ID。未保存编辑不自动上传，分析不等于应用，不写原简历。
- 后端仍501，页面明确“开发中”，不生成固定建议或虚假成功。原保存/导出/预览不改。旧Resume.vue骨架保留但不再由路由加载。


先读 [公共约定](00-shared-contracts.md) 与 [当前方案](../career_platform_plan.md)。已有简历 CRUD、只读观览、面试用文件简历，以及分析、历史和确认应用。2026-11-22 的 `migration` 合入保留文件简历上传与解析；分析/应用继续使用主分支的版本、证据、事务和幂等实现。真实模型质量、MySQL 并发与部署仍需独立验收。

## 修改边界与目标

负责 `backend/career_platform/resume/`、`views/resume.py`、`models/resume.py`、`backend/resumes/`、Resume.vue；公共契约/序列化器/组装/迁移集成人审核。不得改自由面试主链路、另建简历表、客户端指定owner、自动将建议覆盖原稿。文件简历可由多模态模型解析，但结果仅供面试选择，不自动补写经历或修改平台编辑稿，也不执行自动投递。

## Facade、Strategy 和 Adapter

`ResumeAnalysisService` 是Facade，只提供 analyze/list_runs/get_run/apply。文本匹配Strategy处理JD技能抽取、分段和证据匹配；ModelGateway Adapter隔离供应商与超时；repository读取/保存快照和回执。Vue只处理输入、原文/建议/理由/证据展示和逐条选择，不拼模型请求；Django视图只鉴权和校验。

## 分析与应用流程

| 动作 | 输入、步骤、输出和保存 | 异常与不变量 |
| --- | --- | --- |
| analyze | jd_text、可选job_id、resume_revision、request_id→读取当前用户Resume及子项→检查版本→快照→JD抽取→分段匹配→模型建议→结构/事实校验→保存ResumeAnalysisRun | 无简历404；版本409；超时/无效输出失败且原稿不变，不保存假成功 |
| list/get | 当前用户过滤→分页或UUID详情→返回原快照/匹配/缺项/建议 | 其他账号/不存在404；不得回查新简历替代历史 |
| apply | analysis ID、base_revision、accepted_suggestion_ids、request_id→权限/建议归属→锁Resume→版本检查→仅已接受字段写回→版本递增→回执 | 未接受项不变；旧版本409且零写入；同键复用首次结果 |

建议结构按00，可写字段仅限 `skills`、`self_evaluation`；项目/经历只生成 STAR 原文摘录和缺项问题，不直接写回。字段必须使用白名单、归属检查和原文比对，禁止任意 setattr 或用户/主键路径。证据必须逐字存在于对应目标字段；JD 只能支持“岗位要求/缺项”，不能据此写成用户已有技能。无用户事实依据的技能、职责、成果数字必须拒绝或改为待补充问题，不允许以 LLM 自检取代规则验证。

示例：原文“使用Java完成课程项目”，JD要求Redis；可以建议清晰说明已有Java项目职责，并将Redis列入 gaps，不能改成“使用Redis将性能提升50%”。分析输出包含该原文片段和字段位置，拒绝建议后数据库完全不变。

用户编辑建议通过 apply.suggestion_edits 提交，格式为建议UUID到编辑文本字典，默认空。只允许编辑本次已接受建议，服务端必须重新校验字段、原文及事实依据，再原子应用。不能只在界面编辑却保存旧建议。

版本方案：模型调用在锁外，对成功分析保留base_revision；应用时事务select_for_update读取当前简历。Resume.save已经维护主表更新版本，成员须覆盖所有子表修改入口及禁止绕过版本的bulk写。并发两次应用只有一个成功；另一个409；相同request_id返回同回执，不重复递增。模型失败与重试保留前端输入，重试必须由用户明确触发。

### 面试用文件简历（2026-11-22）

`ResumeUpload` 保存当前登录用户最多两份文件简历，字段为原始文件名、文件 URL、模型结构化结果、解析降级标记和上传时间。`GET/POST /api/resumes/uploads/` 负责列表和上传，`DELETE /api/resumes/uploads/<id>/` 删除；超过两份返回 HTTP 409 和 `RESUME_UPLOAD_LIMIT`。文件简历与平台编辑的 Resume 分离，不参与分析建议的自动应用。

上传支持 PDF、JPG、PNG、WebP，最大 10MB；PDF 最多读取前5页。PDF 使用 PyMuPDF 在进程内渲染，图片和 PDF 页面交给已配置的多模态模型提取目标岗位、年限、技能、教育、经历和项目；解析失败只保存降级状态，不生成假简历。`resumes.0005` 把历史单文件迁移为一条 `ResumeUpload`，并补齐 `Resume.parsed`、`Resume.parsed_degraded`；运行时依赖新增 `PyMuPDF==1.26.7`。

面试开始页提供“平台编辑的简历 / 已上传的简历”选择。上传模式只向聊天接口提交 `uploaded_resume_id`，后端按当前用户读取解析结果并加入系统提示词；客户端不能直接提交任意解析文本。选择上传文件后不再同时注入 `localStorage.resume`。

## 接入与分步验收

### 2026-11-10 共享网关与练习简历快照影响

`b127df1` 在唯一 composition 中向 ResumeAnalysisService 注入与 records/rag 共用的 `JsonModelGateway`，但没有实现 analyze/list/apply；本模块固定3项仍因501失败，不能把网关注入描述为简历优化完成。

练习 Repository 只读取当前登录用户 Resume，保存 id、edit_revision、target_position、skills、self_evaluation 和教育/经历/项目/证书/奖项字段；不写简历、版本或子表，也不保存姓名、电话、邮箱、地址和头像顶层字段。无简历时当前保存空快照 `{}`，不阻止按题目练习。自由文本仍可能自行包含私人信息，顶层白名单不等于全文自动脱敏。

Resume 子项统一输出名为 educations/experiences/projects/certificates/awards，分别读取 ORM 的 education/experience/projects/certificates/awards 关联。该快照用于还原练习当时内容，不从历史 JSON 反向更新当前简历，也不替代本模块的 ResumeAnalysisRun。

生产网关延迟导入 ChatOpenAI，读取既有后端 LLM_* 配置；未配置或生成失败不会提供固定建议。本轮未调用真实模型、未迁移真实数据库、未改变既有简历 CRUD 或 legacy 面试。

构造器注入 matcher/model_gateway/repository；测试模型分别返回有依据建议、虚构数字、非法字段、超时，repository使用隔离ORM或确定性替身。生产不能默认返回固定建议。成员1提供岗位快照，成员2经公开匹配接口评估，不复制分段算法。

| 步骤 | 实施与观察 | 固定验收 |
| --- | --- | --- |
| 1 | JD抽取/简历分段/证据纯函数 | 引文能定位原文；缺项不转成事实 |
| 2 | 完整分析Facade | 成功保存快照、版本和模型/提示词版本；超时/非法输出不改原稿 |
| 3 | 原文、建议、理由、证据与选择/编辑页面 | 拒绝不保存；编辑内容必须实际经过服务端校验和应用 |
| 4 | 应用事务/幂等/版本/所有入口维护 | 旧版409、新版原文保留；并发不覆盖；他人分析404 |
| 5 | 历史分析列表/详情 | 更新简历后旧分析快照仍可还原 |

运行 `python ci/project_acceptance.py --stage complete --module resume`，补跑既有简历/登录回归及前端测试/构建。测试需比较原稿和子项、version、回执数量，不能只检查文本看起来合理。

## 验收记录

| 提交号 | 执行命令 | 结果 | 环境 | 模拟/真实范围 | 已知限制 | 证据位置 |
| --- | --- | --- | --- | --- | --- | --- |
| d12128b + dirty | 待执行resume complete | 未实现 | 隔离SQLite | 无真实模型 | 501，编辑字段已预留 | output/ |
| 83fe086 + dirty | 上传解析、用户隔离、两份上限、面试来源选择与真实流式联调 | passed | 本地 MySQL；Chrome；真实模型 | 示例 PDF 解析和两种简历来源 | 非远端 CI/部署；手机为模拟视口 | `backend/tests/test_resume_uploads.py`; `frontend/tests/resume-uploads.test.mjs` |
| 2369055 + dirty | resume complete、all、现有 API 回归 | passed | 隔离 SQLite；离线 Gateway | 不调用真实模型 | MySQL并发、真实生成质量另验 | `.runtime/resume-complete.json` |

## 文档更新与 PR 检查表

| 变更 | 同步文档 |
| --- | --- |
| 字段路径/建议校验/版本更新方式 | 本文及00，列全现有写入口 |
| 匹配策略/模型提示词 | 本文及02，记录版本和证据限制 |
| 验收完成 | 上表实际执行证据，独立写真实模型范围 |

- [x] 事实不编造、权限、版本、幂等、事务及超时/非法输出用例通过。
- [x] 编辑确认后写入的是已展示/确认内容；拒绝时原稿不变。
- [x] 原有简历 CRUD/观览与文件简历选择不回归，秘密不进入前端。
- [x] 实现、固定测试、本说明及必要公共约定同 PR 更新。


### 2026-10-28 本地准备状态

本轮补齐实施文档和固定验收/CI草稿，业务仍未实现。用户曾要求暂不推送、不再验收；现已授权推送开发准备内容，继续不追加本地验收。最后修改未复测。此记录仅描述执行过的检查范围，不作为模块完成声明。

```acceptance-record
{
  "commit": "d12128b + dirty",
  "command": "python ci/project_acceptance.py --stage complete --module all",
  "result": "not_implemented",
  "environment": "Windows; isolated SQLite; 2026-10-28",
  "scope": "Offline fixtures only. Earlier run: 17 business tests rejected the unfinished services; 7 scaffold and 7 document-gate unit tests passed before final edits.",
  "limitations": "Latest contract, CI and documentation edits have not been retested. User authorized pushing this preparation baseline without additional local acceptance. No MySQL runner, browser flow, real model, remote CI or deployment acceptance.",
  "evidence": "output/full-expected-failure.json; output/scaffold-resumed.json; local changes on codex/team-scaffold"
}
```


### 2026-11-01 交付拆分与原业务门禁

仅细化交付配置选择，不修改本模块业务或固定验收用例。交付编排和真实网关联调独立验证；验收规则变更仍触发原完整业务门禁。本模块仍是未完成骨架，不将交付验证作为业务完成证据。

```acceptance-record
{
  "commit": "15828fa + dirty",
  "command": "python ci/project_acceptance.py --stage complete --module all --output output/split-delivery/business-complete.json",
  "result": "failed",
  "environment": "Windows；隔离 SQLite；2026-11-01",
  "scope": "交付拆分仅调整选择范围，原固定 complete 用例保留。17 项业务测试因 501/FeatureNotImplemented 出现 14 failures、3 errors；骨架 7 项通过。",
  "limitations": "五个业务模块仍未实现；此本地记录不覆盖 MySQL runner、镜像发布、服务器部署、真实模型或浏览器验收。",
  "evidence": "output/split-delivery/business-complete.json; output/split-delivery/scaffold.json; ci/test_project_changes.py; docs/split-delivery.md"
}
```


### 2026-11-01 首次网关切换工具

本模块业务与固定验收不变；交付工具测试不代表业务完成。

```acceptance-record
{
  "commit": "7909ecf + dirty",
  "command": "python -m unittest discover -s ci -p test_*.py -q; preserved complete acceptance in Actions 41304123356",
  "result": "failed",
  "environment": "Windows/WSL isolated offline fixtures; 2026-11-01",
  "scope": "85 delivery tests passed on WSL; 71 passed and 14 POSIX skipped on Windows. Cutover success, pull failure, environment mismatch and frontend rollback tested. Original business complete suite remains failed (501 skeletons), not modified.",
  "limitations": "No business implementation; no model calls or database migrations. Server install not yet performed in this record. Existing business failure accepted for delivery-only merge.",
  "evidence": "ci/test_server_cutover.py; ci/test_split_topology.py; Actions 41304123356; docs/split-delivery.md"
}
```


### 2026-11-01 首次维护传输与超时修复

交付工具变更保留本模块现有业务状态；不将构建或服务器审计作为业务完成证据。

```acceptance-record
{
  "commit": "e301070 + dirty",
  "command": "wsl -d Ubuntu-22.04 --cd /mnt/e/CS-Career-Guide-split-delivery -- python3 -m unittest discover -s ci -p 'test_*.py' -q; original complete suite: Actions 41305627720",
  "result": "failed",
  "environment": "2026-11-01；WSL 离线隔离测试；既有完整业务验收为 Actions SQLite/MySQL",
  "scope": "压缩网关归档、限量解压及旧归档兼容；87 项交付测试通过。维护 workflow 超时变更仍触发原完整业务门禁，五模块 501 骨架失败保留，不修改业务代码或固定验收。",
  "limitations": "本记录的交付单元测试不代表业务完成。线上首次切换尚未成功；独立审计确认旧容器健康且未变。无真实模型、数据库迁移或浏览器验收。",
  "evidence": "ci/test_server_maintenance.py; ci/test_server_cutover.py; Actions 41308721534; docs/deployment-status.md"
}
```


### 2026-11-01 首次网关 ACR 传输

不修改本模块业务及验收规则；交付测试和业务完成分别记录。

```acceptance-record
{
  "commit": "7ab4193 + dirty",
  "command": "wsl -d Ubuntu-22.04 --cd /mnt/e/CS-Career-Guide-split-delivery -- python3 -m unittest discover -s ci -p 'test_*.py' -q; original complete suite: Actions 41309171882",
  "result": "failed",
  "environment": "2026-11-01；WSL 离线隔离测试；Actions SQLite/MySQL 原业务验收",
  "scope": "88 项交付单元测试通过。首次网关镜像改走已授权 ACR 专用基础设施标签，按 digest/image ID 验证；业务接口和固定验收保持原样，现有完整业务 14 failures/3 errors 为 501 骨架。",
  "limitations": "此交付验证不代表五模块实现；没有重启线上后端、迁移数据或真实模型调用。此前 SSH 传输超时，审计确认旧容器未变。",
  "evidence": "ci/test_server_maintenance.py; ci/cutover_smoke.py; Actions 41311002510; docs/deployment-status.md"
}
```

### 2026-11-02 发布门禁复核

本次调整既有简历页面及面试简历观览的交互和样式，公共导航变更要求同步本模块记录。新的 JD 对照分析、建议证据、人工确认与幂等应用服务仍未实现，不将原简历 CRUD 的回归通过计为 resume complete。

```acceptance-record
{
  "commit": "c34a98a6a2d0538e3b9c47d53f2e0c066e326202",
  "command": "python ci/project_acceptance.py --stage scaffold --output .runtime/gate-repair/scaffold.json; python ci/project_acceptance.py --stage complete --module all --output .runtime/gate-repair/complete.json",
  "result": "failed",
  "environment": "2026-11-02；Windows；现有 D:/python/python.exe；隔离内存 SQLite；PLATFORM_TEST_MYSQL=0",
  "scope": "骨架 7 项通过；固定完整业务验收 17 项为 14 failures、3 errors，五模块 501 / FeatureNotImplemented。测试提交 c34a98a 与部署目标 master 0f64e4e 的 tree 均为 cb53fd5f04e5e5197b289dadef18a8aea55c48b3。",
  "limitations": "五个业务模块尚未实现，本次未修改业务代码、固定测试或门禁。未重新验证 MySQL、真实模型或浏览器，未执行镜像发布、服务器重建或线上迁移。用户选择保留门禁，完整验收通过前不部署。",
  "evidence": ".runtime/gate-repair/scaffold.json; .runtime/gate-repair/scaffold.log; .runtime/gate-repair/complete.json; .runtime/gate-repair/complete.log; GitHub Actions 41456388774（文档门禁失败、应用测试/双镜像/联调成功）；41467510972（只读 SSH 审计成功）"
}
```


### 2026-11-09 文本检索演示发布候选

本次新增经过 Token 鉴权的 `POST /api/career-platform/questions/demo-retrieve/`，与正式 `questions/retrieve/` 隔离。页面 `/career-platform/practice` 改为明确标注的文本检索演示，提供条件筛选、排名与来源证据。候选为 `rag/demo.py` 专门编写的9条虚构演示材料，不导入测试 fixture、不写数据库、不创建会话或反馈；pending/restricted 不返回。正式五模块服务和旧自由面试边界保留。共享 URL 新增使本次按原规则核对六份文档与全部固定验收，不降低既有用例。详细输入、输出和范围见成员4说明。

```acceptance-record
{
  "commit": "93640dd + dirty",
  "command": "python -m unittest discover -s backend/tests -p test_text_retrieval.py -v; python -m unittest discover -s backend/tests -p test_retrieval_demo.py -v; node --test frontend/tests/*.test.mjs; node frontend/node_modules/vite/bin/vite.js build (cwd=frontend); python ci/project_acceptance.py --stage scaffold; python ci/project_acceptance.py --stage complete --module all",
  "result": "failed",
  "environment": "2026-11-09；Windows；隔离内存 SQLite；本地浏览器通过隔离预览 API 调用真实文本策略，无生产数据",
  "scope": "文本策略17项、演示接口6项、前端78项和生产构建通过；骨架7项通过。固定完整业务17项仍为14 failures、3 errors，原因是五模块正式服务501。独立演示不冒充正式业务完成。",
  "limitations": "仅发布候选准备。用户明确授权将标注演示的半成品部署到现有网站；允许使用既有手动发布流程，固定测试和门禁规则不改。未接数据库题库、真实模型、练习记录；远端CI、发布和线上浏览器结果另记。",
  "evidence": "backend/tests/test_text_retrieval.py; backend/tests/test_retrieval_demo.py; output/retrieval-demo-20261109/scaffold.json; output/retrieval-demo-20261109/complete.json; pre-deploy audit Actions 42551685730"
}
```


### 2026-11-09 课程页面字体统一

共享页面样式调整：沿用全站无衬线字体，课程标题桌面32px/手机28px，内容标题18px、正文与表单14px、辅助文字12px。仅视觉调整，不改变本模块接口、状态或数据流，不代表业务实现完成。

```acceptance-record
{
  "commit": "8607c29",
  "command": "gh run view 42578102031 --repo vacontinuejatotired/CS-Career-Guide; node --test frontend/tests/*.test.mjs; node frontend/node_modules/vite/bin/vite.js build (cwd=frontend)",
  "result": "failed",
  "environment": "2026-11-09；Windows 本地隔离浏览器及 GitHub Actions",
  "scope": "仅课程页面字体样式。前端78项与生产构建通过；浏览器1440/390px检查五个课程入口和个人中心、简历页，共14视图无横向溢出或JS运行异常。Actions前端检查及镜像构建成功，但共享组件变更缺实施文档导致总门禁失败。",
  "limitations": "五模块正式业务未完成，未宣称complete通过；本轮完整业务重跑因WSL互操作失败未启动。浏览器使用隔离模拟API，仅初始页面，不覆盖检索结果和全部失败状态。用户已授权半成品演示上线；仅按既有手动流程发布前端，不修改门禁、不部署后端。线上结果另记。",
  "evidence": "Actions 42578102031；output/playwright/typography-result.txt；frontend/src/features/career-platform/WorkspaceShell.vue；frontend/src/views/career-platform/Practice.vue"
}
```


### 2026-11-09 课程导航统一

五个课程入口共用CourseNav，保持名称、顺序、选中样式与顶部位置一致；自由模拟面试作为练习页辅助入口。内容轻量淡入，尊重减少动态效果设置；不改变本模块业务实现状态。

```acceptance-record
{
  "commit": "66a5159 + dirty",
  "command": "node --test frontend/tests/*.test.mjs; vite build; playwright-cli run-code --filename output/playwright/course-nav-check.js",
  "result": "passed",
  "environment": "2026-11-09；Windows；本地隔离模拟API与Chromium",
  "scope": "仅统一课程导航和切换样式。78项前端测试、生产构建通过；1440/390px各点击五个入口，共10次切换均为同名同序五项导航、一个当前项、无横向溢出，导航纵向位置同尺寸一致；减少动态效果时动画为none。",
  "limitations": "不改变五模块正式业务、API、鉴权或数据；passed仅指此次前端专项，不代表五模块complete成功。未调用真实模型；线上发布及服务器运行版本另验收。用户要求验证后直接上线，仅发布前端，沿用既有半成品演示发布流程，不修改门禁。",
  "evidence": "output/playwright/course-nav-tests.log；output/playwright/course-nav-build.log；output/playwright/course-nav-check.js；output/playwright/course-nav-1440.png；output/playwright/course-nav-390.png"
}
```


### 2026-11-10 共享网关与练习简历快照同步验收

同步生产composition向ResumeAnalysisService注入JsonModelGateway的事实，并注明该服务仍为501。明确练习快照读取范围、无简历时空快照、子项字段名与私人数据最小化；不修改既有Resume.save或CRUD。

```acceptance-record
{
  "commit": "b127df1 + dirty",
  "command": "python -m unittest discover -s ci -p 'test_project*.py' -v; python -m django test career_platform.tests.test_scaffold career_platform.tests.accept_records career_platform.tests.accept_rag career_platform.tests.test_records_runtime --settings=career_platform.test_settings --testrunner=career_platform.tests.runner.FixedAcceptanceRunner --verbosity=1; python ci/project_acceptance.py --stage complete --module all --output .runtime/docs-sync-20261110/all.json; python -m unittest discover -s backend/tests -p 'test_retrieval_demo.py' -v",
  "result": "failed",
  "environment": "2026-11-10；Windows；Python 3.12 / Django 4.2.7；隔离内存SQLite、Gateway Spy；文档门禁PyYAML位于忽略目录，不调用真实模型",
  "scope": "完整all固定17项中的resume3项仍因501失败；原简历建议与应用流程未实现。records/rag组合专项18项通过仅证明练习相关链路，不能替代resume验收。",
  "limitations": "网关注入不等于NLP分析、事实校验或版本应用完成；自由文本仍可含私人数据，不宣称全量脱敏。未修改用户资料或简历数据库，未执行MySQL、真实模型、浏览器或部署。",
  "evidence": "ci/check_project_changes.py; ci/test_project_changes.py; backend/career_platform/tests/test_records_runtime.py; backend/tests/test_retrieval_demo.py; .runtime/docs-sync-20261110/all.json（本机忽略产物，可按命令复现）; GitHub Actions 42771897363 job状态查询"
}
```

```acceptance-record
{"commit":"1782fec + dirty","command":"node --test frontend/tests/*.test.mjs; npm run build --prefix frontend; python ci/project_acceptance.py --stage complete --module all","result":"failed","environment":"2026-11-15；Windows；隔离SQLite；模拟浏览器API","scope":"前端99项、构建通过。浏览器验证旧入口重定向、501明确提示和编辑草稿跨页签保留，三种状态四种尺寸12视图无溢出。完整业务17项13通过4失败，resume3与integration1仍因501失败。","limitations":"只整合入口，不代表NLP、建议或应用实现；未真实写简历、调用模型或迁移数据库；无MySQL、CI、发布部署验收。","evidence":"frontend/src/views/resume/OptimizationPanel.vue; frontend/tests/default-questions.test.mjs; output/resume-default-complete.log; output/playwright/resume-default-check.js（output为本机产物）"}
```


## 2026-11-16 共享网关回归边界

本轮共享网关随题库集成修改了超时映射与隐式重试；未实现或启用简历NLP、建议或应用接口。完整固定业务验收17项中，resume3项与依赖它的integration1项仍因501失败。不能把题库接入或模型专项成功写成简历模块完成，也不通过降低CI门禁掩盖此缺口。

```acceptance-record
{
  "commit": "3837421035e310ec77aeb2fa3c017391f605621a",
  "command": "python -m django test career_platform.evaluation career_platform.records career_platform.rag career_platform.tests.test_records_runtime career_platform.tests.accept_rag career_platform.tests.accept_records career_platform.tests.accept_evaluation --settings=career_platform.test_settings; python -m unittest discover -s backend/tests -p test_interview*.py; python -m unittest discover -s backend/tests -p test_rag_feedback.py; python -m unittest discover -s backend/tests -p test_json_gateway.py; node --test frontend/tests/*.test.mjs; python ci/project_acceptance.py --stage complete --module all",
  "result": "failed",
  "environment": "2026-11-16；Windows/Python3.11；隔离SQLite；本地浏览器使用真实候选API和943题、离线模型替身；服务器独立候选进程使用真实已配置模型和临时账号",
  "scope": "共享网关回归已执行；简历固定专项3项与跨模块integration1项返回501，完整业务尚不通过。",
  "limitations": "完整业务17项13通过4失败（resume3和integration1因简历接口501）；未通过完整门禁、未部署候选；MySQL/容器由Actions验证。检索为词面基线，评测标签未独立人工复核，且无关检测仍误召；真实模型样本不证明总体质量。 真实模型为独立候选进程快照验证，末次提示词及无命中尾注文字调整仅离线回归。",
  "evidence": "backend/career_platform/evaluation/datasets/xiaolin-experiment-v1.json; backend/career_platform/evaluation/tests_xiaolin.py; backend/career_platform/rag/tests_feedback.py; backend/career_platform/records/tests_catalog.py; backend/tests/test_interview_catalog.py; frontend/tests/evaluation-page.test.mjs; output/question-bank-live-result.json; output/playwright/question-bank-api-check.js; output/question-bank-all.json（output为本机验收产物）"
}
```


## 2026-11-16 简历STAR与确认应用首版

首版允许skills/self_evaluation保守改写并逐条确认；项目/经历按STAR原文摘录，缺项提问，不生成新数字；历史、权限、版本、幂等和并发回归。

首版仅写主表skills/self_evaluation；STAR最多20段，逐项最多120字符的原文摘录，缺项保持空并提问，供预览不自动写子记录。有限词典与保守文字规则不等于语义事实或能力评估，人工仍需核对STAR归类。普通简历CRUD跨页签版本协议及所有子表写入口版本维护未在本轮重构；应用时会重验完整快照，当前页会阻止旧草稿直接保存。模型调用在事务外，相同分析键并发可能重复调用模型，但仅保存一条成功记录。SQLite竞争可返回409，显式原键重试恢复。本轮未调用真实模型、未执行线上迁移/发布/部署；MySQL及容器由Actions单独验证。

```acceptance-record
{
  "commit": "3e1d550b9b5d6a12113c2c3cb555756c16de9c3a + dirty",
  "command": "python -m django test career_platform.resume career_platform.evaluation career_platform.records career_platform.rag career_platform.tests.test_records_runtime career_platform.tests.accept_catalog career_platform.tests.accept_evaluation career_platform.tests.accept_resume career_platform.tests.accept_rag career_platform.tests.accept_records career_platform.tests.accept_integration --settings=career_platform.test_settings; python ci/project_acceptance.py --stage complete --module all; python ci/project_acceptance.py --stage scaffold; python -m django makemigrations --check --dry-run --settings=career_platform.test_settings; node --test frontend/tests/*.test.mjs; npm run build --prefix frontend",
  "result": "passed",
  "environment": "2026-11-16；Windows/Python3.11；隔离SQLite；浏览器真实候选API与临时数据库、合成账号和离线模型替身",
  "scope": "首版允许skills/self_evaluation保守改写并逐条确认；项目/经历按STAR原文摘录，缺项提问，不生成新数字；历史、权限、版本、幂等和并发回归。 本地组合59项通过，固定complete17项及scaffold7项通过；前端113项与生产构建通过；迁移无漂移。浏览器1440/390px无横向溢出、无pageerror，验证STAR缺结果、拦截伪造编辑、确认写回、版本递增、历史重载及旧草稿保护。",
  "limitations": "首版仅写主表skills/self_evaluation；STAR最多20段，逐项最多120字符的原文摘录，缺项保持空并提问，供预览不自动写子记录。有限词典与保守文字规则不等于语义事实或能力评估，人工仍需核对STAR归类。普通简历CRUD跨页签版本协议及所有子表写入口版本维护未在本轮重构；应用时会重验完整快照，当前页会阻止旧草稿直接保存。模型调用在事务外，相同分析键并发可能重复调用模型，但仅保存一条成功记录。SQLite竞争可返回409，显式原键重试恢复。本轮未调用真实模型、未执行线上迁移/发布/部署；MySQL及容器由Actions单独验证。",
  "evidence": "backend/career_platform/resume/tests.py; frontend/tests/resume-optimization.test.mjs; backend/career_platform/tests/accept_resume.py; backend/career_platform/tests/accept_integration.py; output/resume-complete.json; output/playwright/resume-optimization-check.js（output为本机验收产物）"
}
```

## 2026-11-16 分析入口与数据来源

- JD 为空时按钮可点击并提示填写、聚焦输入框；保存中明确提示并禁用，避免无反馈。
- 优化页读取当前登录账号 `/api/resumes/my/`，显示姓名、意向岗位、保存版本及纯文本内容预览；不会使用其他账号或示例简历。编辑区未保存修改不参与分析，需先保存再刷新。
- 每次分析重新读取服务器版本；若与预览不同，更新预览并要求重新点击，后端继续检查版本。分析和应用仍分开，STAR 不补造事实或数据。

## 2026-11-16 简历入口与停用助手资源回归

共享前端控制器补充服务器简历来源和缺少JD的反馈，完整业务回归保持原有五模块契约。前端镜像仅保留面试VAD资源；历史3D人物文件不再交付。

```acceptance-record
{
  "commit": "45d65088acee455d20deccf3acb2e65be376ccc5 + dirty",
  "command": "node --test frontend/tests/*.test.mjs; python -m unittest ci.test_build_layout -q; python ci/project_acceptance.py --stage complete --module all --output output/resume-source-complete.json; npm run build --prefix frontend",
  "result": "passed",
  "environment": "2026-11-16；Windows；离线隔离SQLite；Chromium使用临时账号、真实候选API和离线模型替身",
  "scope": "简历分析入口提示与已保存来源预览；移除停用悬浮助手组件、公开配置、页脚链接和镜像GLB资源。共享前端控制器变更触发五模块完整回归，17项通过；115项前端测试、5项构建布局测试及生产构建通过。浏览器1440/390px验证空JD提示与聚焦、服务器来源、未保存草稿隔离、确认应用和历史，无运行时错误或横向溢出。",
  "limitations": "本轮仅修改前端及构建布局回归；未修改后端接口、模型提示词、题库数据或迁移。浏览器模型为离线替身，不代表真实模型质量；MySQL、Docker构建及部署由Actions验证，发布结果另记deployment-status.md。",
  "evidence": "frontend/tests/resume-optimization.test.mjs; ci/test_build_layout.py; output/resume-source-complete.json; output/playwright/resume-source-check.js（output为本机验收产物）"
}
```


## 2026-11-16 通用优化与岗位定向优化

`/resume?tab=optimize` 的工作区页签改为“AI 简历优化”，默认选择通用优化：不需要JD，只读取当前账号已保存版本，整理技能/自评表达和STAR原文。岗位定向优化需要JD，并保留原关键词匹配。切换回通用优化不会发送留存的JD，历史结果按其实际JD显示模式，不随当前表单切换。

分析API的jd_text改为可选，默认空；无job_id且JD为空时不调用匹配器，matches/gaps/evidence为空、matching.version=not-applicable，不能把空缺项解读成岗位匹配成功。有job_id仍核验allowed和岗位内容，旧非空JD请求及已存幂等输入保持兼容。数据表和返回结构不变，无新增迁移。

提示词升级resume-star-extractive-v2：显式提供当前项目/工作记录允许的star_sources路径，删除固定项目ID示例，要求逐字复制路径并区分行动/结果。严格原文/事实/数字校验不放宽；这降低照抄示例的风险，不保证模型每次都返回有效内容。技能/自评仍仅支持保守文字整理，项目/工作STAR仅供预览和补充问题，需返回编辑区自行修改；并未实现任意全文自动润色。


### 2026-11-16 通用简历优化共享回归

简历分析允许省略JD；通用模式无岗位匹配，岗位模式保留原行为。共享序列化器/前端控制器变更按原规则完成五模块回归；未改变题库、检索、练习或评估算法。

```acceptance-record
{
  "commit": "434a7d9293e3ceff99a31b61ed0bdd9a981a58ac + dirty",
  "command": "node --test frontend/tests/*.test.mjs; python -m django test career_platform.resume --settings=career_platform.test_settings; python ci/project_acceptance.py --stage complete --module all --output output/resume-general-complete.json; npm run build --prefix frontend",
  "result": "passed",
  "environment": "2026-11-16；Windows；离线隔离SQLite；Chromium使用临时账号、真实候选API和离线模型替身",
  "scope": "简历分析共享输入允许省略JD；前端默认通用优化，可选岗位定向。前端116项、简历专项18项、固定五模块complete17项及生产构建通过；浏览器验证空JD分析、模式切换与历史、草稿隔离、伪造编辑拒绝和确认写回，1440/390px无溢出或运行时异常。",
  "limitations": "本地模型为替身，不代表真实模型质量；尚未在本轮运行Actions、发布或部署，后续证据另记deployment-status.md。保守改写仍限技能/自评；STAR仅原文预览，不自动写回子项。无新增迁移。",
  "evidence": "backend/career_platform/resume/tests.py; frontend/tests/resume-optimization.test.mjs; output/resume-general-complete.json; output/playwright/resume-general-check.js（output为本机产物）"
}
```

### 2026-11-16 通用优化线上验收

`edb797e`已使用Actions验证归档完成服务器侧备用发布，并依次激活后端/前端；发布失败历史、镜像身份与实际digest见[运维记录](../deployment-status.md)和[脱敏交付证据](../releases/2026-11-16-resume-general.json)。正式Actions运行43820801261仍为失败，不用手动发布覆盖其结果。

真实gateway HTTP加已配置模型的合成简历验证22.2秒通过：省略JD分析200、STAR缺成果留空、原键分析回放、历史、技能/自评建议确认写回、版本+1、回执回放；伪造Redis/50%的编辑被拒绝。临时账号及关联数据已删除。该单样本不代表总体模型质量；此前独立进程的通用32.9秒/岗位16.8秒两样本亦不替代评估集。

公网浏览器使用真实API和另一临时账号，确认分析按钮在空JD下可用、来源预览与保存版本一致、未保存草稿不进入来源、岗位模式空JD明确提示，1440/390px无溢出或pageerror、无GLB请求；无API拦截，本次浏览器未调用模型。浏览器账号已删除。STAR子记录仍仅预览，确认写回仍限主表技能/自评。

```acceptance-record
{
  "commit": "edb797ef26b8881b3ca2b2e94eaf1e7c17afb41d",
  "command": "python output/run_resume_general_http.py; python output/run_resume_live_browser.py; python output/cleanup_resume_browser_user.py; python output/verify_resume_source_release.py",
  "result": "passed",
  "environment": "2026-11-16；已部署演示服务器；真实gateway HTTP和已配置模型；公网Chromium使用合成账号和真实API",
  "scope": "省略JD分析、STAR留空成果、分析/应用回放、历史、伪造编辑拒绝及确认写回；浏览器来源、按钮、草稿隔离、岗位必填和双尺寸；两个临时账号已清理",
  "limitations": "真实模型仅一份线上合成简历，22.2秒，不代表总体质量。浏览器未调用模型。写回仅主表技能/自评，STAR子项仅预览。手动备用发布成功，不代表失败Actions成功；PR50的自动发布复验另记运维状态。output脚本和浏览器产物为本机忽略文件。",
  "evidence": "docs/releases/2026-11-16-resume-general.json; docs/deployment-status.md"
}
```

### 2026-11-23 实施文档冲突合并门禁

逐文件比较 `docs/implementation/` 后，六份冲突文档均恢复 `master` 章节骨架；`migration` 独有的文件简历接口、上传字段、解析限制和自由面试上下文已合入00/03/04/05，01/02未发现 `master` 之外的实质功能描述。未修改测试、固定门禁或业务代码。

```acceptance-record
{
  "commit": "2793067 + dirty",
  "command": "python -m unittest discover -s ci -p 'test_project*.py' -v; python ci/project_acceptance.py --stage scaffold --output .runtime/docs-implementation-merge/scaffold.json; python ci/project_acceptance.py --stage complete --module all --output .runtime/docs-implementation-merge/all.json; git diff --check",
  "result": "passed",
  "environment": "2026-11-23；Windows；隔离内存 SQLite；离线 Gateway；不调用真实模型",
  "scope": "9份实施文档逐一比较，master门禁章节全部保留；文档门禁单测11/11、骨架7/7、完整业务17/17及全部文档结构对比通过。",
  "limitations": "仅本地离线门禁；未运行MySQL、真实模型、浏览器、远端CI或部署。文档改动尚未提交，不代表发布或线上验收。",
  "evidence": ".runtime/docs-implementation-merge/scaffold.json; .runtime/docs-implementation-merge/all.json; ci/test_project_changes.py; docs/implementation/"
}
```
