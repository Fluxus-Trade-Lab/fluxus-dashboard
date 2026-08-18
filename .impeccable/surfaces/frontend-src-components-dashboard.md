---
version: 1
slug: "frontend-src-components-dashboard"
primary_target: "frontend/src/components/dashboard"
related_targets: ["frontend/src/components/groups","frontend/src/components/screener","frontend/src/components/watchlist"]
---

# 晨读三页 · 表面简报

**范围**:Dashboard / Themes / Screener+Watchlist 三页,作为一件东西设计。
**模式**:Operate。**世界已定**(墨底 #12110F、海报蓝红、Plex),这里只定结构与分工。

## 方向(Andy 2026-08-18 亲自定,压过骰子)

**就是三页,不合并、不做步进器、不做劈屏。** 三页各自回答一个层级的同一个问题:
**「什么在变?什么在强?」** —— 层级不同,问题相同。

| 页 | 层级 | 凸显什么 |
|---|---|---|
| **1 Dashboard** | 市场 | 市场读数 · 结论 · **market cycle** · 板块与主题的**一日 / 一周变化** |
| **2 Themes** | 主题 | **变化与相对强度**:什么是恒强的,什么是突然从后面加速。**四态(Leading / Weakening / Lagging / Improving)的存在意义就是这个** —— 强调主题的变化,**不是个股** |
| **3 Screener / Watchlist** | 个股 | 个股的**变化与 RS**。有的是单一个股在变,**有的是所在主题板块一起在变 —— 这是加分项**。此处需要 **TradingView 图**,看个股的月 / 周 / 日级别 |

## 三条由此推出的硬约束

1. **同一个问题,三个层级** —— 三页的骨架应当同形:先说变化,再说强度,最后给名字。
   不同的只是「谁在变」的粒度。
2. **第 2 页不许出现个股主角。** 主题层的产出是主题,个股只作为成分证据出现。
3. **第 3 页必须能回答「这只票是自己在动,还是它整片在动」** —— 板块共振是加分项,
   所以它必须是第 3 页上可见的一列/一个记号,不是要跳回第 2 页才能知道的事。

## 新引入的能力(此前不在产品里)

**TradingView 图表进第 3 页**,月 / 周 / 日三个级别。这是新增依赖,需要单独决定:
嵌入 widget(免费、有品牌、离线不可用)还是用本地 OHLC 自绘(可控、无外链、要自己做多周期)。
**未定,待 Andy 拍。**

## 状态

- 三页分工:**已定**(上表)。
- 各页内部版式:**未定** —— 下一轮在此简报的约束下做。
- 短名单托盘、三页之间是否传状态:**未定**。
