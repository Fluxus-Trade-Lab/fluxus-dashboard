# 合并闸裁决：宪法白名单 vs 编队设计（2026-09-21 JST）

- **日期**：2026-09-21（JST）
- **记录人**：OPS（交互会话中由 Andy 回答问卷；本文件由 T-0921-115 修复第 1 轮补录）
- **形式**：问卷单选

## 问卷问题（逐字）

> 宪法白名单和新编队的合并闸对不上：改 dashboard 数据文件（data/output、data/history，非删除），宪法白名单要求留分支等复核；你 09-18 批的编队设计允许 ALEX 直接合（有数据闸 CI 把关）。两本规矩各说各的，要统一成哪个？

## 选项（逐字）

1. **以编队设计为准 (推荐)**——宪法改成「谁能直接合以 gate.py 判定为准」，ALEX 修数据不用等复核，守住 JST 08:30 死线；删数据仍要复核。数据正确性靠 schema 基线/归档审计这些 CI 闸。
2. **以宪法白名单为准**——把 gate.py 收紧：数据文件改动一律走复核员。更稳，但数据急修多一道复核（平均几分钟到十几分钟）。

> **OPS 注记**：选项一说明里的「以 gate.py 判定为准」「删数据仍要复核」「CI 闸」三处，事后复核发现与代码不符（gate.py 默认过宽、删数据实际走 Andy、CI 闸是事后闸），条文已按 spec §8 与实际代码更正；Andy 选的本意是「ALEX 修数据文件不用等复核」，这一点保留。

## Andy 的选择

**「以编队设计为准 (推荐)」**

## 解释口径（OPS 复核定，T-0921-115 修复第 1 轮）

「编队设计」＝ spec `docs/superpowers/specs/2026-09-18-agent-fleet-v2-design.md` §8 的 gate 表，**不是** fluxus-ops `tools/gate.py` 当时的默认行为（旧 `decide()` 对 spec 没列的路径默认判 none，比 spec 宽）。据此：

- 只有 spec §8 none 档明列的路径（「data/、data/research/、night_reports/、tests/、material_inbox、agent 自己的 memory 与 runs」，非删除）可直接合；
- spec 没列的路径一律走复核员（reviewer）；
- 删数据走 Andy（needs-andy）；
- 问题里说的「数据闸 CI 把关」如实是**事后闸**：`schema_snapshot --check`、`audit_archives` 在数据管线班与周审计里跑，push 时不跑。

## OPS 在 spec 基础上的收紧（2026-09-21）

`data/reference/**` 非删除改动判 **reviewer**，唯一例外 `data/reference/incidents/**` 判 none（它在宪法原白名单里）。理由：spec §8 原文写的是 `data/`，但 `data/reference/` 下放的是规矩文档（DATA_CONTRACTS、METRIC_SOURCES、proposals），改规矩不该自合。**这是 OPS 在 spec 基础上的收紧，理由如上，比 Andy 所选更严，不更宽。**

落地：`CLAUDE.md`「safe-merge：能自己合的就别找人」节；fluxus-ops `tools/gate.py`（未列路径默认 reviewer）。
