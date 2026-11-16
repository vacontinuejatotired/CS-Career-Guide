# 演示部署验收状态与接手记录

## 2026-11-16 MySQL知识点检索与BM25双端上线

- PR #54合并至 `7c429bde8197f9af22f529b73dc463801ec66c1b`，功能提交为 `b4ab16c`。master运行 [43842334129](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/43842334129) 整体success，双端检查、SQLite/MySQL业务验收、双镜像、网关/持久化联调、双端发布、双端部署及summary成功。本次上传正常完成，不表示历史ACR卡顿根因已解决；180秒连续无CLI输出终止规则保留。
- 下载核对两份publisher记录均complete=true、commit一致。服务器frontend/backend/gateway均running/healthy，前后端配置镜像引用与各自发布reference一致：frontend为 `sha256:c6068c3fdb7bc2c6b5b9c67150a5557d1940dc54b41e77c5e41838f71b440156`，backend为 `sha256:81592720271d470d8524b1770bc7fb6cd1bd61b8fae698dda06d02b9d99a1d42`；gateway仍为 `sha256:91fc9c3924b93f76adc9cd36a0bb93e53885ff8e97df10233caa45bb432789a5`。
- 临时账号从后端容器通过实际gateway HTTP验证：目录mysql/MySQL/MYSQL均200、count=140；正式mysql检索200、5题、题目分类均为数据库，大小写变体排序和分数一致；Redis检索4题；未知知识点0题；仅按岗位浏览5题且score均0。mysql的5题分数约为0.583/0.511/0.502/0.460/0.459，是检索相关度，不是答题成绩。持原回执创建练习200、5道题目快照保留数据库分类；匿名目录401。账号和关联练习已删除，allowed题数仍943，未调用生成模型。
- 开发电脑请求公网 `/resume?tab=optimize`、`/career-platform/practice` 及实际懒加载资源均200；简历资源含通用优化/岗位定向优化/无需JD/STAR，练习资源含“检索相关度”。后端只读检查确认JD可选、空JD进入general。这是HTTP、资源和代码检查，不是本轮登录后浏览器交互、App设备或真实模型验收；服务器内部gateway验证也不等同于公网带Token请求。
- 正式检索当前为字段加权BM25词法排序，未启用Embedding/LanceDB。目录topic按规范分类优先、无分类则内容包含匹配；正式检索采用分词关键词约束，两个接口结果不保证相同。离线评估API的四种已注册策略仍为覆盖率基线，不能代表生产BM25质量。无关误召、语义召回、多worker共享回执和STAR子项写回仍有未完成边界。
- 脱敏本机证据：`output/mysql-rag-release/`、`output/mysql-rag-live.json`、`output/mysql-rag-live-runtime.json`、`output/resume-and-practice-assets-live.json`（均为忽略目录产物）。App接口约定已同步至[接入文档](app-api.md)，历史失败及此前模型验收记录保留，不以本次成功覆盖。

## 2026-11-16 后端发布补齐与推送卡顿核验

- PR #52已合并为`b7206e66dc1bfc79a8c6ff5aa63c7129031bfe57`。运行43831847945的双端检查、镜像与网关/持久化联调通过，frontend发布/部署成功；backend发布失败、自动部署跳过，整条Actions结论仍为failure。
- backend镜像load耗时4.7秒；第一次push仅完成2层、7层Waiting，最后一次输出后180秒终止（该次累计270秒），同标签重试后仍2层已存在、7层Waiting，再于累计210秒终止。固定类别诊断未观察到鉴权、限流或5xx；没有足够证据确定具体网络或仓库端根因。180秒按连续无新CLI输出计算，含前期进度及一次重试的job总时间可能更长。
- 本次按用户要求补齐发布：核对该运行的失败发布记录与`backend-smoke-image-43831847945`归档，配置摘要均为`sha256:b45f60b56f426f82be2163a1448c8981a22328a5823faf224a0c6ef3aa05df4a`；与ACR已有`sha256:3e0d32ff90ad11c364e65ccb05672280f510c0a3dffe6e1aa5c6357f267be973`镜像的config、linux/amd64与全部RootFS diff_ids一致。使用官方校验和验证过的crane v0.22.1复用已有manifest，写入并回读`sha-b7206e6/latest`，标签发布3.8秒、含registry核验5.8秒，新增上传图层为0。未构建或改写镜像内容；原Actions失败记录保留。
- 单组件锁定工具按该digest激活backend，耗时13秒。部署前SQLite在线备份quick_check为ok；部署后frontend/backend/gateway均running/healthy，frontend/gateway容器ID、backend卷挂载和`.env`元数据保持。943道allowed题及既有0004迁移存在，无新业务迁移。公网login/resume/interview为200、匿名分析401。应用内容与此前真实模型验收版本相同，本次未重复调用付费模型，也未重新执行浏览器交互验收。
- 只读核验服务器Docker Hub mirror数量为0；仓库publisher配置只设置`max-concurrent-uploads=1`，保留runner原有daemon选项，不能据此断言runner原镜像配置。Docker Hub的`registry-mirrors`用于拉取缓存，不能给向私有ACR的push提供加速；此次失败阶段为push，非基础镜像拉取。180秒规则继续保留，具体网络根因和长期自动传输修复仍未完成。

## 2026-11-16 通用简历优化已上线

应用源码为`edb797ef26b8881b3ca2b2e94eaf1e7c17afb41d`（PR #48的通用优化与PR #49的发布配置）。`/resume?tab=optimize`默认通用优化，无需JD；可切换岗位定向优化。分析使用当前登录账号最后一次保存的简历，页面展示来源和版本，未保存编辑不自动加入分析。

- 正式Actions运行43816175405、43820801261的后端发布失败；后者已应用单层上传配置，仍在180秒无CLI输出后退出，不能把缓解措施记为已解决。两次前端独立发布后均曾恢复旧digest，待后端就绪才重新激活新前端。
- 最终交付复用43820801261的`backend-smoke-image-43820801261`归档，未在本机或服务器重建。跨引擎核对归档manifest/config摘要、linux/amd64及全部RootFS diff_ids；runner配置摘要为`sha256:b45f60b56f426f82be2163a1448c8981a22328a5823faf224a0c6ef3aa05df4a`。使用官方发布包校验和验证过的crane v0.22.1和csdeploy已有登录进行服务器侧备用发布；压缩传输846.1秒、图层合计297081113字节。远端manifest的config摘要及全部diff_ids与验证归档一致，SHA/latest解析到同一digest。
- 已按不可变引用先激活backend，再激活frontend：backend为`sha256:8c5aab50e5ccfdc4d38f3c6f29544c907bbe91350d934b197d9712c958b14583`，frontend为`sha256:9629f4a6c1030040d3540d2585dd609302a8cabc3def79785bed90c2f3acfe8e`。三容器running/healthy；网关容器、命名卷挂载和`.env`元数据保持。无新增业务迁移，既有0004存在，943道allowed题保持；GLB资源缺失、VAD模型存在。
- 部署后使用临时合成简历，经真实gateway HTTP调用已配置模型：省略JD分析200，`resume-star-extractive-v2`生效、无岗位匹配；STAR背景/任务/行动有原文依据，缺少成果时留空。分析回放、历史、建议确认应用200、版本递增到1及回执回放通过；伪造Redis/提升50%的编辑返回400。全流程22.2秒，账号及关联数据已删除。这是单样本验证，不代表总体质量评估。
- 公网Chromium使用真实注册、简历、资料及历史API，无API拦截和模型调用：来源预览与实际保存版本一致、空JD分析按钮可用、草稿隔离、岗位模式空JD反馈通过；1440/390px无溢出或pageerror，无GLB请求。独立临时浏览器账号及关联简历已删除。真实分析/写回由上一项HTTP验收覆盖，未将两项合称浏览器模型全链路。
- 公网`/login`、`/resume`、`/interview`为200；匿名分析接口401；入口资源`index-B17KHjN-.js`及简历资源`Index-BAAvTFnc.js`为200并包含本次功能。

脱敏证据见[通用简历优化交付记录](releases/2026-11-16-resume-general.json)。PR #50曾将180秒无CLI输出改为提示并继续等待900秒总预算，预合并CI 43825887485/43825923832成功。master `3dac3c3`运行43827174324因frontend发布等待过久，已于2026-11-16按用户要求取消，结论为cancelled；frontend未执行激活，不能记为完整自动交付成功。本次恢复连续180秒无输出终止本次推送，保留900秒单次总预算及一次有限重试。

当前应用边界：可确认写回`skills/self_evaluation`的保守文字整理；项目/工作STAR供预览及补充问题，尚不自动写回子记录，也不提供任意全文自动重写。

后续自动发布核验：43827174324的backend发布和部署成功，当前backend为`sha256:3e0d32ff90ad11c364e65ccb05672280f510c0a3dffe6e1aa5c6357f267be973`，其config摘要与上述runner配置摘要相同；内容未改，但压缩表示不同使manifest digest不同。部署后用同一合成样例再次经真实gateway HTTP完成分析、应用和伪造编辑拒绝，29.5秒通过、账号已清理；这仍是单份样例的重复验证。该运行frontend publisher已取消，frontend部署也为cancelled。取消后再次只读核验，frontend保持上文已验收digest，frontend/backend/gateway均running/healthy，容器ID及环境文件元数据保持，GLB缺席、VAD存在。

## 2026-11-16 简历分析入口与停用助手资源已上线

- PR #46 合入 master `db2344686545936034c2fb654b1aaa912b2ab2b8`。分支/PR CI 43803050000 / 43803057044 成功；正式发布 43803661111 整体成功，含 SQLite/MySQL 五模块验收、双镜像、共享网关/持久化联调、双端发布与部署。
- 前端移除停用 AIFloat 组件、头像 URL 配置和无效页脚链接；镜像仅保留面试 VAD，Actions 容器冒烟及部署后只读检查均确认无 GLB、VAD 模型存在。历史 GLB 源文件保留，未读取或修改。前端归档 133.3 MiB，发布 job 从 04:26:15Z 到 04:27:08Z 约 53 秒；这不是仅 push 子命令计时，也不能证明旧网络故障已根治。
- 简历优化增加当前账号已保存简历的姓名/意向岗位/版本/内容预览；JD 为空时点击提示并聚焦，保存中明确等待。分析前重读版本，变化后先核对；编辑区未保存内容不参与分析，确认应用和历史流程保留。
- 服务器 frontend RepoDigest 与发布一致 `sha256:0c8361edd14d92d57983ccaac07becf923fe064397a7b446c987e96bd93aa072`。backend 内容 digest 仍为 `sha256:878a41842a8a1f76cbd4edd68970d30d20d522f54752cbba6c4247aef6552736`，gateway 仍为 `sha256:91fc9c3924b93f76adc9cd36a0bb93e53885ff8e97df10233caa45bb432789a5`；三容器 running/healthy，无新增迁移。
- 公网 login/resume/interview 为 200，未认证分析接口为 401；主资源 `index-Jc1-r2Bp.js`、简历懒加载资源 `Index-B9OaLd9f.js` 含本次来源预览与 JD 提示。已发布前端的隔离 Chromium 验证空 JD、来源预览、未保存草稿不改变来源、分析请求 revision=7、无旧助手入口与 GLB 请求，1440/390px 无溢出或运行时异常；该浏览器验证全部 API 使用样例拦截，没有读取真实用户简历、写生产数据或调用真实模型。
- 本地 115 项前端测试、固定 complete 17 项及生产构建通过；交付工具 103 项中 89 通过、14 项 Windows 不适用跳过，Linux runner 由正式 CI 验证。本轮未修改真实模型提示词或事实校验规则；此前真实模型偶发 STAR 字段路径错误的限制继续保留，不能以入口验收代替模型质量验收。


## 2026-11-16 授权题库与 STAR 简历候选

用户已授权改完直接上线。PR #43 将题库集成及简历优化完整候选合入 master，提交 `809266651bd451cab9cdc0855993fffac5df68eb`；PR #42 的提交已包含其中。分支候选 `f379fd6a832f8fd577886c82297eea29a18e8800` 的 CI 43795944455 全部通过；master 发布运行见 [43797130336](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/43797130336)。

- 迁移前完成 SQLite 在线备份 `/data/catalog-backups/before-resume-20261116T031505Z.sqlite3`，大小 5509120 字节，权限 0600，`quick_check=ok`，SHA256 `34450c2ae95562c955da0b95c8331e2f7dd79d4fe155f6f63e98055ad6400133`。保持现有 SQLite、卷和网关，不切换数据库。
- 后端已发布并部署，运行镜像 RepoDigest 与发布记录匹配 `sha256:878a41842a8a1f76cbd4edd68970d30d20d522f54752cbba6c4247aef6552736`，容器 running/healthy；迁移 `0004_resumeapplyreceipt_input_payload` 已执行。
- 部署后通过真实网关 HTTP 与已配置模型验证合成简历：分析 200，Java/MySQL 匹配而 Redis 为缺口；STAR 背景/任务/行动均逐字摘录，没有依据的结果为空。分析原键重放、历史查询、确认应用 200、版本递增到 1、应用回执重放均通过；添加 Redis 与提升 50% 的编辑返回 400。临时账号及关联数据已删除，943 道 allowed 题目保持。真实模型检查耗时 19.8 秒，为单份合成样本，不代表总体质量评估。
- 原 master 运行 43797130336 的前端首次 SHA 标签 push 在900秒超时，重跑仍长时间未完成，随后取消旧运行；未将其记为发布成功。PR #40 补齐脱敏层进度、错误类别、180秒无CLI输出退出和一次有限超时重试，24项发布专项通过，分支与PR CI 43799603835/43799608316均成功后合入 `171adda617e406bf34cfc09b9416ed300aef36a1`。
- 最终发布 [43800231536](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/43800231536) 整体成功：前后端检查、双镜像、交付检查、网关联调、双端发布、双端部署及summary均成功；本次仅修改CI工具，固定五模块业务验收按路径规则skipped，完整业务验收依据此前8092666运行的SQLite/MySQL通过结果。
- 前端 SHA 标签推送22.8秒、latest推送7.0秒，12层完成，未触发重试；运行镜像 RepoDigest 匹配 `sha256:032b2d5bc41457b710398cb32c6125fc5d1df8c8fbc0ce836eebb1085b1acd4f`，后端digest保持上述值，三容器running/healthy。旧失败的sha-8092666 manifest不存在；不能据此确认具体网络或ACR根因，也不能把本次成功视作偶发故障已根治。
- 最终公网 `/login`、`/resume`、`/interview` 返回200，简历懒加载资源 `Index-opwsJ7QP.js` 返回200且包含STAR/`star_reviews`；未登录分析接口返回401。此项为HTTP资源验收，不代替线上登录后的浏览器交互。
- 双端部署后再次使用同类合成简历调用真实模型，分析返回400/VALIDATION_ERROR，未完成该次闭环，临时账号已删除。前一次真实模型分析/应用成功不能代表输出稳定；当前保守校验会拒绝不符合证据或结构约束的输出，需要继续优化模型契约及失败恢复体验，不能将本版本记为真实模型总体质量验收通过。
- 随后的独立进程诊断复用已部署代码与真实模型，捕获 `invalid STAR source`：模型返回示例路径 `projects.1.description`，而非当前简历项目ID。该错误被拒绝且临时账号已删除；应将可选路径显式传给模型、避免示例ID被照抄，并继续验证STAR结果槽位语义。诊断不替换线上代码，也不证明此前HTTP400的每个具体原因完全相同。

待完善：STAR 项目/经历确认写回、岗位与简历评测、检索质量调优、多 worker 共享回执和并发一致性。当前 STAR 仅预览，技能/个人自评可确认写回；保守文字规则不等于通用语义事实验证。普通简历 CRUD 跨页签版本协议尚未整体重构。此前本地离线浏览器验收通过，线上登录后的浏览器交互未重新验收。

## 2026-11-03 双端部署与独立审计通过

按用户本次授权，现有应用改动已通过 GitHub Actions 部署到服务器；五模块完整业务验收跳过，原固定测试、业务变更路径规则及 SSH 校验继续保留。五模块仍为 `501 / FEATURE_NOT_IMPLEMENTED` 骨架，不将跳过写成业务通过。

- 部署版本：`deccc0cd18f647fc43622161ac28fda8789afae6`，已合并 [PR #19](https://github.com/vacontinuejatotired/CS-Career-Guide/pull/19) 的 publisher digest 输出修复；此前现有应用与文档改动均包含在此版本中。
- [master 发布 41611783087](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/41611783087) 整体成功：前后端测试、交付配置、文档门禁、双镜像、完整网关与 SQLite 持久化联调、双端 ACR 发布及两个 SSH 激活任务均通过；`Platform acceptance` 为 skipped。
- 两份发布记录均为 `complete=true`、源码版本一致、`compatibility=candidate-integration`。frontend digest 为 `sha256:0eaff01c024d2fe0ed67ebc894488eb89e5671c0c12e053ba8a1631bd0914449`；backend digest 为 `sha256:069aa3a67c4c54c694e1f5ce29ee5cee48f2c1946152c8e6d81963ab16c2ea67`。
- [部署后独立只读审计 41614838351](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/41614838351) 成功：frontend/backend/gateway 均 running、healthy；前后端容器已重建，实际配置镜像及 RepoDigests 与各自发布记录完全一致。
- 与发布前审计 `41467510972` 比较，gateway 容器与 digest、Compose 项目、各服务命名卷及端口映射保持；SQLite/static/media 卷保留，Watchtower 继续 exited。审计记录不包含真实环境变量值。
- 部署后公网只读 HTTP 检查：`/`、`/login` 均 200 且包含 SPA 入口，`/static/admin/css/base.css` 为 200，未携带 Token 的 `/api/users/profile/` 为预期 401。
- 后端正常启动入口先执行 `migrate` 再启动 Gunicorn，已完成启动并健康；包含 `users.0013_normalize_gender_choices`，但本次未独立读取迁移表或用户数据，不声称完成数据库逐项审计。未切换数据库、导入示例业务数据、执行真实模型或浏览器业务验收。

脱敏发布、运行镜像、容器/卷和检查范围记录见 [2026-11-03-deccc0c.json](releases/2026-11-03-deccc0c.json)。以下失败历史保留，不能用其结果覆盖本次成功记录。

## 2026-11-02 授权手动发布与后续重试

用户在同日文档门禁复核后明确要求将现有修改部署到服务器，并跳过五模块业务开发的 CI 检测；该授权替代此前暂停部署的决定，仅适用于本次发布。五模块仍为 501 骨架，本地完整验收的 14 failures、3 errors 保留，不作为已实现或已通过处理。

- 代码版本：`65d9ea711848500edfebcd4ce68eedb967bbc26d`，已合并 [PR #18](https://github.com/vacontinuejatotired/CS-Career-Guide/pull/18) 的六份真实验收记录。
- 发布入口：[手动 CI/CD 41470153714](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/41470153714)，`master`、`component=all`。本次五模块 `Platform acceptance` 为 skipped；原固定测试、push/PR 路径规则和发布依赖未修改。前后端应用测试、交付配置、双镜像检查、完整容器联调、镜像身份验证与 SSH 健康等待继续执行。
- 发布前检查：[只读 SSH 审计 41467510972](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/41467510972) 成功，frontend/backend/gateway 均 healthy，Watchtower 为 exited；原前后端 digest 分别为 `eaecc62f23c1b2c2aec66c4467a2e009fc85bec024df83d89dc71269ea1c634f`、`75110f2b4dff6b5488bab73ffd563cf7ed431979e0050d1bdd32bb5b48ea2cf9`。
- 后端沿用既有启动入口执行迁移，包括已提交的 `users.0013_normalize_gender_choices`；不切换数据库、不导入示例数据、不执行真实模型调用。网关和已有命名卷由原部署保留。
- 该次双端应用测试、镜像构建、完整容器联调和两端 ACR 发布均成功，五模块完整验收 skipped。首次运行及后续失败任务重试的 SSH 激活均失败，未宣称服务器已更新。
- 根因：两个 publisher 的日志均出现 `Skip output 'image' since it may contain secret`；registry/namespace 使用 Secrets 时完整仓库引用被 GitHub 丢弃，导致 deploy 的 `DEPLOY_IMAGE` 为空，脚本在 SSH 连接前拒绝执行。单纯重跑失败任务不能修复此问题。
- 后续只读 SSH 审计 [41609961586](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/41609961586) 成功，证明 Actions 的现有 SSH 通道可用。修复方式为 publisher 仅输出经格式与引用一致性校验的 digest，deploy 在自身环境内使用 ACR 坐标组装完整引用；不降低主机密钥核验、敏感输出保护或镜像版本校验。
- 修复后的发布与服务器实际 digest 需以新的运行及独立审计记录为准；本段不将现有 501 骨架或跳过的业务验收写成成功。

## 2026-11-01 独立交付已合并并完成服务器切换

这是当日验收快照，实时操作仍须重新核对 Git/Actions/服务器。[PR #9](https://github.com/vacontinuejatotired/CS-Career-Guide/pull/9) 至 [PR #15](https://github.com/vacontinuejatotired/CS-Career-Guide/pull/15) 已合入本 fork master，代码基线为 `d9395a319be3c99d67b3ff062266ee6d8edee5ce`。最终交付修复的 [PR Actions 41312995286](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/41312995286) 整体成功：两端检查、各自镜像、完整网关/持久化/SSE/IP 联调和真实首次切换均通过；该次纯交付改动按既有路径规则跳过完整业务验收，不代表五模块业务完成。

- 本地：最终 89 项 CI 工具测试在 WSL 离线隔离环境通过。本机没有 Docker 构建或容器联调。
- 镜像：[首次前端独立发布 41304757512](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/41304757512) 成功，`complete=true`、只含 frontend、证据为 component-contracts；该次 backend 全链路与完整候选联调 skipped。前端 digest `sha256:eaecc62f23c1b2c2aec66c4467a2e009fc85bec024df83d89dc71269ea1c634f`，源码 `7909ecf`。本轮没有发布新 backend 镜像。
- 服务器：[安装 41313632683](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/41313632683) 成功，[随后独立审计 41313707147](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/41313707147) 成功。frontend 运行上述新 digest，gateway 固定 ACR 镜像 digest `sha256:91fc9c3924b93f76adc9cd36a0bb93e53885ff8e97df10233caa45bb432789a5`，均 healthy。80/48080 原端口映射转给 gateway；frontend 无宿主端口、无后端共享卷。网关基础设施镜像使用现有 frontend 仓库的专用 `gateway-nginx-<imageID>` 标签，不覆盖应用 latest/SHA 标签。
- 保留状态：backend 仍是原容器 `e547601b906ed8ed0be4d309734f7fbb999fd82f40e9d849a0491a933fe179e6`，healthy，运行 RepoDigest 为 `sha256:75110f2b4dff6b5488bab73ffd563cf7ed431979e0050d1bdd32bb5b48ea2cf9`。原 SQLite/static/media 命名卷、项目、真实 `.env` inode/mtime/size 均保持；没有启动后端入口或迁移。Watchtower 保持停止。
- 单端实测：安装后调用正式单组件激活函数，再单独重建一次 frontend；确认 frontend ID 改变，backend/gateway ID 与 `.env` 不变。只读 HTTP `/`、`/login` 为 200 SPA，admin CSS 为 200，无 Token 的 profile 为 401，不存在 media 为 404。服务器没有新增账号、写入业务数据或调用真实模型。
- 自动交付：安装与独立审计成功后，回读确认 `SPLIT_DELIVERY_RELEASE_ENABLED`、`DEPLOY_ENV_SYNC_ENABLED`、`DEPLOY_FRONTEND_ENABLED`、`DEPLOY_BACKEND_ENABLED` 均为 true。启用开关本身不触发发布或重启；未来 master 变更仍须通过对应门禁，按组件发布/激活完整 digest。网关不随单端应用更新重建。

原完整业务验收在 [41309171882](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/41309171882) 与 [41311945848](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/41311945848) 的 SQLite/MySQL 都运行 17 项，14 failures、3 errors，原因是现有五模块返回 `501 / FEATURE_NOT_IMPLEMENTED`；没有指向数据库连接或迁移故障。用户已明确接受保留这一失败后合并交付修复；固定验收和业务接口未被降级或伪造实现。

首次安装曾遇 Docker Hub 超时、SSH 大归档超时，以及跨引擎本地 image ID 核验拒绝；每次独立 audit 确认旧前后端健康、ID 未变。最终使用已授权 ACR 专用标签/digest 传送网关，通过 RepoDigest、内容层、启动配置和平台核验，绕过 SSH 大镜像传输。失败历史与最终成功分别保留，不能复用较早失败运行作为成功证据。

完整脱敏记录见 [2026-11-01-split-delivery.json](releases/2026-11-01-split-delivery.json)，单服务 digest 回滚见[独立交付](split-delivery.md#单服务部署与-digest-回滚)。服务器未做真实模型、SSE 业务调用、浏览器交互、语音、生产 digest 回滚演练或数据库迁移；SSE/鉴权/持久化的完整容器证据来自 runner。App 客户端不在本轮范围，后端 API/Token 边界继续保留。构建缓存命中与耗时见[CI/CD](ci-cd.md#缓存与耗时定位)。

## 2026-10-26 历史发布与业务基线：82f1293

这是本次已完成的发布验收快照，不代表后续实时状态。制定需求准备文档时，以最新 `origin/master` 及对应实现为代码基线；下文较早提交仅保留为历史证据。

- [PR #4](https://github.com/vacontinuejatotired/CS-Career-Guide/pull/4) 的文字/音频解耦与控制修复、[PR #5](https://github.com/vacontinuejatotired/CS-Career-Guide/pull/5) 的流式显示、可选时长、整页工作区和简历观览均已合入 master。最终提交 `82f12931de08e2cab71823d9e8c2b9aa6d2a6dec` 的 [Actions 40319566238](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/40319566238) 全部成功，包括双镜像验证、发布、AI 配置同步、容器重建和健康等待。
- 前后端运行 RepoDigests 与[成对发布记录](releases/2026-10-26-82f1293.json)一致；两个容器均 healthy，非 AI 配置摘要与此前基线相同，Watchtower 保持停止。默认演示数据库是 SQLite，保留 MySQL 配置不等于已切换 MySQL；新需求方案中的数据库和 RAG 目标需要另行设计、验收。
- 使用临时账号和虚构简历验证真实注册登录、空简历、简历保存及面板刷新，七类正文分区均显示。默认 45 分钟及对应模型提示词、暂停计时、桌面/手机满视口、回答草稿保留均通过。
- 本次 1 次真实模型请求返回 62 个文字块、0 个音频块，记录到 246 个不同可见文字长度阶段，最终页面文字与完整回复一致。此前 d04157a 上另行验证了真实 TTS 播放、暂停、继续和关闭；本次默认文字验收不等同于重新覆盖完整语音链路。
- 临时账号、虚构简历与测试会话已清理。职业路径、测评题、企业、招聘会及岗位列表再次核对为 HTTP 200、0 条数据；业务数据未导入，不能据此声称这些内容模块完整可用。
- 待完成：域名/HTTPS 和真实浏览器录音；完整职业报告、全部面试风格及多轮质量验收；真实数据导入、MySQL 切换和回滚恢复演练。当前网页面试仍是 legacy 适配器及共享流式接口，不是新方案中的题库 RAG、逐题评价和复练闭环。

## 2026-10-26 实时核验与补通

本节依据当天实际 GitHub 查询、SSH 检查及少量已授权真实模型请求；下文 2026-10-23 内容保留为历史记录。

- [Actions 40279477861](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/40279477861) 已验证、发布并完成真实 AI 环境同步、容器重建和健康等待。部署开关 `DEPLOY_ENV_SYNC_ENABLED=true`，旧 Watchtower 已停止，后续统一由 Actions 更新应用。
- 服务器 Compose 补齐 `CAREER_REPORT_MODEL`、ASR 三项和 TTS 四项映射；部署账号的私有镜像拉取成功。`.env` 的非 AI 行与备份逐字节比较一致，数据库、域名、资源和镜像选择未被同步覆盖。
- 自动同步只读取基础 Compose。首次重建曾丢失旧容器的 80 端口；已将服务器原有 80 和 48080 映射同时写入实际基础文件并重建前端，公网登录页恢复 HTTP 200。不要假设 override 或旧容器参数会自动继承。
- 操作前的配置、SQLite 在线一致性备份及容器身份位于服务器部署目录的 `backups/ai-connect-20261026T062229Z/`，权限限制在服务器内；不上传含密钥或用户数据的备份。
- 真实文本模型 `qwen3.8-flash` 和 `qwen3.7-plus` 均返回短文本；测试显式关闭思考模式并限制输出，初次 16 token 的思考模式测试没有得到正文，失败记录保留。
- 实际 Nginx/Django HTTP 链路的注册、登录、资料、简历保存读取均通过；面试 SSE 返回文本、14 个音频块和会话 ID，复盘保存及详情读取通过。复盘保存使用明确的合成测试记录，不能当作模型生成复盘质量验收；临时账号与测试会话已清理。
- [PR #2](https://github.com/vacontinuejatotired/CS-Career-Guide/pull/2) 已通过完整 PR CI 并合并：补 Fun-ASR `sentence` 协议与失败处理，以及 `career_paths` 初始迁移。本地新增 12 项 ASR 和 1 项隔离真实迁移测试通过；前端 32 项、面试 6 项、配置 16 项、部署 7 项通过，CI 工具 36 项中 Windows 跳过 4 项 POSIX 检查。最终 master [Actions 40280652973](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/40280652973) 的全部验证、镜像发布、配置同步、重建和 release-summary 成功；代码提交为 `4fda51cef670ec33460e9d0db10dbb6e8b918dab`。
- 2026-10-26 14:50（Asia/Shanghai）复测：`career_paths` 路径和题目接口从 500 恢复为 200，目前返回空列表；注册、登录、资料、简历读写及当前页面使用的企业、招聘会、岗位列表接口均成功。`cosyvoice-v3-flash` 合成约 3.1 秒 PCM，再经真实上传接口 `/api/asr/speech-to-text/` 调用 `fun-asr-realtime`，准确返回“你好，这是面试语音测试。”；测试音频和临时账号均已清理。
- 前后端均 healthy，运行镜像的 RepoDigests 与本次成对发布记录一致。永久记录见 [2026-10-26-4fda51c.json](releases/2026-10-26-4fda51c.json)，不把容器 `.Image` 当作 Registry manifest digest。公网登录页 HTTP 200，旧 Watchtower 停止，非 AI 环境行再次核对为原样保留。

### 尚未完成的独立验收

- 职业路径、测评题库、岗位、招聘会、企业评价等当前数据库表为空，接口可用不代表已导入业务数据；不伪造招聘或测评数据。`company_info_backup` 属于未托管的外部数据表，当前缺失。旧 `/company-api` 返回 503，但该旧客户端没有被当前页面使用，不能把它等同于当前企业页面的所有接口都不可用。
- 未配置域名/HTTPS，用户已确认先完成后端服务。公网 HTTP 浏览器麦克风与完整语音页面未验收；后端音频成功不等于浏览器录音权限成功。
- 本地 Embedding 继续关闭并使用关键词降级；完整职业报告工作流、报告质量、全部面试风格和多轮时长未做真实模型全覆盖；没有 MySQL 切换、历史数据导入或回滚演练。

## 2026-10-23 历史快照

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


## 2026-11-09 课程字体统一前端上线

- 样式 PR #22 已合并；部署条件修复 PR #23 已合并至 `63ae3fdd72bb2d0a9be4814201a55cd02de15f29`。修复仅为前端激活补充 `always() && !cancelled()`，原发布成功、仓库/master及部署开关要求保留。
- PR #22 的原五模块 SQLite/MySQL complete 仍因501/FeatureNotImplemented失败，不将其解释为业务完成。PR #23 与 master 验证42591945685通过双端构建及runner联调；原测试和业务门禁未修改。
- 合并交付修复时临时关闭 `SPLIT_DELIVERY_RELEASE_ENABLED`，等待自动验证结束后恢复原值true，防止此次共享CI改动发布后端。
- 用户授权的手动前端发布部署 [42593151066](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/42593151066) 整体成功：前端检查、镜像、发布、前端激活及summary成功；后端构建/发布/激活和完整联调均skipped。独立组件发布不代表五模块业务验收成功。
- 已发布记录complete=true、components=[frontend]。独立只读服务器审计 [42593666642](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/42593666642) 成功，前端running/healthy且RepoDigest匹配 `sha256:9d980766066ae8bd2e0633382f19b6b5219b850c3fa8875685425f8c68f7ef6e`；backend/gateway均healthy。后端仍为 `sha256:de98d373555230f5610f167184b100d91d0a2f8c79102c21be348d2139458a67`。审计未读取或替换真实环境文件。
- 本地78项前端测试和生产构建通过；隔离模拟API下五课程页及个人中心、简历页在1440/390px共14视图无横向溢出或JS异常。初始页字体统一；检索结果/失败状态、线上登录后浏览器及真实模型未重新验收，不能以容器健康替代这些验收。
- 脱敏运维证据位于Actions Artifact：`published-frontend-42593151066`、`split-deployment-audit-42593666642`。线上使用效果仍待用户浏览确认。


## 2026-11-09 课程导航统一上线

PR #25合并至`59e086f6bf6cd8ad5297163f807c11cc5d2b2786`，五课程页共用五项导航及一致顶部位置，练习页自由面试改为辅助入口；内容160ms淡入，减少动态效果时禁用。78项前端测试、构建及1440/390px共10次隔离浏览器切换验证通过。PR原SQLite/MySQL正式业务验收仍因FeatureNotImplemented失败，未改门禁。

用户授权的手动仅前端发布部署[42595704965](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/42595704965)整体成功；后端相关构建/发布/部署skipped。独立只读审计[42596613922](https://github.com/vacontinuejatotired/CS-Career-Guide/actions/runs/42596613922)确认frontend healthy且RepoDigest匹配`sha256:18d39353e0fe455d7380df3ee511df36205d660ec41699fb3e9c8512687e00f3`；与审计42593666642相比backend/gateway容器ID未变。未调用真实模型，线上登录后视觉效果待用户确认，不能将单组件发布视作完整业务验收。
