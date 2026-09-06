# Setup 分类法 —— Andy 亲定（2026-09-06 口述，原话照录）

*worksheet.csv 第一列的官方词汇表。前提永远是：First find leader in strong theme。*
*三个 setup 的止损全部是 low of day。*

## Andy 原话（一字未动）

> My favorite entry models:
>
> First find leader in strong theme
>
> **1. Breakouts**
>
> Leader sets up in tight base
> VCP pattern forming
> Declining volume
>
> Enter on break of key level (EMA reclaim, high of base break)
>
> **2. Undercut and rally**
>
> Leader sets up in a tight base
> Breaks under a key support level (Previous days low, low of base, daily EMA)
> Instead of breaking down, leader reclaims key level of support
>
> Enter on the reclaim of key level
>
> **3. 30m pivot**
>
> Leader pulls into a big weekly/daily level (8EMA, 50EMA, retest level)
> Wait for first green 30m candle to from off level
> Once first 30m green candle high is broken, entry is triggered
>
> Stop loss for all setups is low of day
>
> In strong momentum environments I like #1,3
>
> In weaker environment I like #2

## 标注用法

- **标准名三个**（worksheet `setup` 列直接填）：`Breakout` · `Undercut & Rally` · `30m Pivot`
- 对不上三类的交易照实另起名（如 `Counter-trend`、`Earnings gap`……），**不要硬塞**——对不上的名字本身就是复盘信息
- 环境对照可作交叉检验：强动能期的交易该多为 1/3，弱环境该多为 2；标完按月分组一看便知他有没有在弱环境里硬做 Breakout
- ⚠️ `machine_guess` 列的现有词汇（"Breakout / near 52W high"、"Long below MA200 — counter-trend"…）是 08-26 生成时自造的，与本分类法**不对齐**；三类的判定特征（tight base / undercut-reclaim / 回踩大级别位）大多可从已算好的 24 个字段近似重算——待谁接这个活时对齐

## machine_guess_v2（2026-09-06，Andy 批「急的要做」后跑）

用 worksheet 现有 24 个入场日快照字段按三类近似预填（无日内数据、不外抓）。**快照分得出突破族 vs 回踩族；U&R 与 30m Pivot 的区分需要日内走势，标 `Pullback — 手标定` 留给 Andy**。

363 笔分布：
| 桶 | 笔数 | 说明 |
|---|---|---|
| Breakout | 77 (+33 临界) | 入场贴 20 日高 ≥−2%（临界档 −2~−4%） |
| Pullback — U&R 或 30m Pivot | 65 | 回撤 >4% 且贴 20/50 均线 ±3% 内 |
| Short | 33 | 三类之外（三类全是 long 模型） |
| Counter-trend (below MA200) | 12 | 违反 leader 前提 |
| **Other — 对不上三类** | **143 (39%)** | **画像：距 20 日高中位 −11.2%、ma20 上方 +6.1%、不贴任何关键位、中位持仓 2 天——悬空入场的短打。这批不属于三个 favorite models 中的任何一个，是手标时最值得看的一堆** |

判定代码内嵌于生成脚本（本文件 git log 对应 commit），阈值：贴 20 日高 −2%、贴均线 ±3%、回撤线 −4%——均为自造近似值，非标准口径，只作预填不作结论。
