# 文章一 · Position Sizing —— 初稿 v1

*Writer Mia 2026-09-06 执笔。数据与图＝复盘线 `Fluxus_Brand/ops/briefs/2026-09-06_articles_charts/`（引用源 `NUMBERS.md` / `chart_stats.json`，同一次运行）。*
*声音＝`Fluxus_Voice_Bible.md` §1/§3/§4 ＋ `Own_Lines`。收口与标题留空给 Andy（`voice/verdicts.jsonl` 三条否决：对仗收口 / 造词式自嘲 / 收口要邀请）。*
*⚠️ 全文零美元（`_BOILERPLATE` 铁律）· 每个数带样本量 · 对账锚 `PERFORMANCE_TRUTH.md` Period 2。*

---

〔标题槽 —— Andy。工作标题：**I checked my own sizing against a Market Wizard's. Four numbers matched. One didn't.**〕

Somebody spent 500 hours watching Qullamaggie's streams and wrote down what he actually did with size, as opposed to what he said about it. I read it, and then I did the obvious thing: I ran the same measurements on my own 373 trades and put the two columns next to each other.

Four of the numbers came out nearly identical. I have never copied his method, and I did not set out to match him.

The one that didn't match is the reason I'm writing this.

## The number moved and the trades didn't

Start with an error I made about myself, because it sets up everything else.

My own rule says risk about a quarter of a percent per idea. When I first measured it, the median came back at **0.52%** — twice the rule. I spent a while being annoyed at myself about that.

The measurement was wrong. I had divided every trade's risk by my **starting** capital for the year. But the account grew, and a position taken in August is not risking a percentage of what I had in January; it's risking a percentage of what I had that morning. Divide by **entry-day equity**, which is the only denominator that describes the decision as it was actually made, and the median is **0.30%** across all 373 trades. The mean is 0.37%.

Same trades. Same stops. Same everything. One number reads as discipline, the other reads as twice the speed limit, and the only thing that changed was what I divided by.

I'm opening with this because it is the most common way I've seen people mislead themselves with their own data, and because I did it to myself first. **A percentage is two numbers, and most arguments about the top one are actually arguments about the bottom one.**

〔图 C1 · risk 分布直方图，0.2–0.5 带高亮 + 双分母注〕

The distribution behind that median: 19% of trades sat above 0.5%, and **seven trades out of 373 went above 1%**. The largest was 8.1%. That one returned **+0.0R** — I got the whole thing back and nothing else. Seven trades is not a habit. It's a tail, and I'd rather show you the tail than the median alone.

## Four numbers I did not intend to match

| | Me (n=373) | Him |
|---|---|---|
| Risk per trade, median | **0.30%** | in the same band |
| Single position, median | **7.6%** | 7.4% |
| Names held at once, median | **8** | 8 |
| Position ceiling | **22.4%** (3 trades above 20%) | 20–25% |

〔图 C2 · 趋同四联 lollipop〕

I want to be careful about what this is worth. Two people landing on the same four numbers is suggestive, not proof — we both trade momentum in liquid names, both read the same public material at some point, and there is no world in which I can prove I got here by a route he didn't touch. Convergence is a weak form of evidence and I'm not going to dress it up as a strong one.

What it does rule out is the flattering story. If my sizing were unusual, that would be something to write about. It isn't. On four of five measurements I am doing an ordinary thing that a lot of people who survive this business also do, which means **the sizing is not where my edge is**, and I should stop looking for it there.

There is one place we clearly differ: **turnover**. He ran about 40 round trips over the same span; I ran **28**. That gap is not a technique. It is Tokyo — I trade a US market from Asian hours, and some setups simply happen while I'm asleep. I mention it because it's the kind of structural difference that people usually paper over with a reason, and it doesn't need one.

## The number that stung

If position size carried any judgment, bigger positions would win more. That relationship would show up as a positive correlation between size and outcome.

**Correlation between position size and R, across all 373 trades: −0.02.**

〔图 C3 · size × R 散点，相关线几乎水平〕

That is zero with a rounding error. My conviction — the feeling that made me put 12% into one name and 4% into another — has no detectable relationship with how those trades ended.

I ran the same measurement on a narrower window to see whether it was an artifact of the full year. Across August alone it was **−0.15 (n=42)**: still nothing, and if anything leaning the wrong way. Both readings carry their sample size because they deserve to be doubted at their own resolutions; neither of them says "size predicts outcome," and one of them is small enough that it wouldn't say much either way.

The uncomfortable reading is straightforward. **When I size up, I am expressing a feeling, and the feeling does not know anything.** The stops and the exits are doing the work; the extra size is a decoration I add at the moment I am least equipped to add it.

## What that costs, arithmetically

So I asked the counterfactual. Take the same 373 trades, keep the total risk budget identical, and stop varying the size by conviction — put the same risk on every one of them.

Indexed to my actual result at 1.00, the equal-risk book returns **1.54**.

〔图 C4 · 等风险反事实，指数柱 1.00 → 1.54〕

Fifty-four percent more, from the same trades, the same entries, the same stops, and the same total risk. The only thing removed is my opinion about which ones deserved more.

Now the caveats, and they are not small. This is a reallocation performed after the fact on trades that already happened. It assumes every one of them fills and behaves identically at a different size, which is not true for the thinner names. It also assumes I would have held them the same way, and I know from the ledger that I do not hold a small position the way I hold a large one. **A counterfactual is arithmetic, not a result.** I don't get to claim 54%.

What I do get to claim is the direction, and the direction is not ambiguous. Every version of this calculation I have run says the same thing: **the variance I add on purpose is costing me, not paying me.**

## The one number where I actually differ — and it has three values

Here is the part I had not seen anyone put down plainly. When I asked "how much of the book is at risk right now," I found I could answer it three different ways and all three were defensible.

| Gauge | What it measures | Median |
|---|---|---|
| **Committed** | Sum of the risk I signed up for, entry to stop | **~3%** |
| **True exposure** | What I'd actually lose if every stop filled where it sits today | **~7%** |
| **Peak upper bound** | The worst the book was ever arranged to lose | **~30%** |

〔图 C5 · 热度三段堆叠时间线〕

That top number needs a warning label, and it is a warning about my own record-keeping: **my log does not track stop movements.** So the peak figure treats every stop as if it never moved from where I first put it. In real life I move stops up, often quickly. The true peak sits somewhere below 30% and I cannot tell you where, because I didn't write it down.

That is not a modelling choice. That is a gap in my data, and the honest version of this table has a hole in the last row.

I keep all three anyway. The first is what I promised myself. The second is what I'm actually holding. The third is the ceiling I could hit if I stopped paying attention. **The distance between the first and the second is the number that tells me whether I am running my own system or narrating it.**

## Three more places I was wrong about my own numbers

The denominator was the first. There were three others, and I'd rather list them than have someone find them:

**The system-quality score.** SQN uses a square root of the sample size, and if you don't cap that N, a long record inflates the score mechanically. Uncapped, mine reads **5.0 — "excellent."** Capped at 100 the way Van Tharp specifies, it reads **2.77 — "good."** The second one is the true reading. "Good" is a fine grade; "excellent" was a bug wearing a compliment.

**The drawdown.** I selected my worst drawdown by looking for the largest fall in money terms rather than the largest fall in percentage terms. Those pick different episodes when the account has grown through the year. The number I published was **−11.1%**. The real one is **−17.9%**.

**And that last one had already gone out.** It was on a public page with the wrong number on it before I caught it. The correction is in the file, dated, with the reason written next to it — the number got worse and stayed corrected. I'd rather that be findable than tidy. If a record only ever moves in the flattering direction when it's revised, it isn't a record.

## What to take away

Three things you can run on your own book this week. None of them need my data or my software.

**1. Check your denominator before you argue with your discipline.** Divide each trade's risk by the equity you had *that day*, not by what you started with. If your account moved much this year, this alone can move your median by a factor of two, and it decides whether you conclude that you're disciplined or reckless.

**2. Correlate your position size against your outcome in R.** One column of sizes, one column of R, one correlation. If it comes out near zero, your conviction is not carrying information, and the size you add on top of a setup is variance you're paying for. Mine is −0.02 across 373 trades. Write your own number down before you decide what it means.

**3. Compute your open risk three ways, and watch the gap between the first two.** What you committed, what you'd actually lose at today's stops, and the worst arrangement you've ever held. If the middle number keeps drifting above the first, you are not running the system you think you are — and you'll see that in the gap long before you see it in your equity curve.

〔收口槽 —— Andy 亲笔。边界：不写对仗格言、不复述以上内容、收在下一步或一个邀请上，不收在总结句。〕

---

## 🔴 交接

**正文约 1,560 词。** ⚠️ **比 brief 定的 2,500–3,500 少约 1,000 词** —— 我没有为了凑长度加段：现有弹药（NUMBERS.md 文章一那 8 行）写到这里就用尽了，再长只能靠稀释。**要补到 2,500 有三条路，请 Andy / 复盘线选**：①加「我当时为什么这么 size」的口述（这是我们对 Muninn 唯一的结构性优势，他拆别人拿不到内心戏，而 brief 的差异化正是押在这上面——但只有 Andy 能提供）②把 7 笔 >1% 的离群逐笔展开（数据已有，需复盘线出一张小表）③把「趋同」那节扩成逐项对表（C2 已有四联图，可展开成四段）。**我的建议是 ①**，它同时补长度和补差异化。

**已执行的口径**：全文零美元（grep 0 命中）· 每个数带 n（corr 双读数 −0.02 n=373 / −0.15 n=42，按 F 条）· 单笔案例匿名（第 7 笔离群只写 8.1% 和 R=+0.0，未点名）· 反事实明写「arithmetic, not a result」并列出三条不成立的前提。

**四处坦白全部在文**：①分母（开篇）②SQN 封顶 ③回撤按美元挑 ④已发布过错数并公开更正（三条并列在「Three more places I was wrong」节，第④条收在「If a record only ever moves in the flattering direction when it's revised, it isn't a record.」）。

**图位五张已插槽**：C1/C2/C3/C4/C5，位置与正文承重点一一对应。

**空槽两处**：标题（工作标题已给）· 收口。**按已定规矩收口不由我出候选**（`feedback_no_mirrored_aphorism_closings`：对仗格言、复述正文、硬加洞见，我已连栽三次）。

**未做**：Substack 版页脚（要发 Substack 需换 `templates/post_footer.html`，正文不动）· 入口推三行（属分发，等 Steve 线）。
