# 文章二 · Profit Taking —— 初稿 v1

*Writer Mia 2026-09-06 执笔。数据与图＝`Fluxus_Brand/ops/briefs/2026-09-06_articles_charts/`（`NUMBERS.md` / `chart_stats.json` 同一次运行）。*
*⚠️ **引用规则已锁进机读源**（`bootstrap_1000x.d5_share_of_peak_pct.citation_rule`）：锚 Muninn 的 **91（n=829）**，我们的 92 只作**复刻**、永不单独承重；**峰值日三峰、p5–p95 = d4–d18，任何点值不可引**。*
*全文零美元 · 每个数带 n · 单笔案例匿名 · 收口与标题留空给 Andy。*

---

〔标题槽 —— Andy。工作标题：**Most of the move is over inside a week. Two different books, same answer.**〕

There is a number I did not want to be true, so I checked it against somebody else's book before I let myself believe it.

Somebody had already measured Qullamaggie's winners day by day and found that by the fifth day, about **91%** of the eventual move was already on the table. That's from **829 trades**. It's a big sample and it isn't mine.

I ran the same measurement on my own **139 winners**. I got the same answer.

That agreement is the entire reason this article exists, and I want to be precise about why — because my number on its own is not strong enough to carry it.

## What the path looks like

〔图 C6 · 赢家 day-path，中位 vs 均值 — 镇文之图〕

Median winner, indexed from the entry-day close:

| Day | 1 | 3 | 5 | 9 | 20 |
|---|---|---|---|---|---|
| Median gain | +5.3 | +8.9 | **+11.1** | +12.1 | +7.4 |

By day five the median winner has **+11.1** of an eventual **+12.1**. The move is essentially finished in a week, and then it gives a chunk back.

Now the part most people would skip. My figure for "share of the move done by day five" is **92%** — and I am not going to let that number stand by itself, because when I resampled my own 139 winners a thousand times, that 92 landed at the **80th percentile of its own distribution**. The 90% interval runs **70 to 100**. If I quote 92 as a fact, I'm quoting the flattering end of my own noise.

The interval is wide, but the conclusion doesn't flip anywhere inside it. At 70 the move is mostly done in a week. At 100 it's entirely done in a week. **And his 91, from a sample six times the size of mine, sits inside my interval.**

So the claim I'll actually defend is not a percentage. It's this: **the first week does most of the work, in two books that have nothing to do with each other.** His number is the evidence. Mine is the replication.

**One thing I will not quote at all: the exact day the median winner peaks.** I could tell you it's day nine. Resample it and the peak day scatters from day four to day eighteen, with clumps in three places. That number is noise wearing a decimal point, and if you build an exit rule on it you've built on sand.

**The mean tells a different story, and the difference is the point.** By day 20 the mean winner is still climbing — **+11.9 and rising** — while the median has already faded to +7.4. That gap is a handful of enormous trades dragging the average up. **The median describes the trade you are in right now. The mean describes the trades you will remember.** You need an exit plan for both, and they want opposite things.

## What I actually capture

If the move is largely over in a week, the obvious question is how much of it I take home.

**Median capture: 34%. Mean: 42%. (n=145.)** Measured entry to exit, against the highest close within ten days of my exit — so the denominator includes what the name did right after I left.

〔图 C7 · 捕获率分布，34% / 50% 两线〕

His is around **50%**.

That is the gap, and it is the one number in this article where I come out clearly behind. Sixteen points of the move, on the trades that worked, that I identified correctly and then handed back by leaving.

## The one that got away

〔图 C8 · 忏悔案例，买卖点 + 错过区着色〕

The clearest single instance: my **largest position among the ten best trades of the year**. I was out completely on **day 13** at an average of about **+12%**.

The name then went on to run **176 points** further without me.

I sized it correctly. I identified it correctly. I was early on it. And I captured roughly **14%** of what it did — against a median of 34% and his 50%.

I've gone back and forth about whether this is a rule failure or a single bad exit. The ledger says the second. Across my top ten trades, **nine captured between 53% and 100%** of their move. **One captured 14%.**

〔图 C9 · top10 捕获子弹图〕

So this isn't a habit I need to break. It's one trade that cost more than the rest combined were worth, and the useful question is not "why do I always do this" — I don't — but **"what would have kept a piece of that one on the table."**

## Why I can't just copy his exit rule

The obvious fix is a trailing stop: leave the whole position on the ten-day line and let it decide.

I ran that on my top ten trades. **Total: −64R.**

〔图 C10 · 集中度 Pareto，top10 = 46% 总 R〕

Trailing everything on the ten-day line kills the trades that go vertical in a single session, and enough of my best ones do exactly that. His book can absorb that rule. Mine can't — not because his rule is wrong, but because **it was fitted to a different distribution of winners than the one I actually produce.**

This is the part I'd underline for anybody reading somebody else's exit rules, including these. **Test the rule against your own path data before you adopt it.** The same rule applied to two books produces opposite outcomes, and the only way to know which book you have is to measure your own.

And the stakes are concentrated. **My top ten trades are 46% of my total R** across 373. A rule that improves the average trade and damages the top ten is a losing trade on my book, no matter how good the average looks.

## What I'm changing

One rule, narrow enough that it doesn't touch the trades that go vertical.

**When a position is up 2R or more unrealised, the last 20–25% of it doesn't get sold on my schedule. It gets left on the 10- or 20-day line and stopped out rather than taken out.**

That's it. The first three-quarters still come off the way they always did, so the vertical single-session trades still get banked before they can round-trip. The residual is small enough that giving it back doesn't hurt, and large enough that when a name runs 176 points after I leave, I'm still in the room for part of it.

Run against the trade above, that residual was worth roughly **50 points** I did not collect.

I don't have out-of-sample evidence for this rule yet. It's a change with an arithmetic behind it and no track record, and I'll report what it does — including if it does nothing.

## What to take away

**1. Plot your winners day by day from entry, median and mean separately.** Where the median flattens tells you when your edge is spent. Where the mean keeps climbing tells you what your tail is worth. If you only look at one, you'll build the wrong exit.

**2. Compute your capture rate.** What you took, over what was available within ten days of your exit. Median and mean, with your sample size. Then compare it to your own trades — not to mine, and not to his.

**3. Before you adopt anybody's exit rule, apply it backwards to your ten best trades.** Not your average trade — your best ten, because that's where the money is. If the rule costs you there, it doesn't matter what it does to the average.

〔收口槽 —— Andy 亲笔。边界：不写对仗格言、不复述以上内容、收在下一步或一个邀请上。〕

---

## 🔴 交接

**正文约 1,180 词。** ⚠️ 同文章一，**低于 brief 的 2,500–3,500**。文章二的弹药更少（NUMBERS.md 只有 8 行），且 bootstrap 判定砍掉了两个原本可以展开的段（峰值日不可引 / 92 不可单独承重）。**补长度的路**：①忏悔案例的口述（当时为什么第 13 天全出——只有 Andy 有）②把 top10 那 9 笔 53–100% 逐笔展开（数据在 C9，需复盘线出表）③把「10 日线 −64R」拆成分笔归因。**建议 ①**，理由同文章一。

**引用规则已严格执行**：锚 Muninn 的 **91（n=829）**；我们的 92 **从未单独出现**，每次出现都带「P80 of its own distribution / 区间 70–100」；**峰值日一次都没作为事实引用**，正文明写「noise wearing a decimal point」。均值 vs 中位那段是从 bootstrap 结论里长出来的，不是原 brief 的架构，但它承的是同一个 thesis。

**已执行**：零美元（grep 0）· 单笔案例全程匿名（只写「top10 里最大仓位」「day 13」「+12%」「176 点」，未点名）· 新规则明写「no out-of-sample evidence yet」，不冒充已验证。

**与文章一的分工**：文章一讲「进场时押多大」，文章二讲「赢了之后拿多少」；两篇共用「我的边不在我以为的地方」这个底层判断，但各自独立成立，没有互相依赖的段落。四处坦白全在文章一，文章二只有一处自陈（14% 捕获那笔）。

**空槽两处**：标题（工作标题已给）· 收口。
