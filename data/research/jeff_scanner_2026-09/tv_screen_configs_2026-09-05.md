# TradingView 筛选器配置底账 — Andy 自建 26 个 + Jeff 分享页实录（2026-09-05 抓取）

**来源**：Andy 的 TradingView 账号（他已把 Jeff 的分享 Copy 成自己的并改造/补建）。抓取方式 = 浏览器内同源读取
screener-storage 的已存清单（页面自身调用的接口，登录态浏览，无爬虫）。**这是「口径先行」的原配置，
jeff_sun.py 里逆向的 13 个 TV 规格应以此为准对账。**

记号：`COL[...]` = 列对列比较；`range A to null` = 仅下限；`GT/LT/EQ` = >/</=（原文符号）；
`Sector(20) EXCLUDES Health Technology` = 全部 21 个 TV sector 只排除生物科技/制药（Jeff 硬规则③）；`wl_n 1` = 该筛挂在自选表上（watchlist 域）。

## 一、Andy 的股票筛（23 个，编号 1–15 对应 Jeff 体系）

### 1. CAN-SLIM Style Strong Growth Weekly Screener（sort Industry desc）
- MarketCap ≥ 300M；EpsDilutedGrowth(YoYQuaterly) > 25；RevenueGrowth(YoYQuaterly) > 25
- Performance(1W) in [-5, 5]；Price ≥ MA50；EMA10 ≥ MA20
- AvgVol(60D) > 800K；Volume(1D) > 500K；ADR% ≥ 4

### 2. High ADR% + Inside Day Qullamaggie Style（sort Industry desc）
- Sector(20) 排除 Health Technology；Performance(6M) > 30；AvgVol(60D) > 500K；Volume(1D) > 100K
- ADR% ≥ 3；Price > 1；MarketCap in [1B, 200B]；**Pattern IN harami_bullish（= inside day 的 K 线模式实现）**

### 3. Long Base Compression（sort Industry desc）
- MarketCap ≥ 300M；Sector(20) 排除 Health Technology；**Performance(YTD) < 0**
- AvgVol(60D) > 1M；Volatility(1W) > 4；Volume(1D) > 500K；Price > 1
- Price > MA50 且 **Price 在 MA200 下方 20% 以内**（belowPercent offset_range_20）——「打回去但守住结构」

### 4. Strongest Mover (1W,1M,3M,6M)（sort Industry desc）
- MarketCap ≥ 500M；Sector(20) 排除 Health Technology；AvgVol(60D) > 2M；Volume(1D) > 500K
- Volatility(1W) > 4；**Performance(1W) > 20 且 Performance(6M) > 50**

### 5. Watchlist Scan (5ema below <5%)（sort Industry desc；wl_n 1）
- MarketCap ≥ 300M；Sector(20) 排除 Health Technology；Volatility(1M) > 3.5；Performance(1W) < 5
- **Price 距 5EMA 上方 0–5% 以内**（abovePercent offset_range_0_5）；EMA10 ≥ MA20

### 6. VCP（sort MarketCap desc）
- MarketCap ≥ 300M；Sector(20) 排除 Health Technology；Price ≥ 10；Exchange AMEX/NASDAQ/NYSE；CommonStock
- **Performance(1W) in [-5,5] 且 Performance(1M) in [-20,20]**（收缩本体）
- Price > EMA10、≥ MA21、≥ MA50、≥ MA200（全多头排列）
- RevenueGrowth(YoYQuaterly) > 20；EpsDilutedGrowth(YoYQuaterly) > 20

### 7. Julian Komar's Strongest Stock Scan（sort MarketCap desc）
- MarketCap ≥ 300M；Sector(20) 排除 Health Technology；AvgVol(60D) > 500K；AMEX/NASDAQ/NYSE；CommonStock
- Price ≥ MA50；RevenueGrowth(YoYQuaterly) > 20；EpsDilutedGrowth(YoYQuaterly) > 20

### 8. Episodic Pivots（sort PreMarketVolume desc）
- MarketCap ≥ 500M；Sector(20) 排除 Health Technology；AvgVol(60D) > 1M；**Volume(1D) > 20M**
- ADR% ≥ 3；Price ≥ 5；**RVOL(1D) > 2.5**

### 9. Pre-Market Screener（sort PreMarketVolume desc）
- Price ≥ 1；**PreMarketChange > 3；PreMarketVolume > 100K**；AvgVol(60D) > 1M
- MarketCap ≥ 100M；ADR% ≥ 4；AMEX/NASDAQ/NYSE

### 10. Liquid Leader Scan（sort Industry desc）
- **MarketCap ≥ 10B**；Sector(20) 排除 Health Technology；AvgVol(60D) > 1M；Volume(1D) > 1M
- **ADR% in [3, 15]**；Price > EMA50、≥ EMA20、≥ 10；AMEX/NASDAQ/NYSE；CommonStock

### 11. Liquid Leader Pullback Scan（sort PreMarketVolume desc）
- 同 10 号全部条件 + **Performance(1W) < 12**（回踩窗口）

### 12. Pre-Market: Earnings Today（sort PreMarketChange desc）
- Price ≥ 1；AvgVol(60D) > 800K；**EarningsRecent = Today**；AMEX/NASDAQ/NYSE

### 13. Bull Snort（sort RVOL(1D) desc）
- MarketCap ≥ 500M；Sector(20) 排除 Health Technology；Price ≥ 20；Volume(1D) > 500K；**RVOL(1D) > 3**；CommonStock

### 14. Doubled（sort RVOL(1D) desc）
- **MarketCap ≥ 10B 且 MarketCapPerf(1Y) > 100**（一年市值翻倍的巨头）

### 15. Weekly 20%+（sort Change(1W) desc）
- Price ≥ 1；**Change(1W) > 20**；MarketCap ≥ 1B；Sector(19) 排除 Health Services + Health Technology
- AvgVol(60D) > 1M；ADR% ≥ 3.5；AMEX/NASDAQ/NYSE

### 无编号（Andy 自建/引进）
- **Live: Biggest mover (Rvol > 1)**（sort RVOL desc）：Price ≥ 1；Change(1D) > 3；RelativeVolumeAtTime > 1；AvgVol(60D) > 1M；Volume > 1M；AMEX/NASDAQ/NYSE；MarketCap ≥ 300M
- **Live: GAP (Rvol > 1)**（sort RVOL desc）：Price ≥ 1；RelativeVolumeAtTime > 1；**Gap(1D) > 3**；AvgVol(60D) > 1M；Volume > 1M；MarketCap ≥ 100M
- **Marios-Trend Leaders**（sort MarketCap desc）：Price > EMA10；MarketCap ≥ 1B；Sector(20) 排除 Health Technology；CommonStock；ADR% ≥ 3.5；**EMA10 ≥ EMA21 ≥ EMA50 ≥ MA150 ≥ MA200 全链**
- **Above 10/20/50-MA**（sort MarketCap desc）：MarketCap ≥ 1B；Sector(20) 排除 Health Technology；Price > MA10/MA20/MA50；CommonStock；AvgVol(60D) > 1M；ADR% ≥ 5；RevenueGrowth(YoYTTM) > 0
- **Best winners- Julian K v.2**（sort Performance(3M) desc）：Price ≥ 1；ADR% ≥ 4.5；**Price ≥ 52周低点上方 70%**（offset_range_70）；PriceAvgVolume(30D) > 10M；VolumePrice(1D) > 5M；EMA8 > EMA21；Price > EMA60；MarketCap ≥ 1B
- **Focus List (RVOL)**（sort RVOL desc；wl_n 1）：零条件——纯粹把自选表按 RVOL 排序（= Jeff 的盘中 Focus List 用法）
- **AH: WL-Compression**（sort Sector asc；wl_n 1）：Performance(1W) in [-5,5]；Price ≥ MA5；ADR% ≥ 4；AvgVol(60D) > 800K
- **explosive=high short float+low flow+high adr**：空草稿（全部条件未填值）

## 二、Andy 的 ETF 筛（3 个）

- **Live Market: Gappers ETF**（sort Change desc）：AvgVol(10D) > 1M；ADR% ≥ 4；**ChangeFromOpen(1D) > 1**；非杠杆
- **16. HIGH PERFORMANCE LIQUID ETF**（sort Change desc）：非杠杆；AvgVol(60D) > 1M；ADR% ≥ 3；Volatility(1W) > 3
- **Post-Market-WL-ETF-Compression**（sort ADR% desc；wl_n 1）：Performance(1W) in [-10,10]；Price ≥ MA5；EMA10 ≥ MA20

## 三、Jeff 的 Screen Sharing 原版（2025-10-27 公告帖 [1982678925483684325](https://x.com/jfsrev/status/1982678925483684325)，本日实测）

8 条 TV 分享链接实测：**6 活 2 死**（y9Vb5TZ4「Pre-market Earnings」与 plHIxbZ9「Live Gappers」404——Andy 的 12 号与 Live: GAP 已覆盖同用途）。活链实录：

1. **Pre-Market: Movers**（/screener/4UQQvtiZ/）：Price ≥ 1；Sector(20) 排除 Health Technology；PreMktChg > 3；AvgVol(60D) > 2M；PreMktVol > 100K；MarketCap ≥ 100M；VolumePrice(1D) > $10M
2. **Market: Biggest mover (Rvol > 1)**（/screener/aEGWcBbP/）：Change(1D) > 3；Sector(20) 排除 Health Technology；RelativeVolumeAtTime > 1；AvgVol(60D) > 2M；MarketCap ≥ 100M；**ADR% ≥ 3**；VolumePrice(1D) > $10M
3. **Market: Gappers ETF**（/etf-screener/5SvZkfBa/）：AvgVol(10D) > 1M；Performance(1W) > 0；Price ≥ 1
4. **Focus List (RVOL)**（/screener/ZSL0eeqU/）：零条件，watchlist 域按 RVOL 排序
5. **Compression（股）**（/screener/NrDDZqUi/）：watchlist 域；**Price ≥ EMA20；High(1D) < 1月High；ChangeFromOpen in [-3.5, 3.5]**；sort Industry asc
6. **Compression（ETF）**（/etf-screener/K5IuxSty/）：watchlist 域；Price ≥ EMA20；High(1D) < 1月High；ChangeFromOpen in [-2.5, 2.5]（他的私有 watchlist 不随链接分享，故复制品打不开结果——但过滤逻辑完整）

**对比读数**：Andy 的复制品普遍把门槛改得更严（Biggest mover 的 MarketCap 100M→300M、加了 Vol>1M/交易所白名单），并砍掉了 Jeff 的 VolumePrice($10M) 换成自己的流动性组合——对账时以「结构同、参数自调」理解，不算漂移。

同帖的 6 条 Finviz 链接（t.co 码：WxaYfRrpSr / z3DhNR9SR4 / OMn8QPVsrV / A4Gk86LRsP / mWHKoGsS38 / x84gKoydiJ），关键参数摘要：
1. **CANSLIM Calibrated**：cap_midover · sales QoQ high + YoY TTM high · 行业白名单（约140行业，排除生物科技/制药）· avgvol>2M · curvol>1M · **insttrans_pos（机构净买入，Finviz 独有）** · 20日/50日高点距离<5% · 周波动>4
2. **Bases at Beaten Down**：cap_smallover · price>1 · 距历史高点>70%下方 · 距50日高<15% · 距52周低<30%上方 · YTD 下跌 · SMA200 ±20% · 周波动>4 · insttrans_pos
3. **Hottest Stock**：cap 0.15B+ · avgvol>2M · float<500M · **short_high** · 13周涨>30% · 周波动>5 · 按行业排
4. **Highest Short Float**：cap_smallover · avgvol>1M · **float<100M · short>30%** · v=131（所有权视图）
5. **IPO**：cap_midover · **ipodate_prevyear** · avgvol>1M · insttrans_pos
6. **Liquid ETF**：ind_exchangetradedfund · avgvol>1M · 周波动>3

## 四、与 jeff_sun.py 对账的待办

- [ ] `TV_SCANS`（Colab 逆向 13 个）逐条 diff 本文件第一节的同名者——**以本文件为准**修正参数漂移
- [ ] `local_mask` 缺列清单可缩短：EarningsRecent/Pattern(harami) 仍缺源；MA/EMA 链、ADR%、RVOL 我们已有
- [ ] Finviz 的 insttrans（机构净买入）无自动免费源——PLAN.md 数据源决策的输入

*抓取：DATA ALEX 2026-09-05（Andy 授权用其登录态浏览器；无 scanner API 爬取，全部为页面自身请求）。*
