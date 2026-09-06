# 那 18 个 index 分别是什么

《Stock Trader's Almanac》第 96 / 98 页 *Sector Index Seasonality Strategy Calendar* 用的全是
**1990 年代的交易所板块指数代码**（AMEX / PHLX / NYSE Arca 那一套），不是今天常说的 ETF 代号。
所以看着陌生。以下逐个核实（2026-09-07 用 Yahoo 逐个拉行情确认代码仍活着、名称以其返回的
`longName` 为准；**不是凭记忆写的**）。

「对应 ETF」一列是**可交易的近似替身**，不是官方挂钩关系——大多数这些指数没有直接跟踪它的
ETF，替身只是成分和口径最接近的那个。用它做季节性时，替身和原指数会有偏差，别当同一个东西。

## p.96 的 9 行

| 代码 | 全称（Yahoo 实测） | 中文 | 对应 ETF（近似） |
|---|---|---|---|
| **BKX** | KBW Nasdaq Bank Index | 银行 | KBE / KBWB |
| **BTK** | NYSE Arca Biotechnology Index | 生物科技 | XBI（等权，口径最近）/ IBB |
| **S5COND** | S&P 500 Consumer Discretionary | 可选消费 | XLY |
| **S5CONS** | S&P 500 Consumer Staples | 必选消费 | XLP |
| **S5INDU** | S&P 500 Industrials | 工业 | XLI |
| **DJT** | Dow Jones Transportation Average | 道琼斯运输 | IYT |
| **DRG** | NYSE Arca Pharmaceutical Index | 制药 | PPH / XPH |
| **S5HLTH** | S&P 500 Health Care | 医疗保健 | XLV |
| **S5INFT** | S&P 500 Information Technology | 信息技术 | XLK |
| **RMZ** | MSCI US REIT Index | 房地产信托 | VNQ / ICF |

> ⚠️ 书上把 **S5COND & S5CONS 并成一行**（可选消费与必选消费共用同一套季节性区间）。
> 这两个板块在现实里经常反向，合成一行是他们的简化，不是共识——照抄要留神。

## p.98 的 9 行

| 代码 | 全称（Yahoo 实测） | 中文 | 对应 ETF（近似） |
|---|---|---|---|
| **S5MATR** | S&P 500 Materials | 原材料 | XLB |
| **SOX** | PHLX Semiconductor | 半导体 | SOXX / SMH |
| **UTY** | PHLX Utility Sector | 公用事业 | XLU |
| **XAU** | PHLX Gold/Silver Sector | 金银矿 | GDX（仅近似：XAU 只 30 来只大矿商） |
| **XBD** | NYSE Arca Securities Broker/Dealer | 券商 / 经纪商 | IAI |
| **XCI** | NYSE Arca Computer Technology | 计算机科技 | XLK / IGV（无直接对应） |
| **XNG** | NYSE Arca Natural Gas Index | 天然气 | FCG |
| **XOI** | NYSE Arca Oil Index | 石油（综合大盘股） | XLE / IEO |
| **XTC** | NYSE Arca North American Telecom | 北美电信 | IYZ / XTL |

**S&P 的 `S5xxxx` 那一族**（S5COND / S5CONS / S5INDU / S5HLTH / S5INFT / S5MATR）是彭博终端的
S&P 500 行业指数代码，一一对应今天的 SPDR 板块 ETF（XLY / XLP / XLI / XLV / XLK / XLB）——
这一组是全表里对应关系最干净的。

## 图怎么读

每个指数一行，行内分上下两条通道：**L = 做多、S = 做空**。
横轴是 12 个月 × 每月三段（**B**egin / **M**iddle / **E**nd，上/中/下旬）。
色块 = 持仓区间，**箭头 `→` = 入场点**。所以一行同时给出**方向 × 时段 × 起点**三件事——
比常见的季节性热力图（只画平均涨跌）多一个维度。**这个编码结构值得学，内容不能抄**（版权，见 README）。

书上注明这两页是第 94 页 *Sector Index Seasonality Percentage Plays* 的图形版——
**胜率与平均涨幅那张表我们没有拍**，所以这两页只有区间、没有样本量和胜率。
这也正是自己重做时该补的那一列。

## 与我们自己的主题表怎么对上

我们 `data/output/groups.json` 里 56 个主题中，能直接对上的：Semiconductors Broad（≈SOX）、
Utilities（≈UTY）、Gold Miners（≈XAU）、Oil & Gas（≈XOI）、Real Estate（≈RMZ）、
Defense / Financials / Regional Banks（≈BKX 的一部分）、Genomics（≈BTK 的一部分）。
**没有对应的**：XCI（计算机科技，我们拆成 Software / Cloud Software）、XTC（电信，我们没有）、
XNG（天然气，我们只有 Oil & Gas 混在一起）、XBD（券商，只有 Finviz 行业层的 Capital Markets）。

*核实：DATA ALEX 2026-09-07。13 个非 S&P 代码逐个拉 Yahoo 行情确认仍在交易，名称照抄其 longName。*
