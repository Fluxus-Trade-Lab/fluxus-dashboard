# Screener 页 · 筛选参数与预设盘点(数据端视角)

*2026-08-17 从活代码抽取:`frontend/src/lib/screenerFilter.js`(筛选引擎)、`frontend/public/data/screener-presets.json`(10 个只读预设)、`frontend/src/components/screener/WatchlistTab.jsx`(Watchlist 叠加默认)、`pipeline/screeners/run_all.py` + `pipeline/adapters/*.py`(字段生产)。*
*姊妹文件:`screener_presets_archive_2026-08-12.md`(08-12 存档,当时 21EMA Watch adrPct.min 还是 3.5)。*

---

## 一、筛选参数(引擎认得的全部键)

规则:引擎里每个 range 键是 `{enabled, min, max}`;`min`/`max` 为 `''` 或 `null` 表示该侧不设限;**数据缺失的行一律不通过**(`null` → 剔除,不是当 0)。

### 1. 门槛与开关

| 键 | 数据字段 | 单位换算 | 生产处 | 定义 |
|---|---|---|---|---|
| `marketCapMin`(受 `marketCapEnabled`) | `market_cap` | 输入 $B → ×1e9 | Finviz | 市值 |
| `vol50dMin`(受 `vol50dEnabled`) | `avg_volume` | 输入 M 股 → ×1e6 | Finviz | 平均成交量(Finviz 的 Avg Volume) |
| `excludeHealthcare` | `sector` | — | Finviz | `sector != 'Healthcare'` |
| `trendBaseOnly` | `trend_base` | bool | yfinance_adapter | **close > SMA50 且 周线 WMA10 > WMA30**(需 ≥30 周历史,否则 False) |
| `pocketPivotOnly` | `pocket_pivot` | bool | yfinance_adapter | **当日阳线 且 当日量 > 前 10 根的最大量**(⚠️ 与 Morales 原版不同:原版只比前 10 根里的**阴线**量;审计过、Andy 说先不改) |
| `momentum97Only` | `momentum_97` | bool | run_all | 见 `momentum_97.py`,由 perf_1w/3m 分位 + trend_base 得出 |

### 2. 涨跌幅区间(数据小数,用户输入整数 %)

| 键 | 字段 | 定义 |
|---|---|---|
| `dailyPct` | `change_pct` | 当日涨跌(Finviz `Change`/`Change %`,yfinance 兜底 `close/prev_close−1`) |
| `weeklyPct` | `perf_1w` | Finviz 5 日累计 |
| `monthlyPct` | `perf_1m` | Finviz 21 日累计 |
| `fromOpenPct` | `from_open_pct` | `(close − open)/open`,当日 |

### 3. 均线距离(数据小数,输入 %)

| 键 | 字段 | 定义 |
|---|---|---|
| `sma20Dist` / `sma50Dist` / `sma200Dist` | `sma20_dist` / `sma50_dist` / `sma200_dist` | Finviz `(close − SMA)/SMA` |
| `ema21LowDist` | `ema21_low_dist` | `(当日 low − EMA21)/EMA21`,yfinance |
| `high52wDist` | `high_52w_dist` | `(close − 52 周高)/52 周高`,≤ 0 |

### 4. ⚠️ "ATR 距离"区间 —— **字段不是 R 值**

| 键 | 字段 | 引擎注释说的 | 字段实际是 |
|---|---|---|---|
| `ema21Atr` | `ema21_r` | "R-multiple, user enters R value directly" | **`1 + sma20_dist` = close / SMA20 的比值**(中位 1.016,p5 0.86,p95 1.20) |
| `sma50Atr` | `sma50_r` | 同上 | **`1 + sma50_dist` = close / SMA50 的比值** |

生产处 `run_all.py:291-292`,03-15 首版即如此,原 spec 里列名就叫 `'21EMA R', type: 'ratio'`。也就是说**字段一直是比值,是预设把它当成了 ATR 倍数**。而且叫 21EMA,算的是 SMA20。后果见第三节。

### 5. 其他区间

| 键 | 字段 | 数据单位 | 输入单位 | 定义 |
|---|---|---|---|---|
| `adrPct` | `adr_pct` | % | % | `ATR / close × 100`(Finviz ATR) |
| `vcs` | `vcs` | 0–100 | 同 | 波动收缩分 —— **2026-08-17 起为 oratnek VCS v2 忠实移植**(`pipeline/screeners/vcs.py`);之前是改造过的老版,尺子不同(中位 50→35) |
| `dcrPct` | `dcr_pct` | 0–1 | 0–100 | `(close − low)/(high − low)`,当日收盘位置 |
| `ppCount` | `pp_count_30d` | 整数 | 同 | 近 30 根里满足口袋支点定义的根数 |
| `relVolume` | `rel_volume` | 倍数 | 同 | Finviz Relative Volume |
| `boCount1m/3m/6m/1y` | `bo_count_*` | 整数 | 同 | 窗口内 **量 ≥ 9M 且涨幅 ≥ 4%** 的天数(Pradeep 原规则,Sugar Babies 用) |

### 6. RS / 分数区间(0–99 整数)

| 键 | 字段 | 定义 |
|---|---|---|
| `rs21d` / `rs63d` / `rs126d` | `rs_21d` / `rs_63d` / `rs_126d` | **别名** → `rs_1m` / `rs_3m` / `rs_6m`:perf_1m/3m/6m 在 **tradeable 集(≥$1B 且 ≥$2M 日成交额,2,557 只)内**的百分位 ×99;非 tradeable 行为 `null`;`na_option='top'`(缺失不得分,08-12 事故后统一) |
| `rsIbd` | `rs_ibd` | `0.4·rs_3m + 0.4·rs_6m + 0.2·rank(perf_1y)`,记录型指标(衡量过去一年的成绩单,不是当下) |
| `hScore` | `h_score` | `(2·f + 3·i + 1·rs_1m + 2·rs_3m + 2·rs_6m)/10` |
| `fScore` | `f_score` | eps_growth_next_y 与 revenue_growth 均值的分位;**当前两列源头全空 → 恒为 50**(非 tradeable 为 null) |
| `iScore` | `i_score` | 行业内 tradeable 成员 rs_3m **中位数**的分位 |
| `perf1wPctile` / `perf3mPctile` | `perf_1w_pctile` / `perf_3m_pctile` | 全池分位,0–1,`na_option='top'` |

---

## 二、10 个只读预设(`screener-presets.json`,2026-08-17 现值)

所有预设默认 `marketCapMin 1.0`($1B)+ `excludeHealthcare` 除非另注;`max: 999` 视为无上限。

| # | 名称 | 条件 |
|---|---|---|
| 1 | **21EMA Watch** | trend_base · 周涨 0–15% · DCR 20–100 · **ema21Atr −0.5–1 · sma50Atr 0–3(08-17 起 ATR 口径:→ `ema21_atr_dist` / `atr_from_sma50`,前端映射待改)** · PP 数 ≥1 · ADR **3–6**(08-17 上限 10→6) |
| 2 | **4% Bullish** | 日涨 ≥4% · RelVol ≥1 · from-open ≥0 · rs_21d 60–99 · ADR 3.5–10 |
| 3 | **Vol Up Gainers** | 日涨 ≥0 · RelVol ≥1.5 · ADR 3.5–10 |
| 4 | **Weekly Momentum 97**(原 Momentum 97,08-17 改名)| **无市值门槛** · trend_base · perf_1w 分位 ≥0.97 · perf_3m 分位 ≥0.85 · ADR 3.5–10 |
| 5 | **Monthly Leader 97**(原 97 Club,08-17 改名)| trend_base · h_score 80–99 · rs_21d 97–99 · ADR 3.5–**6** |
| 6 | **Stockbee 9M Setup** | **vol50dMin 9M** · RelVol ≥1.5 · 日涨 ≥5% · DCR 60–100 |
| 7 | **Sugar Babies** | bo_count_1y ≥10 · bo_count_3m ≥2 |
| 8 | **Pocket Pivot** | pocket_pivot · trend_base · ADR 3.5–**6** |
| 9 | **PP Count** | trend_base · pp_count_30d ≥3 · ADR 3.5–**6** |
| 10 | **Weekly 20%+ Gainers** | 周涨 20–500% · ADR 3.5–10 |

用户自建预设存 `localStorage['fluxus-screener-presets']`,`readonly:false`,不在仓库。

---

## 三、Watchlist 页的叠加规则(和 Screener 页不同)

`WatchlistTab.jsx:29` 对**每个**预设先套一层默认再叠预设自己的条件:

```
marketCapEnabled: true, marketCapMin: 1.0
vol50dEnabled:    true, vol50dMin:    1.0     ← Screener 页没有这条
excludeHealthcare: false                       ← 会被预设自己的 true 覆盖
```

后果:**Momentum 97 在 Watchlist 上有 $1B 市值门槛、在 Screener 上没有**;所有预设在 Watchlist 上多一道 ≥1M 均量。同一个名字两页出的名单可能不同 —— 这是设计还是疏漏,由 Andy 裁。

卡片内排序 `rs_1m ?? rs_21d` 降序;卡片间按名单长度降序;顶部"出现在多张名单上"的计数由此而来。

---

## 四、这次盘点发现的数据端问题

### ⚠️ A. `ema21_r` / `sma50_r` 是比值,预设按 R 值在用(实测 2026-08-14)

21EMA Watch 的 `ema21_r ∈ [−0.5, 1]` 在比值口径下 = **close ≤ SMA20**;`sma50_r ∈ [0, 3]` 在比值口径下 = 无约束(比值恒 >0、极少 >3)。

| 口径 | 今日命中 |
|---|---|
| 现状(比值) | **13 只,全部价格在 SMA20 之下** |
| 若按真 R:`(close−SMA20)/ATR ∈ [−0.5, 1]` 且 `(close−SMA50)/ATR ∈ [0, 3]` | **53 只** |
| 交集 | 11 |

两种读法都自洽 —— 一种是"回踩到 20SMA 之下",一种是"贴着 21EMA 上方 1 个 ATR 内、且在 50SMA 上方 3 个 ATR 内"。**哪种是 Andy 要的,决定要不要动。** 若要 R 口径:数据端加两列 `ema21_atr_dist`、`sma50_atr_dist`(需先补一列真 EMA21,现在池里没有 `ema21`,只有 `ema21_low_dist` 用过它),预设改指向新列;旧列保留不删。

### B. Screener 表里 30% 的行没有 RS(前端 08-17 量到,今日查因)

`heating_up.json` 50 行里 15 行不在 `groups.json` 的 stocks 表(2,557 只 = tradeable 集)。全部因**未过 $1B 市值 / $2M 日成交额地板**(BLMN 市值 $0.90B、HGTY 成交额 $1.9M,均擦线)。不是链路错位,是准入门槛的设计后果。修法二选一:① 全池打 RS 分(引擎按行算,便宜;主题/色带仍限 tradeable) ② 前端把「—」改成「低于 $1B/$2M 地板,未评分」。

### C. 已知、不动

- `f_score` 恒 50(源头两列空),h_score 里权重 2/10 是常量 —— 记录在 run_all 注释里
- `pocket_pivot` 与 Morales 原版定义不同 —— 审计过,Andy 说先不修
- `rs_21d/63d/126d` 是别名,前端迁到 `rs_1m/3m/6m` 后删
