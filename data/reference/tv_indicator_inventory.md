# TV 常用指标盘点（T-0921-08，2026-09-21）

起因 Andy 09-21 原话：「有一些已经我在tv上经常使用了，所以也可以一次整理出来。」

**方法说明（诚实标注，避免自造口径）**：这份盘点**不是**直接读取 Andy 的 TradingView 账号——那需要
真浏览器同源抓取（09-05 `jeff_scanner_2026-09/tv_screen_configs_2026-09-05.md` 那次用的方法），本任务
没有走那一步。这份表是从仓库里**已经留痕**的证据交叉整理出来的：他自己的 Pine 笔记出处
（[`CANON_LIBRARY.md`](CANON_LIBRARY.md)）、已下载的 TV 广度数据（`breadth_tv/`）、我们已经移植/复刻
的 Pine indicator（`indicators/`）。凡是"我们系统里有没有同名口径"这一列，答案都能追到一个文件；
凡是查不到的，如实写"未核实"，不补一个猜测的状态。

## 一、广度面板类（TV 上作为图表叠加的市场符号，非个股指标）

| TV 符号/指标 | 证据出处（我们已下载/用过） | 我们系统里的对应字段 | 状态 |
|---|---|---|---|
| NYSE TICK（`$TICK`，高/收/低三线） | `data/reference/breadth_tv/USI_TICK_hlc.csv`、`USI_TICK_NY_dhlc.csv`；Linda Raschke 原始指标见 [`indicators/fluxus-lbr-tick-cycle.pine`](../../indicators/fluxus-lbr-tick-cycle.pine) | `data/output/tick_cycle.json`（`ma_high/ma_close/ma_low` 三线） | ✅ 已复刻成我们自己的 Pine indicator + Python 孪生 |
| Put/Call Ratio（`USI_PCC`） | `data/reference/breadth_tv/USI_PCC.csv` | 未核实——数据已下载，未见消费该 CSV 的 pipeline 代码 | 🔲 只有原始数据，没做成读数或 indicator |
| Up/Down Volume（`USI_UVOL`/`USI_DVOL`） | `data/reference/breadth_tv/USI_UVOL.csv`、`USI_DVOL.csv` | 未核实——同上，只见下载未见消费 | 🔲 只有原始数据 |
| Advance/Decline（NYSE `INDEX_ADVN`/`DECN`，Nasdaq `INDEX_ADVQ`/`DECQ`；另有 `USI_ADVN_NY`/`USI_ADVN_NQ`） | `data/reference/breadth_tv/*.csv` | `ad_line`（Advance-Decline Line） | ✅ 一致（[`METRIC_SOURCES.md`](METRIC_SOURCES.md) 行 51） |
| New High/New Low（NYSE `INDEX_HIGN`/`LOWN`，Nasdaq `HIGQ`/`LOWQ`） | 同上；被 `pipeline/risk/regime_ledger.py`（`lamp_nhnl`）与 `pipeline/risk/correction_risk.py` 实际消费 | `new_highs`/`new_lows`（原始计数）；标准比值版见 Record High Percent / High-Low Index | ⚠️ 原始计数保留、比值口径已落地（`METRIC_SOURCES.md` 行 54/82） |
| McClellan（`INDEX_MMTH`） | `data/reference/breadth_tv/INDEX_MMTH.csv` | `mcclellan_osc` | ⚠️ 公式一致但池子不一致（Finviz 全池 vs NYSE，`METRIC_SOURCES.md` 行 50）；McClellan **Summation** Index 🔲 我们没有 |
| S&P 广度百分比（`INDEX_S5TH`，S&P500 成分 % above 某均线家族） | `data/reference/breadth_tv/INDEX_S5TH.csv` | `pct_above_*_sp500` / `t2108_sp500`（挂在 `$SPXA200R` 等具名指数口径上） | ✅ 一致（`METRIC_SOURCES.md` 行 67） |
| HY OAS 信用利差（FRED `BAMLH0A0HYM2`，TV 上常配 `$TICK`/`$PCC` 一起看盘面情绪） | `data/reference/breadth_tv/FRED_BAMLH0A0HYM2.csv`；被 `regime_ledger.py`（`lamp_credit`）消费 | Regime Lamps 信用灯 | ✅ 已做成 [`indicators/fluxus-regime-lamps.pine`](../../indicators/fluxus-regime-lamps.pine) 的一盏灯 |
| VIX / VIX3M 期限结构（backwardation） | `regime_ledger.py`（`lamp_ts`） | Regime Lamps 波动率灯 | ✅ 已做成灯 |
| SPX GEX（gamma exposure，TV 上常见的期权敞口叠加） | `regime_ledger.py`（`lamp_gex`）曾接入 | Regime Lamps GEX 灯 | ⚠️ **已退役**（Andy 09-17「SPX GEX暂时退役」，见 [`data/research/night_reports/INBOX.md:97`](../research/night_reports/INBOX.md) 回执行；数据停在 08-20，非 bug；`com.fluxus.gex-daily`/`skew-daily` 已 launchctl disable） |

## 二、Andy 自己的 Pine 笔记（个股图上叠加的动量/结构指标，来自 `CANON_LIBRARY.md`）

| TV 指标 | 原作者 | 我们系统里的对应口径 | 状态 |
|---|---|---|---|
| ATR Matrix（ATR Ext 阶梯、自入场止损） | SteveDJacobs（Andy 本机 Pine 笔记 `Strategy_Docs/ATR Matrix.txt`） | `atr_from_sma50`（B/A 形式）与 `plain_atr_multiple_from_sma50` | ✅ 两个量都有出处（`CANON_LIBRARY.md` 行 14） |
| Candles Stage Analysis（EMA10/20+SMA50 阶段判定，扩张/衰竭阈值） | @TradeDudeNYC | 我们减仓线 ≥7×ATR 的出处 | ✅ 概念已借用（`CANON_LIBRARY.md` 行 15） |
| 1-Month Relative Strength（RS=close/SPY 自百分位，严格排名） | @jfsrev | `rs_line_pctl_21` | ⚠️ 我们用 `<=`，原版用严格排名——待改（`CANON_LIBRARY.md` 行 16） |

**未核实的部分**：Andy 提到"有一些已经我在tv上经常使用了"，但除了上面三个有 Pine 笔记留痕的，
仓库里**没有**他当前图表模板实际挂载的指标清单——那需要他本人在 TV 上导出，或授权用同源浏览器
读 `chart-storage`/`indicator-storage`（09-05 screener 那次的同一套方法，只是这次读的是图表而不是
筛选器）。这是本任务留给他确认的空白，不是我漏查。

## 三、我们自己移植/原创、且已经是 Pine indicator 的（`indicators/` 目录全量）

| Indicator | 类型 | 状态 |
|---|---|---|
| `fluxus-3-10-oscillator.pine` | Linda Raschke 3/10 动量振荡器复刻 | ✅ 已有 |
| `fluxus-lbr-tick-cycle.pine` | NYSE TICK 高/收/低三线中期周期 | ✅ 已有（见上表 TICK 行） |
| `fluxus-regime-lamps.pine` | 我们自己的四盏灯风险状态机 | ✅ 已有，Python 孪生 `pipeline/risk/regime_ledger.py` |
| `fluxus-trading-risk-manager.pine` | 仓位/止损计算器（我们原创，非 TV 内置指标复刻） | ✅ 已有 |
| `indicators/third_party/oratnek_*.pine` | Structure Pivot / VCS（oratnek 原版，已移植进 `pipeline/screeners/structure_pivot.py` 与 `yfinance_adapter.py::calculate_vcs`） | ✅ 已有 |

## 四、值得做成 indicator 但目前只是数据/结论（候选，未动手，留给 Andy 挑优先级）

- **Put/Call Ratio、Up/Down Volume**——CSV 已经在下载，缺一步把它们接进某个 Python 计算或 Pine 叠加；对应上表"🔲 只有原始数据"两行
- **McClellan Summation Index**——原始振荡器我们有，累加版本没做（`METRIC_SOURCES.md` 行 89 早已记录"我们没有"）
- **Market Conditions（oratnek 15 条件复合分）**——Andy 已裁"可以直接闭了，欠条烧掉"（`METRIC_SOURCES.md` 行 101），不建议重启

## 结论（一句话）

我们已有 8 个 TV 指标/广度符号的对应口径（多数 ✅ 一致，少数 ⚠️ 标了偏离原因），3 个只下载了数据没做成读数，
1 个已退役（GEX）；Andy 本人日常图表上还在用什么、这份表之外是否有遗漏，需要他本人确认或授权一次同源抓取。
