---
name: daily-recap
description: 用我们自己的数据 + Andy 自己的话，生成每日市场复盘（Daily Market Recap，中英双语 PDF 的正文底稿）。取代「Revere 视频 transcript」作为源头。触发：Andy 说「做 X 月 X 日的复盘」「出 recap」「今天的 briefing」。产出是给 Andy 审的底稿，判断句留白，机器永不代他下判断。
when_to_use: 复盘、recap、briefing、market recap、每日市场、生成 PDF 底稿。不触发：盘中提醒、个股 tearsheet（有专门 skill）、Substack 周刊（另一条流程）。
---

# daily-recap — 你的数据认形态，Andy 的话下判断

> 2026-09-05/06 一天六轮实测纠正换来的。每条判据都带他的原话出处，改这份文件前先读裁决记录。
> 口径引用 `data/reference/METRIC_SOURCES.md`，**本文件不重复定义任何指标**。

## 三条法（Andy 2026-09-06 亲定，凌驾一切）

- **A · 无标准（或标准不指这件事）——不得当标准读数上页。** 自造的量必须自报家门。
- **B · 有标准但本仓库算不出——那就不用。** 不许用近似量顶替（例：FTD / distribution day 需要指数日成交量，`data/output/` 没有 → 这两个词不出现，直到数据源补上）。
- **C · 判断力是 Andy 的。** 判断句只从他的 Discord #live-commentary 与 Founders Note 取，润色限于补主语、接句、加标点——**不加他没说过的判断**。命名权（谁是 the tell、关键位在哪、教学选题）一律留白，标 `⟨Andy⟩`。

## 一行值不值得印（四问，全过才印）

1. **它昨天是什么？** 一样就删——没变的状态没有信息量（他原话：「他今天站上 50 均线，他昨天也站上 50 均线了，所以你在说这个传达什么信息呢」）。「没变」本身是新闻时报连续次数，不报状态。
2. **数字核过原始字段吗？** 位置字段（`*_dist` / `atr_from_*`）≠ 事件字段（`cross_*`）。09-05 一天读反两次，方向全错。他的话：「数据一定要准确，这个是无法原谅的错误。」
3. **评论有指向性吗？** 评论要有，但一句；「读数 + 感想」（That's the whole spread 之类）等于没写。
4. **说法有出处吗？** 查 METRIC_SOURCES.md。没登记的说法不用（09-05 把财报大跌错叫 intermediate climax top——O'Neil 的口径根本不指那个）。

## 均线规则

- **只以事件出现**：reclaimed / lost / rejected / 贴着。永不写「在 X 均上方」。
- **分尺度**：5/8 日＝动能呼吸（丢了常是噪音）· 21EMA＝强势股生命线 · 50 日＝中期/机构成本 · 200 日＝牛熊界（他的规则七：「跌破 200 日之前谈不上真正的麻烦」）。同一个 lost，尺度差三个量级，不许平铺。
- **震荡闸（先过闸再报事件）**：排列（8>21>50 或全反）+ 斜率同向 + 缠绕度（三线最大间距/ATR，暂用 1.5 阈值，待标定）。三项不全成立＝震荡盘，**一个均线事件都不报**，改报结构位与相对强度——他 09-02 期原文：「in a flat market the moving average is noise; the level that holds or fails is the signal」（trigger over indicator）。
- **均线交叉**（20/50、50/200）是换季信号，频率低含义重，单独一行，不与日内事件混排。

## 结构（对齐他的 PDF 规格 `Daily_Recap_Workflow_Spec.md`，每节一句话职责）

1. **标题**：paraphrase 当天性格 + 谁领涨 + 谁是问题；基调色 涨绿/跌红/震荡蓝
2. **The Big Picture**：一段。骨架用他当天 Discord 的句子（例：「QQQ starts acting strong while SPY weaker now. since semi and mags are stronger」），每句挂上量化它的读数
3. **Index Action**：三列等宽表 `% | 技术变化（事件！）| 关键位/备注`；关键位是判断 → `⟨Andy⟩`
4. **Founders Note**：他手写的，Sheet 里取；取不到留白，永不代笔
5. **What Led**：按板块分组，个股一行＝名字+%+RS+事件；**他点过名的票必须在**（Top watch / 论点股 / doing good 的全算）
6. **What Lagged / Blew Up**：不 working 的是画面的一半；财报失望（数据源补齐前只写他提到的）
7. **主线深挖**：当天唯一最大的事（09-04＝Memory & Storage），成分展开、放量与站位分开说
8. **（仅周五）Weekly**：周收盘视角——`perf_1w`、`wk_ema10/20`、`three_weeks_tight`、`rs_0_1w`；他的话：「weekly close very important」。30 周线补上前不引 Weinstein stage
9. **Tomorrow**：加速度排名在这儿用——他的口径是**为明天做准备**，不是描述昨天；写成「看什么」清单
10. **The Rules**：他的七条，固定文本照抄
11. **Portfolio Update**：指标条+截图+一句中性点评；依赖他先更新 tracker（人肉前置，堵了就留占位）

## 工作流

1. 读当天 `data/output/`：breadth（state_board/mm/verdict）· groups（themes/industries 的 state+accel+perf_1d）· rotation（cuts+verdict）· asset_signals（`*_dist`+`rs_line_pctl_21`+`rel_volume`）· universe（个股 RS/量比/`atr_from_sma50`）· shortlist · market_health（算排列/斜率/缠绕）
2. **对昨日做差**（breadth_archive / groups_history / asset_signals.csv）——只留变了的格子
3. 收 Andy 当天的话：Discord #live-commentary（截图或导出）+ Founders Note；一句都不许丢
4. 过四问 + 均线规则 + 三条法，拼结构
5. 交给 Andy：留白处标 `⟨Andy⟩`，数字全部可溯源（每个数标来源字段）
6. **他给 Revere transcript 之后**才做 diff：「他们有而我们没有的」记进本文件裁决记录，逐条决定融不融

## 裁决记录

### [2026-09-05] 建账日六轮纠正（全部他原话，出处 `Fluxus_Brand/ops/briefs/2026-09-05_andy_review_process.md`）
- 「你有很多很多的废话」→ 一行一件事；「就是一句话 Index is not market」但那句也「没有指向性」
- 「我没有让你直接去数字就够了……评论是要加的但只需要加一句话」
- 「memory 和 storage 这点是对的……应该继续深入进去」→ 主线深挖节
- 「其他的板块呢？比方说软件比方说大科技 mag7……在变差的板块是什么」→ What Lagged 必有
- 「今天站上 50 均线，他昨天也站上 50 均线了，你在说这个传达什么信息呢」→ 四问第 1 条
- 「数据一定要准确，这个是无法原谅的错误」（21 均方向全反）→ 四问第 2 条
### [2026-09-06] 三条法 + 口语裁定
- 「候选行批了……"hot potato" / "the tell" / "lone standout" 都是口语，忽略」——口语可出现在他自己的句子里，机器不主动用
- A/B 两条法原话见顶部；「最后是没有判断力」→ C 条
### [2026-09-06] 周五规格
- 「周五的复盘通常可以加上一些周线级别的复盘信息。只针对周五」

### [2026-09-06] 首次对卷（eval #1 · 09-04 vs Revere transcript vs 旧工具 PDF）
- **偷来的框架一件：三档 gauge（短/中/长）+ 升降级事件**。短=周收 vs 21EMA，中=中小盘 vs 50 日，长=200 日。
  形态天然满足「只报变化」，且全部可算——加进结构第 0 节，Bottom line 一句跟在后面。
- **周五的财报动作用周框架**：DELL 我写成周五 +1.5%，真故事是周 +15%/周量 200%。周五版里
  财报驱动的名字一律标 W、给周读数。
- **报自家清单的当日成绩**（shortlist 六席 / zones）——对标方每天报 21over21/Turbo12/Mag7，我们有清单没报过。
- **外部补入一律标 ◇**：新闻、缺失指数（MDY/VIX/DXY）、读图结论（DTL/launchpad/pivot 位）。
  ◇ 是引用不是背书；图形结构语言仍属 A 法（要么 Andy 读图，要么不写）。
- **我们的数字当裁判**：transcript 自打架（小盘均线在头顶 vs Russell 在 50/100 上方），
  我方 IWM 50 日下方 −0.34% 裁定前者对。对卷时凡数字冲突，以可溯源字段为准并标注。
- HOOD/META 论点股：无新事件仍可入——挂在「行情对论点的回应」下（HOOD 周 +16.5% 收复 120◇）。
### [2026-09-06] 五档放行
Andy 原话「可以放行 这个五档是可以用的」——自家五档（Defence / Caution / Neutral / Constructive / Euphoria）
连同其中的 Neutral 一词照用；它是我们的方案，不算借词。复盘与页面继续用它，三套档位词的收敛不再立项。
