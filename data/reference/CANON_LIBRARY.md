# 本机正典库：口径的一手来源在哪

**立于 2026-09-04。** Andy 当天定的：「我们的核心标准应该是 IBD / TraderLion / SMB / Stan Weinstein / Oliver Kell 这一套知识体系」。
这份是**盘点**，不是书评：每本在哪、里面有什么能当口径用、没有什么。下次查口径先翻这里，再上网。
引用顺序：**本机一手 → 发明者/官方网页 → 社区复刻**。

## 有，且给了可抄的规则

| 来源 | 路径 | 能抄什么 | 注意 |
|---|---|---|---|
| **IBD · CAN SLIM Chart Pattern Cheat Sheet** | `~/Downloads/Trading/03_Trading_Strategies/Strategy_Docs/CAN_SLIM_Chart_Pattern_Cheat_Sheet.pdf` | **3 Tight Closes：closes within 1.5%，vol drops，secondary BP**；Short Stroke：within 1%；High Tight Flag 3–5 wks / 10–20%；**所有 BP +10 cents**；旗、杯柄、平底等的周数与深度 | 只有数字没有**形式**（相邻两两 vs 全域带宽）；形式引 IBD 文章 |
| **Gregory Morris · The Complete Guide to Market Breadth Indicators** | `~/Downloads/Documents/The_Complete_Guide_to_Market_Breadth_Indicators…epub` | 广度正典。**新高/新低 = 52 周**（NYSE 1978 起固定窗）；**New Highs/Lows adjusted for Total Issues**（比值口径）；**Cohen (Investors Intelligence)：10 日均的 NH/(NH+NL)**——即 Record High Percent / High-Low Index 的谱系；Fosback **High Low Logic Index**（min(NH/TI, NL/TI) 的 50 日 EMA）；McClellan **Ratio-Adjusted**；A-D 的全套 | 我们 08-31 采用比值口径，这本是它的一手依据 |
| **TraderLion · Ultimate Trading Guide**（115 页） | Google Drive `Fluxus Trade Lab/03_Resources/Education/Old Education Folder/The-TraderLion-Ultimate-Trading-Guide.pdf` | **Closing Range = 收盘在当日 H–L 中的位置**（我们的 `dcr_pct` ✅）；**10-Day Pocket Pivot = 上涨日成交量 > 过去 10 日任一下跌日成交量**（我们的 `pocket_pivot` ✅）；**Weinstein 四阶段用 50d/10w、150d/30w、200d/40w** 三条均线；RS line 章；止损 1–3%（波动大 5%） | 这是本机唯一的 Weinstein 来源（TraderLion 转述）；**无 ADR / RMV / 3WT / oops** |
| **SteveDJacobs · ATR Matrix**（你的 Pine 笔记） | `…/Strategy_Docs/ATR Matrix.txt` | `ATR Ext = (close−SMA50)/ATR`，0–11× 阶梯；止损 −1/−2 ATR 自入场；**`extAtrAsPctOfATR = (close/SMA50−1)/(ATR/close)`**——即 Jeff Sun 的 B/A 形式 | 我们 `atr_from_sma50`（B/A）与 `plain_atr_multiple_from_sma50` **两个量都有出处** |
| **@TradeDudeNYC · Candles Stage Analysis**（你的 Pine 笔记） | `…/Strategy_Docs/Candles Stage Analysis.txt` | 阶段判定用 EMA10/20 + SMA50 排列；**扩张 ≥7× ATR、衰竭 ≥11×** | **我们 ≥7 的减仓线来自这里**，不是 Weinstein 原书 |
| **@jfsrev · 1-Month RS**（你的 Pine 笔记） | `…/Strategy_Docs/1-Month Relative Strength.txt` | RS = close/SPY，**自百分位**，`rank/(N−1)×100`（严格排名，下限 0） | 我们 `rs_line_pctl_21` 的谱系；**我们用 `<=`，它用严格排名**——待改 |
| **Qullamaggie · Swing Trading School 笔记（harisd）** | `…/Strategy_Docs/harisd_summary…pdf` | 用 **ADR** 作波动尺（“High ADR of 13%”），10/20/50 dma，“tight range with higher lows” | 笔记里**无 ADR 公式**；公式仍引 Qullamaggie FAQ / Deepvue / TradingView |

## 有，但是图集或过程书（不给公式）

| 来源 | 路径 | 里面是什么 |
|---|---|---|
| TraderLion **Model Book 2021** | Google Drive `…/Swing Class 2025/…/2021-TraderLion-Model-Book.pdf` | 47 页模型股图 |
| Ian Leatherbury **2016 Model Book v1** | `~/Downloads/2016 — Model Book v1.pdf` | 22 页图，几乎无文字 |
| TraderLion **Trade-Lab Breakouts Model Book（Fall 2025）** | Google Drive `…/Old Education Folder/Trade-Lab-Breakouts-Model-Book.pdf` | 图标签词汇：**Oops Reversal、Tight Setup Day、Low RMV / RMV Tight Signal、Inside Day、Base Pivot、Range Breakout、MA cluster**；四类 base 的文字描述（IPO / Continuation / Bottoming / Base Breakout ≥5 周） | 
| Oliver Kell **Victory in Stock Trading** | `~/Downloads/Trading/03_Trading_Strategies/Books_References/Victory in Stock Trading_Oliver Kell.pdf` | 周期词汇：Wedge Pop / Wedge Drop / EMA Crossback / Base n' Break / Reversal & Exhaustion Extension。**形态语言，无数值规则** |
| Mike Bellafiore **One Good Trade**（SMB） | `…/Books_References/Bellafiore…pdf` | 交易过程与训练，**无指标公式**（“oops” 命中全是感叹词） |
| Dan Zanger 方法 · Brian Shannon 多周期 · Coyle《Principles of Great Traders》(`TradeBookFinal.pdf`) | `Books_References/` | 参考读物 |
| 2022 TraderLion Conference · DTT Synopsis · Trading Process | Google Drive `Old Education Folder/` | 会议/过程材料，无口径 |

## 没有（查过）

- **Stan Weinstein《Secrets for Profiting in Bull and Bear Markets》原书**——本机无；阶段口径只有 TraderLion 转述。
- **TraderLion 对 "three weeks tight" 的文字定义**——三本 TraderLion 材料一处都没有；IBD 那张表有数字。
- **"oops reversal" 的定义**——只在 Trade-Lab 图集作标签出现 23 次，无一句定义；Larry Williams 原创，TraderLion 借用。
- **"mini coil"**——本机所有书与转录零命中（只在我们自己的研究 README 里）。是口头/视频词汇。
- **IBD RS Rating 的季度权重**——无一手；网上是社区互抄。
- **Deepvue RMV 公式**——无（图集里只当标签）。

## 用法

1. `METRIC_SOURCES.md` 的「标准口径」列，凡本表有的，先引本表路径。
2. 想给一个词写代码之前，先在本表「没有」一节找一眼——**在那里的词，没有定义就不能进代码**，先补定义再动手。
