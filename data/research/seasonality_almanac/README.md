# Sector seasonality — 停车场条目（2026-08-26 存档）

Andy 2026-08-25 拍了《Stock Trader's Almanac》第 96 / 98 页的
**Sector Index Seasonality Strategy Calendar**，想做成前端上一张漂亮的图。
**当周未动工**（撞本周停做清单两条），此处只存档，防丢。

## 那两页画的是什么

18 个指数 × 12 个月 × 每月三段（B/M/E = 上/中/下旬），每行两条通道：
**L = 做多、S = 做空**，箭头 `→` 标入场点。也就是把
**方向 × 时段 × 起点**三件事压进一行——比常见的「季节性热力图」多一个维度，
后者通常只画「平均涨跌」。这个**编码结构**值得学，内容不能抄（见下）。

- **p.96**：BKX · BTK · S5COND&S5CONS · S5INDU · DJT · DRG · S5HLTH · S5INFT · RMZ
- **p.98**：S5MATR · SOX · UTY · XAU · XBD · XCI · XNG · XOI · XTC

原始照片已入库（2026-09-07）：[`photos/p96_sector_index_seasonality.jpg`](photos/p96_sector_index_seasonality.jpg) ·
[`photos/p98_sector_index_seasonality.jpg`](photos/p98_sector_index_seasonality.jpg)。
原图 5569×3774，入库前压到 2400px 宽（共 1.6 MB，表格仍可读全）；原始分辨率版留在 `~/Downloads/sector seasonality*.jpg`。

**那 18 个 index 代码分别是什么** → [`INDEX_GLOSSARY.md`](INDEX_GLOSSARY.md)（2026-09-07 逐个拉行情核实，非凭记忆）。

## 动工前必须先解决的两件事

1. **版权**：那是书里的图。照着重画一份对外发 = 把受版权保护的表换个皮。
   正路是**用我们自己的数据算同一个东西**——图是我们的、可验证、每年自动更新，
   还能把**样本量**印在图上（他们那张没印）。概念注明出处即可。
2. **数据我们现在没有**（2026-08-26 实测）：
   - `SqueezeMetrics/spx_ohlc.csv` = 2011-01 → 2026-02，约 15 年，**只有大盘**，且已停更。
   - 分行业长历史**一根都没有**：`data/output/tickers/` 里连 SPY / XLK / XLE 都没有文件；
     个股文件只有 `ohlc_2y`（两年，做季节性远远不够）。
   - 要做行业版：先抓 11 个行业 ETF 的 15–20 年日线 —— 数据端的活，且属「新研究」。

## 可以先做的最小一步（不需要数据端）

用手上真有的 SPX 15 年数据做**一张大盘月度季节性图**：一张图、真数字、零版权问题、
可直接当内容发。视觉语言先在这张上定稿，对了再谈扩到行业。

## 立项三件套（未填 —— 填了才动工）

| | |
|---|---|
| ① 发布物 | 待定 |
| ② 截止日 | 待定 |
| ③ 到期规则 | 待定 |
