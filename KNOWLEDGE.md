# KNOWLEDGE.md — 真理地图（哪类问题去哪查）

> Andy 2026-08-27 立项：「目前还没有完整 absolute truth 的资料库」——对。真理**不集中迁移**（搬家=砸断全仓引用），但从今天起有这张地图。每个会话开工遇到「我该信哪份文件」时，答案从这里出。无人值守读权威版一律 `git show origin/main:<path>`（例外：内容台五件套以主树工作区为准，见 CLAUDE.md）。

## 权威层（规矩，冲突时以此为准；改动需 Andy 批）
| 文件 | 管什么 | 更新机制 |
|---|---|---|
| `CLAUDE.md` | 全会话宪法（git/通讯/回执/safe-merge/风格） | OPS 经 Andy 批后改 |
| `TEAM.md` | 花名册/文件边界/单一写入方 | OPS |
| `NOW.md` | Andy 的优先级/关卡/停做清单（只约束 Andy） | Andy 手改 + OPS 代记 |
| `PROJECTS.md` | 生意档案 P0–P7 / 生产线 | OPS |
| `data/reference/DATA_CONTRACTS.md` | 跨线契约与裁决（§七/§12…） | append-only 公箱 |
| `data/reference/DATA_RELIABILITY.md` | 数据可靠性机制 | ALEX 正文 / Joe §六追行 |
| `data/reference/RESEARCH_PROTOCOL.md` | 研究预注册/holdout 协议 | 研究线 |

## 结论层（量过的事实；引用必须带日期——结论会过期）
- `data/research/claims/claims.jsonl` — 研究结论台账（gate_basis / waiver / evidence_grade）
- `data/research/<课题>_*/report|results.md` — 各轮实测原始报告
- `data/research/night_reports/*.md` — Zac 晨报（含 NULL 结果）；`INBOX.md` = 收件与裁决
- `data/growth/weekly/*.md` + `metrics.csv` — 会员/收入的量化事实（PII 在 `private/` 不入库）

## 教训层（防坑账；同形状事故先查这里）
- memory/`MEMORY.md` 索引 + pitfall_* — 各会话共享的防坑账
- `data/reference/incidents/` — 事故档（else 重绑/测试写真树/群发系列…）

## 台账层（append-only 流水）
- `data/content/posts.csv`（发布记录·Steve）· `Fluxus_Receipts/`（交易收据）· `Fluxus_Brand/ops/material_inbox.md`（素材箱）

## 资料层（只读引用区，所有线不改）
- `JeffSun_Wiki/` · `Fluxus_References/` · `SqueezeMetrics/` · `_source_material/` · `data/output/library/`（对外 Library）· `data/research/collection.md`（收藏夹判定归档）

## 数字权威表（Andy 2026-08-27 立：「一个 agent 更新了另一个看不到还去 quote 旧的——完全避免」）
**每个业务数字只有一个家。引用任何数字前必须 `git show origin/main:` 现场读权威源，禁止转抄二手——包括你自己 memory 里的、昨天对话里的、别的文档里的。** 读到的与你记忆不符时，以权威源为准并顺手更正你正要发的内容；发现权威源本身过期，修权威源而不是在别处写新数。

| 数字 | 唯一权威源 | 读法 |
|---|---|---|
| 会员数 / MRR / Discord 人数 | `data/growth/metrics.csv` | 每列取**最后一个非空值**（notes 列带口径） |
| 会员明细 / 身份合并 | `data/growth/private/` 最新 members_master | PII 不出 private |
| 发布记录 / views | `data/content/posts.csv` | 按 post_id 行 |
| 研究结论 | `data/research/claims/claims.jsonl` | 引用带日期与 evidence_grade |
| 交易绩效 | `data/portfolio/` performance_review 产物 | H1 +90.5% 等口径以此为准 |
| 关卡进度 | 日推第一行 / NOW.md 🎮 节 | |

## 还不存在的（别假装有）
- 全文检索/向量索引：没有，检索靠 grep + 本地图。哪天真需要再立项，先过 MVP 闸。
