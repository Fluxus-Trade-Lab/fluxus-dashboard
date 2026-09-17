# 宇宙翻倍之后，牌面上那个词没跟着改

**2026-09-18 夜班（Nighty Zac）** · 复现：`python3 data/research/breadth_universe_break_2026-09-18/measure.py`
（在基于 `origin/main` 的树里跑；两张表全部由脚本打印，本文不手抄数字）
**独立复核**：两个只读 agent 各自从头核过一遍，结论与数字一致，并纠了本文两处措辞、加了三处我没查到的东西（见第七节）。
**闸**：`pipeline/tests/test_frontend_count_thresholds.py`（本班新增，已合）

## 一句话

2026-08-10 起 Finviz 宇宙从约 2,600 只翻到约 5,620 只，**后端当天就把 thrust 的门槛改成了按宇宙缩放，前端那张牌面上的 300 没人动**——
27 个交易日里 **20 天**牌面上的词和引擎自己的读数对不上，"churn / volatile" 在牌面上出现在 **55.6%** 的日子，
而它在此前 559 场里只出现过 **0.5%**（3 天）。
牌面在一个默认关着的折叠块里（`Reference label="Summary tiles"`，关着时根本不 mount），
所以准确说法是**每有人点开一次就误导一次**，不是每天都在误导——也正因为没有日常目击者，它错了 27 场没人报。

## 二、事情的形状

| | 家数门槛 | 出处 |
|---|---|---|
| 后端 | `max(60, 0.113 × universe_size)` = 今天 **634** | `pipeline/screeners/breadth_signals.py:83` `thrust_count()`，`16db6a88b`（2026-08-09）|
| 前端 | 硬编码 **300** | `frontend/src/components/breadth/MarketStateSummary.jsx:15-17` |

`16db6a88b` 的 commit message 自己写了这件事该怎么防：

> state_board imports the same function rather than keeping its own copy of the constant,
> **which is how the two would have drifted**

后端那一侧照做了（`state_board.py` 去 import 那个函数）。**前端这一份拷贝没人知道它存在**，于是它就是被预言的那次漂移。

`0.113` 不是随手取的：它＝ 300 ÷ 老宇宙（2,647）——就是"把历史操作点原样搬过去"。所以**300 和 0.113 是同一条线在两个宇宙下的两个写法**，
问题不是谁对，是宇宙翻倍之后只有一边跟着走。
断点**之前**两边也不是完全一致（22/559 = 3.9% 的日子不同），所以更准的说法是：
**08-10 把一个近似正确的常数变成了系统性错误**，不是"它一直是错的"。

## 三、量出来的

断点后 27 场（`measure.py` 第一节）：

- 牌面 vs 引擎**不一致 20/27 场**；断点前是 22/559 场（3.9%）。
- `churn / volatile` 出现率：牌面 **0.5% → 55.6%**；引擎 0.4% → **0.0%**。
- 最近一场 2026-09-16：up_4pct 292 / down_4pct 580。牌面写 **bearish thrust**（580 ≥ 300）；
  同一份 `breadth.json` 里引擎自己写的是 `{"key":"thrust","side":"neutral","line":634.043,"margin":-342.043}`。
  **同一个页面上，同一份 JSON，两个相反的话。** 那块砖的颜色（`tone`，`MarketStateSummary.jsx:36`）也由这个词决定，所以红绿也跟着错。

## 四、修法（`frontend/` 是 UI Claire 的文件，本线一个字节没改）

payload 里**已经带着正确的线**：`verdict.vote_detail` 里 `key == 'thrust'` 那条的 `line` 字段（今天 634.043）。
所以修法是把 `MarketStateSummary.jsx` 的三个 `>= 300` 换成 `>= line`，取不到时再回落到 300。
⚠️ 别指望从 `mm` 里算：`mm` 块只有十二个计数字段，**没有 `universe_size`**（实测 `mm.universe_size` 是 None）。
线在 `verdict` 那边（`verdict.vote_detail` 的 thrust 条、`verdict.universe_size`），**后端 payload 不用改**。
`VoteGlyphs.jsx:36` 的 `RANGE.thrust = 300` **不是**这个问题——那是画图的量程（半幅），不是判定线。
但它已经失准：今天 margin = −342，`VoteGlyphs.jsx:96` 的 `Math.max(-1, …)` 把它夹死，那根柱子**顶格**，
08-10 之后常态超出 ±300，这枚 glyph 已经没有分辨率了。是美观缺陷不是读数错误，修法同样是读 payload 里那条 `line`。

## 五、顺带量到的第二处：历史分位在跨宇宙比

`breadth_signals.percentile_context()` 把当日读数排进**整个归档**的分位，其中四个是**原始家数**
（`up_4pct` / `down_4pct` / `nh_nl_net` / `qtr_spread`），另三个是比率（`ratio_5d` / `t2108` / `mcclellan_osc`，不受影响）。
归档 586 场里只有 4.6%（27 场）来自新宇宙，其余全是老宇宙——于是新宇宙的家数天然排在历史高位。

把同样的算法换成"家数 ÷ 当日 universe_size"再算一遍（`measure.py` 第二节）：

| | 家数口径比比率口径高（中位） | 最大 |
|---|---|---|
| `up_4pct` | **+39 分位点** | +50 |
| `down_4pct` | **+35 分位点** | +50 |
| `nh_nl_net` | +5 | 24 |
| `qtr_spread` | −3 | 15 |

前端 `MarketStateSummary.jsx:35` 那行 `down-4% {n}th pctile` 印的就是这个数。

⚠️ **比率化不等于干净**：多出来的三千个名字不见得和原来那批是同一种票，所以比率也只是另一个不可比的量。
这一条的老实说法是**不该跨 08-10 排分位**，不是"改成比率就对了"。
另外归档里还有**第二个断点**：2026-03 `source` 从 `backfill` 变 `live`，月中位 2,858 → 2,490。

## 六、这轮没有说什么

- **没有说 0.113 是对的门槛。** 它只是把 300 在老宇宙里的操作点搬了过来，本身没有外部口径背书
  （`METRIC_SOURCES.md` 里 `up_4pct` 登记的是"只有涨幅一条件"的自造口径，标准 Stockbee 4% 口径是另外两列 `up_4pct_stockbee` / `down_4pct_stockbee`，2026-09-04 才开始有值，8 行）。
  本文量的是**两边不一致**，不是哪一边更接近真相。
- **没有改任何前端或管线文件。** 两处修法都在别人的边界里，已按契约行 + 门铃路由。

## 七、复核时多查出来的（我逐条自己核过，不是照抄 agent）

1. **后端自己也留了两句 300 的散文，而且是给用户看的。**
   `pipeline/screeners/breadth_signals.py:405`（`_PLAYBOOK['OVERSOLD']`）写「wait for a 300+ up-4% thrust day」，
   `:420`（`_GUIDANCE[('OVERSOLD','Elevated')]`）写「the next 300+ up-4% day is the signal that matters」。
   两句都随 `verdict.playbook` / `verdict.guidance` 上前端。T2108 跌破 20 的那天，页面会叫人等一个 300 的日子，
   而同一份 payload 里 `vote_detail` 写着需要 634。**这两行在管线里，不是前端能修的**——归 DATA ALEX。
   （今天 env=BEARISH，这两句没上台；它们在下一次 OVERSOLD 时才出现。）
2. **`0.113` 没有登记。** `METRIC_SOURCES.md` 里 grep `0.113` 零命中，thrust 门槛一行都没有。
   按宪法「先找口径，别自己造」，自造量要登记、要写明偏离了哪个标准。它现在只活在
   `breadth_signals.py:20-31` 的注释里（那段注释自己用的词是 **tuned**——照 2,650 只的老宇宙反推的工作点）。
   连带一件同样没登记的：thrust 判定用的分子是 `up_4pct`（**只有涨幅一条件**的自造列），
   不是 `METRIC_SOURCES.md:85` 登记的 Stockbee 口径 `up_4pct_stockbee`。2026-09-16 两者差一倍：292/580 vs 159/246。
3. **前端这半边没有测试。** 后端 `pipeline/tests/test_breadth_signals.py` 有四个测试钉住缩放行为
   （`thrust_count({'universe_size': 5615}) == 634`）；`frontend/` 那边 grep `thrust` 零命中。
   闸只装在写规则的一侧，拷贝规则的那一侧裸奔——本班补的 `pipeline/tests/test_frontend_count_thresholds.py` 补的就是这个位置。
