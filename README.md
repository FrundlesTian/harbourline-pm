# Harbourline AI PM：MA6094 Capstone 可运行系统

这是一个前后端一体的最小实现：Python 标准库 HTTP 服务、SQLite 存储，前端是原生 HTML/JS，**无需 pip install**。它为 Harbourline Community Hub Refurbishment 实现了六个 Agent 模块和一层治理层（Governance layer），并附带一套包含 33 个测试案例的评估工具，覆盖 Brief 规定的五项指标。

## 启动

```bash
cd harbourline-pm
python3 server.py          # 或 ./run.sh
# 浏览器打开 http://127.0.0.1:8000
```

* 首次启动会自动完成以下步骤：导入 data pack，校验事实库（共 78 条事实，每条的 quote 都必须能在原文中找到），然后跑一次完整流程。
* 打开页面后需要**登录**。审批人就是当前登录账号，所有人工检查点（HC1–HC7）都会记录审批人姓名、账号和账号角色，不能再手填别人的名字。
* **LLM 生成（默认）**：在 `.env` 中填写 `GEMINI_API_KEY`（主用，Google AI Studio 免费层）和/或 `DEEPSEEK_API_KEY`（备用）后，核心产出由 LLM **从原始资料生成**；Gemini 调用失败时自动改用 DeepSeek 重试，详见下文“LLM 生成与基线回退”。不填 key（或设 `HCH_GENERATION=baseline`）时，使用人工整理的基线内容，以确定性模式完整运行（成本为零）。
* **Jira（可选）**：配置 `JIRA_BASE_URL / JIRA_EMAIL / JIRA_API_TOKEN / JIRA_PROJECT_KEY` 后写入真实的 Jira Cloud；三项必填缺任何一项都使用本地 SQLite 模拟看板，两者使用同一份数据契约。详见下文“Jira 联动”。
* 运行评估：`python3 eval/run_eval.py --no-llm`，结果写入 `eval/results/latest.md` 和 `latest.json`。也可以在 UI 的 Evaluation 页点击运行。
* **界面语言**：页面右上角的“中文 / EN”按钮可即时切换界面，选择会保存在浏览器中。导航、操作控件、提示、状态及内置确定性报告提供中文译文；启用 DeepSeek 时，动态生成的项目文字也会按需翻译。来源引文和用户输入保留原文，便于核对证据。

## LLM 生成与基线回退

配置 LLM 后（默认；Gemini 为主，DeepSeek 为备用），各 Agent 的核心产出都由 LLM 根据 brief、Sponsor Answers 和 data pack 生成，再由确定性校验把关：

| 产出 | LLM 生成什么 | 确定性校验 | 回退 |
|---|---|---|---|
| Planning（`app/planning.py`） | scope、Sponsor Questions（含状态/答案）、WBS L1–L3 + dictionary、milestone 与依赖 | 来源 id 必须存在；WBS 层级和 scope 可追溯性（不可追溯的标为 flagged）；依赖只能指向前序 milestone；日期必须出现在所引来源中，否则改为 NOT FOUND/TBD | 人工整理的基线计划 |
| Risk（`app/risk.py`） | 风险登记册（基于 seed register 修复缺陷 + 新增风险） | L、I 为 1–5；WBS 链接和来源必须存在；必须有 owner 和 trigger；缺少供应商变更风险时自动补上 | 基线登记册 |
| Reporting（`app/reporting.py`） | EDC / NRF 报告的每一行（引用 fact/来源 id） | Critic 追溯每个数字、日期、人名；STOP 时把问题和失败行反馈给 Agent 修订，最多 3 轮 | 确定性模板 |
| Change（`app/change.py`） | 成本/工期影响、Sponsor 决策、UNRESOLVED、风险重新评分建议 | 成本行经 Critic 追溯（1 轮修订，仍无法追溯的丢弃）；决策须有来源；重新评分只能针对已存在的风险 | CE-01 / CE-02 基线分析 |

* 冲突检测、seed register 质检、what-if 计算、受影响项识别和 stale 判定仍是确定性计算。
* 每个产出用哪条路径生成会显示在 Overview 页的“产出来源”中，回退原因写入审计日志（outcome = fallback）。
* LLM 响应按输入缓存（temperature 0），所以同一数据库上重跑结果完全一致、不消耗 token，HC2/HC4 审批和看板不会因重跑而变化；`HCH_LLM_FRESH=1` 可强制重新生成。注意：DeepSeek 在不同的全新数据库上不能保证逐字一致，因此 "fresh-DB identical" 只在基线模式下成立。
* 实测（全新数据库、完整流程）：约 110 秒，约 7.4 万 token，约 US$0.024；之后重跑 0 token。
* 评估工具加 `--no-llm` 运行基线回归（33 个案例）；部分案例针对基线中的固定 ID（如 R01、MS12），在 LLM 模式下可能不适用。

## 登录、角色与权限隔离

首次启动会创建四个演示账号（密码可通过 `.env` 中的 `HCH_ADMIN_PASSWORD / HCH_PM_PASSWORD / HCH_LEADER_PASSWORD / HCH_SUPERVISOR_PASSWORD` 覆盖，正式使用前请修改）：

| 账号 / 默认密码 | 角色 | 可见页面 | 可执行操作 | 可审批检查点 |
|---|---|---|---|---|
| `admin` / `admin123` | System Admin 系统管理员 | 全部，含 Admin console | 全部，含重置演示、用户管理 | HC1–HC7 |
| `pm` / `pm1234` | Project Manager 项目经理 | 面板、总览、规划、PM tool、记忆、风险、报告、变更、Agent cards | 运行流程、写看板、问答、记录决策、注入变更、重新生成报告 | HC1 HC2 HC3 HC6 |
| `leader` / `leader123` | Group Leader 组长 | 面板、总览、规划、记忆、风险、报告、变更、Agent cards | 问答、重新生成报告、植入审查故障 | HC4 HC5 |
| `supervisor` / `super123` | Supervisor 监督员 | 面板、总览、记忆、风险、报告、变更、治理、Agent cards、评估 | 问答、查看/导出审计、运行评估 | HC7 |

* **权限在服务器端强制执行**（`app/auth.py`，`server.py` 中的 `PERMS` 表）。界面只是把无权的按钮置灰、把无权的页面从导航中隐藏；直接调用 API 也会得到 403，并在审计日志中记为 `access denied`（outcome = blocked）。
* 可视化面板的数据接口 `/api/dashboard` 按角色裁剪：例如组长拿不到审计活动数据，监督员拿不到里程碑和看板数据。
* 会话使用 HttpOnly + SameSite=Strict cookie，密码使用 PBKDF2-SHA256 加盐存储。登录、登出、登录失败、用户变更都会写入审计日志。
* 管理员可在 **Admin console** 中创建用户、修改角色、停用账号、重置密码；系统会阻止停用最后一个管理员或降级自己。

## Jira 联动

1. 在 `.env` 中填写 `JIRA_BASE_URL=https://<site>.atlassian.net`、`JIRA_EMAIL`（API token 所属账号的邮箱）、`JIRA_API_TOKEN`、`JIRA_PROJECT_KEY`，然后重启服务。
2. 运行 `python3 scripts/jira_check.py` 做只读检查：账号、项目、事项类型映射、Blocks 关联类型。也可以在 PM tool 页点 **Test Jira connection**。
3. 在 PM tool 页先 **Preview**（只读），再由项目经理或管理员做 **HC3** 审批并写入。写入完成后系统会立即读回校验。

实现要点（`app/pmtool.py`）：

* **类型映射与语言无关**：按 Jira 的 hierarchyLevel 识别 Epic（1）、普通事项（0）和子任务（-1），创建时用类型 id，所以中文站点（长篇故事 / 任务 / 子任务）无需配置。如需指定，可用 `JIRA_TYPE_EPIC / TASK / SUBTASK` 覆盖。
* **不重复创建**：Jira 的 JQL 搜索索引会滞后几秒。系统用一次 JQL 搜索找出现有事项，再对已写入过的 key 调用 bulkfetch（强一致读）补齐，所以写入后立即再同步也不会重复创建。实测一次完整同步约 150 次 API 调用；原来是每个事项各查一次。
* **依赖关系**：里程碑之间的依赖写成 Blocks 链接，已存在的链接会跳过不再创建。第一次创建链接后会读回校验方向，方向反了就自动更正（删除 agent 刚建的那条错误链接，并记入审计）。
* **人工标签保留**：HC6 批准后加上的 `change-*` 标签，在之后的同步中会保留，不会被覆盖。
* **护栏不变**：Agent 只能创建、更新和评论，不能关闭、删除事项或把事项移到 Done。“Done”按状态类别判断，不依赖状态名，所以中文状态名也能识别。
* **容错**：遇到 429/503 会按 Retry-After 重试；401/403/404 会附带排查提示。Jira 出错时页面显示错误信息，不会崩溃。
* 评估工具（`eval/run_eval.py`）始终使用模拟看板，不会往真实项目写测试数据；如确需对 Jira 运行，加 `--jira` 参数。

## 可视化面板（Dashboard）

登录后默认进入，内容包括：

* **端到端流程图**：数据源 → 六个 Agent → 七个人工检查点 → 看板/读者，按泳道排列。节点颜色反映实时状态（已产出 / 未运行 / 需关注 / Critic STOP），检查点显示已批准 / 待审批 / 已拒绝，机器交接用动态虚线表示；点击节点直接跳转到对应模块，悬停查看详情。
* **HC1–HC7 检查点轨道**：每个检查点的当前状态、最近审批人和负责角色。
* **图表**：风险热力图、Top 风险评分、Sponsor 问题状态分布、WBS 层级、报告版本状态、看板状态、各检查点审批次数、按账号统计的被拒访问、审计活动时间分布（agent / human / system）、里程碑时间线与依赖关系。
* **管理员演示引导**（仅 admin）：把下面的 8 步演示路径做成进度清单，根据数据库实时判断每步是否完成，并标注负责角色。

**Admin console** 另外提供：角色 → 检查点审批权限关系图、完整权限矩阵、用户管理和访问日志。

## 需求 → 实现对照

| Brief 要求 | 实现位置 | 说明 |
|---|---|---|
| 1 Planning：scope、Sponsor Questions、WBS L3 + dictionary、带依赖的 milestone | `app/planning.py` | 包含 20 个 Sponsor Question（每个注明状态、答案或 assumption），以及 12 个跨来源冲突。WBS 共 74 个元素（L3 有 49 个），**每个元素都可追溯到某一条 scope line**；无法追溯的 4 个候选项标为 flagged，不保留。共 18 个 milestone，在 sponsor 给出日期前用相对时间（M+n）表示，没有日期的写 TBD 或 NOT FOUND |
| 2 Tool integration：人工确认后写入 Jira 并读回 | `app/pmtool.py` | HC2 审批的是某一版计划的 hash，HC3 审批的是某一份 diff preview，两者都通过才会写入。用 `ext-HCH-WBS-x-y-z` 作为稳定的外部 key：第二次运行只会出现 0 created / 0 updated，不会产生重复。写入后读回校验：检查缺失、不一致、重复、未加标签的条目 |
| 3 Memory：带出处回答，资料里没有就返回 NOT FOUND，决策跨会话保留 | `app/sources.py`、`app/memory.py` | 用 BM25 检索文本块，每个块都有文件名、章节和行号。证据不足、或问题要的是数值/日期而原文没有时，返回 NOT FOUND。来源相互冲突时把双方都列出。人工决策写入 Decision log，下次会话仍能检索到 |
| 4 Risk & what-if | `app/risk.py` | 风险登记册共 22 条，每条都有 L×I 评分、owner、trigger、关联的 WBS 和出处。对 2025 年的 seed register 做了质检：R06 评分算错、R08 被错误关闭、R03 与 R04 重复、R01 的 owner 已离职等。另有三个 what-if（W1 石棉、W2 不关闭设施、W3 推迟屋顶花园），CE-02 时会额外生成 W4 |
| 5 Reporting + Critic | `app/reporting.py`、`app/critic.py` | 同一个事实库生成两份报告：EDC 一页式例外报告，以及 NRF 3.2 要求的月报。Critic 会把每个数字和日期追溯到引文，并检查必需章节、top 5 风险、冲突标注、隐藏的缺口和变更事件。出现任意 STOP，报告就**不能发布**（HC5 会拒绝） |
| 6 Change handling（Week 12 CE-01 / CE-02） | `app/change.py`、`change_events/` | 事件作为新输入注入，原 data pack 保持不变。系统输出：受影响的 WBS、deliverables、milestone（含下游）和风险；哪些内容已 stale；成本和工期影响（附出处）；需要 Sponsor 做的决策（什么、谁、何时）；UNRESOLVED 项；待 HC6 审批的动作。stale 的 what-if 和报告会**自动重新生成草稿** |
| Governance：命名检查点、审计、Agent 不能关闭或删除、偏差检查 | `app/audit.py`、`app/governance.py` | HC1–HC7 每个检查点都有名称和角色。所有 Agent 写操作和人工审批都写入审计日志，可导出 CSV/JSON。删除、关闭、移到 Done 的尝试会被拦截，并记为 BLOCKED。另对居民咨询做了偏差与公平性检查：年龄和渠道分布、非英语评论、按年龄重加权后主题排序会变化等，需 HC7 签字 |
| 至少一次无人工复制的 hand-off | `handoffs` 表 | 自动交接链：planning→risk→reporting→critic，以及 change→reporting |
| Agent cards | `app/agents.py`，UI 的 Agent cards 页 | 每张卡片写明 role、context、inputs、outputs、tools、stop condition 和 checkpoint |

## 当前评估结果（确定性模式）

33/33 个测试案例通过。

| 指标 | 结果 |
|---|---|
| Gap recall | 91%（20/22）。漏掉的 2 项是 100 个托育名额是否足够、施工时段限制。金标准见 `eval/gold_gaps.json`，请团队复核 |
| Invention rate | 0%（共抽样 75 条 claim）。第一次评估抽出 2 条无法溯源（R20 trigger 里的 "65+"、R21 缺少 D16 出处），修正后降到 0，可以作为 governance log 里的 incident |
| Re-run stability | 在新库上两次运行，plan、风险、gap、报告全部相同；第二次 PM 同步为 0 created、0 updated，没有重复 |
| Critic catch rate | 100%（21/21 个植入缺陷） |
| 每次完整运行的成本与时间 | 约 0.2 s，确定性模式下 0 token。启用 DeepSeek 后，token 数和费用会记在 `runs` 表和 Overview 页 |

## 演示路径（约 10 分钟录屏）

以 `admin` 登录，可在 Dashboard / Admin console 的演示引导中逐步完成；也可以中途退出，换用对应角色登录，展示权限隔离（例如组长无法批准 HC2，项目经理看不到治理页和审计导出）。

1. **Overview**：点 Run，展示 hand-off 记录和运行耗时。
2. **Planning**：浏览 gaps、conflicts、WBS 的可追溯性和 flagged 项，然后做 HC1 和 HC2 审批。
3. **PM tool**：先 Preview，再做 HC3 审批并写入；再跑一次 Preview，应显示全部 unchanged。然后演示 Agent 尝试 Done/close/delete 被拦截。
4. **Memory**：提问 "What is the maximum grant?" 和 "What is the energy performance target?"（后者应返回 NOT FOUND）。
5. **Risk**：展示热力图、seed QA 结果和 what-if，然后做 HC4 审批。
6. **Reports**：植入一个故障，展示 Critic 返回 STOP；再用干净草稿走 HC5 发布。
7. **Change**：注入 CE-01 或 CE-02（学号末位奇数选 CE-01，偶数选 CE-02），查看 stale 项、自动重生成的草稿和 Impact Note，然后逐条做 HC6 审批。
8. **Governance**：展示偏差检查并做 HC7 签字，再导出审计记录。

## 文档

* 设计文档：`docs/design/design_document.md`（架构图 `architecture.mmd`、结论溯源 `claims_trace.md`、待补充项 `open_items.md`）
* 评测报告：`docs/evaluation/evaluation_report.md`（结果在 `eval/results/`，LLM 模式日志在 `docs/design/evidence/`）
* 治理日志：`docs/governance/governance_log.md`（审计与审批导出在 `docs/governance/evidence/`，用 `python3 scripts/governance_demo.py` 重新生成）

## 说明与限制

* CE-01 和 CE-02 的文本是根据 Week 12 Guide 的内容整理的英文版本。如果和课件原文措辞不同，请直接修改 `change_events/CE-0x.json`，或在 UI 里注入自定义事件。
* `Finance Director` 和 `April committee meeting` 在资料里都找不到确切对应：前者资料里只有 Finance Manager，后者只能找到下一次会议是 2027-04-08。系统把这两项列为 UNRESOLVED，没有自行假设。
* 风险评分、owner、trigger 都是 Agent 的提议，要经过 HC4 审批才算生效。Seabreeze 的类比数据都标注了 "indicative only"。
* Agent 从不删除、关闭任务或把任务移到 Done。在模拟看板上，"Done" 按钮是人工操作，会记录操作人的姓名。
* `data/harbourline.db` 是演示数据库，删除后重启即可恢复干净状态（审计日志也会一起清掉）。UI 里的 "Reset demo outputs" 会保留审计和审批记录。
