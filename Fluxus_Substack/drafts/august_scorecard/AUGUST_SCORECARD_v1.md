# 8 月月报成稿 —— Two thirds of my trades went into one bracket. It paid back less than its share.

*Writer Mia 2026-09-06 执笔。毛坯＝`Fluxus_Brand/ops/campaigns/2026-09-01_august-scorecard/04_flagship.md`（Marketing Steve 夜间产线，G1 已于第 2 轮修复）。*
*载体：X Article 长文 · 语言 EN · 口径日 **as-of 2026-08-28 收盘**（权威源 `data/portfolio/reviews/monthly_2026-08.html`，mtime 08-31 15:25，本轮第一手重读四档 20 格）。*
*⚠️ 收口是空槽，留给 Andy 亲笔。*

---

### Two thirds of my trades went into one bracket. It paid back less than its share.

You have the spreadsheet open. R's down one column, entry dates down the other, and a number at the bottom you'd rather not look at. Forty-something. So you go hunting for the habit to cut, and there's an obvious way to find it — rank your trade types by money and cut the one at the bottom.

Run that on my August and you'd cut the wrong thing. The habit that most needed looking at came out at the **top** of that ranking.

Here is the account. Forty-two trades closed their last leg in August — thirty-four all the way out, eight of them partial trims still holding a piece. Every one got filed by a single 0–100 read of the market taken on **the day I entered**. The four brackets aren't cut from these forty-two — they're fixed score ranges my own tooling drew off a year and change of daily readings, worst tape to best: Damaged, Mixed, Healthy, Extended. Each trade drops into whichever range its entry-day read falls in, so the groups come out uneven. Twenty-eight of the forty-two landed in the top one.

Twenty-eight trades, winning 35.7% of the time. They also brought back **+28.7R — the most of the four.** That's the sentence that lets a low win rate off the hook, and I've used it on myself before. Then you divide. Per trade, that bracket returned **+1.02R**. The two other brackets that made money returned **+1.57R** and **+3.37R**. My biggest earner is my worst earner. Both sentences are true, and they point in opposite directions.

A money total can only ever answer one question — how much did this bracket make. It cannot answer whether the bracket was worth doing, because a bracket holding two thirds of your trades *ought* to make the most money. It would be alarming if it didn't. So which of the four should I cut? Sorted by money, none. Sorted by money, everything I do is working.

The question that survives the division is about share. What share of my trades went in, and what share of my R came back out?

**66.67% of the trades went in. 59.54% of the R came back. The difference is 7.13 points**, and that difference is the rate this bracket charges me. Healthy took 7.14% of the trades and returned 20.95% of the R — a difference of **−13.81**. That one didn't charge me. It refunded.

There's a line I've used about myself for years: you'll notice I get stopped out a lot, part of that is discipline and part of it is that I trade too much. Those 7.13 points are what the second half of that sentence looks like once somebody makes you write it down.

#### The month, as of the August 28 close

| Bracket (the read on my entry day) | Trades | Win rate | Avg R | Total R |
|---|---|---|---|---|
| Damaged 0–47 | 6 | 66.7% | +1.6R | +9.4R |
| Mixed 47–63 | 5 | 0.0% | −0.0R | −0.0R  |
| Healthy 63–75 | 3 | 100.0% | +3.4R | +10.1R |
| Extended 75–100 | 28 | 35.7% | +1.0R | +28.7R |

*Forty-two trades, 40.5% win rate, +48.2R. A reconstruction as of the August 28 close, not a month-end final.*

#### The same four rows, divided

| Bracket | Share of trades | Share of R | Difference |
|---|---|---|---|
| Damaged 0–47 | 14.29% | 19.50% | **−5.21** |
| Mixed 47–63 | 11.90% | −0.00% | **+11.90** |
| Healthy 63–75 | 7.14% | 20.95% | **−13.81** |
| Extended 75–100 | 66.67% | 59.54% | **+7.13** |

#### Four things this table cannot do

It does not predict returns. The 0–100 read was validated over 558 trading days for one job only — separating drawdown risk. Read it as a risk budget, never as a timing signal.

It files by entry date. A trade opened under one bracket and closed two weeks later into a completely different tape is still counted in the first one. So the table says what I was **opening into**, not what I was **making money in**. Those are not the same table and I only have the first one.

Its four names are range labels from my own tooling — empirical quartiles, not rankings, and not the five-tier sizing language I use everywhere else. Same words, different animal. Don't cross them.

And three of the four brackets are **n = 6, 5, and 3**. "100% win rate" up there is three trades. "0%" is five. Only the top bracket, at twenty-eight, has any weight at all, which is a strange kind of luck: the one bracket big enough to judge is the one I need to judge.

#### Do it to your own book — two steps

**1. Label every row by the day you entered.** It does not have to be clever. Any 0–100 read works — a breadth number, your own morning score, honestly even "how good did this tape look to me, 0 to 10" — as long as the same ruler runs down every row and you never re-score a trade after you know how it ended. Set the cut points off your own history, not off this month: run the same ruler back as far as you have it, split that range at the quarter marks, and file each trade under whichever bracket its entry-day read falls in. Leave the groups where they land — they will not come out even. The names don't matter; where the cut points come from does.

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

That's the whole tool. It needs nothing of mine — not my data, not my software, not your agreement with a single judgment above. It needs two columns you already have.

**[ CLOSING — 空槽，留给 Andy 亲笔 ]**

—

---

## 🔴 交接

### 我对毛坯做了什么（两处，都有据）

**① 执行 `_BOILERPLATE.md` 全刊铁律：删掉全部美元。** 毛坯 §四明写保留美元列，理由是「不印出来，『最赚钱的那一档同时是最差的那一档』就不可复算」。**这个理由不成立**——按 `Total R` 排序与按美元排序**顺序完全相同**（Extended +28.7R > Healthy +10.1R > Damaged +9.4R > Mixed −0.0R；美元 137,857 > 54,499 > 46,161 > −130）。「the most of the four」用 R 就能复算，读者一格都不少。铁律原文：「任何一篇里都不出现美元金额、不出现账户量级、不出现绝对盈亏……例外：订阅定价。除此之外零例外。」发布前 grep 现在为 0 命中。

**② 两处四舍五入按现场复算改了 0.01。** 毛坯 −5.22 / +7.12，我按权威源逐格复算是 **−5.21 / +7.13**（14.29−19.50、66.67−59.54）。差异无实质影响，但正文里出现的每个数都要能被读者用表上的数复算出来，所以采用复算值。

### 我核过的（第一手读 `monthly_2026-08.html`，未转抄毛坯）

四档 20 格逐格一致：Damaged 6 / 66.7% / +1.6R / +9.4R · Mixed 5 / 0.0% / −0.0R / −0.0R · Healthy 3 / 100.0% / +3.4R / +10.1R · Extended 28 / 35.7% / +1.0R / +28.7R。合计 **48.2R**，与月报「+48.2R / 42 笔 / 胜率 40.5%」一致。份额表四行 8 个百分比全部由这 4 行除法得出，我复算无误。

### 仍然空着的

**收口一段**——毛坯故意留空，我照留。理由在案：`feedback_no_mirrored_aphorism_closings`（①对仗格言 ②复述正文，我连栽两次），#001 已定「收口默认留空槽给 Andy」。

### 没有动的（属别人边界或需 Andy 裁）

- **⑤ 分发站**（入口推五条）在 campaign 目录里，属 Marketing Steve 的产线 isolate 区，我不碰。
- **Gate 第 1 轮的 G2 / G3 两条拦路项在分发节**，同上，需 Steve 线处理后本稿才能走完整闸。
- **载体确认**：毛坯定的是 X Article。若 Andy 要同时上 Substack，页脚需换成 `templates/post_footer.html`，正文不用改。
