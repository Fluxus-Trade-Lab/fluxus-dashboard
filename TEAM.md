# TEAM.md — 会话花名册（唯一权威）

> **本表是「谁是谁、谁管什么」的唯一权威。** 会话的自述不是权威（08-21 已出过三次认领事故）。
> 任何会话开工前先在这里认领身份；对不上号的工作先停下来问 Andy。
> **「完成」的定义：合进 main 且 Andy 能点开看到。** 未 push 的 commit 不算完成。
> 架构说明见手册：Fluxus 会话联邦（artifact，链接在 memory `project_session_federation`）。

## 花名册

| 线名（会话启动用 `claude -n <线名>`） | 职责 | 文件边界（只在边界内写） | 分支习惯 |
|---|---|---|---|
| `frontend-ui` | Dashboard 前端 UI | `frontend/` | `feat/*` 短分支，合并即删 |
| `data-pipeline` | 数据管道 + 数据契约 | `pipeline/screeners\|tickers\|adapters/`、`data/output/`、`data/history/`、`data/reference/DATA_CONTRACTS.md`（含 §七）、`DATA_RELIABILITY.md` 正文 | 数据直推 main；代码走 `feat/*` |
| `model-rnd` | 模型研发（correction_risk / regime_ledger / turin 线） | 模型线文件；`data/history/regime_ledger.csv` 唯一写入方 | `feat/*` |
| `marketing` | 品牌与内容（含视觉设计） | `Fluxus_Brand/`、`Fluxus_Substack/`、`Fluxus_Marketing_Visual_Design/`、`visuals/` | 视觉走 `design/*`；文稿小改直推 main |
| `night-study` | 夜间自学（04:30 JST 定时） | `data/research/night_reports/`；其余只读 | `auto/night-YYYYMMDD-*`，push 即备份，不合 main |
| `plumbing` | 可靠性巡检 + 研究 | `pipeline/tools/audit_*` 及测试、`data/reference/incidents/`、`data/research/` | `auto/*`，发现只报不修 |

- 未列入的目录（`JeffSun_Wiki/`、`PrimeTrading_Obsidian/`、`Fluxus_References/`、`_source_material/`、`SqueezeMetrics/` 等）＝**资料区**：所有线只读；整理需 Andy 发起。
- 健身 / 皮质醇等生活类定时会话不属于本仓库任何线，不应写本仓库文件（健身仓库在 `~/Documents/Fitness-2026`）。

## 单一写入方规则

每个数据文件只有一条线有写入权，其他线一律只读（08 月已发生两线同时追加同一 CSV 的静默冲突）：

- `data/output/`、`data/history/`（除 regime_ledger）→ `data-pipeline`
- `data/history/regime_ledger.csv` → `model-rnd`
- `data/reference/incidents/`、`DATA_RELIABILITY.md` §六 追加行 → `plumbing`
- `data/research/night_reports/` → `night-study`

## 通信纪律

1. **跨线请求/答复：先在 `data/reference/DATA_CONTRACTS.md` §七 写一行，再发消息。** 契约行是投递，消息只是门铃（「§七 有你的新行」）。
2. 契约行里引用的事实**必须带日期**——把曾经为真当现在为真是 08-21 三次事故的共同形状。
3. 收到发错的消息：先把内容记进 §七，再回「不是我」。
