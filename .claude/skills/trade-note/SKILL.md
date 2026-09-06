---
name: trade-note
description: 把 Andy 对某一笔交易的想法落进仓库（data/portfolio/trade_notes/）。凡他讲到任何一笔具体交易的进出理由、悔手、复盘感想——「记一笔」「这笔我当时看到…」「那笔就是 fomo 了」「XX 那单应该…」，甚至只是聊天里带过一句对某票某单的评价——都用本 skill 当场落档，不许让那句话只活在对话框或 Discord 里。周复盘（weekly-review）靠读这些条目才能选出「本周最好的一笔」，漏记一条它就瞎一格。
when_to_use: 记一笔、trade note、交易笔记、这笔交易我、那单、复盘某笔、对持仓/已平仓的任何第一人称评价。不触发：盘面评论（那归 daily-recap 的原话收集）、组合层面数字（归 tracker）。
---

# trade-note — 每笔交易的思考，从 Discord 和对话框搬进仓库

> 立项出处：`Fluxus_Brand/ops/briefs/2026-09-06_review_mechanism_reconcile.md`（Andy 四条裁决：顺序 #1→#2→#3、五字段、skills 归 OPS、OPS 开写本 skill）。
> 它是复盘三层机制的地基：trade-note → weekly-review → monthly-review。

## 五个字段（Andy 亲批，「少一个你就不填，多一个你也不填」）

`ticker · 开仓日 · setup · 我看到什么 · 现在会怎么改`

- **setup** 用他 2026-09-06 亲定的词汇表（`data/research/setup_labeling/SETUP_DEFINITIONS.md`）：`Breakout` / `Undercut & Rally` / `30m Pivot`；对不上就照实另起名，不硬塞。
- **「我看到什么」「现在会怎么改」是判断——只能是他的原话**（daily-recap C 法同源）：润色限补主语、接句、标点；他没说的字段留 `⟨Andy⟩`，追问一句即可，**不代写不编造**。

## 落点与格式

`data/portfolio/trade_notes/YYYY-MM.md`（按开仓月归档，append-only），一条一块：

```markdown
## MU · 2026-08-28 · Breakout
- 我看到什么: memory 主题领涨、盘前跳空放量
- 现在会怎么改: 仓位应该再大一点
- （记于 2026-09-06 · 口述）
```

同一笔的第二条想法：同标题下追加新的两行，带各自日期。**格式固定**——weekly-review 靠标题行 `## TICKER · YYYY-MM-DD · SETUP` 机器解析。

## 工作流

1. **原话先落**（口述桶铁律：先落盘再结构化）——他的话一字不丢。
2. 补缺字段：开仓日从 tracker / `data/research/setup_labeling/worksheet.csv` 查（trade_id 形如 `MU_2026-08-28_000`）；setup 可用 `machine_guess_v2` 预填**并标注是预填**；查不到的留 `⟨Andy⟩`。
3. 写入当月文件，**走直推 main 标准动作**（临时树 + 指名 add + push；写完 ≠ 送到，合进 main 才算）。
4. 回他一行确认：ticker + 哪个字段留了白。

## 裁决记录

### [2026-09-06] 建账（Andy 四条裁决原话见立项 brief）
- 五字段、顺序、归属均他亲批；本 skill 按当日新立的方法层机制建：评估先行（`evals/evals.json` 三条先于正文写）、description pushy、原话先落。
