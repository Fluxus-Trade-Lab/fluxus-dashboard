date: 2026-09-02
tier: B
source: queue（08-29 包 V1 待批 + W5 收割毛坯 + 定时队列）
gate: 🎮 0/5 · streak 1 周
---
## C1
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
why: 08-29 包里唯一还活着的一条。V4（昨天的 C1）窗口写死「周一收盘后作废」，ET 最近完成场就是 08-31 周一——那扇门今天关了；V1 是包里标了「⭐ 常青弹药：零 ticker、零日期、零盘面状态」的那条，Gate 三轮零拦路，任何一天都能原样发。
---
## C2
bucket: BUILD | entry: 6
We ran 10,913 breakouts to ask one question: what part of a move is predictable?

Rank the stock's 20-day volatility BEFORE the event. Then measure what happened AFTER.

Size of the move: rho = +0.296.
Direction of the move: rho = -0.006.

Same variable. One column is nearly certain. The other is literally zero.

Probability of a big right-tail move goes from 3.4% in the quietest fifth to 19.0% in the noisiest. Holdout replicated it: 3.4% to 17.5%.

Here's the part nobody wants: it is not a buy signal. The left tail grew with the right tail. Expectancy is negative at both ends.

It's not a signal. It's a divisor. Same dollars into the noisiest bucket = 2.4x the five-day volatility — and that difference was chosen by the screener, not by you.
why: W5 收割的六条毛坯里最贴交易的一条，且是刊名「How Much」的论据本身——可预测的是「多大」不是「往哪」。数字全部来自 `data/research/amplitude_2026-08/results.md`，有 holdout 复现，不依赖今天的盘面。
---
## C3
bucket: VOICE | entry: -
Borrowed conviction was never conviction.
why: 定时队列本周排的就是 09-02 这一条（`Fluxus_Queue.md` 本周队列 #3），你自己的原句 `Fluxus_Own_Lines.md:446`。队列的存在意义是断更保险——C1/C2 都要你拍板，这条不用，粘上就走。
---
## notes
⚠️ 昨天的 C1（V4）今天下架：RECORD 写死它「只在 08-31 周一 ET 盘前成立，周一收盘后作废」，ET 最近完成交易日 = 2026-09-01（周一），窗口已过。数字本身没错，是它的时间标签（"Friday's close"）现在指向三场之前。
⚠️ 09-01 的新 campaign `2026-09-01_august-scorecard` status = **flagship**（在旗舰站，没过闸），所以本班不是 A 档——按任务书只有 queued/approved 才当主菜。
⏰ `APPROVAL_QUEUE.md` 里 `2026-08-29_extension-arithmetic` 连续第 2 天挂在「待批」，`verdicts.jsonl` 至今 0 条真判决。C1 一旦你点头就能发；否了也请给一个字，那是判决账的第一条真记录。
🟡 C1 待你拍的一处（Gate 三轮点名，AI 不代拍）：收口 `The trim line isn't where … It's where …` 是负面清单上的「不是 A，是 B」镜像句。非镜像备选：`By the time a chart reaches the trim line, the division has already cut you to two thirds. Nobody had to decide the stock got dangerous.`
📌 补位弹药（今天没排上，随时可取）：W5 毛坯 ①「我给自己造了个游戏逼自己发帖」——押后条件（第一次过关）08-30 已达成，只差你把最后一段换成自己的话；毛坯 ⑥「我们把他的脚注实现了七个月」。均在 `Fluxus_Brand/ops/weekly/2026-08-30_W5.md`。
📉 输入现状：`voice/raw/` 最新一份是 08-30，近 7 天只有 1 份你的原料；`posts.csv` 最后一条是 08-28。本周关卡 0/5。
