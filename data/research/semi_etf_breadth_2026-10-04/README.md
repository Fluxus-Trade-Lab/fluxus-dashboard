# SMH 与 SOXX：区别，以及两者成分股的内部宽度（2026-08-03 → 10-02）

*T-1004-10 · linda · 回答 Andy 2026-10-04 的两问：「SMH和SOXX的区别呢？宽度是否也可以量。」*
*数据文件：[`semi_etf_breadth_series.csv`](semi_etf_breadth_series.csv)（44 行）· 持仓原件（已去掉金额列）：[`holdings_smh_2026-10-01.csv`](holdings_smh_2026-10-01.csv)、[`holdings_soxx_2026-10-01.csv`](holdings_soxx_2026-10-01.csv) · 汇总数：[`etf_facts.json`](etf_facts.json) · 重算脚本：[`build_series.py`](build_series.py) · 闸：[`pipeline/tests/test_semi_etf_breadth_series.py`](../../../pipeline/tests/test_semi_etf_breadth_series.py)*

---

## 一句话结论

**SOXX 更能代表「半导体整体」**：它装 30 只、最大一只 9.44%、30 只全是半导体或半导体设备。SMH 只装 25 只、NVDA 一只占 19.27%，还把 CDNS 和 SNPS 两只 EDA 软件股算了进来。

**但内部宽度两者几乎一样。** 10-02 的等权 50 日线上方占比：SMH 96.00%，SOXX 93.33%，差 **2.67 个百分点**。44 个交易日的平均绝对差只有 **5.02 个百分点**，最大 15.09（8-11）。

真正分开两只 ETF 的不是宽度高低，是**宽度和它自己价格的关系**：

| | SMH | SOXX |
|---|---|---|
| 加权宽度减等权宽度，44 天均值 | **+14.32** 个百分点 | **+4.54** 个百分点 |
| 加权高于等权的天数 | 42 / 44 | 34 / 44 |
| 最大那天 | +25.07（9-16） | +19.95（9-16） |

SMH 的涨，比 SOXX 更依赖它最大的那几只票。同一天同一批票，SMH 的加权读数比它的等权读数高出一大截，就是 NVDA 的 19.27% 在抬它。

⚠️ **两个篮子在这 44 天里一共 0 次 52 周新高、0 次新低。**

所以稿子第 3 段那句「SMH 9 月 22 日创新高」站不住。9-22 收盘，SMH 离自己的 52 周高点 **−9.58%**，SOXX **−12.62%**。到 10-02，两只分别是 **−6.14%** 和 **−10.16%**。两只的 52 周高点都是 **2026-06-22** 立的。这一条和 T-1002-80 的结论一致，换成 ETF 自己的持仓重算一遍，答案没变。

---

## 一、两者的区别

每行写明取数日期与来源。持仓那几行一律以发行方当日持仓文件为准，不凭记忆。

| 项 | SMH | SOXX | 取数日期 | 来源 |
|---|---|---|---|---|
| 发行方 | VanEck | iShares（BlackRock） | 2026-10-03 | [vaneck.com SMH](https://www.vaneck.com/us/en/investments/semiconductor-etf-smh/) · [ishares.com SOXX](https://www.ishares.com/us/products/239705/ishares-phlx-semiconductor-etf) |
| 跟踪指数 | MVIS® US Listed Semiconductor 25 Index（MVSMHTR） | NYSE Semiconductor Index（ICESEMI，2021-06-21 起；此前是 PHLX SOX） | 2026-10-03 | 同上两页（SOXX 的指数更名说明在该页 Benchmark Index 的提示气泡里）；SOXX 另见[招募说明书 S-1](https://www.ishares.com/us/literature/summary-prospectus/sp-ishares-phlx-semiconductor-etf-3-31.pdf) |
| 成分数（股票，不含现金） | **25** | **30** | **2026-10-01** | [SMH 持仓 xlsx](https://www.vaneck.com/us/en/etf/equity/smh/holdings/download/xlsx/) · [SOXX 持仓 csv](https://www.ishares.com/us/products/239705/ishares-semiconductor-etf/latest-holdings.csv) |
| 入选门槛 | 美国上市、半导体收入 ≥ 50%，取最大最流动的 25 只 | ICE 行业分类里半导体行业、美国上市，取最大的 30 只 | 2026-10-03 | [MVIS 指数页](https://www.marketvector.com/indices/sector/mvis-us-listed-semiconductor-25) · [SOXX 招募说明书 S-1](https://www.ishares.com/us/literature/summary-prospectus/sp-ishares-phlx-semiconductor-etf-3-31.pdf) |
| 加权方式 | 自由流通市值修正加权 | 自由流通市值修正加权 | 2026-10-03 | [MVSMH 指数指南 §2.3](https://www.marketvector.com/rulebooks/download/MVSMH_Index_Guide.pdf) · [NYSE Arca 公告 RB-21-075](https://www.nyse.com/publicdocs/nyse/markets/nyse-arca/rule-interpretations/2021/NYSE%20Arca%20Equities%20RB-21-075.pdf) |
| 单只上限（规则） | 大权重组单只 **20%**（下限 5%），小权重组单只 **4.5%**，大权重组合计 50% | **没取到公开主源**（见下面那条小字） | 2026-10-03 | [MVSMH 指数指南 §2.3](https://www.marketvector.com/rulebooks/download/MVSMH_Index_Guide.pdf) |
| 实际最大权重 | **NVDA 19.27%** | **INTC 9.44%** | **2026-10-01** | 同上两个持仓文件 |
| 前五大合计 | **43.94%**（NVDA·TSM·AMD·AVGO·MU） | **40.60%**（INTC·AMD·MU·NVDA·AVGO） | **2026-10-01** | 同上两个持仓文件 |
| 海外注册的 ADR | **5 只，合计 20.12%**（TSM·SKHY·ASML·ARM·STM） | **8 只，合计 11.29%**（SKHY·TSM·ASML·TSEM·ASX·UMC·ARM·STM） | **2026-10-01** | SOXX 持仓文件的 `Location` 列（见下面那条小字） |
| 行业构成（Finviz） | Semiconductors 18 · Semi Equipment 5 · **Software 2**（CDNS、SNPS） | Semiconductors 24 · Semi Equipment 6 | 2026-10-02 | `data/output/universe.json`（timestamp `2026-10-02T22:03:12Z`） |
| 两者重叠 | 23 只，占 SMH 权重 **95.97%** | 23 只，占 SOXX 权重 **92.32%** | **2026-10-01** | 同上两个持仓文件 |
| 只在 SMH 里 | CDNS、SNPS | — | **2026-10-01** | 同上 |
| 只在 SOXX 里 | — | ASX、CBRS、CRDO、ENTG、MTSI、TSEM、UMC | **2026-10-01** | 同上 |
| 8-03 → 10-02 涨幅 | **+15.61%** | **+16.07%** | 2026-10-02 | yfinance 日线，`auto_adjust=True`，见 `etf_facts.json` |

三条小字：

- **SOXX 的逐条权重上限，查过，没取到公开主源。** 能取到的公开文件只说到「自由流通市值修正加权、美国上市最大的 30 只」（NYSE Arca RB-21-075、SOXX 招募说明书 S-1）。ICE 的完整规则书在 `indices.theice.com` 上要登录，`ice.com/publicdocs` 下只有一份 2022-01-28 的变更通知，而那份只改发布频率。二手资料常写「前五 8%、其余 4%」——**本页不引用它**，因为没有主源。可引用的是实测：10-01 最大权重 9.44%，已经高过那个说法，说明若有 8% 的上限，它只在调仓日生效、之后随价格漂移。
- **ADR 那一行的域籍标签来自 SOXX 持仓文件的 `Location` 列。** VanEck 的持仓文件没有这一列。两只 ETF 共有的 23 只是同一批证券（同一条 ADR），所以用 SOXX 的标签给 SMH 的同名 ticker 定性。这是推断，不是 VanEck 发布的字段。
- **指数名那一行有个坑**：SOXX 的 URL 和文件名至今仍写 `ishares-phlx-semiconductor-etf`，容易让人以为它还在跟 PHLX SOX。页面上的 Benchmark Index 写的是 NYSE Semiconductor Index，招募说明书 S-1 也写 NYSE Semiconductor Index。**按页面和说明书，不按 URL。**

---

## 二、宽度能量，两套序列都在

能。口径和 T-1002-80 完全一样（阈值逐条抄自 `pipeline/screeners/breadth_metrics.py`），只换池子：从 120 只主题组并集，换成每只 ETF 自己的持仓。
每只 ETF 两条臂：**等权**（数名字，这就是「这个 ETF 内部的宽度」）和**按权重加权**（数指数权重，这是 ETF 价格实际跟的东西）。

### 头尾读数

| | SMH 8-03 | SMH 10-02 | SOXX 8-03 | SOXX 10-02 |
|---|---|---|---|---|
| 50 日线上方占比 · 等权 | 4.17% | **96.00%** | 6.90% | **93.33%** |
| 50 日线上方占比 · 加权 | 20.20% | 94.99% | 8.43% | 92.67% |
| 200 日线上方占比 · 等权 | 87.50% | 91.67% | 92.86% | 92.86% |
| 200 日线上方占比 · 加权 | 93.08% | 93.69% | 93.02% | 90.13% |
| 52 周新高家数 | 0 | 0 | 0 | 0 |
| 52 周新低家数 | 0 | 0 | 0 | 0 |
| 中位票离 52 周高点 | −31.38% | **−16.80%** | −31.38% | **−19.05%** |

8-03 两只的中位数一模一样，不是抄错：两个篮子的中位都落在同一对票上（LRCX −32.81%、AMAT −29.94% 取平均）。
| ETF 自己离 52 周高点 | −18.81% | **−6.14%** | −22.60% | **−10.16%** |

### 池子越窄，读数越好

同一天（10-01），同一把 50 日线尺子，四个池子：

| 池子 | 只数 | 50 日线上方占比（等权） |
|---|---|---|
| 全市场（已发布） | 5,617 | 25.21% |
| 半导体主题三组并集（T-1002-80） | 120 | 74.17% |
| SOXX 持仓 | 30 | 93.33% |
| SMH 持仓 | 25 | 96.00% |

**ETF 内部宽度是一句大市值的话。** 32 只 ETF 成分全部已经在 T-1002-80 那 120 只名单里——这两条序列是那个池子里最大的一截，不是另一个样本。拿「SMH 内部 96% 的票在 50 日线上」去说「半导体宽度好」，等于拿前 25 名去说全班成绩。

### 52 周新高新低：全零，不能当阈值

44 个交易日 × 两个篮子，52 周新高 **0** 次、新低 **0** 次。换 20 日窗口才有读数：SMH 全窗口 6 次（单日最多 2 只），SOXX 9 次（单日最多 4 只）；20 日新低各 1 次。

这和 T-1002-80 的 120 只池子对上：那边 43 天也只有 1 次 52 周新高（SLAB，9-03）。**这是一次从回撤里的修复，不是新高行情**，池子换成 ETF 持仓之后这句话更干净——ETF 篮子里一次都没有。

### 等权与加权的差，是这两只 ETF 真正不同的地方

| | SMH | SOXX |
|---|---|---|
| 加权 − 等权，均值 | **+14.32** | **+4.54** |
| 最大 | +25.07（9-16） | +19.95（9-16） |
| 最小 | −1.01（10-01） | −6.50（8-12） |
| 加权 > 等权的天数 | **42 / 44** | **34 / 44** |

读法：**正数＝大票比小票强，ETF 的价格比它的篮子好看。** SMH 这个差几乎全程为正且大一倍多，因为它的头部集中度更高（单只 19.27% 对 9.44%）。

同一件事在 9-14 那天反过来看得最清楚：SMH 的加权读数从 9-11 的 59.85% 掉到 **8.47%**，等权从 37.5% 掉到 8.33%。头部一倒，加权的优势一天内消失——集中度在两个方向上都放大。

---

## 三、给稿子的两条用法

### 第 3 段用哪个 ETF 做代表

**用 SOXX。** 三条理由，都能在上面的表里查到：

1. 30 只对 25 只，单只上限 9.44% 对 19.27%——SOXX 更像「这个行业」，SMH 更像「NVDA 加一篮子」。
2. SOXX 的 30 只全在半导体/半导体设备行业；SMH 有 2 只 EDA 软件（CDNS、SNPS）。稿子讲的是半导体，不是半导体加 EDA。
3. SOXX 的加权与等权只差 4.54 个百分点，它的价格更接近它篮子的平均票。拿 SOXX 的走势讲宽度，论据和结论指的是同一件事。

⚠️ 换成 SOXX 之后，「创新高」那句仍然要改。SOXX 离 52 周高点 −10.16%，比 SMH 还远 4 个百分点。

可改的说法（两种都有数支撑）：「SOXX 9 月 22 日突破了 9 月区间」，或者直接用 10-02 的 **SOXX 成分里 93.33% 的票收在 50 日线上方**。

### 第 7 段第一条作废条件读哪条序列

**读 `soxx_eq_pct_above_200sma`，不读 50 日线那条。** 理由和 T-1002-80 第六节同一条，这里的数更极端：

- 50 日线那条五周能走 **89.88 个百分点**（SOXX 从 9-01 的 3.45% 到 10-02 的 93.33%）。任何固定阈值在这个窗口里会触发两次方向相反的信号。
- 200 日线那条全窗口在 **71.43%–96.43%** 之间，8-03 和 10-02 都是 92.86%。它说这个篮子的长期上升结构没断。**这条被吃光，才是「刹车论证的前提失效」。**
- 52 周新高新低在 30 只的篮子里恒为 0，不能当阈值。20 日窗口单日最多 4 只，也偏钝。

阈值本身归 Andy 定，这里只交该知道的三个事实。

---

## 四、必须跟着数一起交出去的四条告知

### ⚠️ 1. 权重是 10-01 定格的，没有回溯

加权那两条臂，44 天用的是**同一份** 2026-10-01 的权重。两只 ETF 在 8 月和 9 月的真实权重和 10-01 不一样（指数季度调仓 + 价格漂移）。
方向：这会**低估**加权臂在窗口早期的波动，因为 8 月的头部权重分布被换成了 10 月的。
两只 ETF 都用同一个做法，所以上面那张「加权 − 等权」的对照表在**两只之间**是可比的；每一天的绝对值不可比。

### ⚠️ 2. 持仓是 10-01 的，序列到 10-02

两份持仓文件的 as-of 都是 **2026-10-01**（同一天，这是好事：两只 ETF 的成分表可对账）。宽度序列跑到 **2026-10-02**，因为那是最近完成的交易日（`pipeline.marketcal.last_completed_session`）。
10-02 那一天的读数用的是 10-01 的成分表。一天的成分漂移，不是零，但 ETF 季度调仓，10-01→10-02 之间没有调仓日。

### ⚠️ 幸存者偏差（照常注明）

池子是 **10-01 的持仓表倒推回 8 月**。8 月真实在册、后来掉出指数的名字不在这两个篮子里。
方向是**乐观偏差**：活到 10-01 还在名单上的票，平均比当时的真实名单强。
`*_n_present` 列记了每天实际有行情的只数：SMH 全程 25，SOXX 全程 30，所以这个窗口里**掉出去的名字一只都没有被量到**——偏差存在，但它不表现为缺行情。

### ⚠️ 两只票过不了 52 周那道闸

共同股闸在这两个篮子里有一半是空转的：32 只里 **0 只**是 `Shell Companies`。真正起作用的是 200 根日线那条门槛：

- **SKHY**（SK Hynix ADR）两只 ETF 都持有，10-02 时日线不足 200 根，所以不进 52 周新高新低的分母；它在 8-03 连 50 根都不够，所以 50 日线那条臂的分母在 9-18 之前是 SMH 24 / SOXX 29。
- **CBRS**（Cerebras，只在 SOXX 里）同样不足 200 根。

所以 52 周那两列的分母是 SMH **24**、SOXX **28**，不是 25 和 30。CSV 里 `*_n_gate_52w`、`*_n_gate_4w`、`*_n_with_sma50` 三个分母都单列了。

---

## 五、尺子校准

组内序列是我自己从 yfinance 日线算的；已发布的全市场序列走的是 Finviz 字段。两把尺子先对上，否则上面所有对照都是在比两件不同的东西。

10-02 逐票对照（脚本里的 `verify_control()`，带 assert，尺子漂了会当场崩）：

| 项 | 结果 |
|---|---|
| 50 日线距离，中位绝对差 | **0.00000**（最大 0.0000） |
| 50 日线**符号**不一致的票 | **0 / 32** |
| 50 日线上方只数 | 我算 **30**，已发布 **30** |
| 52 周高点距离（用**日内最高价**滚动），中位绝对差 | **0.00000** |
| 52 周高点距离（用**收盘价**滚动），中位绝对差 | 0.01298 ← **阴性对照臂** |
| 新高旗标不一致的票 | **0 / 30** |

收盘价那一臂是故意留着的：Finviz 的 52 周区间走日内高低点。`verify_control()` 里断言「收盘价臂的误差必须比日内高价臂大 5 倍以上」——哪天它不再明显更差，这个对照就分辨不出两种做法了，那时脚本会崩，而不是给我一个好看的绿。

### 新代码那条臂的闸

加权臂是这一轮的新代码，也是新的缺陷面。它有两种长得很正常的坏法：符号反了（数成线下的权重），或者分母用了全部已发布权重（而不是当天真有读数那些票的权重）。
[`pipeline/tests/test_semi_etf_breadth_series.py`](../../../pipeline/tests/test_semi_etf_breadth_series.py) 的 13 道闸每一条都**两侧各探一次**（重仓票放到线上、再放到线下），期望值写成字面量，不从被测代码读的那本权重字典里取。

按「能坏的方式」造的五个阳性对照，各打红对应的闸（本轮实测）：

| 变异 | 结果 |
|---|---|
| 加权臂符号反过来 | 6 failed |
| 加权臂分母换成全部已发布权重 | 3 failed |
| `min_periods` 改回 pandas 默认（252 根门槛） | 1 failed |
| 空分母返回 0.0 而不是 None | 1 failed |
| 没有行情的持仓算成「线下」 | 1 failed |
| 原样 | 13 passed |

---

## 六、重算

```bash
python3 data/research/semi_etf_breadth_2026-10-04/build_series.py        # 重取 bars，重建 csv
python3 -m pytest -q pipeline/tests/test_semi_etf_breadth_series.py      # 13 道闸，不联网
```

现抓 yfinance 日线（32 只成分 + 两只 ETF，本轮实测 8 秒），重建全窗口，跑完 `verify_control()` 的四条断言才写文件。

持仓文件不自动重取——两份 CSV 是 2026-10-01 的快照，committed 在本目录里。要换一天：

```bash
# SMH（xlsx）
curl -sS -A "Mozilla/5.0" -c /tmp/vcj -b /tmp/vcj -L \
  -o /tmp/smh.xlsx "https://www.vaneck.com/us/en/etf/equity/smh/holdings/download/xlsx/"
# SOXX（csv）
curl -sS -A "Mozilla/5.0" -L \
  -o /tmp/soxx.csv "https://www.ishares.com/us/products/239705/ishares-semiconductor-etf/latest-holdings.csv"
```

⚠️ **换持仓必须同时重跑脚本并重新提交两份 CSV 和 `etf_facts.json`。**
闸里有一条 `test_holdings_files_and_published_facts_agree` 卡这件事：持仓文件换了而 `etf_facts.json` 没跟着重建，它会红。

⚠️ 仓库是 PUBLIC。两份持仓 CSV **只留 ticker、名称、权重百分比、域籍、交易所**，发行方原件里的市值、股数、价格列全部删掉了。重取时照同样的做法删，别把原件整份提交。
