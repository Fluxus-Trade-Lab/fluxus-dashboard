# 暂停记录 + 架构事实底稿

*2026-08-09。设计暂停在这里,等 Andy 重新整理 dashboard 的思路和架构后回来。*
*这份文件**只写事实和张力,不写提案**。新架构是你的活,这是给你垫在下面的底稿。*

---

## 一、我们停在哪

### 已经落进产品的(不用重做)

| 页 | 组件 | 提交 |
|---|---|---|
| 市况 | `breadth/StateBoard.jsx` + `VerdictBanner.jsx` | `28658bf` `67cfcaf` |
| 筛选器 | `screener/HeatingUp.jsx` | `bcd0be1` `9454e77` |
| 个股 | `ticker/TickerSignalHistory.jsx` | `6ee30e5` |
| 持仓 | `portfolio/ui/CapitalAtRiskWidget.jsx` | `57546af` `f742e43` `0d8522c` |

### 停在半截的一件

**首页整页版面** —— 稿子在 `explorations/2026-08-08/home.html`(提交 `6351171`),
真数据出图在 `visuals/out/20260809_home_layout.png`。**没进 React**。

它提的是「三个观看距离」:3 米一个决策(可裁剪单发)· 1 米证据 · 20 厘米参考(折叠)。
配套换掉了交通灯 —— 五格对五项 power-trend 检查,QQQ 恰好挂一项,那是灯显示不了的。

**回来时的第一个岔路口就在这里**:这版整页是继续走,还是等你的新架构定完再重画。
我的判断是**等** —— 它假设了首页只有一个决策,而那正是你要重新想的事。

### 别的 session 在跑的

- `task_90a7a031` —— ExposureTab 条件 hook(清空持仓会崩)
- `task_2f21c83d` —— breadth 往非交易日写行(周六那行还在,周五 08-07 还是丢的)

### 只等你按键的

- 零结果那条推:图 `visuals/out/20260809_null_result.png` + 文案
  `Fluxus_Brand/record/2026-08-09_null_result_post.md`
- 角色画:简报和提示词包就绪,要交给绘图模型

### 还没清干净的

`claude/sharp-boyd-7ee3fc` 和 `fix/ohlc-staleness-guard` 两个本地分支还钉着含实盘持仓的旧提交。
`feat/visual-v2` 已经干净。那两个 worktree 里有没提交的活,所以没动。

---

## 二、设计文件:有什么,缺什么

### 有(全在 `Fluxus_Brand/visual/`,加仓库根的 `DESIGN.md`)

| 文件 | 管什么 | 层级 |
|---|---|---|
| `DESIGN.md` | 字体 · 编码 · 四语域 · 怪度 1–5 · 各界面规格 · 八条拒绝 | **视觉系统** |
| `Fluxus_Operator_Model.md` | 事实→解读→预期→行动;修复阶梯;传导链 | **内容模型** |
| `Fluxus_Refusals.md` | 八条拒绝 + 怪度定义 + 表现色使用表 | 视觉系统 |
| `Fluxus_Voice_To_Template.md` | 声音→模板;演员表→记号 | 品牌 |
| `Fluxus_Work_Forms.md` | 艺术史上的作品形态 | 品牌 |
| `Fluxus_Poster_System.md` | 海报框 + 日历触发器 | 外放件 |
| `Fluxus_Visual_Library.md` | 68 条图像语料 + 情绪索引 | 外放件 |
| `Fluxus_Image_Method.md` · `Fluxus_Character*.md` | 图像方法论 · 角色 | 品牌 |

### 缺 —— 你这次要的那份,一份都没有

现有的全是**「长什么样」和「说什么话」**。没有一份写**「是什么东西」**:

- ❌ **源数据台账** —— 每个字段从哪来、谁算的、多久更新、坏了怎么知道
- ❌ **信息架构** —— 九个页面各回答什么问题、谁看、进来第一眼干什么
- ❌ **受众定义** —— 自己用 vs 会员用 vs 公开,同一页面对不同人显示什么
- ❌ **wayfinding** —— 页面之间怎么跳、从哪进、断在哪
- ❌ **数据契约** —— 前端假设了什么、管线保证了什么、中间那层谁负责

**这就是「自己用的工具」变成「产品」时冒出来的那一层。** 之前不需要,因为你就是唯一的用户,
架构在你脑子里。

---

## 三、事实底稿:现在到底是什么样

### 3.1 源数据 → 文件

| 产出文件 | 谁算的 | 前端真的在读吗 |
|---|---|---|
| `signals.json` | `breadth_signals.py` | ✅ 主加载器 |
| `breadth.json` | `breadth_store.py` | ✅ 主加载器 |
| `market_health.json` | `breadth_signals.py` | ✅(可选,失败容忍) |
| `etf_data.json` | `run_all.py` | ✅ 主加载器 |
| `momentum_97 / gainers_4pct / vol_up_gainers / ema21_watch / healthy_charts / episodic_pivot / vcp / stockbee_ratio` | 各自 screener | ✅ 主加载器(8 个) |
| `heating_up.json` · `ticker_events.json` · `performance.json` · `briefs.json` · `breadth_replay.json` | `run_all.py` | ✅ 各自单独取 |
| `tickers/*.json` · `trades/*.json` · `tickers/_benchmarks.json` | 各自任务 | ✅ 按需取 |
| `universe.json` · `groups.json` | `atr_enrichment.py` / `ema21_watch.py` | ✅ 各自 hook |
| `h1_2026_stats.json` | `portfolio/h1_report.py` | ❌ 前端不读 —— 供**投资人 pitch + 内部复盘**两份报告共用(设计如此) |
| `sentiment.json` | `macro/sentiment.py` | ❌ 前端不读。**每天在更新**(08-09),但没人消费 |
| `portfolio_backtest.json` | `portfolio/backtest_optimizer.py` | ❌ 前端不读。最后一次 **05-24**,是一次性跑的产物 |

### 3.2 加载方式 —— 这里有个架构事实

`frontend/src/hooks/useMarketData.js` 用**一个 `Promise.all` 阻塞加载 11 个文件**,
然后 `Layout` 把整包 `data` 往下传。后果两条,都在现在的代码里:

1. **任何一页都要等齐 11 个文件**,哪怕它只用其中一个
2. **任何一个文件 404,整包挂掉** —— `Promise.all` 里是 `throw`,只有 `market_health`
   被单独包了 try/catch 容忍缺失

这不是 bug,是「一个人用、一次全取」时代的合理设计。变成产品后它是第一批要改的东西之一。

### 3.3 九个页面

| 导航名 | 路由 | 它回答的问题 | 名字描述的是 |
|---|---|---|---|
| Dashboard | `#/dashboard` | (混合,12 个物件等权) | 位置 |
| Screener | `#/screener` | 现在哪些票在共振 | 工具 |
| Portfolio | `#/portfolio` | 我现在能亏多少 | 对象 |
| Trade Journal | `#/trades` | 我做过什么 | 对象 |
| AI Coach | `#/journal` | 我哪里漏钱 | 角色 |
| Briefing | `#/briefing` | 今天读什么 | 对象 |
| Breadth | `#/breadth` | 今天能不能上、上多大 | **数据名** |
| Groups | `#/groups` | 哪个板块在动 | **数据名** |
| Model Books | `#/modelbooks` | 历史上长这样的赢家 | 对象 |

另有四个不在主导航的公开页:`method` · `results` · `pricing` · `brief`。

**注意路由和标签对不上两处**:`#/journal` 显示 "AI Coach",`#/trades` 显示 "Trade Journal"。
从外面看是两个 journal。

---

## 四、和 TSF 的结构差(你指的那件事)

| | TSF | 我们 |
|---|---|---|
| 页数 | 6 | 9 + 4 公开页 |
| 命名 | Market Overview · Thematic Focus · Focus Stocks · Live RS Theme Tracker · Theme Leaderboard · Stock Screener | 一半按数据命名(Breadth · Groups) |
| 教学层 | **在导航里**(FAQ & Video Tutorials 是一级项) | 无 |
| 账户层 | 在导航里(Account / Sign out) | 无 |
| 每页物件数 | 1–3 | 首页 12 |
| 求助入口 | 常驻「Need help?」浮标 | 无 |

**他们的六页每一页只回答一个问题,而且名字就是那个问题的答案。**
`Theme Leaderboard` 你不用点进去就知道会看到什么。`Breadth` 不会 —— 它是一个指标族的名字。

但也要记着上次那条判断:**他们的力量来自稀疏,不来自解决了什么。**
`Gold Miners +14.86%` 上榜正因为它涨了,没有分母、没有证伪。
**要拿他们的层级和命名,不要拿他们的认识论。**

---

## 五、我看到的张力(供你重排时参考,不是提案)

1. **首页没有主语。** 12 个物件等权,所以没有第一个。其他页各自成立,首页是拼盘。
2. **一半页面按数据命名,一半按对象命名。** 混着排,导航就没法一眼扫。
3. **受众没分层。** 同一套页面既是你 6:30 的仪器,又要当会员产品。
   「个人声音」和「产品可信度」现在挤在同一屏上。
4. **没有 wayfinding。** 页面之间不互相引用 —— 筛选器出了名字,不指向个股页;
   个股页出了信号,不指回市况页当天的判决。每页都是终点站。
5. **数据新鲜度是每页各说各话。** 市况说 08-08,热度说 08-06,行情缓存有的停在 05-22。
   现在是各页各自披露,没有一个统一的「这份数据截止到什么时候」。
6. **`sentiment.json` 每天在算,没人看。** `macro/sentiment.py` 昨天还在写(08-09),
   前端一行都没读。要么接进来,要么停掉 —— 每天跑一个没有读者的东西是最贵的那种沉默。
   (另外两个不算问题:`h1_2026_stats` 本来就是给报告用的,`portfolio_backtest` 是
   05-24 一次性跑的。)

---

## 六、回来时从哪儿接

按依赖排:

1. **受众和页面清单**(你的活)—— 定了这个,下面全部有参照
2. **数据契约** —— 谁保证什么、坏了怎么显示。第 5 条张力全挂在这里
3. **wayfinding** —— 页面之间的路
4. 然后才回到视觉:`home.html` 那版三距离要么落地,要么按新架构重画

**别先动视觉。** 那版首页稿假设了「首页只有一个决策」,而那正是第 1 步要定的事。
