# 8 月月报 · Substack 发布版 v2 —— Five of every seven trades went into one bracket

*Writer Mia 2026-09-12 重写。**v1 作废**：v1 读的是 8/28 截点预览版，权威源已于 09-06 17:01 重新生成（含 8/31 交易日）。*
*数字第一手读 `data/portfolio/reviews/monthly_2026-08.html`（gitignored，本机）。深剖节数据＝复盘线 `00fd3232`，全节仅 % 与 R。*
*载体改为 **Substack**（Andy 09-12 定「月报绝对可以明天发 Substack 上」）。⚠️ 发布前需挂 `templates/post_footer.html`。*
*全文零美元 · 收口留空槽给 Andy。*

---

〔标题槽 —— Andy。工作标题：**Five of every seven trades went into one bracket. It paid back less than its share.**〕

You have the spreadsheet open. R down one column, entry dates down the other, and a win rate at the bottom you'd rather not look at. So you go hunting for the habit to cut, and there's an obvious way to find it: rank your trade types by what they made, and cut the one at the bottom.

Run that on my August and you'd cut the wrong thing. The habit that most needed looking at came out at the **top** of that ranking.

## The month, filed by the tape I entered into

Thirty-five trades closed their last leg in August — thirty-four all the way out, one partial trim still holding a piece. Every one got filed by a single 0–100 reading of the market taken **on the day I entered**.

The four brackets aren't cut from these thirty-five. They're fixed score ranges my own tooling drew off a year and change of daily readings, worst tape to best. Each trade drops into whichever range its entry-day reading falls in, so the groups come out uneven — and one of them is enormous.

| Bracket (the reading on my entry day) | Trades | Win rate | Avg R | Total R |
|---|---|---|---|---|
| Damaged 0–47 | 5 | 60.0% | +1.8R | +8.9R |
| Mixed 47–63 | 2 | 0.0% | −0.0R | −0.0R |
| Healthy 63–75 | 3 | 100.0% | +3.4R | +10.1R |
| **Extended 75–100** | **25** | **32.0%** | +1.0R | **+24.0R** |

*Thirty-five trades, 40.0% win rate, +43.0R for the month.*

Twenty-five trades in the top bracket, winning 32% of the time. They also brought back **+24.0R — more than the other three brackets combined.** That's the sentence that lets a low win rate off the hook, and I have used it on myself before.

Then you divide. Per trade, that bracket returned **+1.0R**. The two other brackets that made money returned **+1.8R** and **+3.4R**. **My biggest earner is my worst earner.** Both sentences are true and they point in opposite directions.

A total can only answer one question — how much did this bracket make. It cannot answer whether the bracket was worth doing, because a bracket holding five of every seven trades *ought* to make the most. It would be alarming if it didn't.

## The question that survives the division

What share of my trades went in, and what share of my R came back out?

| Bracket | Share of trades | Share of R | Difference |
|---|---|---|---|
| Damaged 0–47 | 14.29% | 20.70% | **−6.41** |
| Mixed 47–63 | 5.71% | −0.00% | **+5.71** |
| Healthy 63–75 | 8.57% | 23.49% | **−14.92** |
| **Extended 75–100** | **71.43%** | **55.81%** | **+15.61** |

**Seventy-one percent of the trades went in. Fifty-six percent of the R came back.** The difference is **15.61 points**, and that difference is the rate this bracket charges me.

Healthy took 8.57% of the trades and returned 23.49% of the R — a difference of **−14.92**. That one didn't charge me. It refunded.

There's a line I've used about myself for years: you'll notice I get stopped out a lot, part of that is discipline and part of it is that I trade too much. Those 15.61 points are what the second half of that sentence looks like once somebody makes you write it down.

## The two trades that bracket the month came from the same place

This is the part that changed how I read the table.

**Best trade of the month — six days, three exits, +22.3R.** Entered on a market reading of **99**. Position size: **5.1%** of equity. Risk at entry: **0.22%**. It ran +174% from my entry before it was done; my average exit was +96.5%, so I captured **55%** of it.

**Worst trade of the month — two days, two exits, −2.4R.** Entered on a market reading of **100**. Position size: **15.3%**. Risk at entry: **0.43%**. It gapped 2% against me on the day I entered and I was out two days later at −6.7% average. The setup label my own review engine put on it: *knife-catch, below a falling 50-day*.

Ninety-nine and one hundred. The best and the worst trade of my month were entered into virtually the same tape, and the review engine filed them in the same bracket.

**So the bracket is not the problem. The problem is what I do inside it.** The trade that worked got 5.1% of the book. The trade that didn't got **15.3% — three times the size**, on a setup that was catching a falling knife.

That is not a market-conditions error. That is a sizing error, made at the one moment the market reading was least able to tell me anything, because at a reading of 99 to 100 everything looks the same.

## The number underneath it

| | |
|---|---|
| Average position | **7.6%** |
| Largest position | **15%** |
| Correlation between size and R | **−0.15** |
| Share of all losses from the largest quartile of positions | **39%** |

A correlation of −0.15 means my bigger bets did slightly *worse*, not better. And the largest quarter of my positions produced **39% of everything I lost**.

The conviction I feel when I size up is not carrying information. It is carrying variance, and the ledger shows me paying for it.

## Four things this table cannot do

**It does not predict returns.** The 0–100 reading was validated for one job only: separating drawdown risk. Read it as a risk budget, never as a timing signal.

**It files by entry date.** A trade opened under one bracket and closed two weeks later into a completely different tape is still counted in the first one. The table says what I was *opening into*, not what I was *making money in*.

**Its four names are range labels from my own tooling** — empirical quartiles, not rankings, and not the sizing language I use everywhere else. Same words, different animal.

**And three of the four brackets are n = 5, 2, and 3.** "100% win rate" up there is three trades. "0%" is two. Only the top bracket, at twenty-five, has any weight at all — which is a strange kind of luck, because the one bracket big enough to judge is the one I need to judge.

## Do it to your own book — two steps

**1. Label every row by the day you entered.** It doesn't have to be clever. Any 0–100 reading works — a breadth number, your own morning score, honestly even "how good did this tape look to me, 0 to 10" — as long as the same ruler runs down every row and you never re-score a trade after you know how it ended. Set the cut points off your own history, not off this month: run the same ruler back as far as you have it, split that range at the quarter marks, and file each trade under whichever bracket its entry-day reading falls in. Leave the groups where they land. They will not come out even.

**2. Do one subtraction per group.** Share of your trades, minus share of your total R.

| Your bracket | Share of trades | Share of R | Difference |
|---|---|---|---|
| 1 | ___% | ___% | ___ |
| 2 | ___% | ___% | ___ |
| 3 | ___% | ___% | ___ |
| 4 | ___% | ___% | ___ |

**Positive** — that bracket is diluting you. You put in more than it gives back, and the bigger the number, the heavier the rate.
**Negative** — it is paying you back above its share.
**Around zero** — it returns what it takes, no more.

One boundary, and it is not decoration: **any bracket under ten trades gets no verdict, only its n written next to it.** Mine fails that test in three of four columns. Write the number, don't write a conclusion.

Then, if your biggest bracket is charging you a rate: go look at what you sized up inside it. That's where mine was.

〔收口槽 —— Andy 亲笔。边界：不写对仗格言、不复述以上内容、收在下一步或一个邀请上。〕

---

## 🔴 交接

### ⚠️ v1 作废的原因（重要，别再引 v1 的任何数）

v1（`9ea79bc4`，09-06 04:18 交）读的是 `monthly_2026-08.html` 的 **8/28 截点预览版**。权威源在 **09-06 17:01** 重新生成（含 8/31 交易日），四档表整片变动。Linda 09-06 已在 INBOX 标注「旧数 +12.9% 是 8/28 截点预览版，作废勿引」，但 v1 当时已交、无人回头改。

| | v1（作废） | v2（终版） |
|---|---|---|
| 合计 | 42 笔 / +48.2R / 胜率 40.5% | **35 笔（34 全平 + 1 部分）/ +43.0R / 40.0%** |
| Damaged | 6 / 66.7% / +9.4R | **5 / 60.0% / +8.9R** |
| Mixed | 5 / 0.0% | **2 / 0.0%** |
| Healthy | 3 / 100.0% / +10.1R | 3 / 100.0% / +10.1R（唯一未变） |
| Extended | 28 / 35.7% / +28.7R | **25 / 32.0% / +24.0R** |
| **Extended 的「税」** | +7.13 | **+15.61** |

**论点没垮，反而更硬**：那个差从 7.13 涨到 15.61。份额表 8 个百分比全部由上表四行现场除法得出，我逐格复算过。

### v2 新增的一节，以及它为什么不是附加物

复盘线 `00fd3232` 的 Best & Worst 深剖（全节仅 %/R，可直接摘入对外稿）给出了一个 v1 没有的东西：

**最好的一笔入场时市场分 99、仓位 5.1%；最差的一笔入场时市场分 100、仓位 15.3%。** 两笔落在同一档。

这把整篇的落点从「哪一档在稀释我」推进到「**我在最分不清的地方下最大的注**」——并且和同一份月报里的 `size↔R 相关 −0.15`、`最大四分位仓位贡献 39% 的总亏损` 咬合成一条链。最差那笔的 setup 标签是引擎自己打的：*knife-catch, below a falling 50SMA*。

### 发布前还缺三样

1. **收口** —— 空槽，按已定规矩不由本线出候选（`feedback_no_mirrored_aphorism_closings`）。
2. **页脚** —— 载体从 X Article 改成 Substack，需挂 `Fluxus_Substack/templates/post_footer.html`，正文不用动。
3. **要不要挂 boilerplate 块 A** —— 块 A 是给 How Much 周信定的（「每篇正文最上方」）。月报是不是同一个产品序列，归 Andy 定。**我的建议：挂**，理由是它同一个站、同一批读者，而块 A 的后半段（What this is not）本身就是免责。

### 已执行
零美元（grep 0 命中；⚠️ 权威源的个股复盘表带 $，已全部换成 R）· 每个数带样本量或口径 · 深剖两笔**匿名**（未点名 MRNA / INTC，Andy 若裁点名，加名字即可，不影响其余）· 三个 n<10 的档明写「不给结论只写 n」。

### 正文约 1,180 词
比 v1（963）长，多的是深剖那一节。月报不受周信 1,100–1,300 规格约束，但这个长度正好落在里面。
