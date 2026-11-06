# Harbourline AI PM：MA6094 Capstone 可运行系统

这是一个前后端一体的最小实现：Python 标准库 HTTP 服务、SQLite 存储，前端是原生 HTML/JS，**无需 pip install**。它为 Harbourline Community Hub Refurbishment 实现了六个 Agent 模块和一层治理层（Governance layer），并附带一套包含 33 个测试案例的评估工具，覆盖 Brief 规定的五项指标。

## 启动

```bash
cd harbourline-pm
python3 server.py          # 或 ./run.sh
# 浏览器打开 http://127.0.0.1:8000
```

* 首次启动会自动完成以下步骤：导入 data pack，校验事实库（共 78 条事实，每条的 quote 都必须能在原文中找到），然后跑一次完整流程。
* 页面右上角的 **Approver** 栏必须填写本人姓名。所有人工检查点（HC1–HC7）都会记录审批人的姓名。
* **LLM（可选）**：在 `.env` 中填写 `DEEPSEEK_API_KEY` 即可启用 DeepSeek。不填时系统以确定性模式完整运行（成本为零，重跑结果完全一致）。LLM 产出的内容必须先经过引用校验和 Critic 的数字溯源检查，才会被采用；不通过就丢弃，并记入审计日志。
* **Jira（可选）**：配置 `JIRA_BASE_URL / JIRA_EMAIL / JIRA_API_TOKEN / JIRA_PROJECT_KEY` 后写入真实的 Jira Cloud Free；不配置时写入本地 SQLite 模拟看板。两者使用同一份数据契约。
* 运行评估：`python3 eval/run_eval.py --no-llm`，结果写入 `eval/results/latest.md` 和 `latest.json`。也可以在 UI 的 Evaluation 页点击运行。

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

1. **Overview**：点 Run，展示 hand-off 记录和运行耗时。
2. **Planning**：浏览 gaps、conflicts、WBS 的可追溯性和 flagged 项，然后做 HC1 和 HC2 审批。
3. **PM tool**：先 Preview，再做 HC3 审批并写入；再跑一次 Preview，应显示全部 unchanged。然后演示 Agent 尝试 Done/close/delete 被拦截。
4. **Memory**：提问 "What is the maximum grant?" 和 "What is the energy performance target?"（后者应返回 NOT FOUND）。
5. **Risk**：展示热力图、seed QA 结果和 what-if，然后做 HC4 审批。
6. **Reports**：植入一个故障，展示 Critic 返回 STOP；再用干净草稿走 HC5 发布。
7. **Change**：注入 CE-01 或 CE-02（学号末位奇数选 CE-01，偶数选 CE-02），查看 stale 项、自动重生成的草稿和 Impact Note，然后逐条做 HC6 审批。
8. **Governance**：展示偏差检查并做 HC7 签字，再导出审计记录。

## 说明与限制

* CE-01 和 CE-02 的文本是根据 Week 12 Guide 的内容整理的英文版本。如果和课件原文措辞不同，请直接修改 `change_events/CE-0x.json`，或在 UI 里注入自定义事件。
* `Finance Director` 和 `April committee meeting` 在资料里都找不到确切对应：前者资料里只有 Finance Manager，后者只能找到下一次会议是 2027-04-08。系统把这两项列为 UNRESOLVED，没有自行假设。
* 风险评分、owner、trigger 都是 Agent 的提议，要经过 HC4 审批才算生效。Seabreeze 的类比数据都标注了 "indicative only"。
* Agent 从不删除、关闭任务或把任务移到 Done。在模拟看板上，"Done" 按钮是人工操作，会记录操作人的姓名。
* `data/harbourline.db` 是演示数据库，删除后重启即可恢复干净状态（审计日志也会一起清掉）。UI 里的 "Reset demo outputs" 会保留审计和审批记录。
