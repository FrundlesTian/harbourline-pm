# Harbourline AI PM

面向 Harbourline Community Hub Refurbishment 的项目管理演示系统，包含规划、PM 工具同步、证据问答、风险分析、报告、变更管理和人工治理检查点。后端使用 Python 标准库与 SQLite，前端使用原生 HTML/JS，无需安装 Python 包。

A project management demo for the Harbourline Community Hub Refurbishment. It covers planning, PM tool sync, evidence based Q&A, risk analysis, reporting, change handling, and human governance checkpoints. It uses Python's standard library, SQLite, and plain HTML/JS; no Python packages are required.

## 中文

### 启动

需要 Python 3.9+。在项目根目录运行：

```bash
./run.sh
# 等价命令：python3 server.py
```

打开 <http://127.0.0.1:8000>，选择身份即可进入，右上角可退出登录并切换身份。首次启动会导入资料并生成演示数据；配置了 LLM 密钥时，首次生成可能需要几分钟。默认使用本地模拟看板，不需要 API 密钥。此演示系统不验证密码，任何访问者都能选择任意可用身份。
身份选择页每次打开都默认显示英文；进入系统后仍可手动切换中文。

身份选择页的 **重置** 会先预览影响范围。确认后清除本地演示数据、审批、决策和自定义身份，恢复内置基线；审计历史保留。如果已配置 Jira 凭据，重置还会删除所配置 Jira 项目中的**全部事项**（包括非本系统创建的事项），需要输入项目键确认。

| 账号 | 角色 |
| --- | --- |
| `admin` | 系统管理员 / System Admin |
| `pm` | 项目经理 / Project Manager |
| `leader` | 组长 / Group Leader |
| `supervisor` | 监督员 / Supervisor |

### 可选配置与评估

如果尚无 `.env`，可将 `.env.example` 复制为 `.env`，按需填写 `GEMINI_API_KEY` 或 `DEEPSEEK_API_KEY`。未配置密钥时使用确定性基线；设置 `HCH_GENERATION=baseline` 可强制使用基线。配置 `JIRA_BASE_URL`、`JIRA_EMAIL` 和 `JIRA_API_TOKEN` 后可连接 Jira Cloud；写入前需在界面中预览并审批。端口可用 `HCH_PORT` 修改。

```bash
cp -n .env.example .env
python3 eval/run_eval.py --no-llm
```

评估结果写入 `eval/results/latest.md` 和 `eval/results/latest.json`。评估默认使用独立临时数据库和模拟看板。

## English

### Run

Requires Python 3.9+. From the project root:

```bash
./run.sh
# Equivalent: python3 server.py
```

Open <http://127.0.0.1:8000> and select an identity. Use **Sign out** in the upper right to leave or switch identities. The first launch imports source material and generates demo data; generation may take a few minutes when an LLM key is configured. The local mock board works without API keys. This demo does not verify passwords: anyone with access can select any active identity.
The identity selection page opens in English each time; you can switch to Chinese after entering the app.

**Reset demo** on the identity selection page previews the scope before restoring the bundled baseline. It clears local demo data, approvals, decisions, and custom identities while retaining audit history. When Jira credentials are configured, it also deletes **every issue in the configured Jira project**, including issues created outside this system; confirmation requires typing the project key.

### Optional setup and evaluation

If `.env` does not exist, copy `.env.example` to `.env` and optionally set `GEMINI_API_KEY` or `DEEPSEEK_API_KEY`. Without a key, the app uses its deterministic baseline; set `HCH_GENERATION=baseline` to force it. Set `JIRA_BASE_URL`, `JIRA_EMAIL`, and `JIRA_API_TOKEN` to connect to Jira Cloud; preview and approval are required before writing. Use `HCH_PORT` to change the port.

```bash
cp -n .env.example .env
python3 eval/run_eval.py --no-llm
```

Results are saved to `eval/results/latest.md` and `eval/results/latest.json`. Evaluation uses a separate temporary database and the mock board by default.

## 文档 / Documentation

- [设计与架构 / Design and architecture](docs/design/design_document.md)
- [评估报告 / Evaluation report](docs/evaluation/evaluation_report.md)
- [治理日志 / Governance log](docs/governance/governance_log.md)
