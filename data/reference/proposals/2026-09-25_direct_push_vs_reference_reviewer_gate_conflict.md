# 提案：CLAUDE.md「直推 main 标准动作」与「data/reference/** 走 reviewer」互相矛盾

**状态**：待 Andy 裁；在他采纳之前不是规矩，任何会话不得引用本文件作为直推 `data/reference/**` 的依据。
**起因**：T-0925-27（监测「合并闸」不合格，追查 `audits/monitor/2026-09-25.md` 第 6 项）。
**写这份提案而不是自己改 CLAUDE.md 的原因**：本提案要豁免/收紧的路径（`data/reference/DATA_CONTRACTS.md`）与我（ops）当天提交的路径直接重合（`336ed617`、`d8953b7d`），按 CLAUDE.md「改宪法的判据」利益冲突规则——「这条规矩豁免/开放的路径，与作者当日提交的路径，有没有交集？有 → 不许自己合，写成提案放 `data/reference/proposals/` 等 Andy 裁」——这条必须留给 Andy，不能我自己拍板。

## 证据：三个提交，全部真实绕过了 reviewer 档，且不是个人失误

`audits/monitor/2026-09-25.md` 第 6 项报了 4 个提交，逐条核实：

| 提交 | 改动路径 | 判据 | 核实结论 |
|---|---|---|---|
| `c0e85487` | `data/reference/METRIC_SOURCES.md`、`Fluxus_Brand/voice/raw/…` | reviewer（`data/reference/` 非 incidents） | **真绕过，低风险**——METRIC_SOURCES 加一行 O'Neil 口径登记，未走 branch-review。关联的 `T-0923-132`（claire 的前端视觉核对任务）、`T-0924-122`（数据哨兵巡检）都只是碰巧在 `result:` 字段留下了这个 sha（收工时记录当时的 main HEAD），两者都不是审核这条 METRIC_SOURCES 改动的任务，不构成审核证据 |
| `d8953b7d` | `data/reference/DATA_CONTRACTS.md` | reviewer | **真绕过，低风险**——UI Claire 答复 §七 契约行（YTD 口径回执），关联 `T-0924-81`（`gate: none`，从未跑过 `taskboard.py gate` 重算）|
| `336ed617` | `data/reference/DATA_CONTRACTS.md` | reviewer | **真绕过，低风险**——同一条 YTD 口径讨论的开场契约行（OPS 发现问题时记的），无任务号，直推 |
| `e89a2842` | `Fluxus_Brand/ops/tools/x_watch/fetch.py`、`data/content/x_watch/README.md` | reviewer（默认档） | **误报，非回退**——见下节 |

`d8953b7d`/`336ed617` 与 09-24 的 `d3f9865a`（T-0924-41 判定为「低风险非回退」的 Vercel P0 紧急记录）是**同一个形状连续第 2/3 次出现**：Andy 直接派下的追问 / 紧急发现，写手当场把结论/事实记进 `DATA_CONTRACTS.md` §七，全程没有走 reviewer。

## 根因：宪法内部两条规矩互相矛盾

**CLAUDE.md「直推 main 的标准动作（08-23 v2）」原文**：
> 任何会话要把 **docs/契约行/收藏/素材小改**直推 main 时，永不在共享主树上 commit。统一走临时树……

**契约行 = `DATA_CONTRACTS.md` §七的条目**——这段文字明确把「契约行小改」列为可以用临时树直推 main 的东西，只字未提要先走 reviewer gate。

**CLAUDE.md「safe-merge：能自己合的就别找人」+「碰到其他路径」两节（OPS 2026-09-21 收紧后）**：
> 白名单…**但 `data/reference/**` 除外**（放的是规矩文档：DATA_CONTRACTS、METRIC_SOURCES、proposals，改规矩不自合，走 reviewer），其中只有 `data/reference/incidents/**` 仍可直接合

`DATA_CONTRACTS.md`、`METRIC_SOURCES.md` 明确点名要走 reviewer，`incidents/` 才是例外。

**两条谁都没提对方**：「直推 main 标准动作」那段写于 08-23，早于 09-21 的收紧；09-21 收紧时只改了「safe-merge」节的白名单描述，没有回头修「直推 main 标准动作」里举的例子（它举的例子原文就是「docs/**契约行**/收藏/素材」）。结果是：任何交互会话读「直推 main 标准动作」一节，会合理地认为契约行可以直接用那套流程推 main——这正是三次实测出现的行为，不是三次巧合的个人疏忽。

`c0e85487` 是同一根因的姊妹案例：`METRIC_SOURCES.md` 同样被「规矩文档记口径事实」的直觉当成了可以直推的档案（类比 `voice/raw`——同一条 commit 恰好也碰了 `voice/raw`，那部分是真的豁免）。

## 待 Andy 裁的问题

选一个（或给别的方向）：

**A. 改「直推 main 标准动作」，明确排除 `data/reference/**`（incidents 除外）**——契约行如果要直推，先必须过 reviewer；紧急/Andy 亲自派下的追问另开小路径（比如走 `data/reference/incidents/` 记录，或者给「Andy 当场追问的即时回执」单独开一条 none 档，类比 `incidents/`）。

**B. 反过来把 `DATA_CONTRACTS.md`/`METRIC_SOURCES.md` 的追加式记账行（§七 契约行、口径登记）挪回 none 档**，理由类比 `material_inbox.md`/`receipts.md`（append-only 记账不算「改规矩」）——但 T-0924-41 已经注意到这样会削弱「改口径需要复核」的保护，如果 §七 混杂了纯记事实的回执和真正的口径裁决，需要先把两者拆开才能安全下放权限。

**C. 维持现状（reviewer 档不变），但把「直推 main 标准动作」那段的例子明确改成「docs/收藏/素材小改（不含 data/reference/**）」**，同时给「Andy 亲自派下、要求当场记录」的场景一条低摩擦路径（比如：`taskboard.py gate` 判 reviewer 时，若任务 `andy:` 字段非空则自动降级—— 这条 `check_merge_gate::covers()` 09-24 已经实现了同等语义，只是「先直推再回填 andy 字段」这个顺序仍然会被判违规，需要倒过来：先有 `andy:` 字段（或先开单），再推）。

## 附：`e89a2842` 是检测误报，不是真回退（已核实，不需要 Andy 裁）

- `e89a2842` 是 `T-0924-104`（x-watch 复核任务）复核第 1 轮反馈后的修正提交。
- `T-0924-104` **确实拿到过 PASS**：ops 仓 git 历史里有提交 `8bbc60c task: review PASS T-0924-104`。
- 后来该任务因为验收里有一条「需下一班日报产出后才能观测」的条目物理上验不了，被 `block_if_claimed` 把 `review` 字段整体覆盖成 `BLOCKED …（复核 PASS）`——原 PASS 语义还留在文字里，但不再是 `startswith("PASS")`。
- `monitor.py::_passed_task_ids` 的兜底（扫 git log 里 `task: review PASS <id>` 格式的提交）本该兜住这种情况，但 `e89a2842` 自己的 commit message 没提任务号，它的父提交 `bc0771ce9`（提了 `T-0924-104`）与它相隔 361 秒——超过 `_CHAIN_MAX_SECONDS`（120 秒，专门用来区分「同一次 push」和「不相关的后续改动」，`test_merge_gate_chain_does_not_bridge_distant_commits` 明确测的就是「超过窗口不该被链式豁免带过」，回测案例 `b50f7944` 是真回退）。
- **不建议放宽 `_CHAIN_MAX_SECONDS`**：跑一轮 pytest+改代码通常要几分钟，放宽窗口会连带模糊掉「同一次 push」和「隔了一段真实工作时间的后续改动」的边界，削弱 `b50f7944` 那类真回退的检测力。这次的正确修法是**写 commit message 的人自己记得带上任务号**，不是改判据——记进 `agents/ops/memory/methods.md`（见下）。

## 下一步

- Andy 裁 A/B/C 任一方向（或给别的裁决）后，由不当日提交 `data/reference/**` 的会话/复核员执行修订，走 `taskboard.py gate` 判 reviewer。
- 在此之前：任何会话往 `DATA_CONTRACTS.md`/`METRIC_SOURCES.md` 追加契约行，按现行（未修订）的 CLAUDE.md 字面走 reviewer——即使这会让「Andy 当场要求记一笔」变慢，也不要援引本提案自行放行。
