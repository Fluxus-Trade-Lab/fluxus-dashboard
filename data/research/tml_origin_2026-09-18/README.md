# TML（True Market Leader）的来源与各家定义 · 2026-09-18（DATA ALEX）

Andy 09-18：「查阅一下TML 概念 权威的是谁从哪里来 然后 谁在用这个概念 他们又是怎么定义的 和Alex的有什么区别」

## 结论
- **概念源头：William O'Neil**（CANSLIM 的 L = Leader；他把这类股叫 *Model Book Stocks*）。O'Neil 本人**没有**用「TML」这个缩写。
- **「TML / True Market Leader」这个词与定义：TraderLion 的 Richard Moglen**，[X 长帖 2020-11-06](https://x.com/RichardMoglen/status/1324813953474678787)（原文经 buzzchronicles 展开页 curl 逐字取得）。TraderLion 至今在用（Ross Haber 的付费周报 *The TML Report*）。
- **Alex Desjardins（TradersLab）没有定义过 TML**；他有的是「Liquid Leaders scan」。Andy 课程里「True Market Leaders」是 Phase 2 的章节名。

## Moglen 2020 原文（逐字）
> In one sentence a TML is an institutional quality stock in a leading industry group with superior fundamentals and technicals. These are monster stocks which over the course of weeks and months increase +100% to +5,000%.
> TMLs are popular with traders/investors whose methodology is based on the CANSLIM system developed by William O'Neil. He called them Model Book Stocks.

- 基本面：Quarterly Sales Growth > 25% YoY · Quarterly Earnings Growth > 25% YoY · Pre+After Tax Margins >20% Recent Quarters · ROE >17% · Annual Earnings Ests for the next year > 25% · Story（新产品/服务）。"Not every TML will have all of these criteria"。
- 行业：often in the Top 20 Industry groups。
- 流动性：Dollar Volume > $30 Million is essential（@Upticken likes > $100 Million）。
- 技术面：Above a Rising 30 Week Moving Average · Breaking out of a Stage 1 or Stage 2 Base · Trending above Key Moving Averages (10, 21ema, 50sma) · Volume and Price contractions within bases · Up/Down Vol > 1.2 · Huge gaps up on volume after Earning Beat。
- 相对强度："This. is. vital. RS Rating over 97 is ideal"；调整期里应接近历史新高。

## 对照
| | O'Neil（源头） | Moglen / TraderLion（TML 原文） | Alex · Liquid Leaders scan | 我们现在的 TML 面板 |
|---|---|---|---|---|
| 相对强度 | RS Rating 80–90+（book 统计大赢家起涨前均值 87） | RS > 97 理想 | Top RS rank（无数字） | `rs_1m` ≥ 80（我们自造的 1 月横截面分位） |
| 行业/主题 | 本行业第一名 | Top 20 industry groups 的领头者 | Group & Theme RS > 50 | 所在组状态 = Leading（自造四态） |
| 基本面 | C、A、N 各项 | 季度营收/盈利 >25%、利润率 >20%、ROE >17%、明年预估 >25% | 无 | 无 |
| 流动性 | — | $ 成交 > $30M（偏好 >$100M） | $100M/日、≥1M 股、价 >$10、市值 >$1B | liquid_leader（课程版：ADV ≥ 2M 股、站上 50 日线、RS 前 20%） |
| 趋势/形态 | 杯柄等底部突破 | 30 周线上行、Stage 1/2 突破、10/21/50 之上、量价收缩、U/D > 1.2 | ADR 3–15% | 无 |
| 剔除 | — | — | 中港、五个板块 | — |

## 没读到的（写明，不猜）
- O'Neil 原书本机无，引用来自二手转述（RS 80–90、均值 87）。
- TraderLion 现行页面（Leadership Blueprints、Ross Haber RS 线一文）与 ChartMill「How to Spot True Market Leaders」清单：均被站点拦截（403 / Cloudflare），未读原文。
