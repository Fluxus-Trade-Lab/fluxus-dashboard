# TSF 四态分类：查过，没有公式（2026-09-23）

Andy 09-22 要求：「查找TSF的原始定义，我们有他的substack全文和图片，看看有没有痕迹」→ 09-23「先读那篇」。

## 查了哪些（全部现场取页）

| 来源 | 档位 | 有没有四态的算法 |
|---|---|---|
| 平台 Market Overview「How To Interpret The Groups」（抄录在 `Fluxus_Receipts/tsf/raw_data.md:182-185`） | 平台内 | ❌ 只有文字：正/负 RS × 动能加速/减速。无窗口、无公式 |
| [Space Stocks Exploding…](https://thesetupfactory.substack.com/p/space-stocks-exploding-use-the-tsf)（2025-12-23） | 免费 | ❌ 方法只写一句「I use proprietary timeframes and calculations」 |
| [Market Composite Score - Backtests](https://thesetupfactory.substack.com/p/the-tsf-market-composite-score-backtests)（2025-12-26） | 免费 | ❌ 只列输入大类（趋势/趋势动能/广度/广度动能/信用＋自称 secret sauce），不给参数 |
| [Guide For Assessing Relative Strength](https://thesetupfactory.substack.com/p/tsf-guide-for-assessing-relative)（2026-05-05） | **付费**，用 Andy 的登录读过，正文不抄进仓库 | ❌ 全篇是目视判据：RS 线结构（更高的低点/更高的高点）、RS 线先于价格创新高（日线与周线）、弱市里还站在 10SMA/EMA21/50SMA 上、离 52 周高 10–15% 以内、同组内谁最抗跌。平台自述 proprietary |

## 结论

**TSF 的四态无法照原文复刻**——作者明说算法专有，公开材料里只有文字定义。RRG（四态名字的真正出处）同样只公开象限规则、不公开 RS-Ratio / RS-Momentum 的公式。
因此四态重做只有两条诚实的路：①做近似 RRG 并写明近似；②承认是自造并换掉这四个名字。待 Andy 裁（T-0921-07）。

## 顺带两条可用的事实

- **他的分组每周五收盘才更新一次**（平台自述），我们每天重算——同一主题读数对不上，时钟不同是原因之一（08-10 页面对照已记）。
- 他的 Screener 列是 `RS 0-2W / 0-4W / 0-10W` ＋单独一列 `RS Accel`：**强度用累计窗口、加速度另算**，和我们 08-09 实测选的取法同向。
- 那篇指南里唯一能直接借用的思路：**个股不只比大盘，还要比它自己所在的组**（"We will measure stocks relative performance against their own industry group, theme or sector"）——Screener 那列个股四态若要重做，这是有出处的做法。
