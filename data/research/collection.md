# 馆藏 —— Andy 的收藏夹（Nighty Zac 整理）

> 来源：`night_reports/INBOX.md` 收藏夹节。每条：日期 · 链接 · 三五句摘要 · 判定（✅采纳→去向 / 📦存档 / 🗑丢弃+理由）。判定在晨报同步给 Andy。

---

## 2026-08-24 判定

### 📦 存档｜[08-23] How to Catch Powerful Stock Reversals (4B- Setup)

- **链接**：https://www.youtube.com/watch?v=1k3KRbktibQ
- **实为**：Deepvue 的产品 webinar（频道 Deepvue，2024-10-19，**69 分钟**，6,892 次观看）。不是独立教学，是**软件演示**——一半时长在讲怎么在 Deepvue 里加列、配指标、存 watchlist。
- **Andy 的话**：「reversal setup，我们图书馆和课程里没有详细记录和了解的」

**它讲的是什么**：Stan Weinstein 的四阶段分析（Stage Analysis），核心桥段是 **4B Minus 反转 setup** —— Stage 4 下跌末端的**筑底**买点。视频自己给的关键规则只有一句（时间戳 48:22 原文）：

> "Key rules for trading the 4B Minus setup (**higher low, reclaim 50-day MA**)"

配套还讲了 Mansfield Relative Strength 指标、Stage 2 vs 2A（早期 Stage 2）的区别、以及 Weinstein 本人在 Netflix 上用 4B- 的实例。

**和哪条线有关 —— 我们其实两个零件都有，只是没接起来**：

| 4B- 的成分 | 我们的现成实现 |
|---|---|
| higher low（下跌后的更高低点） | `sp_hl` / `ll_hl_1st` / `ll_hl_2nd` 面板（[structure_pivot.py:110](../../pipeline/screeners/structure_pivot.py#L110)、[watchlist.py](../../pipeline/screeners/watchlist.py)） |
| reclaim 50-day MA | `ma_reclaim` 面板（close 上穿 21EMA / 50SMA，[watchlist.py:130](../../pipeline/screeners/watchlist.py#L130)） |
| Stage 2 闸 | `trend_base` = close>SMA50 且周线 WMA10>WMA30 —— [screener_methods.md:38](../reference/screener_methods.md) 自己就注了这是「Stan Weinstein 式的在 Stage 2 闸」 |
| **Stage 4（下跌中）前置条件** | ❌ **我们没有**。我们只有「在 Stage 2」的正向闸，没有四阶段分类 |
| **Mansfield RS** | ❌ 没有。我们有 `rs_line_pctl_*`，不是 Mansfield 那个公式 |

**判定：📦 存档，不采纳**。理由三条：

1. **它的方法内容我们已覆盖 3/5**，缺的两块（Stage 4 分类、Mansfield RS）是**定义问题不是发现问题**——真要补，读 Weinstein 原书比看软件演示准。
2. **它是产品演示**。69 分钟里方法密度低，且所有 setup 都绑在 Deepvue 的界面上。
3. **`ll_hl_*` 链条正在被审**：08-23 的 waiver 裁决里，第一波链 holdout 失败已从 entry 席移除。现在往这条链上再加 setup **是规格先于证据**（[[pitfall_shipped_before_out_of_sample]]）。

**存档但记一条可测的问题**（给 Andy，不动工）：我们的 `ll_hl_1st` 和 `ma_reclaim` 现在是**两个独立面板**，Weinstein 的 4B- 说这两件事**必须同时**。我们的归档能直接回答「两个同时命中的票，和只命中一个的，前瞻收益差多少」——**零新数据、零新定义**。如果 Andy 想要一个便宜的实测，这是最便宜的一个。

---

## 2026-08-25 判定

> 本批四条全是 X 帖。走 OPS 08-24 定的镜像 `api.fxtwitter.com/<用户>/status/<id>` —— **四条全通**（08-24 直连 x.com 那次是 402 登录墙）。
> **两条是 X Article（长文）入口帖，正文镜像取不到**（`/i/article/<id>` 返回 404）——见下。

### ✅ 采纳｜[08-24] @Hrundel75 —— 「price direction is mostly noise. but volatility? predictable.」

- **链接**：https://x.com/Hrundel75/status/2091187956589690972 · 2026-08-22 · 2,710 粉
- **传播**：791,498 曝光 / 4,067 ♥ / **11,357 收藏** —— **收藏/赞 = 2.79，压过 Muninn 的 2.60，是我们量过的全库新高**。
  2,710 粉做到 79 万曝光 = **292× 粉丝数**。（「收藏比与粉丝无关」第七次复现，数据点归 [Fluxus_Muninn_Teardown.md](../../Fluxus_Brand/research/Fluxus_Muninn_Teardown.md) 那张表。）
- **Andy 的话**：「好像很重要」

**它说的是什么**（原文照引，他的话）：

> quant desks at citadel and D.E. Shaw don't ask "will it go up?" - they ask **"will the next move be large or small?"**
> because sizing correctly inside a vol regime is worth more than being right on direction

> the predictable part of markets was never price direction / it was the distribution of price. the size of the moves. which regime you're currently inside

**⭐ 这一句和 Andy 08-24 自己写的第三类问题逐字相同**，而他们互不相识。他给的机制是 Engle 的 GARCH / 波动聚集。

**判定：✅ 采纳 —— 已经变成了一轮预注册实测，当晚跑完。**
→ [`data/research/amplitude_2026-08/`](../amplitude_2026-08/results.md)

结果：**他的定性主张在我们自己的归档上成立，而且分离极干净**——事件前 20 日波动的五分位，
把事后 5 日右尾概率从 3.4% 拉到 19.0%（holdout 复制成 3.4%→17.5%）；
同一变量对方向的预测力 ρ=−0.006，p=0.59。**幅度 ρ=+0.30 (p=5e-157)，方向 ρ≈0。**

**但我们同时测出他没说的那一半**：期望值是**驼峰形**，最高波动分位的期望**翻负**——
右尾长大的同时左尾同步长大，payoff 比没跟着涨。**所以「幅度可预测」不等于「幅度可赚钱」。**
它的正确用法是**除数不是信号**（决定买几股，不决定买不买）。

**未验证的**：他帖里那两个 SPY 数字（低波状态 74% 续、波动尖峰 81% 续）**我们没查**——本轮测的是个股事件不是 SPY 状态机。别引用那两个数字当我们的结论。

---

### ✅ 采纳｜[08-24] @Muninn —— 复盘 Qullamaggie 900 笔入场，ADR 是最有解释力的变量

- **链接**：https://x.com/Muninn/status/2089746393183256879 · 2026-08-18 · 61,965 曝光 / 362 ♥ / 603 收藏（收藏比 1.67）
- **Andy 的话**：「收藏并学习」

原文（他的话）：

> After reviewing over 900 of Qullamaggies entries on breakouts and EPs the most insighftful and biggest epiphany is how important ADR is..
> He tells us to keep our entries <1 ADR... His sweet spot is 0.33 - 0.66 ADR.
> **But it turns out having a lower bound is better than a upper bound.** Entering stocks <0.25 ADR has a very low win-rate and negative expectancy..
> The other thing I was surprised by was that when he breaks this rule, cause he does.. its very profitable..

**判定：✅ 采纳为假设（H2），但实测下来在我们的口径里不成立为独立结果。**

两个理由，都要说清：
1. **口径不同**——他量的是**盘中入场那一刻已经走了多少 ADR**，我们只有**全天收盘涨幅 / ADR20**。
   一个是「进场时还剩多少路」，一个是「这天总共走了多远」。**我们这张表不能用来说他错了。**
2. **与 H3 混淆**——`adr20` 与 `pre_vol` 的 spearman = **+0.981**，是同一个东西的两个名字（[[pitfall_same_quantity_three_names]]）。
   `move_adr` 分桶大半是波动分位换了身衣服。holdout 上 `<0.25` 桶只剩 **n=19**，不下结论。

**要真正验证他这条，需要分钟级数据**——我们没有。列为 ❓ 未验证，不是 ❌ 证伪。

---

### 📦 存档（已有档，别重做）｜[08-24] @Muninn —— 「This is the article I wish I had when I started trading」

- **链接**：https://x.com/Muninn/status/2088292776047751193（正文在 X Article `2088143622180921344`）
- **⚠️ 这条我们已经拆过了**：[Fluxus_Brand/research/Fluxus_Muninn_Teardown.md](../../Fluxus_Brand/research/Fluxus_Muninn_Teardown.md)
  就是拿**这一条**做的样本帖（「收藏比 2.60 全库新高」那份）。**别再开第二份。**
- **我今晚的独立读数与那份档对得上**：views 258,506 / ♥ 521 / 收藏 1,353（该档记的是 258,040 / 521 / 1,355 —— 一天的自然漂移，一致）。
- **⚠️ 一处对不上，列进门铃**：该档写「**2026-08-03 发**」，镜像返回的 `created_at` 是 **Fri Aug 14 2026**。差 11 天。
  我不动 Marketing 线的文件，只报。
- **正文取不到**：X Article 长文镜像不支持（`/i/article/` 404）。**需真浏览器（Comet），留交互会话。**

---

### 📦 存档待读｜[08-24] @L1vsun —— X Article 入口帖

- **链接**：https://x.com/L1vsun/status/2088993353111159216 · 2026-08-16 · 5,235 粉
- **传播**：**1,366,198 曝光** / 401 ♥ / 1,543 收藏 —— 曝光是本批最高（**261× 粉丝数**），
  但**收藏/赞 = 3.85** 与 ♥/曝光 = 0.03% 这组合很怪：曝光巨大而互动极低。
  ⚠️ 上面 Hrundel75 那条**引用的正是这一条**，所以这 136 万曝光里有多少是被 Hrundel 带的、有多少是它自己的，**分不开**。
  在没分开之前，**别把这条的曝光数写进任何对标表**（[[pitfall_the_universe_chose_the_answer]]）。
- **帖子本体只有一个链接，零正文。** 正文在 X Article `2088966979189112832`，**镜像 404**。
- **判定：📦 存档待读 —— 需真浏览器（Comet），留交互会话。** 本轮不猜内容、不拿标题当结论。
