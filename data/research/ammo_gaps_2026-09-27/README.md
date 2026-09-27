# 弹药缺口两个量：开盘区间回补 + 枢轴失败之后那一段

**任务 T-0927-64（linda，2026-09-27）** · 起因：X 调研两班连着两天报同一类缺口——
Linda Raschke 的帖密度排到前五、底下没人接话，而我们接不上，因为**没量过那个量**。
取件账 [`09-24n·6`](../../content/x_watch/README.md) / [`09-25n·3`](../../content/x_watch/README.md)。

Andy 的判据是一句话：**这两个量建起来，蹭位榜能不能从「只接形态」变成「我们算过」。**

---

## 一句话结论

**两个都建，都不用新数据源，加起来一周。** 第二个（枢轴失败）先做——它的事件**每天晚上都在算，
只是算完就扔**，接线成本两行，每拖一天永久少一天样本。

| | 有没有标准口径 | 归档动哪里 | 排期 |
|---|---|---|---|
| **① 真跳空后第一小时回补比例** | **有**（Full Gap + gap fill 都照抄 ChartSchool）；**「几成」是自造** | 新建 `data/history/opening_range.csv`，不动任何现有归档 | **W41（10-06 那周）**，半周 |
| **② 失败测试跌破枢轴之后那一段** | 事件有（Wyckoff spring/upthrust）；长度有（MFE/MAE）；**「多久失效」自造** | `sp_failed_today` 一个字段 + 新建 `data/history/pivot_fail_log.csv` | **接线 W40（09-29 那周）**，研究 W42 |

口径已登记：[`data/reference/METRIC_SOURCES.md`](../../reference/METRIC_SOURCES.md) §「弹药缺口两量」。

---

## ① 真跳空之后第一小时回补比例

### 试跑读数（已经算出来了，今天就能当弹药用）

SPY，**728 个 session（2023-10-30 → 2026-09-25）**，真跳空 **292 个（40%）**：上 189、下 103。

| 样本 | n | 首小时回补比例 p25 / 中位 / p75 | 首小时就填平缺口 |
|---|---|---|---|
| 全部真跳空 | 292 | 0.20 / **0.43** / 0.85 | **21%** |
| 跳空 ≥ 0.25 ATR | 223 | 0.17 / **0.35** / 0.60 | **10%** |
| 跳空 ≥ 0.50 ATR | 126 | 0.15 / **0.28** / 0.49 | **4%** |

**能直接发的一句：跳空越大，第一小时还回来的越少。** 缺口大到半根 ATR 以上时，
第一小时填平的只有 25 次里 1 次。方向不改变这件事（≥0.25 ATR 里上跳中位 0.34、下跳 0.36）。

⚠️ **分母换一个，头条数就翻一倍。** 上表的分母是「开盘价 − 昨收」（ChartSchool 的填补目标）。
换成「开盘价 − 昨日极值」，中位数从 0.43 变成 **0.86**，而且小缺口的比值会炸（p90 顶到 3.0）。
两个都讲得通，但发出去必须写死是哪一个——这正是口径要进表的原因。

复算：`.venv/bin/python data/research/ammo_gaps_2026-09-27/probe_gap_fill.py` →
[`gap_fill_pilot.json`](gap_fill_pilot.json)。

### ① 标准口径：有，抄了两处，自造一处

- **真跳空 = Full Gap**：开盘价高过**昨日最高**（上跳）或低过**昨日最低**（下跳）；只越过昨收的是
  Partial Gap。出处 [StockCharts ChartSchool · Gap Trading Strategies](https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/gap-trading-strategies)。
  **照抄**——这正好是 Linda 说的「真跳空」，不用我们定义。
- **回补 = 回到跳空前那根的收盘**：出处 [ChartSchool · Gaps and Gap Analysis](https://chartschool.stockcharts.com/table-of-contents/chart-analysis/gaps-and-gap-analysis)。**照抄。**
- **第一小时 = Opening Range / Initial Balance**：Crabel 1990 原书（*Day Trading with Short-Term
  Price Patterns and Opening Range Breakout*）用前 10 分钟，现代 ORB 文献常用 5 分钟
  （[Zarattini & Aziz, SSRN 4416622](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4416622)），
  Market Profile 的 initial balance 是前两个 30 分钟 bracket ——**就是第一小时，也正是我们代码里
  已有的那个口径**（[`pipeline/profile/tpo.py:278`](../../../pipeline/profile/tpo.py#L278)
  「Dalton's definition exactly」）。Linda 问的是「第一小时」，所以用 IB 这一档，**照抄。**
- **⚠️ 「回补了几成」是自造的**：标准只定义**填没填**这个是非题，不定义比例。已在 METRIC_SOURCES
  明写偏离，不得上页冒充标准读数。ATR 尺寸闸也是自造，所以上表按闸**扫**给出，不挑一个。

### ② 归档动哪里：**新建**，一个现有文件都不改

`data/history/opening_range.csv`，一行一 (session, symbol)：
`date, symbol, open, prev_close, prev_high, prev_low, atr14, or_high, or_low, or_close, gap_type`。

- **不改任何现有归档**，因为改归档要过 `schema_snapshot --check` 基线，09-17 那次删
  `sentiment.json` 就是漏了基线、把 09-16 正班挡在闸外。新增文件不碰基线。
- **数据源 yfinance 1h，不要 TWS**：今天实测能取到 **729 根 09:30 ET 首小时 bar，
  回溯到 2023-10-27**。yfinance 的美股 1h bar 起点就是 09:30，第一根**就是**第一小时，不用重采样。
- **IBKR 只在要 30 分钟 bracket 或 ES 时才用。** `pipeline/profile/` 那套 open type / day type
  分类器（`daytype.py:67` `OPEN_WINDOW = 3`）已经写完并在 496 个 session 上出过 base rate，
  但它的取数走 `scripts/daytype_base_rate.py` → IBKR，要 TWS 开着；`data/profile/` 里的 session 档
  **停在 2026-08-14**，那条线现在不在跑。所以新归档顺手存 IB 的高低，
  **等于给那个已经造好的分类器补一份不依赖 TWS 的输入**——不是新建轮子，是给它接电。
- 归属：`data/history/**` 归 DATA ALEX，新增文件走 data-contract + reviewer，我不自合。

### ③ 排期：**W41（10-06 那周）**，半周

理由：读数已经有了（上表），真正欠的是**把它变成每天自动更新的归档**，这样下次 Linda 再发盘前计划，
速报当场就能挂数而不是挂形态。不排更早，是因为量 ② 更划算（见下）。

---

## ② 失败测试跌破枢轴之后那一段

### 最值钱的发现：这个事件**我们每天都在算，算完扔掉**

[`pipeline/screeners/structure_pivot.py`](../../../pipeline/screeners/structure_pivot.py)
是 oratnek "Advanced Structure Pivot" 的逐行移植（带 TradingView golden check）。它有一个字段
`failed_today`（[:90](../../../pipeline/screeners/structure_pivot.py#L90)），
判据在 [:335-337](../../../pipeline/screeners/structure_pivot.py#L335)——
**「fail: LOW under the MA」，跌破就死**。这正是 Linda 说的失败测试。

它每天晚上对全池算一遍（[`yfinance_adapter.py:1259`](../../../pipeline/adapters/yfinance_adapter.py#L1259)），
然后 **`Result.to_row()` 不吐它、`SP_FIELDS` 不列它**
（[`structure_pivot.py:107-122`](../../../pipeline/screeners/structure_pivot.py#L107) ·
[`yfinance_adapter.py:623`](../../../pipeline/adapters/yfinance_adapter.py#L623)）。
十六个 `sp_*` 字段进了 `universe.json`，唯独这个没有。**尺子已经造好，只是没接线。**

### ① 标准口径：事件有名字，长度有工具，中间那一段是自造

- **事件**：Wyckoff 的 **spring**（跌破支撑后失败收回）/ **upthrust**（突破阻力后失败跌回）——
  出处 [ChartSchool · The Wyckoff Method](https://chartschool.stockcharts.com/table-of-contents/market-analysis/wyckoff-analysis-articles/the-wyckoff-method-a-tutorial)。
  **但我们有更精确的等价物**：`failed_today` 的判据是可执行代码、有原作 golden check，
  而 Wyckoff 的 spring 是描述性的、没有 cutoff。**用我们的，在表里写明它对应哪个标准概念。**
- **有多长、有多远**：**MFE / MAE**（Maximum Favorable / Adverse Excursion，John Sweeney 1996，
  *Maximum Adverse Excursion*，Wiley）。**我们已经在用**：
  [`scanner_event_study.py:53,70-71`](../../../pipeline/tools/scanner_event_study.py#L53)
  出 `mfe20` / `mae20`，外加 5/10/20 日 horizon、SPY 基准、同日随机对照。**照抄，不自造。**
- **⚠️ 「多久失效」是自造的**：我建议两个数——**bars-to-MAE**（那一段走完要几根）和
  **几日内收回枢轴上方**（失效判据）。Sweeney 定义的是幅度不是时间，标准里没有这一条。
  两个都要在 METRIC_SOURCES 标自造。

### ② 归档动哪里：一个字段 + 一张新表

1. **字段**：`sp_failed_today` 加进 `Result.to_row()` 与 `SP_FIELDS`。
   两处都在 DATA ALEX 边界里（`pipeline/screeners/` + `pipeline/adapters/`），
   **走 data-contract + reviewer，我不自合**。
2. **表**：新建 `data/history/pivot_fail_log.csv`，一行一 (date, ticker)，
   带 `sp_len` / `sp_hl` / `sp_stop` / 当日 close，供事后复现。

**实测事件率：7–17 次 / 票 / 年**（AMD 16.1、NVDA 17.1、SPY 7.0，各 251 个 session）。
全池一年约 **5–9 万行**，与 `ticker_events.csv` 同一量级，存得下。

⚠️ **倒填别用笨办法。** `SP.run()` 本身就是逐 bar 模拟，再「每根 bar 调一次 run()」就是平方级：
实测 **19.6 ms / 次**，全池一年 **7.7 小时**。两条路——
(a) 在 `run()` 里一趟吐出逐 bar 状态（正路）；
(b) 干脆不倒填，**从接线那天起向前记**，半年后就有 2–4 万行。
先做 (b)，(a) 视研究需要再说。

复算：`.venv/bin/python data/research/ammo_gaps_2026-09-27/probe_pivot_fail_rate.py` →
[`pivot_fail_pilot.json`](pivot_fail_pilot.json)。

### ③ 排期：**接线 W40（09-29 那周），研究 W42**

**接线先做，因为它在漏水。** 事件已经在算，不存下来就是每天永久丢一天样本；
成本是两行代码加一张表。研究（MFE/MAE + 失效时间）等攒够样本或做倒填，排 W42。

---

## 本轮没做的事（说清楚，免得下一班以为做过）

- **没有建归档**，本轮只出口径、落点、排期和两份试跑读数——任务原话是「让缺口可见并请你定优先级」。
- **量 ② 的前瞻收益没算**：naive 复算 20 支票顶穿了前台超时（正是上面那条 7.7 小时的来源）。
  事件率与成本已量出，足够定排期；MFE/MAE 读数等接线后用现成的 `scanner_event_study` 出。
- **量 ① 只做了 SPY**。QQQ / IWM / 个股要等归档建起来再批量跑。

## 证据清单

| 说法 | 怎么验 |
|---|---|
| 首小时回补中位 0.43 / 0.35 / 0.28 | 跑 `probe_gap_fill.py`，比 `gap_fill_pilot.json` |
| yfinance 1h 能回溯到 2023-10-27、729 根首小时 bar | 同上，`sessions` / `first_session` 两个字段 |
| 枢轴失败事件率 7–17 次/票/年 | 跑 `probe_pivot_fail_rate.py` |
| naive 倒填全池一年 7.7 小时 | 同上，`naive_replay.projected_hours_full_universe_1y` |
| `failed_today` 算了但没发 | `grep -n failed_today pipeline/screeners/structure_pivot.py`（4 处）对 `grep -n sp_failed pipeline/`（0 处） |
| profile 那条线不在跑 | `ls data/profile/profile_*.json` 最后一档是 `20260814` |
