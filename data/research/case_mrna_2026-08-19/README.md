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

## 过去一个月的蛛丝马迹（Andy 08-20 追问；快照 = git 里当晚的 universe.json，K 线 = yfinance 复算）

**07-17 → 08-06：真没有。** RS 线自百分位 5–24、在 21EMA 下方 4–14%、量 0.5–0.8×、离 52 周高点 −30%。系统安静是对的——那会儿它就是一只弱票（06-02 见 3 个月低点 45.64）。

**08-07 起，八个交易日，脚印一条接一条：**

| 日期 | 事件 | 我们哪里看得见 | 哪里被闸住 |
|---|---|---|---|
| 08-07 | **+9.9%、收复 21EMA**（e21 −8.2% → +0.8%） | `cross_ema21_up` 会是 True（字段 08-19 才上线） | **rv 0.93**：4% 筛选器（量 ≥1）差 7% 拦住；ma_reclaim 的量 ≥1 闸也会拦 |
| 08-10 | **收复 50SMA**（s50 −0.2% → +0.5%） | `cross_sma50_up` True | rv 0.85，同上 |
| 08-11 | trend_base 翻 True | 快照 | |
| 08-12 | **+5.1%、20 日新高** | hi20 ✓ | **rv 0.90**，4% 筛选器又差 10% |
| 08-14 | 进 liquid leader 名册（rs_3m 82） | leaders_log ✓（当晚归档） | |
| 08-17 | **20 日新高 + RS 线 21 日自百分位 = 100 同日**——验刀里 recall 51% 的"最早最广脚印" | healthy_charts 亮（归档 ✓）；rsL21=100 | 无 4%/PP/20% 周涨，三个"脚印格"都不亮——安静爬升的新高没有格 |
| 08-18 | 安静 −2.3% 回踩 | **Liquid Leader Pullback 格，页面可见**（归档 ✓） | 主题 Genomics 还是 Weakening——五步法会滤掉 |
| 08-19 | EP +177%、rv 12.8 | 四筛选器 + TML + pp_today + extended | |

快照里最干净的一条线：**rs_3m 八个交易日 56 → 63 → 83 → 81 → 82 → 82 → 86 → 88**、RS 线自百分位 48 → 100——底部翻身的全过程都在我们每晚的归档里，只是没有一个格以"安静的新高"为键。

**新发现（第三例了，待 Andy 拍）**：08-07/08-10/08-12 三次都被**量 ≥1 的闸**拦住（rv 0.85–0.93）——和验刀里 MU 08-04（rv 0.7）同型：**深跌后的底部反转，量比天然低**，因为分母（50 日均量）被崩盘时的天量抬高了。`ma_reclaim` 的量闸建议从 ≥1.0 降到 ≥0.8 或干脆去掉只显示 rv——只探不筛的格，闸太紧就失去了它存在的意义（它就是为 V 反造的）。

## 落地（Andy 08-20"三个都同意"）

1. **EP 格上 Today's List**：entries 区第二格 `episodic_pivot`（≥10% × 量 ≥3×，与筛选器同配方、测试锁死；**不排除 Healthcare**）。08-19 当天它会显示 MRNA。
2. **heat 单日合流加成**：同日 **≥4** 个筛选器（≥3 太松：档案里一天 23.5 次、286 只受益、门槛反被抬高；≥4 一天 4.2 次）+2 分/日。MRNA 9.0 → **11.0，第 43 名**，进榜。新字段 `confluence_days`。
3. 动量三格的 Healthcare 闸保留（对齐预设与 oratnek）。
