# 度量的权威口径表

**立于 2026-08-31（Andy 亲定）。** 起因：我为了给"新高新低"配一个短窗版本，
手搓了三个选择——4 周窗口、`$5/股 + $5M 成交额`的流动性闸、200 根 K 线下限。
Andy：**「很多数据是有专业的衡量的，不需要你去计算去创造。只需要去哪里找。」**

一查就知道他是对的，而且不是小对：

- **行业标准的做法根本不是流动性闸，是证券类型过滤。** NYSE / Nasdaq / NYSE Arca
  的官方新高新低口径明确排除 unit investment trusts、closed-end funds、warrants、
  preferred、ETF、**SPAC**、非 SIC 分类(OTC)股。我们被 SPAC 污染的那 88%，
  在标准口径里**根本不该进这个池子**。我的成交额闸只是它的粗糙代理，
  而且会顺手扔掉合法的小盘普通股。
- **「4 周新高新低」不是一个行业指标。** 52 周是机构惯例。那个时间尺度上的标准量是
  %above-20MA、T2108(%above-40MA)、McClellan——**这三个我们本来就有**。
- **标准工具箱里有两个我们没有的东西，正好治我们的病**：`Record High Percent`
  = NH/(NH+NL)，和 `High-Low Index` = 前者的 10 日均。它们是**比值**，
  所以对 08-14 那次 universe 从 3000 涨到 5614 的断层免疫——
  而我一直在用会被断层污染的原始计数做时序比较。

## 规矩

> **动手算一个量之前，先查它有没有专业口径和公开源。有就照抄，没有才自己造，
> 并把「查了什么、为什么没有」写进本表。**

判定「有没有」的最低动作：一次针对性检索（指标名 + "definition" / "calculation"）
+ 至少一个权威来源（StockCharts ChartSchool、Worden、交易所官方口径、指数编制方法书、
学术原文）。查不到也要留痕——写"查过，无标准"，比不查就造强。

自造的量必须在代码注释和契约行里**明写它是自造的**，并写清它偏离了哪个标准、为什么。
自造量**不得**出现在页面上冒充标准读数。

## 登记表

| 我们发的 | 标准名 | 标准口径 | 状态 |
|---|---|---|---|
| `mcclellan_osc` | McClellan Oscillator | RANA = net/(adv+dec)×1000，19 与 39 日 EMA 之差 | ✅ **一致**（`breadth_store.py:84-91`） |
| `ad_line` | Advance-Decline Line | 净涨跌家数累加 | ✅ 一致 |
| `t2108` | Worden T2108 | 40 日均线上方占比 | ✅ 一致 |
| `pct_above_20/50/200sma` | Percent Above Moving Average | 同名 | ✅ 一致 |
| `new_highs` / `new_lows` | 52-week New Highs/Lows | 52 周极值，**池子只含普通股** | ⚠️ **原始计数保留不动**（574 行档案的连续性），标准口径另发下一行 |
| `new_highs_common` / `new_lows_common` | 同上 | 排除 UIT / CEF / warrant / preferred / ETF / **SPAC** / 非 SIC OTC | ✅ **一致**（2026-08-31 落地）。Finviz 已挡住 ETF/CEF/preferred/warrant，我们补上 `industry == "Shell Companies"` |
| `record_high_pct` | Record High Percent | NH/(NH+NL) | ✅ **一致**（2026-08-31 落地），用 common 计数做分子 |
| `high_low_index` | High-Low Index | Record High Percent 的 10 日均 | ✅ **一致**（2026-08-31 落地） |
| `new_highs_4w` / `new_lows_4w` | *(查过，无标准)* | 52 周是机构惯例；该时间尺度的标准量是 %above-20MA / T2108 / McClellan | ⚠️ **自造**。仅供研究，不得当标准读数上页 |
| — | McClellan Summation Index | McClellan 振荡器累加 | 🔲 我们没有 |
| — | Arms Index (TRIN) | (adv/dec)÷(上涨量/下跌量) | 🔲 我们没有 |
| — | Bullish Percent Index | P&F 买入信号占比 | 🔲 我们没有 |

## 已登记的债

1. **把新高新低的池子换成标准的普通股口径**（排除 SPAC/CEF/ETF/preferred/warrant/
   非 SIC）。这是根治；现在的 `*_liq` 三道闸是代理，替换后应退役。
   需要证券类型字段——Finviz 有没有、还是要另找源，未查。
2. **建 `Record High Percent` 与 `High-Low Index`**。比值口径能让 08-14 断层
   前后的序列重新可比，我们现在整段历史的原始计数是不可比的。
3. `new_highs_4w` 的去留，等 1 和 2 落地后重估——很可能标准量已经够用，
   它就不必存在。
4. 本表的三个阈值（`$5`、`$5M`、`200 根`）**没有搜索过备选、没有对标任何标准**，
   是我拍的。替换为类型过滤后它们应当消失，而不是被"调优"。

## 相关

- 事故与实测数字：[nhnl_4w.md](../research/canary_2026-08/nhnl_4w.md)
- 研究纪律（预注册/证据分级/holdout）：[RESEARCH_PROTOCOL.md](RESEARCH_PROTOCOL.md)
- 数字的唯一权威源：`KNOWLEDGE.md` 数字权威表（本表管**口径**，那张表管**数值**）

来源：[StockCharts ChartSchool 市场指标目录](https://chartschool.stockcharts.com/table-of-contents/market-indicators) ·
[Barchart 新高新低汇总（池子排除规则）](https://www.barchart.com/stocks/highs-lows/summary) ·
[AAII: Using New Highs and New Lows to Measure Market Breadth](https://www.aaii.com/journal/article/455994-using-new-highs-and-new-lows-to-measure-market-breadth)
