# universe 字段盘点 — 2026-09-04（谁在用 · 有没有权威口径）

**一句话结论**：每晚发出去的字段里，有一批**从来没人读**、有一批是**同一个数的第二个名字**，还有一批**顶着行业术语的名字、算的却不是那个东西**——三件里只有第三件会伤到判断，前两件只是让这张表看起来比它实际能回答的问题多。

**Action Plan（三条，按性价比）**
1. **`adr_pct` 先修**：它算的是 ATR%，闸口的阈值却是从 ADR% 世界借来的——闸比 Andy 以为的松。→ DATA ALEX
2. **`hybrid_rs` 这个名字要改**，并在 `METRIC_SOURCES.md` 立行写明「自造权重、零出处」：它是 ShortList 六席的主排序键，最容易被当成标准读数。→ DATA ALEX + OPS
3. **死字段整批删**（改动小、零行为变化），从三个纯别名开刀。→ DATA ALEX

> 上一份 [`yahoo_pipeline_audit_2026-09-04.md`](yahoo_pipeline_audit_2026-09-04.md) 回答的是「一晚打了多少次 Yahoo」。这份只补两件它没查的事：**谁在用**、**有没有权威口径**。两份不重叠。

---

## 一、「数据太多，真的用的又几个」— 删除清单

先说一句可能不合直觉的：**删掉下面全部字段，一次 Yahoo 请求都省不下来。** 它们全部产在 `yfinance_adapter` 的 enrich 路径上，用的是那份**已经下载好的 1y 面板**——真正多打一遍 Yahoo 的那个字段（`vol_5d_50d`，见上一份审计第 2 条）反而是有人用的。所以这一节省的不是网络，是每晚全场的滚动计算、随 `universe.json` 发到每个浏览器的字节，以及「这张表上的数都有意义」这个错觉。

排序按代价：滚动窗口越长、覆盖行数越多，排越前；纯别名排最后。

| # | 字段 | 每晚算什么 | 覆盖 | 到 UI | 删它要改几处 |
|---|---|---|---|---|---|
| 1 | `atr_pctl_252` | ATR(14)/Close 的 252 根自百分位 | 5555/5630 | 无渲染点（**已进 shortlist.json 名片**，NameCard 是写死的 10 格读数表） | 产出 + 导出 + 名片 readings |
| 2 | `range5_pctl_252` | 5 根包络 / Close，再取 252 根自百分位 | — | 同上 | 同上 |
| 3 | `atr_pctl_63` | 同 ①，窗口 63 | — | 同上 | 同上 |
| 4 | `vol10_green_count_30d` | 30 根内 vol10_green 计数 | 5555/5630（98.7%） | 无 | 产出 + 导出（连 `oratnek_diff.py:48` 的诊断列都只带了 10d 那个） |
| 5 | `ad_ratio_20` | 20 日上涨日成交量占比 | 98.6% | 无 | 产出 + 导出 |
| 6 | `cmf21` | Chaikin Money Flow 21 | 98.6% | 无 | 产出 + 导出 |
| 7 | `bo_count_1m` | is_bo 序列的 21 根切片 | — | 无（`preset_hits.py:54` 与 `screenerFilter.js:230` 两侧都接好了线，两侧都没有开关） | 产出 + 两处映射 |
| 8 | `bo_count_6m` | 同上，126 根切片 | — | 无 | 同上 |
| 9 | `ema21_low_dist` | (当日 low − EMA21)/EMA21 | 5553/5623 | 无（两条筛选分支实证走不通） | 产出 + 导出 + 两条死分支 |
| 10 | `rs_126d` | `df['rs_126d'] = df['rs_6m']` | — | 无 | `run_all.py:264` 与 `:849` 两行 |
| 11 | `ema21_r` | `1 + sma20_dist` | 5555/5630 | 无 | 计算 + 取整 + 导出 + 一条回归测试 |
| 12 | `sma50_r` | `1 + sma50_dist` | 5487/5630 | 无 | 同上 |
| 13 | `prev_volume` | 昨日量 | **线上 universe.json 里连这个 key 都没有** | 无 | 产出 + 导出 |

`prev_volume` 是这批里最刺眼的一个：`DATA_CONTRACTS.md:495` 记着它是为 Stockbee 4% 扫描的硬条件 `v > v1` 加的，而本该消费它的 `gainers_4pct.py` 里**没有任何昨日量比较**——它既没人读，也还没到货（今天 15:45 的 commit `79b34cf6` 才把它变成 universe 列，今晚 cron 之后才第一次真的发出来）。这个形状值得单独记一笔：**字段被加进来时对应的那道闸从来没写**。

### 半死：内部有读者，但没有任何显示或筛选消费者

| 字段 | 唯一读者 | 判断 |
|---|---|---|
| `volume` | `quality.py:58` 只用它的**缺失率**、不用它的**值** | 与 `rel_volume × avg_volume` 构成恒等式（5415 只可算，相对误差中位 0.0003、p90 0.009）——三个字段两个自由度，只有它没有任何展示或筛选消费者 |
| `min_vol_3d` | 一个手工跑的 CLI（`anticipation_scan.py`），打印到终端 | 不写任何前端读的文件、不在夜间 cron 链条上。⚠️ 注意 `watchlist.py:201-204` 的 anticipation **面板**没有用它 |

### 这一节的搜索留痕

每个「零消费者」的结论都不是一次 `grep` 得出的。逐字段搜过的拼法示例：`rs_126d / rs126d / rs-126d / RS126 / rs6`；`atr_pctl_252 / atrPctl / atrPct252 / atr14__pct252 / compression_pctl / 一年压缩位`；`ema21_low_dist / ema21LowDist / 21emaLow / low_dist / lowDist`；`prev_volume / prevVolume / prev_vol`。目录覆盖 `pipeline/` 全部 py、`frontend/src/` 全部 jsx|js、`frontend/public/`、`api/`、`scripts/`、`data/reference/` 文档、`screener-presets.json`。

`ema21_low_dist` 那条判定依据尤其值得抄：不是「grep 干净」，是**两条消费路径都实证走不通**——十个只读预设逐个查过 filters 的 key，没有它；Screener 页改版后已无数值筛选面板，`applyFilters` 现在只被 `WatchlistTab.jsx` 用预设调用，而**那个组件全仓没有任何人 import**。

> ⚠️ 顺带挖出的一条更大的：`frontend/src/lib/screenerFilter.js` 整个文件是死代码。它唯一的调用者 `WatchlistTab.jsx` 全仓无人挂载。这意味着**浏览器端的预设筛选整条路径已经不通**，预设现在真正生效的地方是服务端 `preset_hits.py`。这条不属于字段盘点，但影响到上面十几个字段的「有没有消费者」判定——凡是只在 `screenerFilter.js` 里出现的映射，一律不算消费者。

---

## 二、「好多也是重复」— 留哪个

**八组**。前五组是字面别名或仿射复制（成分等价，删了不会有任何数字变化），后三组要动代码。

| # | 组 | 关系 | 留哪个 | 为什么 |
|---|---|---|---|---|
| 1 | `rs_126d` ≡ `rs_6m` | 同一个 pandas Series | `rs_6m` | 别名零消费者，删它零风险 |
| 2 | `rs_63d` ≡ `rs_3m` | 同一个 Series | `rs_3m` | 别名只有一个真消费者：个股页 Stats 那一格（`TickerStats.jsx:29`）。改它读 `rs_3m`，其余全是永不触发的回落 |
| 3 | `rs_21d` ≡ `rs_1m` | 同一个 Series | `rs_1m` | ⚠️ **这组别删快了**：4% Bullish 面板（`watchlist.py:231`）和两个 preset 读的是**别名而不是本名**，个股页 Stats 也单独印了它。删它要改 3 处代码 + `screener-presets.json` 里两个 preset 的键 |
| 4 | `ema21_r` ≡ `1 + sma20_dist` | 仿射 | `sma20_dist` | 名字骗人两次：既不是 EMA21（是 SMA20），也不是 R 倍数（是比值）。零消费者 |
| 5 | `sma50_r` ≡ `1 + sma50_dist` | 仿射 | `sma50_dist` | 文档已两次点名它是陷阱（`DATA_CONTRACTS.md:204`、`screener_competitors_2026-08-17.md:55`）。零消费者 |
| 6 | `c_low52w` ≡ `1 + low_52w` | 仿射，**但 load-bearing** | `low_52w` | 它是 Anticipation 面板三分之一条闸。那条闸完全可以直接写成 `low_52w ≥ 0.8`，省掉一列。名字来自 Ian Murphy Double Trouble 的 `c/minl252` 原文 |
| 7 | `high_52w` / `high_52w_dist` | 后者是前者四舍五入到 4 位 | 二选一，全仓统一 | 现状是 **python 端全用 `high_52w`、前端全用 `high_52w_dist`**——同一个量按语言分了家 |
| 8 | `volume` / `rel_volume` / `avg_volume` | `volume ≈ rel_volume × avg_volume`（实测，见上表） | 删 `volume` | 三个字段两个自由度，`volume` 是唯一没有展示或筛选消费者的那个 |

### 长得像但**不是**重复的（别顺手删）

| 一对 | 差在哪 |
|---|---|
| `perf_1w` vs `perf_5d` | 一个是 Finviz **日历周**（08-14 那周只有四个交易日），一个是从 bars 数的**五个 session**。Screener 预设和 Watchlist 同名面板故意用了不同的那个 |
| `rel_volume` vs `vol_5d_50d` | 一个是今日/3 月均（Finviz），一个是 5 日均/50 日均（自算 bar） |
| `vol10_green` vs `pocket_pivot` | 一个比前 10 根**全部** bar 的最高量、要求收阳；一个比前 10 根里**下跌日**的最高量。08-09 审计实测两者 Top-10 只重叠 3 个名字 |
| `atr_pctl_252` vs `atr_pctl_63` | 窗口不同，是两个量（虽然都没人用） |
| `cross_ema21_up` vs `cross_sma50_up` | 或关系不是重复，成分不同 |
| `adr_pct`（universe 列） vs `avg_volume`（`vcp_detector.py` 局部）vs `dist_hi20_pct`（`ohlc_store` / `analysis` / 前端 `tradeTechnicals`） | **同名不同物**，各有各的源。全仓有至少三处同名字段属于这个形状 |

---

## 三、「好多可能其实有其他权威的计算方式」

**这轮只查了四格**（Andy 点名的两个 + 两个最可疑的）。四格**全部找到了行业口径**，四格**全部与我们的算法有实质差异**。剩下的字段没查，别把「没列在这里」读成「查过、没标准」。

| 格 | 我们的算法 | 找到的标准 | 建议 |
|---|---|---|---|
| `adr_pct` | `ATR(14)/close×100`，Wilder RMA 平滑，含跳空 | **ADR%（Qullamaggie / Deepvue）**：`100×(mean(H_i/L_i, 20 根) − 1)`，无跳空、算术平均、每日除自己的 low | **照抄标准** |
| `h_score`（前端 `hybrid_rs`） | `(2·f + 3·i + 1·rs1m + 2·rs3m + 2·rs6m)/10`，直接输出加权平均 | **IBD Composite Rating**：六分项、EPS/RS 双权、结果**再排一次**成 1–99 | **保留但写明偏离**（系数抄不到，形状能对齐三处） |
| `rs_ibd` | `0.4·rs_3m + 0.4·rs_6m + 0.2·rank(perf_1y)`，加权的是**已百分位化的 rank** | **IBD RS Rating** 一手只公开「过去 12 个月 + 全市场百分位 + 1–99」 | **保留但改名** |
| tightness 四件（`atr_pctl_252/63`、`range5_pctl_252`、`wk_tight_3`） | 见下 | 四个分量各自对得上具名口径，「tightness」这个总名没有标准 | **保留但改名**（`wk_tight_3` 是唯一该改判据的） |

### 3.1 `adr_pct` — 唯一一个该直接照抄的，而且闸已经在漏

这不是「差一点」的问题。度量的推广者本人在自己的 FAQ 上公布了逐项算术，一家 screener 厂商发的公式一字不差，TradingView 官方文档还专门写了一句 ADR% **不计跳空**、ATR% **计跳空**——**它们在每一个查到的来源里都是两个不同的指标，不是别名**。我们在算 ATR%，然后挂 ADR% 的名字发出去。

五个参数全差，而且**方向一致地偏大**：分子含跳空、窗口 14 而非 20、Wilder 指数平滑而非算术平均（一根宽 bar 会连续抬高读数好几周，标准里第 21 天干净掉出）、分母是整段窗口共用最后一根收盘而非逐日除自己的 low、权重因此是几何而非平坦。

实测（209 只票 × 最近 60 根，我们 vs Qullamaggie 式）：

| 量 | 值 |
|---|---|
| 中位比值（我们/标准） | 1.117 |
| p10–p90 比值 | 0.879 – 1.336 |
| 平均绝对差 | 1.08 pp |
| `MIN_ADR_PCT = 3.5` 过闸名字数 | 我们 184 / 标准 174 |
| 只因为读数偏高才被放进来的名字 | 11（占我们过闸集的 6.0%）：AEO 4.14/3.46 · AVGO 3.79/3.18 · CWEB 3.75/2.53 · CORT 3.99/3.48 · CYTK 3.77/3.27 |

比值不是常数，**乘一个系数校准不回来**。而最要命的一点是阈值的来路：`watchlist.py:44-54` 的注释自己写着 3.5–10 那条带是从 Stockbee/Qullamaggie 借的——**借来的阈值坐在借来的尺子上才成立**。现在它坐在一把系统性偏大的尺子上，波动率地板比 Andy 以为自己设的那个松。

建议的形状不是改名而是拆开：`adr_pct` 改算 Qullamaggie 式（与 `leader_footprint.py:69` 已有的实现对齐），当前这个量改叫 `atr_pct` 单独留着——因为 `atr_from_sma50`、`ema21_atr_dist`、R 倍数仓位计算**真的需要含跳空的 true range**，止损距离本来就该尊重跳空。⚠️ 翻这个开关会移动每一个闸的读数，改完必须在归档 session 上重跑 `oratnek_diff` 并重报格子数，否则 08-25 那条 ADR 闸宽度的结论会在另一把尺子上被悄悄复述一遍。

**怎么验证**：两段。第一段今天就能做、不用抓网页——Qullamaggie 的 FAQ 是闭式公式，照抄实现后与仓库里 `leader_footprint.py:69` 那份对同一批 bar 逐点比，不到浮点噪声就是其中一个错了，这该做成 CI 断言而不是一次性检查。第二段是真正的证伪：两个 TradingView 公开开源实现（`6KVjtmOY`、`QAswFQY2`）源码可读，Deepvue 的 ADR% 是可排序的 screener 列（任何带 ticker + 日期的截图就是一次多点读数——和 oratnek 那次从页面反解 29 个数是同一个形状），Qullamaggie 自己的复盘里也逐笔引用 ADR%。⚠️ 老实话：我们的 bar 是 yfinance、他们不是，单票 1–2% 的差是数据源差异不是公式差异——**先用一个我们已经信得过的量（close、avg_volume）量出这个厂商的噪声地板**，再去读 ADR 那一列，别拿一张已经被筛过的第三方页面当 ground truth。

### 3.2 tightness 四件 — 一个换了判据的老形态，和三个套错壳的百分位

`wk_tight_3` 就是 O'Neil / IBD 的 **Three Weeks Tight**，我们换了名字，还换了判据的形状：

| | IBD 3WT | 我们 |
|---|---|---|
| 比较方式 | **两两相邻**：\|C2/C1−1\| ≤ 1.5% 且 \|C3/C2−1\| ≤ 1.5% | **三根取全域带宽**：(max−min)/C3 ≤ 1.5% |
| 分母 | 每一步除**前一周收盘** | 除**最后一根收盘** |
| 阈值 | 1.5%（1% 更理想；SwingTradeBot 公开实现取 1%） | 1.5%（与 IBD 松边一致，但没写来源） |
| 上下文 | 「前一次突破之后」+ 买点 = 三周高 + $0.10 | above50MA + 距 52 周高 ≥ −15%（**自造代理**） |

后果不是小数点：一段 +1.4%、+1.4% 的单调爬升，IBD **过**（每步都合格），我们**不过**（总跨度超标）。我们比标准严，而严掉的恰好是「稳步小幅抬高」那一类——也就是 IBD 强调的「持股者不获利了结」的形态本体。这是 08-31 新高新低那次的同形第二例。

另外三个的问题是同一个：**归一化方式是标准的，被测的量不是**。`atr_pctl_252` 的 252 窗口 ✅ 与 IV/HV Percentile 一致，但标准测的是日对数收益的年化标准差，我们测的是 Wilder ATR(14)/Close（区间类、指数平滑、含跳空）——「ATR% 的 252 日自百分位」**不是任何机构发过的指标**。比较符也含等号（标准数的是严格低于今天的天数），使读数下限是 1/n×100 而不是 0，等值日多的低价票偏得更多。`range5_pctl_252` 的「5 日跨度」概念在 Deepvue 有出处，但 Crabel 的 NR7 比的是**单根** K 线的绝对区间、输出二值，Deepvue 用的是**绝对阈值 8% 且永远配 RMV15 < 10**——「5 日跨度取 252 日自百分位」这个组合三家都不是。

⚠️ 代码里有一句站不住的话要改：`pipeline/tools/tightness_grid.py:77` 的注释写「RMV as its authors define it」——Deepvue 官方知识库**没有公开 RMV 公式**（只说「比较当前区间与近期平均区间，默认回看 15 根，输出 0-100」）。那行实现是我们的猜测，不是作者的定义。

### 3.3 找不到标准的（宪法要求的留痕）

这一节不是「没查」，是**查了，没有**。

| 我们的量 | 查了什么 | 结论 |
|---|---|---|
| IBD Composite 的六项**系数** | IBD 只公开「EPS 和 RS 双权」一句；Deepvue 一手文档明说不给数值权重；O'Neil+Co 官方评级页实际返回 **HTTP 404**（仅在搜索索引里出现，本轮未读到内容） | **业内不存在可照抄的复合分系数表。** 所以 `h_score` 的权重必然是自造的，这一点消不掉，只能明写 |
| `rs_ibd` 的 `0.4/0.2/0.2/0.2`（「2:1:1:1」） | Optuma 论坛、AmiBroker 论坛、TradingView 各家脚本、Medium、skyte 的 GitHub、Portfolio123 社区——**没有一个引用 IBD 的原始材料**，彼此在互相转抄 | **社区重建（folklore），不是 IBD 公开口径。** 被引用最多的 skyte/relative-strength 自述已停止维护、自曝价格未复权、且从未声称对照过 IBD 读数验证 |
| `atr_pctl_63` 的 **63 窗口** | 业界三个锚点：252 日（IV/HV Percentile）、六个月≈126 根（Bollinger 本人对 Squeeze 的口径）、15 根（Deepvue RMV 默认） | 63 一个都不是。**我们拍的** |
| 「tightness / compression」这个**总名** | 学术侧只有波动率聚集（ARCH/GARCH）解释现象，不提供指标 | **没有名为 tightness 的标准度量。** 只有分量各自有名（BandWidth / TTM Squeeze / NR7 / HV Percentile / 3WT / RMV） |
| Qullamaggie 的量化 tightness 阈值 | 他本人页面只给「盘整 2 周~2 个月」「贴 10/20/50 日线」「止损不宽于 ADR」 | **他本人没给。** 网上流传的「区间/ADR ≤ 3.0」出自二手站点 |
| Wyckoff spring / absorption | Wyckoff SMI 官方词条只给自由裁量的量级（$50 的票穿 3/4~1.5 点算 spring） | **不构成可复现口径** |
| Deepvue **RMV 本体公式** | 官方知识库 | **未公开** |

**抓取留痕**（重要，下轮别重踩）：`investors.com` 对我们的抓取 UA 是**封禁**的（WebSearch 直接报 domain not accessible，WebFetch 与 web.archive.org 均拉不动）——IBD 一手页面本轮**没读到**，一手定义改由其旗下产品 **MarketSmith** 页面取得，另一份 IBD 原文取自 **Yahoo Finance 转载**（一手文字、二手托管）。`traderlion.com` 与 `chartmill.com` 的相关文档页均返回 **403**，那两处表述**仅来自检索摘要，未经一手核实**。Deepvue 那条 ADR% 公式的原 KB 页现在 301 跳到一个只讲 UI 操作、不含公式的新页，公式文本取自搜索索引的旧页缓存——**算旁证，不算独立一手复读**。

---

## 四、`h_score` 与 `rs_ibd` — 一路写到 Andy 眼前那一列

### 4.1 `h_score`：你以为它是个显示的分数，其实它是「你今天看见谁」

它上页的地方只有两格。它真正的分量在**两处排序权**——那两处才是决定 Andy 每天早上看到哪些名字的东西。

```
run_all.py:323  h_score = (2·f_score + 3·i_score + 1·rs_1m + 2·rs_3m + 2·rs_6m)/10
      │
      ├─ run_all.py:851 ────────────────► universe.json 导出列
      │
      ├─ watchlist.py:485 ──────────────► 每个面板的命中按 h_score 降序，只有前 25 进 watchlist.json
      │                                   ⇒ 【Watchlist 页每个面板你看见哪 25 只】← 最重的一处
      ├─ watchlist.py:505 ──────────────► cross_zone（跨区名单）第二排序键
      ├─ watchlist.py:291 ──────────────► 改名 hybrid_rs 放进每只票的 entry
      │                                   （前端从不读这个值，只有它造成的顺序生效）
      ├─ watchlist.py:341 / :388 ───────► leaders_log.csv / panel_hits 归档列
      │
      ├─ name_cards.py:209 hscore() ────► 六个席位的排序键
      │                                   ⇒ 【ShortList 页每个席位坐谁】← 第二重
      ├─ name_cards.py:153 ─────────────► 名字卡 card.readings
      │
      ├─ preset_hits.py:44 ─────────────► preset「Monthly Leader 97」hScore 80–99 闸
      │                                   → ticker_events.csv
      │                                   ⇒ 【个股页 Signal History 上的 Monthly Leader 97 标记】
      │
      ├─ TickerStats.jsx:27 ────────────► 【个股页 Stats 网格「Hybrid RS」格】
      ├─ tickerReadings.js:115 ─────────► 【个股页趋势指标「H / I / F 分」第一个数】
      ├─ manualCards.js:29 / ledger.js:37 ► 手加名字卡/台账快照携带（NameCard 未渲染）
      └─ screenerFilter.js:179 ─────────► 死路（唯一 import 它的 WatchlistTab.jsx 全仓无人挂载）
```

**三件 Andy 该知道的**：

① **它的「综合」比看上去窄得多。** `i_score`（权重 3/10，全族最大）**不是关于这只票的**——它是「这只票所在行业的 rs_3m 中位数排第几」。加上 `rs_3m` 自己的 2/10，**一半的分来自同一个 3 个月窗口**。IBD 的行业项是六分之一、且不在双权名单里；我们把最没出处的一项给了最高权重。

② **它不是百分位，却摆在百分位旁边。** IBD 把合成结果**再排一次**成 1–99，所以「98」严格等于「打败 98%」。我们直接输出百分位的加权平均、**不再排名**，多个百分位取均值必然向中位数收缩、两端够不到——而它在页面上就叫 `hybrid_rs`，和真百分位的 `rs_1m` 并列显示。同一行里两个数看着同尺度，其实一个是百分位一个不是。**这条零成本就能量出来**：取当日全池 h_score 画分布、报 min/max/IQR，实测极值明显窄于 [1,99] 就直接证完。这是三条验证里唯一保证有读数的一条，该先跑它。

③ **它没有可测出的排序优越性**——这不是猜测，是仓库里已有的实测：[`data/research/hscore_ic_2026-08/README.md`](../hscore_ic_2026-08/README.md)（08-20）。牛市段 meanIC +0.030 vs 裸的 `rs_63d` +0.029 打平；逐日对决只在 41% 的日子赢 `rs_63d`；十分位价差还输给 `rs_126d`。当 tie-break 无害，当「优越性」无据。⚠️ 而 `f_score` 那 2/10 在 08-17 之前对全场恒为 50（两个源头列全空），所以那次 IC 研究直接把它排除在测试之外——**h_score 有五分之一的权重从来没被测过**。

④ 名字要改：一个 20% 基本面 + 30% 行业的分不该叫 RS。

### 4.2 `rs_ibd`：全站零显示，但它是三张主题卡的会员资格线

「rs_ibd 用在哪里」的诚实答案是：**它不是一个读数，它是三个主题的入场券。** 这个数在全站没有任何一个位置显示出来——不在个股页、不在 Screener 表、不在名字卡。

```
run_all.py:282  rs_ibd = 0.4·rs_3m + 0.4·rs_6m + 0.2·rank(perf_1y)
      │
      ├─ run_all.py:850 ────────► universe.json 导出列
      │
      ├─ taxonomy.py:79  _high_octane    ： adr_pct≥5 ∧ rs_ibd≥90 ∧ cap≥3e8
      ├─ taxonomy.py:105 _growth_factor  ： rs_ibd≥80 ∧ perf_6m≥20% ∧ 在 200SMA 上
      ├─ taxonomy.py:132 _leaders_52w    ： 离 52 周高 ≤5% ∧ rs_ibd≥85
      │      └─ taxonomy.py:598/607/609 ► 注册成 THEMES 里三个 rule theme
      │              └────────────────► groups.json 的 56 个 themes（已核实三个名字都在）
      │                     ⇒ 【Groups/Themes 页的 High Octane / Growth Factor /
      │                         52-Week High Leaders 三张主题卡的成员构成】
      │                     ⇒ 【Screener 页 theme 过滤器里同样这三个】
      │
      └─ preset_hits.py:50 + screenerFilter.js:185 ► rsIbd 映射两侧都在，
             但 screener-presets.json 的 10 个 preset 没有一个开 rsIbd；前端那条还是死代码
```

**三件该知道的**：

① **它挂着 IBD 的名，而 IBD 唯一公开的那句话我们就不满足。** IBD 一手定义是「过去 **12 个月** 的价格表现，全市场百分位，1–99」。我们把 80% 的权重放在 ≤6 个月里，通用重建版把 60% 权重放在 ≥6 个月上。**方向是反的。**

② **核心结构是自造的，而且全网找不到第二家。** 标准（无论 IBD 一手还是社区重建）加权的都是**原始收益 ROC**，排名只在最后发生**一次**；我们加权的是**已经百分位化的 rank**——rank-of-ranks。百分位是非线性单调变换，先 rank 再加权 ≠ 先加权再 rank，两者会给出不同排序。没有任何一份公开实现（IBD 重建版 / Deepvue / ChartMill / skyte）这么做，而我们**没写明这是自造的**。顺带一条独立的账：即使不谈 IBD，rank-of-ranks 把三段收益的量级信息全丢了——第 60 和第 61 百分位之间的差，被当成和第 1 与第 2 之间一样大。这不是「偏离标准」的问题，是「这个变换有没有道理」的问题，得单独量。

③ **它按定义看不见任何上市不满一年的票**（`perf_1y` 缺 → 那 0.2 权重拿不到分，`run_all.py:274-281` 有明写）。三张主题卡因此结构性地排除新股。

改名建议 `rs_weighted` / `rs_composite`，`preset_hits.py:50` 的 `rsIbd`、`screenerFilter.js:185`、`taxonomy.py` 的三处阈值一起改——那三个 85/90/80 是照着 IBD 语感拍的，改名后要重新说明它们是**我们自己尺子上的分位**，不是 IBD 的 85/90。

**怎么验证**：拿别人公开发布过的读数复现，和 oratnek RS 1M / Jeff Sun ATR multiple 是同一条老路。① IBD 免费文章常规印出 `(ticker, Composite, EPS, RS)` 三元组且带日期，攒 ≥30 组对 Composite 做回归——若「EPS/RS 双权、其余单权」为真，系数应逼近 2:2:1:1:1:1。②验我们这版只能比**排序**不能比数值（他们的百分位分母是他们的池子，我们复现不了）——好在排序对分母免疫，这是能下的最干净的一刀。③三条硬约束：`investors.com` 要用真 Chrome（本仓库已有 SOP）；**先算 n=30 时 Spearman 的分辨率地板**，免得又得到一个「瞎的 NULL」；权重必须在前一半样本上拟合、后一半上报——四个权重三十个点，过拟合是默认结果不是风险。

---

## 五、下一步（按性价比排序）

| # | 动作 | 一句话 | 归线 |
|---|---|---|---|
| 1 | `METRIC_SOURCES.md` 立四行 + 代码注释写「自造」 | 宪法硬性要求，`h_score` 是六席主排序键，最容易被当成标准读数；零风险、今天就能做 | OPS |
| 2 | 量 `h_score` 的分布，证它不是百分位 | 三条验证里唯一保证有读数的一条，不依赖任何外部源，半天出结果 | DATA ALEX |
| 3 | 删三个纯别名 `rs_126d` / `ema21_r` / `sma50_r` | 零消费者、零行为变化，各改两三行 | DATA ALEX |
| 4 | `adr_pct` 改口径 + 拆出 `atr_pct` | 闸在漏（过闸集多出 6.0%），且阈值是借来的；⚠️ 改完必须在归档 session 上重跑 `oratnek_diff` 重报格子数 | DATA ALEX |
| 5 | `hybrid_rs` / `rs_ibd` 改名（含前端标签与三处阈值说明） | 名字本身就是那个假声明 | DATA ALEX + 前端线 |
| 6 | `wk_tight_3` 改成 IBD 两两相邻判据 + 改名 `three_weeks_tight` | 同一形态换了判据，且严错了方向；是 08-31 那个坑的同形第二例 | DATA ALEX |
| 7 | 删剩下的死字段（`atr_pctl_*` / `range5_pctl_252` / `ad_ratio_20` / `cmf21` / `bo_count_1m,6m` / `vol10_green_count_30d` / `ema21_low_dist` / `prev_volume`） | 每晚全场算给没人看；要么给它们配消费者，要么两边一起删——别留在半途 | DATA ALEX |
| 8 | 处理 `screenerFilter.js` 整条死链 | 浏览器端预设筛选已不通，留着会让每次字段盘点都误判消费者 | 前端线 |
| 9 | 合并 `rs_21d` / `rs_63d` 到本名 | ⚠️ `rs_21d` 有真消费者（4% Bullish 面板 + 两个 preset 读的是别名），要连 `screener-presets.json` 一起改 | DATA ALEX + 前端线 |
| 10 | 补 `perf_9m`，并行跑 `rs_oneil` 候选列 | 验证之前不要替换（踩过「发布在验证之前」） | DATA ALEX |
| 11 | 把 ADR% 与 `leader_footprint.py:69` 的逐点一致做成 CI 断言 | 现在是「同一个名字两个量、差 ~12%」，没有闸拦着它再分叉一次 | DATA ALEX |

**这轮没做的、下轮第一件事**：口径检索只覆盖了四格。剩下的字段——尤其 `vcs`、`ti65`、`mdt`、`heat`、`rs_line_pctl_21` 这些同样自带术语名的——**一格都没查**。别把「没列在第三节」读成「查过、没标准」。
