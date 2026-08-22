# TEAM.md — 会话花名册（唯一权威）

> **本表是「谁是谁、谁管什么」的唯一权威。** 会话的自述不是权威（08-21 已出过三次认领事故）。
> 任何会话开工前先在这里认领身份；对不上号的工作先停下来问 Andy。
> **「完成」的定义：合进 main 且 Andy 能点开看到。** 未 push 的 commit 不算完成。
> 架构说明见手册：Fluxus 会话联邦（artifact，链接在 memory `project_session_federation`）。

## 花名册（Andy 2026-08-22 命名）

| 名字（新会话用 `claude -n "<名字>"` 启动） | 职责 | 文件边界（只在边界内写） | 分支习惯 |
|---|---|---|---|
| **UI Claire** | Dashboard 前端 UI | `frontend/` | `feat/*` 短分支，合并即删 |
| **DATA ALEX** | 数据管道 + 数据契约 | `pipeline/screeners\|tickers\|adapters/`、`data/output/`、`data/history/`、`data/reference/DATA_CONTRACTS.md`（含 §七）、`DATA_RELIABILITY.md` 正文 | 数据直推 main；代码走 `feat/*` |
| **RND Linda** | 模型与量化研究（correction_risk / regime_ledger / turin / GEX / 交易数据分析） | 模型线文件；`data/history/regime_ledger.csv` 唯一写入方 | `feat/*` |
| **Marketing Steve** | 品牌、内容、视觉、课程（含 Substack/X/fintwit 调研/数据艺术） | `Fluxus_Brand/`、`Fluxus_Substack/`、`Fluxus_Marketing_Visual_Design/`、`visuals/` | 视觉走 `design/*`；文稿小改直推 main |
| **Nighty Zac** | 夜间自学（04:30 JST 定时窗口内） | `data/research/night_reports/`；其余只读 | `auto/night-YYYYMMDD-*`，push 即备份，不合 main |
| **Plumber Joe** | 可靠性巡检 + 数据研究 | `pipeline/tools/audit_*` 及测试、`data/reference/incidents/`、`data/research/` | `auto/*`，发现只报不修 |
| **OPS**（待 Andy 命名） | 架构与秩序：TEAM.md/CLAUDE.md、大扫除、routines、跨线协调 | `TEAM.md`、`CLAUDE.md`、`.claude/agents/`、`data/research/repo_health/` | 小改直推 main |

## 一条线可以有多个会话

线 = 职责 + 文件边界；会话 = 这条线上的工人，可以有好几个（例如 Marketing Steve 名下同时有日更 routine、Substack 写作、fintwit 调研三个会话）。唯一的铁规矩：

> **同一条线、同一时刻，只有一个会话在「执笔」（写文件）；其余会话只读。**
> 两个会话同时写同一条线的文件 = 已知事故形状（08 月两会话各往同一 CSV 追加了不同的最后一行）。

## 会话归属对照（2026-08-22 盘点 Andy 的常用会话）

- **UI Claire**：Fluxus Dashboard前端UI
- **DATA ALEX**：Dashboard数据端处理+TSF对比
- **RND Linda**：Turkey/Turin correction risk、SPX Gex和模型、交易数据分析
- **Marketing Steve**：营销每日/周报 routine、Digital writing (memo/Substack/X)、Top 100 fintwit 研究调查、课程整理和设计、课程自动视频生成工作流、市场视觉设计、2026H1交易数据艺术可视化、X bookmark pipeline（挂起）
- **Nighty Zac**：dashboard夜间自学 routine、Fluxus data night study
- **Plumber Joe**：data plumbing AM routine
- **OPS**：ClaudeCode 多Agent任务管理架构
- **联邦之外（不属于本仓库任何线，不写本仓库文件）**：健身日报/健身周报、皮质醇×2（家在 `~/Documents/Fitness-2026`）；IB panel Mac mini server 迁移、IB panel+ORB scanner（家在 `~/ibkr_order_panel`，那是另一个联邦）

## 资料区与单一写入方

- 未列入的目录（`JeffSun_Wiki/`、`PrimeTrading_Obsidian/`、`Fluxus_References/`、`_source_material/`、`SqueezeMetrics/` 等）＝**资料区**：所有线只读；整理需 Andy 发起。
- 每个数据文件只有一条线有写入权：
  - `data/output/`、`data/history/`（除 regime_ledger）→ DATA ALEX
  - `data/history/regime_ledger.csv` → RND Linda
  - `data/reference/incidents/`、`DATA_RELIABILITY.md` §六 追加行 → Plumber Joe
  - `data/research/night_reports/` → Nighty Zac
  - `data/research/repo_health/` → OPS（含云端 routine）

## 通信纪律

1. **跨线请求/答复：先在 `data/reference/DATA_CONTRACTS.md` §七 写一行，再发消息。** 契约行是投递，消息只是门铃（「§七 有你的新行」）。
2. 契约行里引用的事实**必须带日期**——把曾经为真当现在为真是 08-21 三次事故的共同形状。
3. 收到发错的消息：先把内容记进 §七，再回「不是我」。
