# 固定块 — 每篇都用,一字不改

> ## 🔒 全刊铁律:永不出现账户规模
>
> **任何一篇里都不出现美元金额、不出现账户量级、不出现绝对盈亏。**
> 全部用 **R 倍数**和**百分比**表达。
>
> 理由有两条,第二条更重要:
> 1. 账户规模是隐私,而且对读者毫无用处
> 2. **R 和 % 是唯一可迁移的单位** —— 五位数账户和八位数账户读到的是同一个方法。
>    一旦写了美元,读者立刻开始算你的钱,而不是学你的算术
>
> 例外:**订阅定价**(必须写美元)。除此之外零例外。
> 发布前 grep 一遍:`grep -nE '\$[0-9]|million|万美元' <文件>`

*TSF 最有效的结构装置就是这两个块。他 355 篇里每一篇的头和尾都是同一段话。*
*重复不是懒 —— 重复是让读者知道这是一份**刊物**而不是一堆帖子。*

---

## 块 A — 开头免责块(对标 TSF 的 "What TSF Is / What TSF Is Not")

> **放在每篇正文最上方,加粗小标题,一字不改。**

```markdown
**What How Much is:**

A market letter by Fluxus. Every idea arrives with its entry, its stop, a portfolio risk in percent.

A trading system existing to do only one thing: find true market leadership early, and hunt the elephant trades with tight risks — the few a year that carry everything.

A quantitative resource to measure market dynamics in thematic/sectoral rotations, and to track two kinds of momentum worth owning — the sustained and the explosive — from everything that merely went up.

A deep dive case study into top opportunities each month with processes, nuances and calculated risks.

**What this is not**

A trade-alert service. Everything here is written after facts, with the arithmetic attached — not so you can copy it in four minutes. For live learning, please consider the Discord membership.

Prediction or opinion. I don't have opinions about where the market goes, only measurements and patience for the next big trade.

*Nothing here is advice or a recommendation to buy or sell anything. I don't know your account, your taxes, or how well you sleep. Measure your own water.*
```

*⚠️ 2026-08-31 Andy 三步定案（最终以本节代码块为准）：③ **块 A 全文由 Andy 亲自撰写并交付**，本文件逐字收录，我只加了 `What this is` / `What this is not` 两个小标题与加粗项目名（对齐他指定的 TSF 结构参照）。前两步过程：① 前半段「What this is」换成短的人话版（原版是产品说明书，不是人在说话）；
② 免责段**加回来，且不许自造语言**——下半段「What this letter is not」逐字沿用 08-25 定稿，一个词没改。
页脚 `templates/post_footer.html` 的免责照旧保留：**头尾同段是刻意的**（本文件开头已写明「重复不是懒——重复是让读者知道这是一份刊物」）。*

<details><summary>原长版（2026-08-25，已停用）</summary>

```markdown
**What this letter is**

A letter about how much. Every idea here arrives with its entry, its stop, and what I'm risking
in percent — of the trade and of the account.

A record kept in public, losers included. My win rate is 39.9%. You will see the ones that
didn't work, because a letter that only shows winners teaches the wrong job.

A method you can run without me. I measure. You decide.

**What this letter is not**

Not alerts. Nothing here is timed for you to copy. I post my own trades because a method you
can't see me actually run is just a claim.

Not predictions. I don't have opinions about where the market goes. I have measurements of what
it's doing and what I'm risking while it does it.

Not advice, and not a recommendation to buy or sell anything. I don't know your account, your
taxes, or how well you sleep. Measure your own water.
```

</details>

**为什么这段比 TSF 那段强:**
- 他的版本是防御性的(「我不是荐股服务」),你的版本**每一条否定后面都跟一个正向承诺**
- 「39.9%」是真数字,做了他那段完全没做的事:**用事实建立可信度,而不是用声明**
- 「Measure your own water」是你自有语言,他那句 "not financial advice" 是通用免责

---

## 块 B — 结尾持仓块(对标 TSF 的 "Jonas's Swing Portfolio In Order Of Size")

> **放在每篇正文最下方。这是 TSF 全套里成本最低、信任回报最高的一个装置 —— 直接抄。**

```markdown
---

**The book, in order of size**

| Position | Size | Entry | Stop | Trade risk | Port risk |
|---|---|---|---|---|---|
| (ticker) | (%) | | | (%) | (%) |
| ... | | | | | |

Cash: (%)

*Risk shown is what I'd lose if every stop filled where I put it. It is not a forecast and not a
recommendation. Positions change without notice and I don't post every change in real time.*
```

**为什么必须每篇都放:**
- 他每篇都放,而他**连业绩都没公开过**。你有 7 年真实记录 + H1 +90.5%,这个块在你手里的说服力是他的数倍
- 成本为零 —— 你本来就在管这个组合
- 它把「风险台账(x% trade risk, y% port risk)」这个你已有的语言习惯变成**刊物的固定资产**

---

## 块 C — P.S. 教学块(你自有,TSF 没有)

> Voice Bible §4:「letter 正文冷,P.S. 暖。这个温差是留存引擎 —— 永远不要写冷的 P.S.」

每篇结尾一句,只做一件事:**把这篇的动作翻译成一条可迁移的判据。**

样例(取自 Voice Bible 模板期):
```
P.S. — The next morning Washington blinked and the tape went vertical off this exact shelf.
I didn't know the catalyst was coming. I knew the sellers were done and my risk was one percent.
That's not a prediction. It's a position.
```

**判据(过「收藏闸」用):** 写完 P.S. 后自问 ——「读者读完这句,最想问的下一个问题是什么?」如果答案不在这篇里,这篇停在了倒数第二步。**立场只拿赞,条件/清单/判据才被收藏。**

---

## 块 D — 付费墙位置(架墙后启用)

TSF 的做法:免费段落给**观察和判断**,付费段落给**具体标的、size 和 stop**。

```
[免费] 开头免责块
[免费] 市场状态 / 这周的读数 / 一条可迁移的判据
[免费] 一句「下面是我实际怎么下手的」
─────────── PAYWALL ───────────
[付费] 具体标的 + 图
[付费] entry / stop / trade risk / port risk
[付费] 结尾持仓块
[付费] P.S.
```

> 免费段必须**自成一篇**,能单独读完有收获。「免费段是付费段的广告」是新手做法,TSF 不这么干 —— 他的免费段本身就是完整的市场观察。
