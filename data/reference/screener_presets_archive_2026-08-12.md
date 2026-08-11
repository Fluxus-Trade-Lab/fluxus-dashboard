# 预设 Screener 存档 · 2026-08-12

*应操作者要求存档,改动前的基线。权威定义:`frontend/public/data/screener-presets.json`;*
*原始快照:[archive/screener-presets_2026-08-12.json](archive/screener-presets_2026-08-12.json)。*

## 求值链(改之前要知道的三件事)

1. **Watchlist 页对每个 readonly 预设先叠一层默认底**(`WatchlistTab.jsx`):
   市值 ≥ $1B、50 日均量 ≥ 1M 股、不剔除 Healthcare —— 预设自己的同名键可覆盖它。
2. **每张卡按 `rs_21d` 降序排**(日历月收益的横截面百分位,即页面右上角 Sorted by RS1M)。
3. **Top Overlap = 出现在 ≥2 个预设里的 ticker**,按次数排,取前 15。

已知关联缺陷(改预设时会撞上):`pp_count_30d` 用的是「量>前10根**全部** K 线」的现行定义,
和 Morales 原定义(只比下跌日)相差 Top10 七个名额 —— 见 `accumulation_audit.md`,你叫停未修。
`rs_21d/63d/126d` 名为交易日、实为日历口径,正名 `rs_1m/3m/6m` 已并存。

**存档过程中修掉的一个活缺陷(2026-08-12):** `perf_1w_pctile / perf_3m_pctile`
也在用 `na_option='bottom'` —— 缺数据的票拿满分位。112 只无周收益的票坐在
≥97 周分位(含 ADSK),它们直接喂 **97 Club 预设**和 **momentum_97 旗标**。
已改 `'top'`;修后 momentum_97 旗标 83 只、全部数据完整。
**这意味着下一次流水线跑完,97 Club 和 Momentum 97 两张卡的名单会变干净、可能变短 —— 是修复,不是预设改动。**

## 21EMA Watch  (readonly)

| 条件 | universe 列 | 范围 | 单位/口径 |
|---|---|---|---|
| `marketCapMin` | `market_cap` | 1.0 | ×$1B |
| `excludeHealthcare` | `sector` | True | 剔除 Healthcare |
| `trendBaseOnly` | `trend_base` | True | 价>50SMA 且 10WMA>30WMA |
| `weeklyPct` | `perf_1w` | 0 … 15 | %(日历周) |
| `dcrPct` | `dcr_pct` | 20 … 100 | %(收盘位于日内区间的位置) |
| `ema21Atr` | `ema21_r` | -0.5 … 1 | ATR 倍数(距 21EMA) |
| `sma50Atr` | `sma50_r` | 0 … 3 | ATR 倍数(距 50SMA) |
| `ppCount` | `pp_count_30d` | 1 … 999 | 30 日内 pocket pivot 次数 |
| `adrPct` | `adr_pct` | 3.5 … 10 | % |

## 4% Bullish  (readonly)

| 条件 | universe 列 | 范围 | 单位/口径 |
|---|---|---|---|
| `marketCapMin` | `market_cap` | 1.0 | ×$1B |
| `excludeHealthcare` | `sector` | True | 剔除 Healthcare |
| `dailyPct` | `change_pct` | 4 … 999 | % |
| `relVolume` | `rel_volume` | 1 … 999 | × |
| `fromOpenPct` | `from_open_pct` | 0 … 999 | % |
| `rs21d` | `rs_21d` | 60 … 99 | 0-99 横截面百分位(日历月收益) |
| `adrPct` | `adr_pct` | 3.5 … 10 | % |

## Vol Up Gainers  (readonly)

| 条件 | universe 列 | 范围 | 单位/口径 |
|---|---|---|---|
| `marketCapMin` | `market_cap` | 1.0 | ×$1B |
| `excludeHealthcare` | `sector` | True | 剔除 Healthcare |
| `dailyPct` | `change_pct` | 0 … 999 | % |
| `relVolume` | `rel_volume` | 1.5 … 999 | × |
| `adrPct` | `adr_pct` | 3.5 … 10 | % |

## Momentum 97  (readonly)

| 条件 | universe 列 | 范围 | 单位/口径 |
|---|---|---|---|
| `excludeHealthcare` | `sector` | True | 剔除 Healthcare |
| `trendBaseOnly` | `trend_base` | True | 价>50SMA 且 10WMA>30WMA |
| `perf1wPctile` | `perf_1w_pctile` | 0.97 … 1 | ? |
| `perf3mPctile` | `perf_3m_pctile` | 0.85 … 1 | ? |
| `adrPct` | `adr_pct` | 3.5 … 10 | % |

## 97 Club  (readonly)

| 条件 | universe 列 | 范围 | 单位/口径 |
|---|---|---|---|
| `marketCapMin` | `market_cap` | 1.0 | ×$1B |
| `excludeHealthcare` | `sector` | True | 剔除 Healthcare |
| `trendBaseOnly` | `trend_base` | True | 价>50SMA 且 10WMA>30WMA |
| `hScore` | `h_score` | 80 … 99 | 0-99 |
| `rs21d` | `rs_21d` | 97 … 99 | 0-99 横截面百分位(日历月收益) |
| `adrPct` | `adr_pct` | 3.5 … 10 | % |

## Stockbee 9M Setup  (readonly)

| 条件 | universe 列 | 范围 | 单位/口径 |
|---|---|---|---|
| `marketCapMin` | `market_cap` | 1.0 | ×$1B |
| `vol50dMin` | `avg_volume` | 9.0 | ×1M 股 |
| `excludeHealthcare` | `sector` | True | 剔除 Healthcare |
| `relVolume` | `rel_volume` | 1.5 … 999 | × |
| `dailyPct` | `change_pct` | 5 … 999 | % |
| `dcrPct` | `dcr_pct` | 60 … 100 | %(收盘位于日内区间的位置) |

## Sugar Babies  (readonly)

| 条件 | universe 列 | 范围 | 单位/口径 |
|---|---|---|---|
| `marketCapMin` | `market_cap` | 1.0 | ×$1B |
| `excludeHealthcare` | `sector` | True | 剔除 Healthcare |
| `boCount1y` | `bo_count_1y` | 10 … 999 | 1年 |
| `boCount3m` | `bo_count_3m` | 2 … 999 | 3月 |

## Pocket Pivot  (readonly)

| 条件 | universe 列 | 范围 | 单位/口径 |
|---|---|---|---|
| `marketCapMin` | `market_cap` | 1.0 | ×$1B |
| `excludeHealthcare` | `sector` | True | 剔除 Healthcare |
| `pocketPivotOnly` | `pocket_pivot` | True | 当日为 pocket pivot(现行定义:量>前10根全部) |
| `trendBaseOnly` | `trend_base` | True | 价>50SMA 且 10WMA>30WMA |
| `adrPct` | `adr_pct` | 3.5 … 10 | % |

## PP Count  (readonly)

| 条件 | universe 列 | 范围 | 单位/口径 |
|---|---|---|---|
| `marketCapMin` | `market_cap` | 1.0 | ×$1B |
| `excludeHealthcare` | `sector` | True | 剔除 Healthcare |
| `trendBaseOnly` | `trend_base` | True | 价>50SMA 且 10WMA>30WMA |
| `ppCount` | `pp_count_30d` | 3 … 999 | 30 日内 pocket pivot 次数 |
| `adrPct` | `adr_pct` | 3.5 … 10 | % |

## Weekly 20%+ Gainers  (readonly)

| 条件 | universe 列 | 范围 | 单位/口径 |
|---|---|---|---|
| `marketCapMin` | `market_cap` | 1.0 | ×$1B |
| `excludeHealthcare` | `sector` | True | 剔除 Healthcare |
| `weeklyPct` | `perf_1w` | 20 … 500 | %(日历周) |
| `adrPct` | `adr_pct` | 3.5 … 10 | % |

---

## 基线后的变更记录

| 日期 | 预设 | 变更 | 当日影响 |
|---|---|---|---|
| 2026-08-12 | 21EMA Watch | `adrPct.min` 3.5 → 3 | 复算与当日截图逐字吻合(4 只);降档后 +1 只(EBAY)。ADR 3–3.5% 档的名字波动更温和,回踩名单会略宽 |
