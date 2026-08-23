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
