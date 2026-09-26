# 会员问卷 · 开场白与 Discord 引导句（2026-09-26）

*任务 T-0926-54 · Writer Mia 执笔。Brief 出处：`data/growth/member_survey_2026-09-26.md`「接上课程通告 · 给 Mia 的润色 brief」节（提交 56fb92aa）。*
*声音对齐 Andy 09-25 会员通告：短句 · 给具体日期 · 先说结论 · 不推销 · 不用敬语 · 中英分写不做对照翻译。*
*表单：https://docs.google.com/forms/d/e/1FAIpQLSeuTr2L32sF6tEpvpIC-amAjLb4xEX-Jlb8M9jkbVHjeMYHWA/viewform*

---

## 一、表单开场白

### 中文

> 昨晚那条课程通告，这是下一步。
>
> 10/1 直播讲什么，按这份问卷的答案定。30 题，多数是选项，5 分钟。最后三题开放，我一条条读。
>
> 有一题问你能扛多大回撤。我今年最深的回撤 17.9%，1 月底到 3 月中。那个坑不是每个人都该踩，我需要知道你站在哪。

### English

> Last night's announcement — this is the next step.
>
> What I cover in the 10/1 live session is decided by these answers. Thirty questions, mostly multiple choice, five minutes. The last three are open. I read those myself.
>
> One of them asks how much drawdown you can sit through. Mine ran 17.9% this year, late January into mid-March. Not everyone should take that ride. I need to know where you stand.

## 二、Discord 引导句（发在通告下面或 #announcement）

### 中文

> 10/1 直播讲什么，按这份问卷定。5 分钟，最后三题我自己读。
> https://docs.google.com/forms/d/e/1FAIpQLSeuTr2L32sF6tEpvpIC-amAjLb4xEX-Jlb8M9jkbVHjeMYHWA/viewform

### English

> The 10/1 live session follows these answers. Five minutes, thirty questions, last three are open — I read those myself.
> https://docs.google.com/forms/d/e/1FAIpQLSeuTr2L32sF6tEpvpIC-amAjLb4xEX-Jlb8M9jkbVHjeMYHWA/viewform

---

## 三、改了什么，为什么

**开场白原稿第三句的数字换掉了。** 原稿写「我自己 YTD 是 130%，SPY 是 11%」——这两个数在仓库里找不到权威源：`PERFORMANCE_TRUTH.md` 最新一期（Period 2）只到 2026-08-30，口径是已实现 **+114.36%**；SPY **+9.60%** 是 H1 到 07-22 那个窗口的数。发给会员的数字不能是转抄来的。

换成 **最大回撤 −17.9%（2026-01-28 → 03-19，盯市）**——`PERFORMANCE_TRUTH.md` 在这一行旁边写着「**This is the number to publish**」。它承担的是同一个修辞任务（把「你能扛多大回撤」那一题立起来），而且比「我赚了多少」更贴那道题问的东西。

🔴 **如果 Andy 想把 YTD 收益放回去**：需要先跑一次 `truth_snapshot.py` 把权威源更新到 09-26，不能直接用 130%/11%。这是一句话的事，但得先跑。

**其余三处润色**：
- 开头从「我想把接下来三个月做对，所以先问你们」换成「昨晚那条课程通告，这是它的下一步」——brief 第 1 点要求第一句就让人想起通告，原稿第一句是自述动机，没接住。
- 「10/1 直播按答案定」从原稿里没有，提到第二段开头——brief 第 2 点说这是答题的即时理由，比「帮助我们改进」强。
- 「最后三题我会一条条读」保留原稿，这句是原稿里最好的一句，它承诺的是人工阅读不是统计。

**四条禁止项自查**：全文零敬语 ✅ · 无内部词 ✅ · 无「更好地服务」这类话 ✅ · 未提问卷末尾那两题的主题 ✅。
**与通告不冲突自查**：未提价格、未提退款、未提老学员升级、未改任何日期承诺；只引用了通告里已有的 10/1 直播。
