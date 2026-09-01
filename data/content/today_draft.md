date: 2026-09-01
tier: A
source: 2026-08-29_extension-arithmetic
gate: 🎮 0/5 · streak 1 周
---
## C1
bucket: ARC | entry: 5
Here's the part sizing threads never print: the number moves when you move the
stop, and they never tell you where they put it.

Friday's close, two charts, one risk budget. Move the stop from the 50-day to
the 21-day and the position the arithmetic hands back grows by 49.8 percent on
one of them and 92.5 on the other. Nothing about either company changed.
Nothing about the market changed. A line moved.

So any position size quoted without its stop is decoration. Including mine,
which is why the stop convention is written into every one of these.

Further from your stop, smaller position — every convention, every time.

Direction is the only part that survives, and it survives under anyone's stop
convention. Nobody had to agree to it.
why: campaign 排期硬结论——「止损约定决定一切」不先落地，包里另外两条都站不住，V4 必须打头阵。

⚠️ 读数已过期（口径日落后一场）：复算命令 ⑤ 今晨实跑，49.81 / 92.52 与稿面 49.8 / 92.5 **逐位对得上**；但口径日仍是 **2026-08-28（周五收盘）**，而 ET 最近完成交易日是 **08-31（周一）**——`universe.json` timestamp `2026-08-30T17:45:49Z`、`quality.json` date `2026-08-28`，**08-31 盘后 cron 未进 main**。RECORD 的窗口写死「周一收盘后即作废」，那个窗口现在已经关了。
⛔ 另有一句待你拍（Gate 第 4 轮点名，AI 不代拍）：`Including mine, which is why the stop convention is written into every one of these.` 是一条**新的对外方法承诺**（承诺此后每条仓位帖都带止损约定）。Gate 核过 Voice Bible §3 的风险台账 tic，判定同族不同条，不豁免。**你不点头这句就得删。**
---
## C2
bucket: ARC | entry: 2
The extension scale draws its lines at 4, 7 and 10. Entry. Trim. Take profit.
Everyone reads it as a temperature.

It's a dosage chart, and nobody turned it over.

Hold your risk budget fixed, hold one stop convention — the 50-day, say — and
those same three lines read out as size instead of heat:

4 — call this one full position.
7 — the arithmetic is already handing you 60 to 68 percent of it.
10 — 44 to 55.

Those ranges are the entire contribution of volatility, across names that move
2 to 8 percent on an average day. Swap a quiet one for a wild one and the
number shifts a few points. The distance does the rest.

The trim line isn't where the stock turns dangerous. It's where the division
already had you at two thirds.
why: 包里**唯一零盘面依赖**的一条——纯函数，零 ticker 零日期，今天原样发不会错；四轮 Gate 零拦路。
🟡 收口那句 `The trim line isn't … It's …` 是负面清单上的镜像句，非镜像备选在 05 §V1：`By the time a chart reaches the trim line, the division has already cut you to two thirds. Nobody had to decide the stock got dangerous.`
---
## C3
bucket: LONGFORM | entry: 2
You've had that chart open all weekend, and you already know what everyone is going to tell you. It's extended. Great. Now type that into the order box.

Your stop isn't a line on a chart. It's rent. The further it sits from your entry, the more you pay for the same square footage. And you don't get to pick it for free — pick one line and hold it, or the number means nothing. Call it the 50-day: at Friday's close $CRM sat 9.73 ATRs above that average, and the rent is 29.34% of the price.

Same 0.25% of risk. Out there it buys 49.7% of the square footage it would have bought four ATRs out — the top of the entry zone. $VEEV gave some back on Friday and sits 8.35 ATRs out — same rule, same risk, 55.1%. Almost none of that gap is the companies. It's the distance.

It runs the other way too, and that half matters more: two ATRs off the 50-day, the same rule buys about 186% of what it buys four ATRs out. Same arithmetic, the other side of one. All it ever reads is how far the exit has to sit from your entry.

You can still buy it. You just can't buy as much of it. Conviction doesn't change the division.
why: 包里的旗舰（221 词长推）；排在 V1 之后是因为它和 V1 第一拍相同（立共识→一句推倒），Gate 要求两条别挨着发。

⚠️ **今天不能原样发，三处**：① 首句 `all weekend` 是写给周一发布的口径，今天周二读起来漏掉整个周一；② `8.35` 已漂到 **8.34**（VEEV ext 8.346→8.341，比值 55.09→55.12），`9.73 / 29.34% / 49.7%` 未变；③ 载体自相矛盾——04 自述「长推 + 一张读数表图」，visual 节写「本卡不配图」，而那张 20 格表**正是本卡唯一的可复用物**（纯函数，逐格未变，永远有效）。裸发＝读者拿不走表；等图＝错过窗口。**这条要你拍。**
---
## notes
⛔ 置顶两件必须你拍（Gate 第 4 轮列明，AI 不代拍）：C1 那句对外方法承诺 · C3 的裸发 or 等图。
⚠️ 排期与陈旧撞车：Gate 定 V4（C1）必须打头阵，但 C1 依赖盘面且窗口已关；**今天唯一零风险可发的是 C2**。先发 C2 会违反「V4 先行」的排期结论——这个取舍归你，我不替你翻 Gate 的排期。
数据源实况：`universe.json` ts `2026-08-30T17:45:49Z` · `quality.json` date `2026-08-28` status ok · **08-31（周一）盘后 cron 未进 main**。今夜 cron 跑通后重跑 05 §复算 ① 与 ⑤，C1 即可刷新复活。
campaign status = `queued`（不是 approved）——`approved` 只有你能写，包在 `Fluxus_Brand/ops/campaigns/APPROVAL_QUEUE.md` 等签字。
下架的 V2 / V3 未进本单：V2 两处实错（减半点那段在新基座下为假 · 全篇缺 ATR% 2–8 前提），V3 无错但入口撞车下架。
`voice/verdicts.jsonl` 仍只有表头、零条判决；`voice/raw/` 最新是 08-30。你对本单的第一个否决就是这本账的第一条真记录。
