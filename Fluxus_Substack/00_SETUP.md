# Substack 开台设置 — 逐字段粘贴稿

*目标站:`fluxuscapital.substack.com`(空置 3 年,内容 0)*
*结构照抄 TSF(见 `../Fluxus_Brand/research/Fluxus_TSF_Teardown.md`),文案走 Fluxus 声音(见 `../Fluxus_Brand/voice/Fluxus_Voice_Bible.md`)。*
*⚠️ 全部为本地草稿。我不会替你发布任何东西 —— 你逐项审完自己粘贴。*

---

## 0. 五字段进度表(开台前必须全绿)

*2026-08-25 建。文案全部定稿、频率口径已统一,**剩下的只是往后台粘**。*

| # | 字段 | 后台位置 | 文案在 | 状态 |
|---|---|---|---|---|
| 1 | **Name** | Settings → Basics → Publication name | §1 | ✅ `How Much` |
| 2 | **Short description / Hero** | Settings → Basics → Publication short description | §1 | ✅ 2026-08-25 粘 |
| 3 | **三档权益** | Settings → Payments → Benefits | §2 | ✅ 2026-08-25 粘(1 free + 3 paid) |
| 4 | **About 页** | 站点 `/about` → Edit page | §4 | ✅ 2026-08-25 换掉 3 年前旧版 |
| 5 | **Welcome 邮件(free)** | Settings → Emails → Welcome email to free subscribers | §5 | ✅ 2026-08-25 粘 |

**顺带两件(零成本,做一次管一年)**:☐ Recommendations(§7 ①,**这是 TSF 那 400 人的真正来源,和粉丝数无关**) · ☐ X bio 改漏斗(§7 ②)

### ⚠️ 粘的时候碰到的四件事(留给下次)

1. **Short description 字段有 255 字硬上限**(`maxlength=255`),而且它的 `name` 就是 `hero_text` ——
   **简介和主页 hero 是同一个字段**,不是两个。原稿三块(简介 139 + promise 95 + 频率 33)= 271,装不下。
   处置:promise 压成一句、去掉 "The promise:" 这个在 hero 上冗余的标签 → 220 字,三个意思都保住。
2. **旧 About 页是 3 年前的**,里面写着「每周一份交易计划 + 一两次周中更新」——**和每周一封直接冲突**,
   还写着「专做 ES/NQ orderflow」。已整段替换。这类三年前的旧文案还可能藏在别处,发布前值得再扫一遍。
3. **Welcome 邮件原稿写「Three things」但加完频率那条是四条** —— 已改成 `Four things`。
4. **`Start here →` / `The record →` 两条链接位暂时拿掉了** —— 指向的文章还没发。
   五篇上架后要回来补进 Welcome 邮件。

### ☐ 还没动的(需要你决定,我没自作主张)

- **Welcome email 的主题行**仍是 Substack 默认的 `You're on the list!` —— 带感叹号,和这份刊物的干冷语气不合,但原稿没写主题行,我不替你编。
- **paid / imported 两封 Welcome 邮件**仍是默认模板(只改了 free 那封)。
- **定价**:后台是 月 $39 / 年 $399,本文件 §3 建议的是 $39 / $349 / founding $599(founding 档还没建)。**钱的事我不碰。**
- 🔴 **导航栏有两个死链**:`My methods` → `/methods` 和 `My A+ setups` → `/A+setups`,**两个都 Page not found**,
  而且第二个 URL 里带 `+` 号。站上一共五个导航位,两个是 404。详见 §6b。

> ⚠️ **频率口径已在 2026-08-25 全站统一为「一周一封,每周日」**(§1 promise / §2 free+paid / §5 welcome / §6c 页脚 / §7 bio 六处)。
> 再改频率就要六处一起改,别只改一处 —— 承诺不一致比承诺高更伤人。

---

## 1. Publication 基本信息

**Name:**
```
How Much
```
**Subtitle:**
```
a market letter by Fluxus
```
> 理由:TSF 用产品名当刊名(The Setup Factory),但 Voice Bible §4.5 已验证 —— 器械/工具命名的刊物是数据里增长最慢的一档(Trader Ferg 441/月、TMT Breakout 438/月),声音/方法命名的最快(Le Shrub 986、Doomberg/Citrini 6,000+)。所以刊名走声音,不走工具。`Fluxus Capital` 留作公司名/域名。

**Short description(Substack 简介,150 字符上限 —— 2026-08-01 定稿,139 字符):**
```
Momentum, risk, and the question underneath it all. Written by a full-time swing trader. Built for risk takers who don't need another idea.
```
> 三句 = **覆盖 / 作者 / 受众**。`Written by… Built for…` 对仗。
> 立场(ally of volatility)不进这个字段 —— 它在 bio、hero、About 各出现一次已足够,**重复三遍会稀释**;而 `full-time` 是这里唯一的硬凭证,在 SEO 位上比一句气质值钱。
> 备用(原短描述,可用于 X 置顶或广告位):*Everyone tells you what to buy. Nobody tells you how much. That's the part that decides your year.*

**The promise(紧随简介,或作 hero 首行):**
```
The promise: every idea arrives with its size and its stop. You'll never have to ask how much.

One letter a week, every Sunday.
```
> **频率单独成行**,不埋进长句 —— 它是承诺不是修饰,而且正是决定订不订的那句。

**Hero text(主页大字块 —— ⚠️ 短版。长版留给 Squarespace,见 `../Fluxus_Brand/ops/Fluxus_Action_Plan.md`):**
```
Momentum, risk, and how much. From Japan, on Asian hours.

• Every idea arrives with its size and its stop — you'll never have to ask how much
• A public record, losers included — 331 trades, 39.9% win rate, and why that's the job
• Fluxus Analytics — the measurement stack I actually trade off: regime, breadth, dealer gamma

I don't have opinions. I have measurements.
```

---

## 2. 三档权益文案(对应 Substack 的 free / paid / founding benefits 字段)

**Free subscription benefits:**
```
Written by Fluxus — a full-time discretionary swing trader in Japan, trained under a hedge fund
manager who had navigated every bear market since the 1980s. Math degree, Erdős number of 3,
seven years of real returns. The free tier gets the method, the record, and the losses.

One letter a week, every Sunday.
```

**Paid subscription benefits:**
```
· How Much — the weekly letter. One a week, every Sunday. Every idea with its entry, its stop,
  and what I'm risking in percent.
· The Ledger — the record kept in public, losers included.
· Fluxus Analytics — the measurement stack I actually trade off: regime, breadth, dealer gamma.
```
> 🔴 **2026-08-25 改**:旧文案写 `Size & Stop — the flagship letter, 2–3x weekly`,
> 承诺是实际频率的 2–3 倍。**断更的代价远大于少发一封** —— 第一批订阅者是在读到频率那句话的
> 瞬间决定订不订的,承诺高了第三周就开始欠债。同时 `Size & Stop` 退役,一个产品一个名字。
> `The Weather Report` 并进旗舰(每周一封里本来就有市场状态那一段),不单列成权益。

**Founding subscription benefits:** 🔒 **不建。Andy 2026-08-25 定。**（下方文案留档,将来要开再取）
```
· Everything above, plus the book itself — my live positions in order of size, updated when they change,
  with the arithmetic that set each one.
```

> **抄 TSF 的关键设计:** founding 档($499 vs $399,只贵 25%)给的是**他本来就要管的自己的组合** —— 零边际成本。你的对应物就是「持仓 + 仓位排序 + 定size的算术」,你每天本来就在做。

---

## 3. 定价 —— 🔒 已定(Andy 2026-08-25)

| 档 | 后台实际 | 状态 |
|---|---|---|
| 月 | **$39** | ✅ 已设 |
| 年 | **$399** | ✅ 已设 |
| Founding | — | 🔒 **不建** |

> 🔒 **付费目前不开启。** 先把货架和读者建起来,架墙的时机另议(墙的位置见 `_BOILERPLATE.md` 块 D)。
> *留档:原建议年费 $349、founding $599。Andy 定 $399 / 不建 founding。定价是他的决定,不再讨论。*

---

## 4. About 页

### 4a. 三家对标(2026-08-25 实读 TSF / JB / Le Shrub 的 About 页)

| | **TSF** | **JB** | **Le Shrub**(#10 Finance, 34K 订阅) | **我们(现行 §4)** |
|---|---|---|---|---|
| 长度 | 中等 | **~1,850 词** | **~120 词** | ~280 词 |
| 开头是 | **产品** | **产品/理念** | **产品** | **人 + 理念** |
| 个人故事 | 无 | 无 | 无 | **有** |
| 写频率 | ✅ 4x/周 | ✅ 日更+周末 | 隐含 | ❌ **没写** |
| 「你能拿到什么」清单 | ✅ 三条 | ✅ 全篇 | ✅ | ❌ **没有** |
| 免责 | ✅ 大段 | ✅ | 模板自带 | ❌ **没有** |
| 报价 | 无 | ✅ $10/天 | 无 | 无 |

**三条读出来的东西:**

1. **长度不是杠杆。** 120 词的 Le Shrub 是 Finance 第 10、34K 订阅,About 基本是 Substack 默认模板;
   1,850 词的 JB 是第 3。**两端都成立** —— 说明 About 页不是增长引擎,别照着 TSF 的样子把它做成落地页。
2. **三家全部「产品先行」,没有一家从人开头。** 我们是唯一从人和理念开头的
   —— 这**不改**。三家都不写这个,正是它成为我们的东西的原因;而且 Le Shrub 证明了
   把 About 优化成 TSF 那样并不带来增长,那就等于白白交出唯一属于自己的一段。
3. **但我们缺的三件他们都有**:频率 · 「你能拿到什么」· 一句免责。
   尤其免责 —— 我们的 About **写了 39.9% 这个具体数字**,一个具体的业绩数字旁边不放免责,是风险不是风格。

**✅ 结论:声音不动,补三件。** 在「I won't promise to be right…」之后、Fluxus 命名那段之前插入:

```
What you get: one letter a week, every Sunday. Every idea with its entry, its stop, and what
I'm risking in percent — of the trade and of the account. The book in order of size. And the
losses, which are most of them: my win rate is 39.9%.
```

结尾追一句(用 `_BOILERPLATE.md` 块 A 已有的自有语言,不另造):

```
None of this is advice. I don't know your account, your taxes, or how well you sleep.
Measure your own water.
```

> ⏳ **状态:待 Andy 点头再粘。** 站上现在是下方 §4 正文(2026-08-25 已替换掉 3 年前旧版),
> 这两块是在它之上的增补,不是重写。

### 4b. 正文(站上现行版本)

```
The market is a game. Most people play it with their feelings.

This is where I write down how I play it with measurements instead.

I'm a full-time discretionary swing trader based in Japan. I started as a day trader, got humbled,
and grew into swing trading — I hunt leaders when momentum is loud and trade ES/NQ when it isn't.
I learned under a hedge fund manager who had navigated every bear market since the 1980s, which is
a long way of saying I learned defense first.

I don't treat the market as the world. I treat it as a game that takes real-world inputs and then,
mostly, ignores them. I hold no strong opinions about where it's going. I hold measurements. The
crowd plays on feelings and shows up late. The big funds play on autopilot and sell whatever their
risk limits tell them to. My only edge is being the calm one in the room who did the arithmetic
before he felt anything.

Everyone tells you what to buy. Almost nobody tells you how much — and how much is the part that
decides your year. So that's what this letter is about. Every idea here comes with its size and its
stop. You'll never have to ask me how much.

I won't promise to be right. Accuracy isn't mine to control. I promise the thinking always walks
the last step.

The name pays tribute to Fluxus, the 1960s–70s art movement that prized the event over the object,
chance over control, and dry wit over spectacle. A trade plan, it turns out, is just an event score.
Volatility is just chance you've decided to befriend.
```

---

## 5. Welcome 页(新订阅者落地页 —— TSF 的 X bio 直接指向这里)

```
Thanks for subscribing.

Three things so you know what you just walked into.

I measure, I don't predict. There are no calls here, no alerts, no price targets pulled out of the
air. I'll tell you what the tape is doing, what it would take to change my read, and what I'm
risking. If you want someone to tell you the future, there are louder letters.

Every idea comes with its size. This is the whole point. An idea without a size isn't a trade, it's
a conversation. You'll see the entry, the stop, the trade risk in percent, and the portfolio risk in
percent — on every single one, winners and losers alike.

You'll see the losses. My win rate is 39.9%. I lose more often than I win and the year still works,
because the winners are 3.40x the losers. If I only showed you the good ones you'd learn the wrong
job.

One letter a week. Every Sunday. If a week gives me something worth an extra one, you'll get it —
but the promise is one, and I'd rather keep a small promise than break a big one.

Start here → [Start Here 那篇的链接]
The record → [Track Record 那篇的链接]

— Fluxus
```

---

## 5b. Welcome email — paid subscribers(草稿,Andy 2026-08-25 指派起草)

*后台位置:Settings → Emails → Welcome email to paid subscribers。目前仍是 Substack 默认模板。*
*⚠️ **付费暂不开启**,所以这封短期内不会触发 —— 但先备好,开墙那天不用临时写。*

**Subject:**
```
You're in.
```

**正文:**
```
You're in. Here's what changes.

You get every letter, not just the free ones — the same letter, with no wall in the middle of
the arithmetic.

You get the book. Positions in order of size, each with its entry, its stop, the trade risk and
the portfolio risk. It goes up before the trade resolves, which is the only version of that
worth reading.

You get the ones that didn't work. My win rate is 39.9%. The losers are in the letter for the
same reason the winners are — a record that shows you only the good half teaches the wrong job.

One letter a week, every Sunday. And if a week goes by where I have nothing measured that's
worth your time, I'll say so instead of filling the space. That's the deal.

— Fluxus
```

> **这封的活儿是消化买家后悔**,不是再推销一次。所以三段都是「你现在拿到了什么」的具体物,
> 不是形容词;最后一段先承认「可能有没东西可写的一周」——**先说出来,比第三周被发现强**。

---

## 5c. Welcome email — imported subscribers(草稿,Andy 2026-08-25 指派起草)

*后台位置:Settings → Emails → Welcome email to imported subscribers。目前仍是 Substack 默认模板。*
*触发场景:从 Discord / 旧名单 / 老 Fluxus 订阅者导进来的人 —— **他们没主动订过这份刊物**。*

**Subject:**
```
This is How Much.
```

**正文:**
```
You're getting this because you're already somewhere I write — the Discord, an old list, or you
signed up for Fluxus before it had a name.

This is How Much. It's a market letter about size: every idea arrives with its entry, its stop,
and what I'm risking in percent. One letter a week, every Sunday.

I measure, I don't predict. No calls, no alerts, no price targets pulled out of the air. And
you'll see the losses — my win rate is 39.9%, and the year still works because the winners are
3.40x the losers.

If that isn't what you want in your inbox, unsubscribe in one click. I'd rather have a short
list that reads than a long one that doesn't.

— Fluxus
```

> **这封唯一的活儿是压住投诉率。** 导入名单最大的风险不是退订,是被标垃圾邮件 —— 一旦标了,
> 后面每一封的送达率都受损。所以**第一段就解释「你为什么会收到这个」**,最后一段**主动把退订推到他面前**。
> 「宁可名单短而有人读」这句不是客气,是这封信的全部策略。

---

## 6. Sections(Substack 分栏)—— 🔒 方案 C:两个栏 + 主 feed

*2026-08-25 改。旧版开 4 栏,和 `06_SECTIONS.md` 论证过的方案 C 冲突。**你现在有 0 篇 —— 4 个空栏比没有栏更难看。***

| 位置 | 内容 | 档位 | 为什么 |
|---|---|---|---|
| **主 feed** | **How Much** —— 旗舰,每周日一封 | 付费(前期免费) | 主 feed 触达最全,旗舰要吃满,不进栏 |
| **Method** | 仓位方法库(`05_SIZING_TERRITORY` 的 20 篇) | 免费 | 会长到 20+ 篇,**天然需要被浏览和被链接**;免费层拆邮件列表的代价最小 |
| **The Ledger** | 月度业绩 + 全部亏损 | 付费 | 月更、格式固定,**独立成栏 = 让人一口气翻完你所有业绩披露,这个动作本身就是转化** |

**先不开的两个**:`Testimonials`(0 订阅者,开了是空的,等 20 条真实反馈)· `Signals`(个股就在旗舰里,单开等于把旗舰拆成两半)。

> **判据**:JB 有 1,259 篇也不分栏;TSF 有 355 篇才用 4 个栏。**分栏是给已有存量的人用的。**
> **提醒:** TSF 互动最高的三篇里两篇是**教学长文**,不是个股。Method 栏别当边角料。

### 6b. 导航栏(不是栏目,零成本,当天可做)—— 这才是 0 篇时最该做的事

*JB 排第 3、1,259 篇、一个分栏没有,**但导航栏钉了 6 篇**。他把说服路径放在导航,不放在分栏。*

#### 🔴 现状对账(2026-08-25 实测)

**Sections 后台是 0 个栏** —— 所以 `My methods` / `My A+ setups` 不是栏目,是**自定义导航链接**。
**两个都指向不存在的页面:**

| 现在的位 | 指向 | 实测 |
|---|---|---|
| Home | `/` | ✅ |
| **My methods** | `/methods` | 🔴 **Page not found** |
| **My A+ setups** | `/A+setups` | 🔴 **Page not found**(URL 里还带 `+`) |
| Archive | `/archive` | ✅(0 篇) |
| About | `/about` | ✅ |

> **五个导航位里两个是 404。** 这不是「和规划不一样」的问题,是站上现在就有的可见破损。
> 五篇上架前必须处理:要么删掉这两个链接,要么把它们指到真实文章。
> 好消息是这两个名字**正对应下表的前两位** —— 上架后直接改指向即可,名字都不用换。

| 导航位 | 指向 | 证明什么 |
|---|---|---|
| Start Here | `01_start_here` | 导航 |
| 我的方法 | `02_nobody_tells_you_how_much` | 方法透明 |
| 完整业绩 | `03_i_lose_more_than_i_win` | 真实且敢亮亏损 |
| 一次失败的研究 | `05_null_result` | 诚实 |
| 我怎么定 size | 仓位公式(`02` 的锚点) | **差异化本身** |
| 测量栈 | dashboard 截图 | 能力 |

### 6c. 每篇页脚(固定块,一字不改)

```
How Much — one letter a week, every Sunday.
Every idea arrives with its size and its stop.
```

---

## 7. 开台当天就要做的两件非内容事

**① 设置 Recommendations(这是他 400 人的真正来源)**
- Substack 后台 → Settings → Recommendations
- 目标 **30–50 个互推伙伴**
- 优先级:① 中文圈交易类 Substack(**他完全吃不到**) ② 你 7 月普查的 46 个 fintwit 账号里有 Substack 的 ③ TSF 那 50 人名单里和你调性不冲突的
- **这件事和粉丝数无关,做一次管一年。开台第一天就做。**

**② X bio 改成漏斗**
当前:
> Full-time thematic swing trader in Japan. Apprentice of mathematics, ally of volatility. Sometimes the job is having no job. 纪律 · 耐心 · 偶尔手痒 | NFA

改成(保留你的味道,加上硬导流 —— 抄 TSF 的三行式):
```
Full-time swing trader in Japan. I don't have opinions, I have measurements.
• How Much — a weekly letter about size. Sundays.
• 7 years of real returns, losers shown
• Fluxus Analytics 👇
```
+ 链接位放 `fluxuscapital.substack.com/welcome`

---

## 8. 中文线(他吃不到的市场)—— 待你决定

TSF 只有英文。你的双语能力是他结构性够不到的地方,而 Substack 推荐网络里中文交易刊物是一个几乎没人做互推的洼地。

三个选项,**这个我不替你决定:**

| 方案 | 做法 | 代价 |
|---|---|---|
| **A. 纯英文**(现在的稿都是) | 和 Voice Bible / Homepage 一致 | 放掉中文洼地 |
| **B. 双语同刊** | 每篇 EN 正文 + 中文摘要块 | 每篇多 20% 工作量,版面变重 |
| **C. 中文独立第二刊** | 另开一个中文 Substack,互推自己 | **抄 TSF 的招** —— 他把 founding 产品独立成第二刊,自己推荐自己,吃第二个推荐位 |

我的倾向是 **C**,但要等英文刊跑顺(≥ 4 周)再开,否则两边都薄。
