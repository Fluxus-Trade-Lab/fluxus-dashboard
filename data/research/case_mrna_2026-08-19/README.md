# MRNA 2026-08-19 · +177% EP —— 我们的数据端抓没抓到

*Andy 08-20："今天市场有一个很大的走势 MRNA…我们的数据端和 scanner 有没有发现它，这是一个很大的 EP。"*
*事件：个性化 mRNA 癌症疫苗 Intismeran（与 Merck Keytruda 联用）三期达标——mRNA 癌症疫苗首个成功三期。当日 +177%（62.96 → 174.38），量 12.8×，$69.6B 市值创近一年新高（离 52 周高点 −1.3%）。*

## 一句话答案

**抓到了，而且是两层**：EP 当天四个筛选器齐亮（EP / 4% / Vol Up / Momentum 97）；更值钱的是**前一天（08-18）它就躺在 Today's List 的 Liquid Leader Pullback 格里**——安静的 −2.3% 日、离 50 日线 0.4 ATR、离 21EMA 0.6 ATR、RS 线自百分位 90、`top_3m=true`。教科书式的"领头股回踩"，第二天等来的是史诗级 catalyst。

## 逐层记录（全部来自当晚归档，非事后重算）

| 层 | 08-18（EP 前一日） | 08-19（EP 日） |
|---|---|---|
| **筛选器** | 08-17 healthy_charts | **episodic_pivot + gainers_4pct + vol_up_gainers + momentum_97** 四连（ticker_events.csv） |
| **Today's List** | **liquid_leader_pullback**（28 只之一，页面可见）+ liquid_leaders | true_market_leaders（**TML 首日**）+ pp_today + **extended**（ATR 位 9.6 = 减仓区） |
| **leaders_log** | 08-14 起连续在 liquid leader 名册（rs_3m 82→88） | tml=True, rs_1m 99, rs_3m 99 |
| **主题层** | Genomics **Weakening**（excess_3m 已连涨 4 天：0.10→0.20） | Genomics 单日翻 **Leading**（excess_3m 0.295, rs_accel 转正） |
| **RS 线** | pctl_21 = 90（一个月高位区） | 21/63 双 100 |
| **heat 榜** | — | 分 9.0，排 **71**/3235，差 0.5 分进 top-50 |

## 哪些格子没显示它（全部是设计使然，不是漏）

- **4% Bullish / Momentum 97 / Weekly 20%+ 面板**：08-19 起与预设对齐 `excludeHealthcare`——MRNA 是 Healthcare，被闸在外。**oratnek 的同名格也会闸掉它**（他的预设同样排除 Healthcare）；这是这道闸的已知代价：生物科技的 EP 永远不走动量格，走 EP 格。
- **momentum97_shadow 三份名单**：同上，Healthcare 被排除。
- **watchlist 没有 EP 格**：EP 只活在 Screener 页的 episodic_pivot.json 里，晨报 zones 里没有它的位置——**这是真缺口**（验刀报告第三节早写过：EP 精度 61% 是最准的入场刀，Today's List 却没有 EP 格）。
- **heat 榜差 0.5 分**：单日四连亮 = 8 分 + 08-17 healthy 1 分 = 9.0，top-50 门槛 9.5——heat 的设计是"多日合流"，对单日核弹钝感。是否给 EP 权重加一档（3→4）或单日 ≥3 个筛选器直接入榜，待议。

## 交易语义（按验刀手册的五步读）

- 08-18 的它：水域 ✗（Genomics 还是 Weakening——**回踩买入要配 Leading 主题，这条会把它滤掉**；NBIS 6 月教训的镜像：这次滤掉的是个 +177%）。这不是规则错了——统计上回踩×Weakening 主题就是负期望——是**规则的代价被一个尾部事件照亮**。规则不因单例改。
- 08-19 的它：EP 日**当天不追**（Delayed EP：42% 击穿 EP 日低点；且 chase 标志 +177% 灼热、ATR 位 9.6 在 extended 减仓区）。**从 08-24 起（EP 后第 3 个交易日）它自动进 delayed_ep_log 的观察窗**——basing→breaking 的二次突破才是我们统计里 61% 精度的入口。fwd 数字 5/10 日后自动可查。

## 待议（不动手，等 Andy）

1. Today's List 加 **EP 格**（entries 区，读 episodic_pivot.json 同配方 + $1B/$20M 门）——验刀报告的旧建议，今天有了最好的案例。
2. heat 对单日多筛选器合流的钝感（9.0 vs 9.5）。
3. `excludeHealthcare` 在三个动量格保留（对齐预设 + oratnek），但 EP 格若建，**不排除** Healthcare——EP 的本质就是重定价，生物科技是主产区。
