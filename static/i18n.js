/* UI localization. Source quotations and report evidence remain in their original language. */
(() => {
  "use strict";
  const ZH = {
    /* login, roles & RBAC */
    "Sign in to continue": "请登录后继续", "Username": "用户名", "Password": "密码", "Sign in": "登录", "Sign out": "退出登录",
    "Demo accounts (click to fill)": "演示账号（点击自动填入）", "Invalid username or password": "用户名或密码错误", "Sign-in failed": "登录失败",
    "System Admin": "系统管理员", "Project Manager": "项目经理", "Group Leader": "组长", "Supervisor": "监督员",
    "admin · sees everything, manages users": "admin · 查看全部内容，管理用户",
    "pm · planning, PM tool, change · HC1 HC2 HC3 HC6": "pm · 规划、项目管理工具、变更 · HC1 HC2 HC3 HC6",
    "leader · risk & reporting · HC4 HC5": "leader · 风险与报告 · HC4 HC5",
    "supervisor · governance, audit, eval · HC7": "supervisor · 治理、审计、评估 · HC7",
    "Dashboard": "可视化面板", "Admin console": "管理控制台", "you": "我",
    /* dashboard */
    "Visual dashboard": "可视化面板", "Live view of the whole governed process for": "整个受治理流程的实时视图，当前用户：",
    "Sections your role may not open are omitted by the server, not just hidden.": "当前角色无权查看的部分由服务器直接省略，而不仅是在界面上隐藏。",
    "Verified facts": "已核验事实", "Open sponsor questions": "未答复的发起人问题", "Approvals logged": "审批记录", "Blocked / rejected": "被拦截／被拒绝",
    "End-to-end process flow": "端到端流程图", "Human checkpoints HC1–HC7": "人工检查点 HC1–HC7",
    "Plan & build": "规划与建设", "Risk & reporting": "风险与报告", "Memory & change": "记忆与变更",
    "Data pack & brief": "资料包与简报", "1 · Planning agent": "1 · 规划智能体", "2 · PM tool agent": "2 · 项目管理工具智能体",
    "Jira / mock board": "Jira／模拟看板", "3 · Memory agent": "3 · 记忆智能体", "5 · Reporting agent": "5 · 报告智能体",
    "Critic": "审查智能体", "EDC / NRF readers": "EDC／NRF 读者", "Change event": "变更事件", "6 · Change agent": "6 · 变更智能体",
    "Plan · register · board": "计划 · 登记册 · 看板", "updated after HC6": "HC6 审批后更新", "Bias & fairness check": "偏差与公平性检查",
    "Consultation summary": "咨询摘要", "cleared for design input": "可作为设计输入", "held": "暂缓", "synced · read back": "已同步 · 已读回",
    "not written": "尚未写入", "diff preview": "差异预览", "write": "写入",
    "Output produced": "已产出", "Not run yet": "尚未运行", "Needs attention": "需要关注", "Critic STOP": "审查阻止",
    "Checkpoint approved": "检查点已批准", "Awaiting a human": "等待人工审批", "Rejected": "已拒绝",
    "Hand-off (machine, no copy-paste)": "自动交接（无需手工复制）", "Click to open": "点击打开", "Not visible to your role": "当前角色不可见",
    "Human checkpoint": "人工检查点", "not started": "未开始", "pending": "待审批",
    "Risk heat map (likelihood × impact)": "风险热力图（可能性 × 影响）", "Top risks by score": "按评分排列的主要风险",
    "Sponsor questions by status": "发起人问题状态分布", "Answered": "已答复", "Partially answered": "部分答复", "Open": "未答复",
    "WBS by level": "各层级 WBS 数量", "Report versions by status": "报告版本状态分布", "PM board items by status": "看板事项状态分布",
    "Audit activity over time": "审计活动时间分布", "Approvals per checkpoint": "各检查点审批次数", "Access denied (RBAC) by account": "各账号被拒访问次数（RBAC）",
    "Milestone timeline & dependencies": "里程碑时间线与依赖关系", "Dated milestone": "已定日期的里程碑", "TBD / not in pack": "待定／资料包未提供",
    "Conflict / at risk": "冲突／有风险", "Dependency": "依赖", "approved": "已批准", "rejected": "已拒绝", "agent": "智能体", "human": "人工", "system": "系统",
    "No activity yet.": "暂无活动。",
    /* admin console */
    "System administrator view: the guided demo path across all roles, who can do what, user accounts and the access log. Every change here is written to the audit trail.": "系统管理员视图：跨角色的演示引导路径、各角色权限、用户账号和访问日志。此处的每项变更都会写入审计记录。",
    "Run the full pipeline": "运行完整流程", "Approve gaps register and plan baseline": "批准缺口登记册和计划基线",
    "Preview, approve and write the PM board": "预览、批准并写入项目管理看板", "Ask memory questions (one NOT FOUND)": "向记忆模块提问（含一次“未找到”）",
    "Approve the risk register": "批准风险登记册", "Plant a fault, then release a clean report": "植入故障，再发布无误报告",
    "Inject a change event and clear HC6 actions": "注入变更事件并处理 HC6 行动", "Sign off the bias check and export the audit": "签署偏差检查并导出审计记录",
    "Role → checkpoint authority": "角色 → 检查点审批权限", "Permission matrix": "权限矩阵", "Views": "页面", "Actions": "操作", "Checkpoints": "检查点",
    "Run pipeline": "运行流程", "Reset demo": "重置演示", "Write PM board": "写入看板", "Ask memory": "记忆问答", "Record decision": "记录决策",
    "Regenerate reports": "重新生成报告", "Plant critic fault": "植入审查故障", "Inject change event": "注入变更事件", "Run evaluation": "运行评估",
    "View audit trail": "查看审计记录", "Export audit": "导出审计", "Manage users": "管理用户",
    "Name": "姓名", "Role": "角色", "Last login": "最近登录", "Sessions": "会话", "Human actions": "人工操作", "Denied": "被拒",
    "Save": "保存", "Reset password": "重置密码", "Disable": "停用", "Enable": "启用", "active": "启用中", "disabled": "已停用",
    "Create user": "创建用户", "Create": "创建", "username": "用户名", "Display name": "显示名称", "Password (min 6)": "密码（至少 6 位）",
    "Access log (logins, denied requests, user changes)": "访问日志（登录、被拒请求、用户变更）", "Account": "账号", "Event": "事件", "Target": "对象", "Outcome": "结果",
    "User updated": "用户已更新", "User created": "用户已创建", "blocked": "已拦截",
    "Open the visual dashboard and full process flowchart →": "打开可视化面板与完整流程图 →",
    /* Jira integration */
    "Jira Cloud": "Jira Cloud", "Mock board (SQLite)": "模拟看板（SQLite）", "Site": "站点", "project": "项目",
    "Test Jira connection": "测试 Jira 连接", "Check configuration": "检查配置", "connection error": "连接错误", "Checking…": "检查中…",
    "Account": "账号", "Project": "项目", "Issue type mapping": "事项类型映射", "\"Blocks\" link type": "“Blocks”关联类型",
    "Synced items": "已同步事项", "never": "从未", "available": "可用", "missing": "缺失", "Open in Jira": "在 Jira 中打开",
    "synced · read back": "已同步 · 已读回", "not written": "尚未写入",
    "Same data contract as Jira. Set JIRA_BASE_URL, JIRA_EMAIL and JIRA_API_TOKEN in .env to write to Jira Cloud.": "与 Jira 使用相同的数据契约。在 .env 中设置 JIRA_BASE_URL、JIRA_EMAIL 和 JIRA_API_TOKEN 即可写入 Jira Cloud。",
    "A Jira API token was found, but Jira stays off until these are set in": "已检测到 Jira API Token，但需在以下文件中补齐配置后才会启用 Jira：",
    "Community Hub Refurbishment · governed agent system": "社区中心翻新 · 受治理约束的智能体系统",
    "Approver (named human)": "审批人（实名）", "Your name": "请输入姓名", "Close": "关闭",
    "Overview": "总览", "1 · Planning": "1 · 规划", "2 · PM tool": "2 · 项目管理工具",
    "3 · Memory": "3 · 记忆检索", "4 · Risk & what-if": "4 · 风险与情景分析",
    "5 · Reports & critic": "5 · 报告与审查", "6 · Change": "6 · 变更",
    "Governance": "治理", "Agent cards": "智能体卡片", "Evaluation": "评估",
    "Loading…": "加载中…", "Nothing yet.": "暂无内容。", "error": "错误",
    "Risk register row - see tab 4.": "风险登记册条目——请查看第 4 页。",
    "Harbourline Community Hub Refurbishment": "Harbourline 社区中心翻新项目",
    "Six agent modules and a governance layer working as one system. Facts come only from the brief, Sponsor Answers Round 1 and the data pack; anything else is reported as NOT FOUND. Agents draft; named humans approve at the checkpoints marked in amber.": "六个智能体模块与治理层协同工作。事实仅来自项目简报、首轮发起人答复和资料包；缺少依据的内容标记为“未找到”。智能体起草内容，由实名人员在琥珀色检查点审批。",
    "1 Planning": "1 规划", "2 PM tool": "2 项目管理工具", "4 Risk & what-if": "4 风险与情景分析",
    "5 Reporting → Critic": "5 报告 → 审查", "6 Change": "6 变更", "Bias check": "偏差检查",
    "Run full pipeline": "运行完整流程", "Reset demo outputs": "重置演示输出",
    "Re-running with the same inputs creates no new versions and no PM duplicates.": "使用相同输入再次运行不会产生新版本或重复的项目管理事项。",
    "Source chunks": "来源片段", "Sponsor Questions / gaps": "发起人问题／缺口", "Conflicts": "冲突",
    "WBS elements": "WBS 工作项", "Milestones": "里程碑", "Risks": "风险", "What-ifs": "情景分析",
    "Report versions": "报告版本", "PM issues": "项目管理事项", "Change events": "变更事件",
    "Pending HC6 actions": "待 HC6 审批的行动", "Audit rows": "审计记录",
    "Human checkpoints": "人工检查点", "Machine hand-offs (no copy-paste)": "模块自动交接（无需手工复制）",
    "Runs · cost and time": "运行记录 · 成本与耗时", "approved (current version)": "已批准（当前版本）",
    "awaiting": "待审批", "awaiting HC7": "待 HC7 审批", "not run": "未运行", "all": "全部通过", "Time": "时间", "From": "来源", "To": "去向",
    "Payload": "交接内容", "Items": "数量", "Run": "运行", "Kind": "类型", "Seconds": "秒",
    "Tokens in/out": "输入／输出 Token", "Cost (US$)": "费用（美元）", "LLM calls": "LLM 调用",
    "LLM off · deterministic": "LLM 关闭 · 确定性模式", "LLM: DeepSeek": "LLM：DeepSeek",
    "Enter your name as approver first (top right). Checkpoints need a named human.": "请先在右上角填写审批人姓名。人工检查点需要实名审批。",
    "Outputs cleared. Audit log and approvals kept.": "输出已清除；审计记录和审批记录已保留。",
    "No plan yet. Run the pipeline from Overview.": "尚无计划。请先在总览页运行完整流程。",
    "Scope statement, Sponsor Questions with an assumption register, the brief's contradictions, a Level-3 WBS with dictionary and traceability, and a milestone plan in relative time (dates only where the sponsor or pack gives them).": "本页展示范围说明、发起人问题与假设登记册、简报中的冲突、可追溯到三级的 WBS 及其词典，以及使用相对时间的里程碑计划。只有发起人或资料包提供日期时才填写具体日期。",
    "Objective.": "目标：", "Success.": "成功标准：", "Scope line": "范围条目", "Source": "来源",
    "Sponsor Questions & assumption register": "发起人问题与假设登记册", "Approve register (HC1)": "批准登记册（HC1）",
    "Topic": "主题", "Question": "问题", "Why (brief evidence)": "原因（简报依据）",
    "Status": "状态", "Answer / assumption": "答复／假设", "sponsor only": "仅发起人可答",
    "Conflicts between sources": "来源之间的冲突", "What disagrees": "冲突内容", "Sources (all named)": "来源（全部列明）",
    "WBS to Level 3 with dictionary": "三级 WBS 与词典", "Approve plan baseline (HC2)": "批准计划基线（HC2）",
    "HC2 (plan version": "HC2（计划版本",
    "Code": "编码", "Element": "工作项", "Traces to": "追溯至", "Deliverables": "交付物",
    "Owner": "负责人", "Dictionary": "词典", "dictionary": "词典", "Flagged, not kept (no traceable scope line)": "已标记但未纳入（无可追溯的范围条目）",
    "Candidate element": "候选工作项", "Reason": "原因", "Sources": "来源",
    "Milestone plan with dependencies": "含依赖关系的里程碑计划", "Dependency check:": "依赖检查：",
    "no ordering violations": "未发现顺序冲突", "Dependency check: no ordering violations.": "依赖检查：未发现顺序冲突。",
    "LLM-proposed": "LLM 提议", "Proposed (LLM) - needs HC1": "LLM 提议，待 HC1 审批",
    "LLM found no support in retrieved sources": "检索到的来源中没有支持该答案的依据",
    "Milestone": "里程碑", "WBS": "WBS", "Relative": "相对时间",
    "Date": "日期", "Depends on": "依赖", "Note": "备注", "TBD": "待定",
    "by": "由", "not approved": "未批准", "approved": "已批准", "rejected": "已拒绝",
    "2 · PM tool integration": "2 · 项目管理工具集成",
    "Backend: ": "后端：",
    "Writes need the plan approved (HC2) and the exact diff approved (HC3). Stable external keys (": "写入前须批准计划（HC2）和对应的差异预览（HC3）。稳定的外部键（",
    " labels) make a second run update rather than duplicate. Agents may create, update and comment; Done, close and delete are human acts.": "标签）确保再次运行时更新既有事项，不产生重复。智能体可以创建、更新和评论；完成、关闭及删除由人工执行。",
    "Backend:": "后端：", "project": "项目", "parent": "父项",
    "(project": "（项目", "). Writes need the plan approved (HC2) and the exact diff approved (HC3). Stable external keys (": "）。写入前须批准计划（HC2）和对应的差异预览（HC3）。稳定的外部键（",
    "labels) make a second run update rather than duplicate. Agents may create, update and comment; Done, close and delete are human acts.": "标签）确保再次运行时更新既有事项，不产生重复。智能体可以创建、更新和评论；完成、关闭及删除由人工执行。",
    "1. Preview diff (read-only)": "1. 预览差异（只读）", "Read back & verify": "读回并核验",
    "Guardrail demo - the agent tries to:": "安全边界演示——智能体尝试：",
    "move to Done": "移至完成", "close": "关闭", "delete": "删除", "Done": "完成",
    "Key": "键值", "Type": "类型", "Summary": "摘要", "Labels": "标签", "Due": "截止日期",
    "Links": "关联", "Comments": "评论", "Human": "人工操作",
    "2. Approve this diff (HC3) and write": "2. 批准此差异（HC3）并写入",
    "External key": "外部键", "Action": "操作", "Remote": "远端事项",
    "verified": "已核验", "not verified": "未通过核验", "not blocked?!": "未被拦截？！",
    "created": "已创建", "updated": "已更新", "unchanged": "未变化",
    "missing": "缺失", "mismatched": "不一致", "duplicates": "重复", "preview": "预览",
    "3 · Memory & retrieval": "3 · 记忆与检索",
    "Ask about the brief, sponsor answers or data pack. Answers cite document, section and lines; the agent says NOT FOUND when the pack is silent, and names both sides when sources conflict. Human decisions recorded below are carried into later sessions.": "可就项目简报、发起人答复或资料包提问。回答会注明文档、章节和行号；资料没有答案时显示“未找到”，来源冲突时列出各方依据。下方记录的人工决策会保留到后续会话。",
    "Ask a question…": "输入问题…", "Ask": "提问", "Decision log (carried forward)": "决策记录（跨会话保留）",
    "e.g. Sponsor decided on 2027-04-08: east core closure accepted with temporary lift": "例如：发起人于 2027-04-08 同意关闭东侧核心区并设置临时电梯",
    "Record decision": "记录决策", "Decision": "决策", "By": "决策人", "When": "时间",
    "Recent questions": "最近的问题", "Answer": "回答", "Mode": "模式", "NOT FOUND": "未找到",
    "sources conflict": "来源冲突", "retrieved passages": "检索到的原文片段", "score": "得分",
    "What is the maximum grant?": "最高拨款额是多少？", "When is practical completion?": "实际竣工时间是什么时候？",
    "Who appoints the active ageing centre operator?": "谁任命活跃乐龄中心的运营方？",
    "How much is the asbestos removal estimate?": "石棉清除估算费用是多少？",
    "What is the energy performance target?": "能源绩效目标是什么？",
    "How much will the rooftop garden cost?": "屋顶花园需要多少钱？",
    "How long does childcare licensing take?": "托育许可需要多久？",
    "What does Tranche 2 require?": "第二笔拨款需要满足哪些条件？",
    "4 · Risk & what-if": "4 · 风险与情景分析", "Risk register": "风险登记册",
    "4 · Risk register & what-if": "4 · 风险登记册与情景分析",
    "Scored L×I with owner, trigger and linked WBS; every row cites its evidence. The 2025 seed register was checked rather than trusted. Re-scoring after a change event is proposed by the agent and applied only after HC6.": "风险按可能性×影响评分，并记录负责人、触发条件和关联 WBS；每条风险都附有证据。系统对 2025 年初始风险登记册进行质检。变更后的重新评分由智能体提出，须经 HC6 批准后执行。",
    "Approve risk register (HC4)": "批准风险登记册（HC4）", "Seed register QA": "初始登记册质检",
    "Approve register (HC4)": "批准登记册（HC4）", "HC4 (register version": "HC4（登记册版本",
    "Seed register QA (computed)": "初始登记册质检（计算结果）", "top 5": "前五项",
    "Risk heatmap": "风险热力图", "Likelihood": "可能性", "Impact": "影响", "Score": "分数",
    "Trigger": "触发条件", "Mitigation": "缓解措施", "What-if scenarios": "情景分析",
    "Assumptions": "假设", "Result": "结果", "stale": "已过期",
    "5 · Reporting with a critic": "5 · 报告与审查",
    "One fact sheet feeds two audiences: a one-page EDC exception update and the NRF monthly report (clause 3.2 contents). The Critic traces every number and date to a cited source, checks required sections, the top five risks, conflicts and change events, and STOPs the draft on any fault. Only Critic-passed drafts can be released (HC5).": "同一事实库生成面向两类读者的报告：EDC 单页例外情况更新和符合第 3.2 条的 NRF 月报。审查模块核对数字、日期、必需章节、前五项风险、冲突和变更事件；发现问题即停止发布。只有通过审查的草稿才能经 HC5 发布。",
    "Regenerate EDC draft": "重新生成 EDC 草稿", "Regenerate NRF draft": "重新生成 NRF 草稿",
    "use LLM summary": "使用 LLM 摘要", "Plant a fault:": "植入故障：",
    "Plant & run Critic": "植入并运行审查", "No reports": "暂无报告",
    "Planted fault:": "植入故障：", "Release to readers (HC5)": "发布给读者（HC5）",
    "Critic findings": "审查结果", "LLM summary (checked)": "LLM 摘要（已核验）",
    "deterministic": "确定性模式", "LLM-generated, Critic-checked": "LLM 生成，已经 Critic 审查",
    "Who produced the outputs": "产出来源", "LLM-generated, validated": "LLM 生成，已校验", "baseline fallback": "基线回退",
    "not run": "未运行", "Planning": "规划", "Risk register": "风险登记册", "Reports": "报告", "Change analysis": "变更分析",
    "LLM-generated outputs are checked before use: unknown sources, WBS codes and tags are dropped, dates must appear in a cited source, every report number is traced by the Critic (up to 3 revision rounds). The curated baseline is used only when the LLM is off or its output fails these checks. Responses are cached, so re-runs on the same inputs are identical.":
      "LLM 生成的内容在使用前都要校验：未知的来源、WBS 编码和标签会被丢弃；日期必须出现在所引用的来源中；报告中的每个数字都由 Critic 溯源（最多 3 轮修订）。只有在 LLM 关闭或其产出未通过校验时，才使用人工整理的基线。响应会被缓存，因此相同输入重跑结果一致。", "critic_passed": "审查通过", "critic_stopped": "审查停止",
    "Progress against the baseline programme": "相对于基线计划的进展",
    "Expenditure to date against eligible cost": "累计支出与合格成本对比",
    "Status of each tranche condition": "各笔拨款条件状态",
    "Top five risks": "前五项风险", "Conflicts flagged": "已标记的冲突",
    "Executive summary": "执行摘要", "Overall status": "总体状态",
    "Decisions required": "待决事项", "Exceptions and escalations": "例外情况与升级事项",
    "Next steps": "后续步骤", "Change event impact": "变更事件影响",
    "released": "已发布", "wrong_number": "数字错误", "invented_figure": "虚构数字",
    "missing_citation": "缺少引文", "drop_section": "缺少章节", "wrong_top5": "前五项风险错误",
    "status_spin": "状态误导", "remove_conflicts": "遗漏冲突", "wrong_date": "日期错误",
    "invented_person": "虚构人员", "hidden_gap": "隐藏缺口", "bad_calc": "计算错误",
    "6 · Change handling": "6 · 变更处理",
    "The Week 12 event is injected as a dated, numbered input; the data pack is never edited. The Change Agent finds affected WBS, deliverables, milestones and risks, marks stale outputs, refreshes what-ifs and report drafts automatically, and drafts actions that wait for HC6. It never edits the baseline, closes or deletes.": "第 12 周事件以带日期和编号的新输入注入，原始资料包不受影响。变更智能体识别受影响的 WBS、交付物、里程碑和风险，标记过期输出，自动重生成情景分析与报告草稿，并拟定待 HC6 审批的行动。",
    "Custom event": "自定义事件", "Title": "标题", "Event text": "事件内容", "Inject custom": "注入自定义事件",
    "Affected": "受影响的内容", "downstream": "下游", "Now stale": "现已过期",
    "Regenerated automatically": "已自动重生成", "Cost and time impact": "成本与工期影响",
    "traced": "可追溯", "untraced": "无法追溯", "LLM summary (Critic-checked):": "LLM 摘要（审查通过）：",
    "Sponsor decisions needed": "需要发起人决策", "What": "事项", "Who": "负责人",
    "UNRESOLVED": "未解决", "View Change Impact Note": "查看变更影响说明",
    "Approve all pending (each logged)": "批准所有待处理行动（逐项留痕）",
    "Target": "目标", "Proposal": "提议", "Approve": "批准", "Reject": "拒绝",
    "pending": "待处理", "applied": "已执行", "analysed": "已分析",
    "Governance layer": "治理层",
    "Named human checkpoints, a complete audit trail of every agent write and human decision, blocked guardrail attempts, and the bias & fairness check on the resident consultation.": "本页展示实名人工检查点、智能体写入与人工决策的完整审计轨迹、被拦截的越界操作，以及居民咨询的偏差与公平性检查。",
    "Export audit (CSV)": "导出审计记录（CSV）", "Export approvals (CSV)": "导出审批记录（CSV）",
    "Export governance pack (JSON)": "导出治理资料包（JSON）", "Checkpoint map": "检查点一览",
    "Checkpoint": "检查点", "Approver role": "审批角色", "Gates": "控制环节", "Approvals": "审批次数",
    "Bias & fairness check — resident consultation": "偏差与公平性检查——居民咨询",
    "Sign off (HC7)": "签署确认（HC7）", "Actions": "行动",
    "Responses by age band": "按年龄段统计答复", "By channel": "按渠道", "By language": "按语言",
    "Themes — raw count": "主题——原始计数", "Themes — each age band weighted equally": "主题——各年龄段等权重",
    "Non-English comment glosses": "非英语评论译文", "Original": "原文", "Gloss": "释义",
    "Blocked or rejected attempts": "被拦截或拒绝的操作", "Actor": "执行者", "Outcome": "结果",
    "Audit log": "审计日志", "Filter (actor, action, target)…": "筛选（执行者、操作、目标）…",
    "Role.": "角色：", "Context.": "背景：", "Inputs.": "输入：", "Outputs.": "输出：",
    "Tools.": "工具：", "Stop condition.": "停止条件：", "Checkpoint.": "检查点：",
    "System prompt": "系统提示词",
    "Role and context are fixed per agent. Every card names its inputs, outputs, tools and stop condition.": "每个智能体的角色和背景固定；卡片列出其输入、输出、工具及停止条件。",
    "The harness runs on a throw-away database: ": "评估工具使用临时数据库运行：",
    "The harness runs on a throw-away database:": "评估工具使用临时数据库运行：",
    "test cases including the brief's gaps and both Week 12 change events, and the five comparable measures.": "个测试案例，涵盖简报中的缺口、第 12 周的两起变更事件，以及五项可比指标。",
    " test cases including the brief's gaps and both Week 12 change events, and the five comparable measures.": "个测试案例，涵盖简报中的缺口、第 12 周的两起变更事件，以及五项可比指标。",
    "Run evaluation (deterministic)": "运行评估（确定性模式）", "Run with LLM": "使用 LLM 运行",
    "Not run yet": "尚未运行", "Gap recall": "缺口召回率", "Invention rate": "无依据内容比例",
    "identical": "一致", "differs": "不一致", "Re-run stability": "重复运行稳定性",
    "Critic catch rate": "审查检出率", "Test cases passed": "通过的测试案例",
    "Category": "类别", "Test": "测试", "Detail": "详情", "Missed gaps:": "遗漏的缺口：",
    "none": "无", "Running evaluation…": "正在运行评估…",
    "Run the pipeline first.": "请先运行完整流程。",
    "Running evaluation with LLM…": "正在使用 LLM 运行评估…",
    "PASS": "通过", "FAIL": "失败", "STOP": "停止", "Open": "未解决",
    "Answered": "已答复", "Partial": "部分答复", "Proposed": "已提议", "REOPENED": "重新开启"
  };

  // Deterministic report text is translated for reading; citation IDs remain unchanged.
  Object.assign(ZH, {
    "Active ageing centre operator not found (one EOI response; policy needs three)": "未找到活跃乐龄中心运营方（仅一份意向答复，政策要求三份）",
    "Authority approvals delayed (e.g. kitchen exhaust permit)": "主管机关审批延迟（例如厨房排风许可证）",
    "Barrier-free access lost to levels 3-4 during 14-week east core lift closure": "东侧核心区电梯关闭 14 周期间，三、四层失去无障碍通道",
    "Childcare floor handover too late for licensing before Jan 2029 intake": "托育楼层移交过晚，无法在 2029 年 1 月招生前完成许可手续",
    "Childcare operator withdraws or delays opening": "托育运营方退出或推迟开业",
    "Committee and grant reporting effort / lateness": "委员会及拨款报告工作量或提交延迟",
    "Completion after 31 Dec 2028 (needs Fund approval) and after 'fully open by Q4 2028'": "竣工晚于 2028-12-31（须基金批准），也晚于 2028 年第四季度全面开放的承诺",
    "Construction price inflation": "建筑成本上涨",
    "Consultation summary under-represents seniors and non-English speakers": "咨询汇总未充分反映长者及非英语使用者意见",
    "Contingency undefined and likely insufficient: ~S$1.18M headroom vs asbestos S$0.35-0.60M + roof strengthening (unpriced)": "预备金尚未定义且可能不足：约 118 万新元余量需应对 35 万至 60 万新元石棉费用及尚未估价的屋顶加固",
    "Design behind plan (26% vs 35%); stage 2 report overdue": "设计进度落后（26%，计划为 35%）；第二阶段报告已逾期",
    "Existing M&E worse than surveyed (sprinkler mains)": "现有机电设施状况比调查结果更差（消防喷淋主管）",
    "Grant conditions reduce eligible cost: cap S$17.0M; food court and rooftop amenity ineligible": "拨款条件减少合格成本：上限 1,700 万新元，餐饮区和屋顶设施不合格",
    "Hazardous materials: asbestos (chrysotile) confirmed in level 2 west wing": "危险材料：二层西翼确认发现石棉（温石棉）",
    "Keeping the Hub open extends the programme; closures not accepted so lift and sports hall packages cannot start as programmed": "维持中心开放会延长工期；关闭安排未获批准，电梯及体育馆工程无法按计划启动",
    "Late AAC appointment forces layout rework after design fixed": "AAC 运营方任命过晚，导致设计确定后仍需修改布局",
    "Noise and dust complaints from residents (merged duplicate R04)": "居民就噪音和扬尘投诉（已合并重复风险 R04）",
    "Public interface with live works": "公众与施工区域接触",
    "Roof slab needs strengthening for rooftop garden loads; cost not estimated": "屋顶花园荷载要求加固屋面板，费用尚未估算",
    "Tranche 2 (30%) delayed: needs signed operator agreements for ALL social service spaces": "第二笔拨款（30%）延迟：所有社会服务空间均须签署运营协议",
    "Two consecutive late NRF reports may suspend the next tranche (Feb report was late)": "连续两份 NRF 报告逾期可能暂停下一笔拨款（二月报告已逾期）",
    "Vendor/tool change affects the AI PM system (brief: log vendor change as a risk)": "供应商或工具变更影响 AI 项目管理系统（简报要求将供应商变更列为风险）",
    "AAC operator appointed": "AAC 运营方获任命", "All operator agreements signed": "所有运营方协议已签署",
    "Baseline programme submitted": "基线计划已提交", "Childcare first intake": "托育首次招生",
    "Consultation summary to contractor": "向承包商提交咨询汇总", "Design stage 2 sign-off": "第二阶段设计批准",
    "Hub fully open": "中心全面开放", "NRF Tranche 1 claim (award + baseline)": "NRF 第一笔拨款申请（合同授予＋基线）",
    "NRF Tranche 2 claim": "NRF 第二笔拨款申请",
    "NRF Tranche 4 (6 months operation + utilisation report)": "NRF 第四笔拨款（运营六个月＋使用情况报告）",
    "Resident consultation closed": "居民咨询结束", "Site possession": "场地移交",
    "Sponsor decision on closures": "发起人就关闭安排作出决策",
    "Structural & M&E rough-in complete": "结构与机电预埋工程完成",
    "TOP + NRF Tranche 3 claim": "取得临时入伙证＋NRF 第三笔拨款申请",
    "AAC appointment due date": "AAC 任命截止日期", "Asbestos variation status": "石棉变更状态",
    "Budget headroom / contingency": "预算余量／预备金", "Childcare handover vs licensing": "托育移交与许可时间冲突",
    "Completion date": "竣工日期", "Contractor progress narrative vs numbers": "承包商进度描述与数字不符",
    "Data quality in deliverables schedule": "交付物进度表数据质量", "EDC meeting cadence": "EDC 会议频率",
    "Grant amount": "拨款金额", "Hub open vs closures vs accessibility": "中心开放、关闭安排与无障碍通道冲突",
    "Seed risk register quality": "初始风险登记册质量",
    "AAC operator withdrawal (CE-02): re-run EOI": "AAC 运营方退出（CE-02）：重新征集意向",
    "Asbestos removal in level 2 west wing": "二层西翼石棉清除",
    "Closures not accepted - keep every area open": "关闭安排未获批准——所有区域保持开放",
    "Defer the rooftop community garden": "推迟屋顶社区花园",
    "Does the 22-month duration include tendering and design, and what is the start date?": "22 个月的工期是否包含招标和设计？起始日期是什么？",
    "Which completion date is the commitment: 22 months from possession, 'fully open by Q4 2028', or KHB's 31 Dec 2028 practical completion - and what does 'fully open' mean?": "承诺的竣工日期究竟是哪一个：场地移交后 22 个月、2028 年第四季度前全面开放，还是 KHB 的 2028-12-31 实际竣工日期？“全面开放”如何定义？",
    "How can lifts and M&E be replaced with the Hub open, and which areas may close in what order?": "中心维持开放期间如何更换电梯和机电系统？哪些区域可以关闭，关闭顺序如何？",
    "Who appoints the active ageing centre operator, and by when?": "谁负责任命活跃乐龄中心运营方？截止日期是什么？",
    "When must the childcare floor be handed over, and how long does the operator need for fit-out and licensing before enrolment?": "托育楼层何时必须移交？运营方在开始招生前需要多久完成装修和许可手续？",
    "What are the grant conditions, eligible costs and tranche milestones?": "拨款条件、合格成本及分期拨款里程碑分别是什么？",
    "Who funds the remaining 40%?": "剩余 40% 的资金由谁承担？",
    "Does the S$18.5M budget include a contingency, is the ~S$1.18M headroom that contingency, and who may draw on it?": "1,850 万新元预算是否包含预备金？约 118 万新元的预算余量是否就是预备金？谁有权动用？",
    "What is the cost of each scope element, especially the ineligible food court refresh and rooftop garden?": "各范围条目的费用是多少？特别是不符合拨款资格的餐饮区翻新和屋顶花园费用是多少？",
    "Is resident consultation before tender or during design-and-build, and who runs it?": "居民咨询是在招标前进行，还是在设计施工总承包期间进行？由谁负责？",
    "How is 'high resident satisfaction' measured, against what baseline and target?": "如何衡量“较高的居民满意度”？基线和目标分别是什么？",
    "What energy-performance target or standard must the refurbishment meet?": "翻新工程必须达到什么能源绩效目标或标准？",
    "During the 14-week east core closure, how is barrier-free access to levels 3-4 kept, and is a temporary lift funded?": "东侧核心区关闭 14 周期间，如何维持三、四层的无障碍通道？是否为临时电梯提供资金？",
    "What happens to existing leases/licences (tuition centre, food court stalls) during closures - relocation or compensation?": "关闭期间现有租约和执照（补习中心、餐饮摊位）如何处理——搬迁还是补偿？",
    "Who approves variations and scope changes, and up to what value, before they go to the EDC or the Fund?": "变更和范围调整在提交 EDC 或基金前由谁批准？其审批金额上限是多少？",
    "What must the weekly EDC update contain, and does it stay weekly?": "每周 EDC 更新必须包含哪些内容？报告频率是否保持每周一次？",
    "Is the rooftop garden kept, deferred or re-scoped given its ineligibility and the roof slab strengthening need?": "考虑到屋顶花园不符合拨款资格且需要加固屋面板，应保留、推迟还是调整其范围？",
    "Who commissions and pays for an intrusive hazardous-materials survey for this 1994 building?": "这栋建于 1994 年的建筑需进行侵入式危险材料调查，由谁委托并支付费用？",
    "Who operates the Hub after completion and owns the 6-month utilisation report needed for Tranche 4?": "竣工后由谁运营中心？第四笔拨款所需的六个月使用情况报告由谁负责？",
    "Who owns the move from spreadsheets to the PM tool and the data in it?": "谁负责从电子表格迁移到项目管理工具，并维护其中的数据？",
    "Project management & governance": "项目管理与治理", "Planning & controls": "规划与控制",
    "Scope statement, Sponsor Questions & assumption register": "范围说明、发起人问题与假设登记册",
    "Baseline programme review & reconciliation (22 months vs Q4 2028)": "基线计划审查与协调（22 个月与 2028 年第四季度）",
    "Risk register maintenance & what-if analysis": "风险登记册维护与情景分析",
    "Weekly/alternate-week EDC exception update": "每周或隔周 EDC 例外情况更新",
    "Monthly NRF progress report (by 10th working day)": "NRF 月度进展报告（第 10 个工作日前）",
    "NRF tranche claims T1-T4": "NRF T1 至 T4 分期拨款申请", "Grant & budget control": "拨款与预算控制",
    "Eligible-cost tracking against S$17.0M cap": "按 1,700 万新元上限跟踪合格成本",
    "Contingency & variation control": "预备金与变更控制", "Design (design-and-build)": "设计（设计施工总承包）",
    "Design stages": "设计阶段", "Design stage 2 report": "第二阶段设计报告",
    "Design stage 3 (detailed) report": "第三阶段详细设计报告",
    "Energy & accessibility design compliance": "能源与无障碍设计合规",
    "Surveys & assessments": "调查与评估", "M&E condition survey": "机电设施状况调查",
    "Hazardous materials survey": "危险材料调查", "Roof structural assessment": "屋顶结构评估",
    "Stakeholders, consultation & operators": "利益相关方、咨询与运营方",
    "Resident consultation": "居民咨询", "Consultation run (online, paper, town hall)": "开展咨询（在线、纸质、居民大会）",
    "Consultation summary with bias & fairness check": "咨询汇总与偏差、公平性检查",
    "Consultation output handed to contractor as design input": "将咨询结果交承包商作为设计输入",
    "Operators": "运营方", "Childcare operator agreement (Little Harbour Learning)": "托育运营方协议（Little Harbour Learning）",
    "AAC operator EOI & appointment": "AAC 运营方意向征集与任命", "AAC operator agreement": "AAC 运营方协议",
    "Hub users & community communications": "中心使用者与社区沟通",
    "Closure notices to users": "向使用者发出关闭通知", "Weekly works notices at lift lobbies": "在电梯大堂发布每周施工通知",
    "Phasing & keeping the Hub open": "分阶段施工并维持中心开放", "Phasing": "分阶段安排",
    "Phasing plan review": "分阶段施工计划审查", "Closure options & sponsor decision": "关闭方案与发起人决策",
    "Temporary barrier-free access plan (lifts)": "临时无障碍通行方案（电梯）",
    "Construction works": "施工工程", "Enabling works": "前期准备工程",
    "Site possession & hoarding": "场地移交与围挡", "Soft-strip": "非结构性拆除",
    "Asbestos removal (level 2 west wing)": "石棉清除（二层西翼）", "Sports hall": "体育馆",
    "Sports hall roof & M&E replacement": "体育馆屋顶与机电系统更换",
    "Sports hall upgrade & fit-out": "体育馆升级与装修", "Early childhood centre": "幼儿中心",
    "Childcare floor works": "托育楼层施工", "Childcare floor handover for fit-out": "托育楼层移交装修",
    "Active ageing centre": "活跃乐龄中心", "AAC floor works": "AAC 楼层施工",
    "AAC layout confirmation with appointed operator": "与获任命的运营方确认 AAC 布局",
    "Community kitchen & food court": "社区厨房与餐饮区", "Kitchen exhaust & grease-trap works": "厨房排风与隔油池工程",
    "Kitchen exhaust permit application": "厨房排风许可证申请",
    "Food court refresh fit-out (grant-ineligible)": "餐饮区翻新装修（不符合拨款资格）",
    "Rooftop community garden": "屋顶社区花园", "Roof slab strengthening": "屋面板加固",
    "Rooftop garden works (grant-ineligible)": "屋顶花园工程（不符合拨款资格）",
    "Accessibility & lifts": "无障碍设施与电梯", "Lift package award": "电梯工程合同授予",
    "East core lift replacement": "东侧核心区电梯更换",
    "Barrier-free access works (ramps, routes)": "无障碍通道工程（坡道、路线）",
    "M&E replacement": "机电系统更换", "Sprinkler mains replacement": "消防喷淋主管更换",
    "Structural & M&E rough-in (incl. level 2 risers)": "结构与机电预埋工程（含二层立管）",
    "Testing & commissioning": "测试与调试", "Completion, handover & grant close-out": "竣工、移交与拨款结项",
    "Completion": "竣工", "Temporary Occupation Permit (whole facility)": "整座设施临时入伙证",
    "Practical completion": "实际竣工", "Operator handovers & Hub fully open": "移交运营方并全面开放中心",
    "Post-occupancy": "投入使用后", "Six months operation & utilisation report (NRF T4)": "运营六个月及使用情况报告（NRF T4）",
    "AAC operator": "活跃乐龄中心运营方", "Change authority": "变更权限", "Childcare handover": "托育设施移交",
    "Completion commitment": "竣工承诺", "Consultation timing": "咨询时间", "Contingency": "预备金",
    "Cost split by scope element": "按范围条目划分成本", "Energy target": "能源目标", "Existing leases": "现有租约",
    "Funding balance": "资金缺口", "Grant conditions": "拨款条件", "Hazardous materials": "危险材料",
    "Hub open vs works": "设施开放与施工", "Operations after handover": "移交后运营",
    "Reporting cadence": "报告频率", "Rooftop garden": "屋顶花园", "Schedule basis": "进度计划依据",
    "Success measure": "成功指标", "Temporary barrier-free access": "临时无障碍通道", "Tracking system": "跟踪系统",
    "Answered (date open)": "已答复（日期待定）", "Answered by data pack": "资料包已答复",
    "Partially answered": "部分答复", "Community Engagement": "社区参与", "Council PM": "理事会项目经理",
    "Estate Development": "物业发展", "Finance": "财务", "Legal": "法律",
    "UNASSIGNED (D14 owner not assigned)": "未指定（D14 负责人未定）", "UNASSIGNED (GQ19)": "未指定（GQ19）",
    "Accessibility": "无障碍", "Cost": "成本", "Delivery system": "交付体系", "Design": "设计",
    "Funding": "资金", "Operator": "运营方", "Programme": "进度计划", "Regulatory": "法规",
    "Reporting": "报告", "Safety": "安全", "Scope": "范围", "Stakeholder": "利益相关方", "Technical": "技术",
    "Open - realised": "未关闭——已发生", "Open - realised in part": "未关闭——部分发生",
    "REOPENED - realised": "重新开启——已发生", "brief": "简报", "pack": "资料包", "seed": "初始登记册",
    "seed+pack": "初始登记册＋资料包", "assumption_update": "更新假设", "milestone_note": "更新里程碑备注",
    "pm_flag": "标记项目管理事项", "risk_rescore": "重新评分风险", "constraint": "约束", "delivery": "交付",
    "in": "包含", "objective": "目标", "out": "不包含",
    "Active ageing / seniors": "活跃乐龄／长者", "Childcare": "托育", "Communication & trust": "沟通与信任",
    "Lifts & barrier-free access": "电梯与无障碍通道", "Online form": "在线表单", "Paper form": "纸质表单",
    "Town hall": "居民大会", "English": "英语", "Chinese": "华语", "Malay": "马来语", "Tamil": "泰米尔语",
    "March 2027": "2027 年 3 月",
    "What changed": "最新变化", "What is late": "延期事项", "Decisions needed": "待决策事项",
    "CE-01 (2027-04-06): Grant eligibility ruling. Change impact note drafted; sponsor decisions and actions await HC6.": "CE-01（2027-04-06）：拨款资格裁定。变更影响说明已起草，发起人决策与行动待 HC6 审批。",
    "CE-01 (2027-04-06): Grant eligibility ruling - effect on tranche conditions and eligible cost is set out in the change impact note.": "CE-01（2027-04-06）：拨款资格裁定。对分期拨款条件和合格成本的影响见变更影响说明。",
    "CE-02 (2027-04-06): Operator withdrawal. Change impact note drafted; sponsor decisions and actions await HC6.": "CE-02（2027-04-06）：运营方退出。变更影响说明已起草，发起人决策与行动待 HC6 审批。",
    "CE-02 (2027-04-06): Operator withdrawal - effect on tranche conditions and eligible cost is set out in the change impact note.": "CE-02（2027-04-06）：运营方退出。对分期拨款条件和合格成本的影响见变更影响说明。",
    "Asbestos (chrysotile) confirmed in level 2 ceiling boards; works in that zone stopped on 2027-03-03.": "二层天花板确认含有石棉（温石棉）；该区域施工已于 2027-03-03 停止。",
    "KHB estimate for removal: S$0.35-0.60M and 4-6 weeks; removal sequence not yet agreed.": "KHB 估计清除费用为 35 万至 60 万新元，需 4 至 6 周；清除顺序尚未商定。",
    "Roof slab needs strengthening for the rooftop garden; cost not yet estimated.": "屋顶花园需要加固屋面板，费用尚未估算。",
    "NRF Tranche 1 claim submitted on 2027-03-19.": "NRF 第一笔拨款申请已于 2027-03-19 提交。",
    "Resident consultation closed with 214 responses; summary still overdue.": "居民咨询已结束，共收到 214 份答复；汇总报告仍未提交。",
    "Physical progress 3.5% against 6.0% planned (KHB March report).": "实际工程进度为 3.5%，低于计划的 6.0%（KHB 三月报告）。",
    "Design completion 26% against 35% planned; Design stage 2 report (D04) overdue.": "设计完成度为 26%，低于计划的 35%；第二阶段设计报告（D04）已逾期。",
    "Temporary access plan for lifts (D07) overdue since 2027-03-31.": "电梯临时通行方案（D07）自 2027-03-31 起逾期。",
    "Active ageing operator appointment (D12) overdue; EOI extended to 2027-04-30 with 1 response.": "活跃乐龄中心运营方任命（D12）已逾期；意向征集延长至 2027-04-30，目前仅收到 1 份答复。",
    "February NRF report was submitted late (2027-03-16).": "NRF 二月报告于 2027-03-16 逾期提交。",
    "Closures: none agreed; KHB estimates 6-8 weeks delay if lift works cannot start June 2027. Options in what-if W2.": "关闭安排尚未获批；KHB 估计若电梯工程无法在 2027 年 6 月启动，将延误 6 至 8 周。备选方案见情景 W2。",
    "Contingency: is the ~S$1.18M headroom contingency, and who may draw on it?": "应急预备金：约 118 万新元的预算余量是否属于预备金，谁有权动用？",
    "Rooftop garden: keep or defer (no decision recorded).": "屋顶花园：保留还是推迟？目前没有决策记录。",
    "Completion: KHB practical completion 2028-12-31 vs brief 'fully open by Q4 2028'; programme not reconciled.": "竣工时间：KHB 的实际竣工日期为 2028-12-31，而简报要求在 2028 年第四季度全面开放；两份进度安排尚未协调。",
    "Baseline programme submitted on 2027-02-24; KHB baseline practical completion 2028-12-31.": "基线计划已于 2027-02-24 提交；KHB 基线中的实际竣工日期为 2028-12-31。",
    "Overall physical progress 3.5% against 6.0% planned.": "总体工程进度为 3.5%，低于计划的 6.0%。",
    "Design completion 26% against 35% planned; submittals approved 10 against 19.": "设计完成度为 26%，低于计划的 35%；19 份提交文件中有 10 份获批。",
    "Works in the level 2 west wing stopped on 2027-03-03 (asbestos); KHB estimates 4-6 weeks for removal.": "因发现石棉，二层西翼工程于 2027-03-03 停止；KHB 估计清除工作需 4 至 6 周。",
    "Cumulative contractor payment claims to March: S$985,000, which is 5.79% of the S$17.0M eligible-cost cap.": "截至三月，承包商累计申报付款 98.5 万新元，占 1,700 万新元合格成本上限的 5.79%。",
    "Eligible / ineligible split of expenditure: NOT FOUND in the data pack (food court and rooftop amenity are ineligible).": "资料包中未找到支出按合格与不合格成本划分的数据（餐饮区和屋顶设施不符合拨款资格）。",
    "Asbestos variation estimate S$0.35-0.60M: grant eligibility NOT FOUND as of this report.": "石棉变更估算费用为 35 万至 60 万新元；截至本报告，尚未找到其拨款资格的依据。",
    "T1 (contract award and baseline programme): claim submitted 2027-03-19.": "T1（合同授予及基线计划）：申请已于 2027-03-19 提交。",
    "T2 (rough-in complete AND signed operator agreements for ALL social service spaces): AT RISK - active ageing operator not appointed (1 EOI response; 3 required); agreement owner not assigned.": "T2（粗装工程完成，且所有社会服务空间均签署运营协议）：存在风险——活跃乐龄中心运营方尚未任命（仅 1 份意向答复，要求 3 份）；协议负责人也未指定。",
    "T3 (TOP for the whole facility): not yet due.": "T3（整座设施取得临时入伙证）：尚未到期。",
    "T4 (six months of operation and utilisation report): not yet due.": "T4（运营满六个月并提交使用情况报告）：尚未到期。",
    "R01 Grant conditions reduce eligible cost: cap S$17.0M; food court and rooftop amenity ineligible - L5 x I4 = 20; owner Finance Manager (M.L. Ong); trigger: Any cost classed ineligible, or eligible forecast above the S$17.0M cap": "R01 拨款条件减少合格成本：上限为 1,700 万新元，餐饮区和屋顶设施不合格；可能性 5 × 影响 4 = 20；负责人：财务经理 M.L. Ong；触发条件：任何成本被列为不合格，或合格成本预测超过上限。",
    "R06 Active ageing centre operator not found (one EOI response; policy needs three) - L4 x I5 = 20; owner Council PM (R. Shankar); trigger: EOI closes 30 Apr 2027 with fewer than three responses": "R06 未找到活跃乐龄中心运营方（仅一份意向答复，政策要求三份）；可能性 4 × 影响 5 = 20；负责人：理事会项目经理 R. Shankar；触发条件：2027-04-30 征集结束时答复不足三份。",
    "R08 Hazardous materials: asbestos (chrysotile) confirmed in level 2 west wing - L5 x I4 = 20; owner KHB (J. Lim) / Council PM for variation; trigger: Triggered 3 Mar 2027; further finds in other zones during soft-strip": "R08 危险材料：二层西翼已确认发现石棉（温石棉）；可能性 5 × 影响 4 = 20；负责人：KHB 的 J. Lim／负责变更的理事会项目经理；触发条件：2027-03-03 已触发，拆除其他区域时可能进一步发现。",
    "R11 Barrier-free access lost to levels 3-4 during 14-week east core lift closure - L4 x I5 = 20; owner Council PM (R. Shankar); trigger: East core closure approved without an accepted temporary access plan (D07 overdue)": "R11 东侧核心区电梯关闭 14 周期间，三、四层失去无障碍通道；可能性 4 × 影响 5 = 20；负责人：理事会项目经理 R. Shankar；触发条件：未批准临时通行方案便批准关闭东侧核心区（D07 已逾期）。",
    "R17 Tranche 2 (30%) delayed: needs signed operator agreements for ALL social service spaces - L4 x I5 = 20; owner Finance Manager (M.L. Ong); trigger: AAC agreement (D14) not signed by 2027-06-30 or still without owner": "R17 第二笔拨款（30%）延迟：所有社会服务空间均须签署运营协议；可能性 4 × 影响 5 = 20；负责人：财务经理 M.L. Ong；触发条件：AAC 协议（D14）在 2027-06-30 前未签署，或仍未指定负责人。",
    "CF01 Completion date - sources disagree, not resolved by the agent: brief: works within 22 months and fully open by Q4 2028; KHB baseline practical completion 2028-12-31; deliverable D22 due 2028-10-31. Completion after 31 December 2028 needs Fund approval.": "CF01 竣工日期存在来源冲突，智能体未自行裁定：简报要求 22 个月内完工并于 2028 年第四季度全面开放；KHB 基线的实际竣工日期为 2028-12-31；交付物 D22 截止日期为 2028-10-31。若晚于 2028-12-31 竣工，需基金批准。",
    "CF03 Grant amount - sources disagree, not resolved by the agent: brief: 60% of the S$18.5M budget is grant-funded; NRF: 60% of ELIGIBLE cost, capped at S$17.0M (maximum S$10.2M), food court and rooftop amenity ineligible.": "CF03 拨款金额存在来源冲突，智能体未自行裁定：简报称 1,850 万新元预算的 60% 由拨款资助；NRF 规定拨款为合格成本的 60%，合格成本上限 1,700 万新元（最高拨款 1,020 万新元），餐饮区和屋顶设施不合格。",
    "CF04 Budget headroom / contingency - sources disagree, not resolved by the agent: about S$1.18M remains after contract and fees, not decided as contingency; asbestos estimate S$0.35-0.60M.": "CF04 预算余量／预备金存在来源冲突，智能体未自行裁定：扣除合同和费用后约剩 118 万新元，尚未决定是否作为预备金；石棉处理估算费用为 35 万至 60 万新元。",
    "CF08 Contractor progress narrative vs numbers - sources disagree, not resolved by the agent: KHB writes 'broadly on programme' while physical progress is 3.5% against 6.0% planned.": "CF08 承包商的进度描述与数据不符，智能体未自行裁定：KHB 称总体符合进度计划，但实际工程进度为 3.5%，低于计划的 6.0%。"
  });

  const patterns = [
    [/^Sources → fact store \((\d+) verified facts\)$/, n => `来源 → 事实库（${n} 条已核验事实）`],
    [/^(.+?) \((\d+)\)$/, (label, n) => ZH[label] ? `${ZH[label]}（${n}）` : null],
    [/^Board \((\d+) items\)$/, n => `看板（${n} 项）`],
    [/^(created|updated|unchanged) (\d+)$/, (kind, n) => `${ZH[kind]} ${n}`],
    [/^(.+?) \((\d+) items\)$/, (label, n) => ZH[label] ? `${ZH[label]}（${n} 项）` : null],
    [/^Actions awaiting HC6 \((\d+)\)$/, n => `待 HC6 审批的行动（${n}）`],
    [/^Audit log \(latest (\d+) of (\d+)\)$/, (n, total) => `审计日志（最近 ${n} 条，共 ${total} 条）`],
    [/^Inject (CE-\d+)$/, id => `注入 ${id}`],
    [/^Last run (.+)$/, date => `上次运行：${date}`],
    [/^(\d+) items$/, n => `${n} 项`],
    [/^Run (.+): (.+)s, (\d+) tokens$/, (id, sec, tokens) => `运行 ${id}：${sec} 秒，${tokens} 个 Token`],
    [/^(HC\d) (approved|rejected) by (.+)$/, (id, decision, name) => `${id} 已由 ${name}${decision === "approved" ? "批准" : "拒绝"}`],
    [/^(CE-\d+) analysed$/, id => `${id} 已分析`],
    [/^(\d+) actions approved by (.+)$/, (n, who) => `${who} 已批准 ${n} 项行动`],
    [/^Per full run · (\d+) tokens · US\$(.+)$/, (n, cost) => `每次完整运行 · ${n} 个 Token · ${cost} 美元`],
    [/^Gap recall \((\d+)\/(\d+)\)$/, (a, b) => `缺口召回率（${a}/${b}）`],
    [/^Invention rate \((\d+)\/(\d+) claims\)$/, (a, b) => `无依据内容比例（${a}/${b} 条断言）`],
    [/^Critic catch rate \((\d+)\/(\d+)\)$/, (a, b) => `审查检出率（${a}/${b}）`],
    [/^Re-run stability · PM 2nd sync created (.+)$/, n => `重复运行稳定性 · 第二次同步创建 ${n} 项`],
    [/^Planted fault: (.+) → (.+)$/, (fault, result) => `植入故障：${ZH[fault] || fault} → ${ZH[result] || result}`],
    [/^NRF monthly progress report - (.+) \(as of (.+)\)$/, (month, date) => `NRF 月度进展报告——${ZH[month] || month}（截至 ${date}）`],
    [/^EDC exception update - as of (.+)$/, date => `EDC 例外情况更新——截至 ${date}`],
    [/^EDC (.+) \(as of (.+)\)$/, (name, date) => `EDC ${name}（截至 ${date}）`],
    [/^all\s+(\d+) claims traced; required sections present$/, n => `全部 ${n} 项断言可追溯；必需章节齐全`],
    [/^(\d+) claims traced; required sections present$/, n => `${n} 项断言可追溯；必需章节齐全`],
    [/^LLM off · deterministic · PM: (.+)$/, pm => `LLM 关闭 · 确定性模式 · PM：${pm}`],
    [/^LLM: DeepSeek · PM: (.+)$/, pm => `LLM：DeepSeek · PM：${pm}`],
    [/^Admin demo walkthrough · (\d+)\/(\d+) complete$/, (a, b) => `管理员演示引导 · 已完成 ${a}/${b}`],
    [/^Users \((\d+)\)$/, n => `用户（${n}）`],
    [/^(\d+) AI items on Jira$/, n => `Jira 上有 ${n} 个 AI 事项`],
    [/^Jira Cloud · (.+)$/, k => `Jira Cloud · ${k}`],
    [/^(.+)-managed$/, k => k === "next-gen" ? "团队管理项目" : k === "classic" ? "公司管理项目" : null],
    [/^(\d+) chunks · (\d+) facts$/, (a, b) => `${a} 个片段 · ${b} 条事实`],
    [/^(\d+) WBS · (\d+) gaps$/, (a, b) => `${a} 个 WBS · ${b} 个缺口`],
    [/^(\d+) board items$/, n => `${n} 个看板事项`],
    [/^(\d+) Q&A · (\d+) decisions$/, (a, b) => `${a} 次问答 · ${b} 条决策`],
    [/^(\d+) risks · (\d+) what-ifs$/, (a, b) => `${a} 项风险 · ${b} 个情景`],
    [/^(\d+) report versions$/, n => `${n} 个报告版本`],
    [/^(\d+) draft\(s\) STOPPED$/, n => `${n} 份草稿被阻止`],
    [/^(\d+) passed$/, n => `${n} 份通过`],
    [/^(\d+) released$/, n => `${n} 份已发布`],
    [/^(\d+) injected$/, n => `已注入 ${n} 个`],
    [/^(\d+) stale items$/, n => `${n} 项已过期`],
    [/^(\d+) waiting$/, n => `${n} 项待处理`],
    [/^by (.+)$/, who => `审批人：${who}`],
    [/^hand-off ×(\d+)$/, n => `交接 ×${n}`],
    [/^Level (\d+)$/, n => `第 ${n} 层`],
    [/^(\d+) account\(s\) · (\d+) checkpoint\(s\)$/, (a, b) => `${a} 个账号 · ${b} 个检查点`],
    [/^Audit log · (\d+) approvals · (\d+) blocked \/ rejected attempts · append-only$/, (a, b) => `审计日志 · ${a} 次审批 · ${b} 次被拦截／拒绝 · 只追加`],
    [/^Your role \((.+)\) cannot open this page\.$/, r => `当前角色（${ZH[r] || r}）无权打开此页面。`],
    [/^Role '(.+)' is not permitted: (.+)$/, (r, p) => `角色“${ZH[r] || r}”无此权限：${p}`],
    [/^Not permitted for (.+): (.+)$/, (r, p) => `${ZH[r] || r} 无此权限：${p}`],
  ];

  let language;
  try { language = localStorage.getItem("hch-language") === "zh" ? "zh" : "en"; }
  catch (_) { language = "en"; }
  const savedText = new WeakMap();
  const savedAttrs = new WeakMap();
  const untouched = node => node.parentElement && node.parentElement.closest("script,style,pre,.cite,[data-no-translate]");

  function translate(value) {
    const match = /^(\s*)([\s\S]*?)(\s*)$/.exec(value);
    const source = match[2];
    if (!source) return value;
    let result = ZH[source];
    if (result === undefined) {
      for (const [pattern, format] of patterns) {
        const found = pattern.exec(source);
        if (found) { result = format(...found.slice(1)); if (result !== null) break; }
      }
    }
    return match[1] + (result === undefined || result === null ? source : result) + match[3];
  }

  function localizeText(node) {
    if (untouched(node)) return;
    let saved = savedText.get(node);
    if (!saved || node.nodeValue !== saved.rendered) saved = { original: node.nodeValue, rendered: node.nodeValue };
    const output = language === "zh" ? translate(saved.original) : saved.original;
    saved.rendered = output;
    savedText.set(node, saved);
    if (node.nodeValue !== output) node.nodeValue = output;
  }

  function localizeAttrs(el) {
    if (el.closest("[data-no-translate]")) return;
    let saved = savedAttrs.get(el) || {};
    for (const name of ["placeholder", "title", "aria-label"]) {
      if (!el.hasAttribute(name)) continue;
      const current = el.getAttribute(name);
      if (!saved[name] || current !== saved[name].rendered) saved[name] = { original: current, rendered: current };
      const output = language === "zh" ? translate(saved[name].original) : saved[name].original;
      saved[name].rendered = output;
      if (current !== output) el.setAttribute(name, output);
    }
    savedAttrs.set(el, saved);
  }

  function localize(root = document.body) {
    if (root.nodeType === Node.TEXT_NODE) return localizeText(root);
    if (root.nodeType !== Node.ELEMENT_NODE) return;
    localizeAttrs(root);
    root.querySelectorAll("[placeholder],[title],[aria-label]").forEach(localizeAttrs);
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) localizeText(walker.currentNode);
  }

  function setLanguage(next) {
    const changed = language !== (next === "zh" ? "zh" : "en");
    language = next === "zh" ? "zh" : "en";
    document.documentElement.lang = language === "zh" ? "zh-CN" : "en";
    for (const code of ["zh", "en"]) {
      const button = document.getElementById(`lang-${code}`);
      button.setAttribute("aria-pressed", String(code === language));
    }
    try { localStorage.setItem("hch-language", language); } catch (_) {}
    localize();
    if (changed) window.dispatchEvent(new Event("hch-languagechange"));
  }

  function addTranslations(pairs) {
    for (const [source, translated] of Object.entries(pairs)) {
      if (typeof translated === "string" && translated !== source && translate(source) === source) {
        ZH[source] = translated;
      }
    }
    if (language === "zh") localize();
  }

  document.getElementById("lang-zh").addEventListener("click", () => setLanguage("zh"));
  document.getElementById("lang-en").addEventListener("click", () => setLanguage("en"));
  const observer = new MutationObserver(records => {
    for (const record of records) {
      if (record.type === "characterData") localizeText(record.target);
      else if (record.type === "attributes") localizeAttrs(record.target);
      else for (const node of record.addedNodes) localize(node);
    }
  });
  observer.observe(document.body, { childList: true, characterData: true, attributes: true,
    attributeFilter: ["placeholder", "title", "aria-label"], subtree: true });
  setLanguage(language);
  window.HCH_I18N = { get language() { return language; }, setLanguage, translate, addTranslations };
})();
