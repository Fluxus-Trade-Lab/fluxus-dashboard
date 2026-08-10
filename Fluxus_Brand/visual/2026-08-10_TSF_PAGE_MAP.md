# TSF 六页逐件对照 —— 数据盘点与前后端取舍

*2026-08-10。Andy 逐页拆完 TSF 全站后的对应清单。原则：数据一律保留在后台不删；
前端一页一主体；没有的暂时空着但记录在案。他的审美不抄，版式不照搬，抄的是
「每个数据背后的选择意图」。*

---

## 一、数据盘点（实查，不是凭记忆）

### 已有、已在用

| TSF 的物件 | 我们的对应 | 数据源 | 状态 |
|---|---|---|---|
| 四态计数 (leadership) | Themes 页 state 计数 | `groups.json` themes[*].state | ✅ 在用 |
| Theme RS 排名 | ThemeBars 横条图 | `groups.json` excess_3m | ✅ 在用 |
| 10 周 history 方块 | persistence 方块 | `persistence/persistence_of` | ✅ 在用（5 格，非 10 周） |
| 6-of-6 分数 | heat score + 记号 | `heating_up.json` score/screeners | ✅ 在用（语法同源） |
| Thematic Focus 的 ribbon | Style Rotation 的 ribbon | `rotation.json` baskets[*].ribbon（5 段双周 × state/level/accel） | ✅ 在用（在 Market State 页） |

### 已有、没用上（TSF 用了，我们躺在后台）

| TSF 的物件 | 我们已有的数据 | 在哪 | 差什么 |
|---|---|---|---|
| 2 周/6 月最好最坏（巨大卡片） | Industries 日/周榜 | `etf_data.json` perf_1w/1m/3m（138 个行业 ETF） | 前端只显示日/周，**月榜是现成字段，挑出来就行** |
| 不同周期的 theme RS | **四个分段 RS 全有** | `groups.json` rs_0_1w / rs_1w_1m / rs_1m_3m / rs_3m_6m | 前端一个都没画；rs_3m_6m 当前为 null（管线待查） |
| theme 点进去看成员技术指标 | **个股全套现成** | `groups.json` stocks（3,207 只：rs 分段/state/群内百分位/top_quartile）+ `universe.json`（5,615 只：rs_21d/63d/126d、perf 全周期、均线距离） | 纯前端工作，零管线改动 |
| Regime 仪表的原料 | 全在 | `breadth.json` verdict(score+12votes) · `signals.json` trend_status/power_trend | 缺一个合成公式（见 §三） |
| how to interpret | HowToRead 已建 | — | 内容要按 theme 页重写一份 |

### 部分有

| TSF 的物件 | 我们有的 | 缺的 |
|---|---|---|
| 10 周逐周 history | `rotation.json` ribbon：5 段双周，但只覆盖 11 个风格篮子 | 74 个 theme 的逐周序列。`groups_archive.csv` 已开始积累（今天第 1 天，cron 已修 4f22387），**约 10 周后自然够** |
| vol surge (5d/50d) | `rel_volume`（1d/50d） | 5 日窗口的版本，管线一行改动 |
| 周线图表 widget | `wk_ema10/wk_ema20` 已算 | TV widget 或自绘周线图 |

### 真没有（记录在案，不删数据、先空着）

| TSF 的物件 | 说明 | 处置 |
|---|---|---|
| Live RS 15 分钟 | 盘中对 SPY 的实时 RS | **RS Live Tracker 槽位已留**。可选路径：TV API / GAS 价格代理扩展 / IBKR。未定，先空 |
| Accumulation score | 他也没说清定义（Andy: 不清楚） | 不抄不明物。若做，用我们自己的 pocket_pivot/bo_count/rel_volume 合成并写明公式 |
| COC (change of character) | 趋势反转确认信号 | `trend_base` 最近但不是一回事。记录，不冒充 |
| Focus Stocks 整页 | Andy: 不好，不可取 | **不做** |

---

## 二、六页取舍（他的页 → 我们的页）

| TSF 页 | 我们的去处 | 动作 |
|---|---|---|
| Market Overview | **Dashboard (Today)** | 重排：读数+十二记号为主体；月榜从 etf_data 挑字段；regime 仪表按 §三设计；Founders note 留空给 Andy |
| Thematic Focus View | **Themes 页的交互升级** | ribbon 语法从 11 篮子推广到 74 theme（等归档积累）；x=时段 y=RS 0线=SPY |
| Focus Stocks | 不做 | — |
| Live RS Theme Tracker | **RS Live Tracker 槽位** | 空页已留好，写明将装什么 |
| Theme Leaderboard | **RS Leaderboard 槽位** | 短期=excess_3m+rs_accel（现成）；长期=10周RS（等归档）。单一功能这点保留，画面超过他 |
| Stock Screener | **Screener 页 + Ticker 页** | 图表 widget 属于 Ticker 页（个股页是复杂工程，已定后做）；theme 内百分位（group_pctile/top_quartile 现成）可先进 screener 列 |

## 三、Regime 仪表设计（Andy 点名要设计的那件）

**输入（全部现成，无新管线）**：
- `breadth.json` verdict.score（−12…+12，宽度九票+权重）
- `signals.json` SPY/QQQ trend_status（价格结构）
- `signals.json` SPY/QQQ power_trend（趋势的趋势）

**合成**：三个来源各投一票（宽度 / 结构 / 动力），不加权平均——
**取最弱的那个作为读数，其余两个印在旁边**。理由：篮子里最烂的苹果决定
这一篮能不能吃；平均会把一个 danger 摊薄成 caution，而那正是最贵的信息。

**输出一个词 + 一个数**：五档 `Defence · Caution · Neutral · Constructive · Full`
（不用他的 euphoria——顶部的词该是仓位语言，不是情绪语言）。数字是距离下一档
还差几票，和 Market State 的「What would change this」同一语法。

**呈现**：不做半圆仪表盘。一条水平五档带，当前档实心，读数下面一行小字印
三个来源各自的原话（+8/12 · Uptrend · Power 3）。点击跳 Market State。
预留槽位：Founders note 在它正下方（Andy 手写）。

## 三 b、Oratnek MC score 参考（Andy 2026-08-10 提供）

@oratnek_ill 的 Market Condition：43 个 ETF/指数 × 12 项指标（perf YTD/1w/1m/1y ·
平均 %>10/20/50/200SMA · 平均 20>50、50>200 占比 · 距 52 周高平均回撤 · VIX），
每项对预设阈值判正负，**MC = 正项占比**（0–100，步进 ~8.3），不加权，EMA2 平滑。

**结构性巧合：我们的 verdict 已经是 MC 式的** —— 十二票、数正负、不加权，
+8/12 结构上等于他的 75/100。差别在票的原料：他数「ETF 篮子的趋势宽度 + VIX」，
我们数「市场内部宽度（±4% 计数、NH/NL、McClellan、T2108…）」。

映射到我们的字段（若做 MC 式第二只表）：
- perf 四窗口：`etf_data` 有 1w/1m/3m，缺 YTD/1y（本地 OHLC 可补）
- %>SMA 宽度：`universe.json` 有 sma20/50/200_dist（5,615 只，比他 43 只宽得多）；缺 sma10
- 20>50、50>200：`universe.json` 无直接字段，OHLC 可算
- 距 52 周高回撤：`high_52w_dist` 现成
- VIX：`signals.json` ^VIX 现成

处置：RegimeBand v1 用「三票取最弱」上线（呈现层已定）；MC-12 作为 v2 的
候选**计算引擎**（管线独立产出，前端换数不换形）。两者可以并印对照跑一段。

## 四、执行顺序（前端为主，管线最小）

1. **月榜**：etf_data 现成字段挑 top1（保留 top3 能力）——最小改动
2. **Today 重排**：读数+十二记号(votes 三态) 为主体 + regime 带 + 月/周榜 + Founders note 槽
3. **Theme Leaderboard 槽位 → 实页**：短期榜用现成字段
4. **Themes 页加分段 RS**（rs_0_1w/1w_1m/1m_3m 已有，rs_3m_6m 查 null 原因）
5. **theme → 成员下钻**：groups.json stocks 现成，纯前端
6. 等归档积累 10 周：Thematic Focus 交互图 + 长期榜
7. Live RS：路径未定，槽位保持空

*不删任何后台数据。所有「暂时没用上」的字段保留原样。*

---

## 五、Thematic Focus 落地记录（2026-08-10）

Themes + RS Rotation 合成一页，三层一个开关一个选择：

- **分布**（值不值得挑）：79 点一轴，零线 SPY，阴影盒 = 中间一半（IQR，数据自定，无参数——草图期的 ±5% 固定带被否，那是又一个发明出来的参数）
- **排名**（挑哪个）：现有横条，行变成选择目标
- **轨迹 + heatstrip**（趋势还是反弹）：四段折线**不做样条**——四个采样点之间的曲线是插值冒充测量，TSF 那些优美波浪就是这个；heatstrip 复用全站唯一状态语法（tone=强弱，实心/描边=扩大/收窄），首段无前段可比 → 只给 tone 半透明

一个开关（1W/1M/3M）同时驱动分布+排名并在轨迹上着色对应区间；1M 需要 SPY 行，
加载前按钮禁用而不是猜零线。一个选择（≤3，感知上限）三个入口：chip 按名、
点按位置、排名行按名次；满员时所有未选目标 cursor:not-allowed——拒绝发生在
点击之前。身份色只答「哪条线是谁」，永不评级。

RS Rotation 从侧栏下线，#/rs-rotation 路由保留指向 Themes。
Industries 页签不进对比（不同 cohort，不同分母，混进一张图就是把不同断言画成一样）。

