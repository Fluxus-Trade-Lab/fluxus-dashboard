# 合并闸裁决：宪法白名单 vs 编队设计（2026-09-21 JST）

- **日期**：2026-09-21（JST）
- **记录人**：OPS（交互会话中由 Andy 回答问卷；本文件由 T-0921-115 修复第 1 轮补录）
- **形式**：问卷单选

## 问卷问题（逐字）

> 宪法白名单和新编队的合并闸对不上：改 dashboard 数据文件（data/output、data/history，非删除），宪法白名单要求留分支等复核；你 09-18 批的编队设计允许 ALEX 直接合（有数据闸 CI 把关）。两本规矩各说各的，要统一成哪个？

## 选项（逐字）

1. 以编队设计为准 (推荐)
2. ⚠️ 第二个选项的逐字文本本记录人未取得，待 OPS 从问卷会话原文补入；在补入之前不得据本文件推断其内容。

## Andy 的选择

**「以编队设计为准 (推荐)」**

## 解释口径（OPS 复核定，T-0921-115 修复第 1 轮）

「编队设计」＝ spec `docs/superpowers/specs/2026-09-18-agent-fleet-v2-design.md` §8 的 gate 表，**不是** fluxus-ops `tools/gate.py` 当时的默认行为（旧 `decide()` 对 spec 没列的路径默认判 none，比 spec 宽）。据此：

- 只有 spec §8 none 档明列的路径（「data/、data/research/、night_reports/、tests/、material_inbox、agent 自己的 memory 与 runs」，非删除）可直接合；
- spec 没列的路径一律走复核员（reviewer）；
- 删数据走 Andy（needs-andy）；
- 问题里说的「数据闸 CI 把关」如实是**事后闸**：`schema_snapshot --check`、`audit_archives` 在数据管线班与周审计里跑，push 时不跑。

落地：`CLAUDE.md`「safe-merge：能自己合的就别找人」节；fluxus-ops `tools/gate.py`（未列路径默认 reviewer）。
