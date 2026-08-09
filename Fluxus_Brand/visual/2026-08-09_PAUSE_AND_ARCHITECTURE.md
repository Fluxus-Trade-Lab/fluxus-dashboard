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

## 五之二、Andy 的切法:向外 / 向内(2026-08-09 补)

> 「一部分是别人可以用的 swing momentum 工具(briefing, RS, screener, thematics/groups,
> breadth),另一部分是向内求的、分析记录自己的(portfolio, ai coach, journal, model books)」

**这个切法解掉了第 3 条张力(受众没分层),而且它比按数据/按对象命名更根本 ——
它切的是「这一页在说谁」。** 底下是拿代码压出来的结果。

### 两处归类要改

| 页 | 你放的 | 代码里是什么 | 应该在哪 |
|---|---|---|---|
| **Model Books** | 向内 | `PATTERN_COLORS`:cup with handle · flat base · VCP · high tight flag · pocket pivot · episodic pivot · base on base —— **历史赢家的形态教材** | **向外**(而且它是教学层,TSF 那个 FAQ & Video 的位置) |
| **Groups** | 向外 ✅ | `rs_level` + `rs_accel` 按板块 —— 就是 TSF `Theme Leaderboard` 的同构物 | 向外,确认 |

Model Books 讲的是**市场长什么样**,不是**你做过什么**。它错放会让「向内」那半看起来比实际大。

### 你没列的那一页,恰好是接缝

**个股页(`#/ticker/<T>`)不在你两个清单里,因为它同时是两边。**
`TickerSignalHistory` 一张图上画两种记号:方块 = 筛选器出现(向外,市场的事实),
三角 = **你自己的成交**(向内)。它是唯一一个两半真的碰在一起的地方。

### 真正的裂缝:决策是两半合出来的

向外那半现在**用第二人称单数说话,而且只对一个人说**:

> TODAY YOU MAY TRADE AT **FULL SIZE**

「Full size」是谁的 full size?这句话只有对着一个风险框架才有意义 ——
0.25% 固定 R、0.47% 带顶、3% 账面上限。**那三个数在向内那半**
(`CapitalAtRiskWidget` 的 `LIMITS`),而且是**你的**,不是用户的。

所以两半不是并列的两个模块,是这个关系:

```
向外  = 市场的状态        对所有人相同    (breadth 8/12 · RS · 共振 · 形态)
向内  = 你的框架 + 你的记录  因人而异      (R 是多少 · 上限多少 · 你漏在哪)
接缝  = 尺寸/决策          需要两边       ("能不能上" 是市场的, "上多大" 是你的)
```

**推论(不是提案,是这个切法自带的后果):**

1. 卖向外那半给别人,**它只能给读数,不能给决策** —— 除非每个用户有自己的向内那半
2. 「FULL SIZE」这类话现在是**你的私人指令**混在了公共读数里。市况页要么改口
   (说市场状态,不说仓位),要么承认它是个人页
3. 向内那半有**硬隐私边界**,向外没有。实盘持仓进 git 那次已经付过一次学费了
4. 九个平铺的导航项其实是**两个模式**,不是九个同级页

### 顺带解掉的旧张力

- 第 2 条(命名混乱)—— 分两半之后,向外按「它回答什么问题」命名,向内按「它记录什么」命名,
  两套语域各自自洽,不用统一
- 第 4 条(没有 wayfinding)—— 路有了方向:向外发现名字 → 个股页(接缝)→ 向内建仓和复盘
- 第 6 条(`sentiment.json` 没人读)—— 它是向外的宏观读数,归属清楚了才好决定接不接

### Briefing:查过了,向外 —— 但它已经死了五个月

`briefs.json` 字段只有 `date / title / summary / watchlist`,**没有仓位**,所以干净地属于向外。

但里面**只有 5 条,全部是 2026-03-17 到 03-21**。今天是 08-09。
**一个一级导航项,在拿三月的数据当今天的简报。**

这条特别要紧,因为 Briefing 在你要卖的那一半里,而且是最像「产品」的那一页
(每天一条、有标题有观察名单)。回来时要么接上真的日更,要么从导航里拿掉 ——
留着一个五个月没动的页,比没有这一页更伤。

### 已决(2026-08-09,Andy 定)

**1. Briefing 从导航拿掉 —— 已做。** `Header.jsx` 的 `NAV_ITEMS` 去掉了这一项,
路由保留(旧链接不断)。TSF 那个位置放的是 Founders Notes ——
**注意那是「人写的东西」,不是一个数据页。我们的对应物是信(`HOW MUCH`),它已经存在,
只是在 app 外面。** 回来时的选择是:把信接进来当这一格,还是这一格干脆不要。

**2. AI Coach 一页两半,要拆。**

| 部分 | 向哪 | 例子 |
|---|---|---|
| 教学 | **向外** | Van Tharp 尺寸课 · SQN · 蒙特卡洛 —— 通用知识,谁都能用 |
| 诊断 | **向内** | 「H1 最大的漏是重攻已破论点(BABA 5 次 −$54k)」· 尺寸是目标的 2× |

教学那半是**产品**(而且是 TSF 拿 FAQ & Video Tutorials 占的那个位置),
诊断那半是**只有喂了你自己的成交记录才存在的东西**。

**3. 「FULL SIZE」—— 我上一条说重了,但要再切一刀。**

你说得对:它说的是市场风险和牛熊方向,TSF 也有,只是他们表达成「80% bull」。
我上一条把它整个当成个人指令,过了。

但拆开看引擎实际吐的是**两样东西**(`breadth_signals.py`):

| 字段 | 是什么 | 归属 |
|---|---|---|
| `env` `score` `risk` | BULLISH · +8/12 · Low —— **市场读数** | **向外**。这就是 TSF 的「80% bull」,我们的是 8/12 = 67% |
| `exposure` `playbook` `guidance` | 「Full / normal size」「press winners, normal pyramids」 | **动作** |

关键事实:**`exposure` 是 `(env, risk)` 的纯查表**,`playbook` 是 `env` 的纯查表 ——
`EXPOSURE[(env, risk)]`、`PLAYBOOK[env]`。也就是说读数是**原语**,动作串是**派生层**,
两者本来就是分开的,拆开零成本。

所以不是「FULL SIZE 是私人的」,而是:

- **读数(+8/12、Low)对所有人相同** → 向外,做头条
- **动作串(Full size、press winners)是把读数翻译成仓位** → 这层翻译对每个人不同,
  因为它落地时要撞上那个人的 R 和上限

TSF 停在读数(「80% bull」)不给动作,所以他们不需要向内那半。
**我们给了动作,所以我们必须有向内那半 —— 这正是你两半划分的经济学根据。**

**4. Model Books = 交易训练健身房 / 游戏。**(Andy 2026-08-09)

素材比预想的大，而且**回放引擎已经有了**：

| 已有的 | 数量 / 位置 |
|---|---|
| 模型册条目 | **1,514 条**，`frontend/public/data/modelbooks/index.json` |
| 每条的日线 | **1,534 个** OHLCV 文件 |
| 字段 | `ticker` `year` `source` `patterns` `key_lessons` `outcome` `gain_pct` `duration_days` |
| 年份跨度 | **1962 – 2026** |
| 「只给当时知道的」引擎 | `breadth/sliceReplay.js` + `useTimeMachine.js` —— **Time Machine 已经在跑了** |

游戏循环几乎是现成的：切一段基底 → 藏掉结果 → 让人下判断 → 揭晓 + `key_lessons`。

#### ⚠️ 但有一件会毁掉它的事

**1,504 条有 `gain_pct` 的条目里，负的有 0 条。最小的一条是 +23.8%，中位 +225%。**
1,464 条来源是 "Big Movers" —— 它们进这个册子**正因为它们涨了**。

> **这副牌里没有「不买」这个选项。**
> 拿它做决策训练，练出来的是对每一个形态都点「买」，因为牌堆里每一张后来都涨了。

这就是筛选器刚修掉的幸存者陷阱，但在训练场里更致命 —— 筛选器只是**显示**了有偏样本，
训练场是拿有偏样本**塑造你的反射**。

两条路(你选):

1. **补失败牌** —— 可行，素材也在：`ticker_events.json` 有历史上筛选器响过的名字，
   本地 OHLC 有后续走势，序列研究(0/42)那套已经算过前瞻收益。
   跑同一套形态识别，留下**没走出来**的那些，就是失败牌堆。
2. **降级成「识别」训练，不叫「决策」训练** —— 并且把这件事写在页面上。
   识别形态本身有价值，但它不是同一件事。

#### 另外两件

- **答案泄漏在四个字段**：`outcome`("20x in 4 years")、`gain_pct`、`duration_days`、
  `key_lessons`。游戏态要全藏。
- **`gain_pct` 有拆股污染**：SAF 2016 = **+465,308%** / 198 天，DDAY 2011 = **+53,800% / 4 天**。
  这是反向拆股没复权，和当初 SOXS 把权益曲线打出 6000% 尖峰**同一类错误**
  (见 `project_split_equity_fix`)。排行榜和任何「平均涨幅」在修掉之前都不能用。

**5. 「上传自己的图表截图 → 和 Model Books 对照」**(Andy 2026-08-09)

> 「后者是历史,前者是我们如何像它靠近,做到优秀的交易,训练自己。」

这是**接缝**的第二个实例(第一个是个股页)。但查完数据有三件要先说:

#### ① 这个闭环的一半已经建好了,而且不需要截图

`data/output/trades/_index.json` —— **220 笔,198 笔已平仓**,每笔带:

| 字段 | 是什么 |
|---|---|
| `realized_R` | 你实际拿到的 |
| **`optimal_R`** | 那笔**当时最多能拿到的** |
| **`capture_pct`** | **你抓住了理想的百分之几** ← 就是「离优秀有多远」 |
| `setup_type` · `lesson` · `hold_days` | 分类 · 教训 · 持有天数 |

**「如何像它靠近」这个数已经在算了。** 截图不是前提。

#### ② 真正缺的是**接口**,而且是命名问题不是技术问题

两套词汇**完全不重叠**:

| 你的 `setup_type`(220 笔) | Model Books 的 `patterns` |
|---|---|
| Long in mixed structure (110) | cup_with_handle (30) |
| Long below MA200 — counter-trend (29) | ipo_base (12) · vcp (12) |
| Extended long — RSI overbought (16) | flat_base (11) · range_breakout (8) |
| Breakout / near 52W high (12) | base_on_base · episodic_pivot · high_tight_flag |

**你的分类讲「价格在均线的什么位置」(市场脉络),模型册讲「基底长什么形状」(形态)。
两个正交的坐标轴,今天没有任何字段能把它们连起来。** 这是这个想法真正的第一步。

#### ③ 模型册的教材部分只有 50 张,不是 1,514 张

**1,514 条里,有 `patterns` 标注的 50 条,有 `key_lessons` 的也是 50 条。**
剩下 1,464 条("Big Movers")只有 ticker + 年份 + 涨幅 + 日线,**没有任何标注**。

所以现状是:**50 张有注解的教材卡 + 1,464 张没注解的走势图**。
当牌堆用没问题,当教材用只有 50 张。

#### ④ 截图真正加的是什么

不是结果(已经算得出),是**当时你在看什么** —— 你画的线、你在哪个周期、你标了什么。
**数据层有「你做到了多少」,截图层有「你当时怎么想」。** 这两件不能互相替代,
但顺序上,能算的先算。

#### ⑤ 一个要先确认定义的数

198 笔已平仓的 `capture_pct`:**24 笔低于 −100%**(极可能是 `optimal_R` 分母太小的假象)。
剔掉离群后 174 笔的**中位数是 −1.5%**。

这个数如果定义没问题,它就是整个向内那半最重要的一行 —— 但**先确认 `capture_pct` 的算法**
再拿它说事。别重蹈 PLTR 那次:数对了,输入错了。

### 还没答的

- 信(`HOW MUCH`)要不要接进 app 当 Founders Notes 那一格

---

## 五之三、排期决定(2026-08-09,Andy 定)

**先外后内。外面不做完,内部一行不动。**

MY BOOK 三页(Portfolio · Trade Journal · AI Coach)保持原样 —— 那是他自己用的,
不急着改。所以持仓页那些改动是**已经落地的例外**,不是开始动内部。

已落地的外部框架:侧栏两模式 + 改名(`fd286c8`)· 每页页头一个层级(`4d302c6`)·
Dashboard 分层(`7f91eec`)。

**Dashboard 上那两个内部物件**(Market Posture · Pre-Market Checklist)**没有删**,
只是压到最底下、挂一条「belongs to My Book」的带子。他 6:30 真的在用 checklist ——
为了图干净拿掉一个能用的东西,是拿功能换示意图。等内部那半重建时它们才搬家。

**搁置:** wayfinding(页面互相引用)。

---

## 五之四、以后要做:交互式探索图表(2026-08-09 记)

Andy:「交互式探索的图表我们以后也要做。」

现在所有图都是**只读的**。交互式探索是另一类东西 —— 读者自己改变量、自己筛、自己对比。

记一条现在就该守的约束,免得以后返工:**交互不许改变编码。**
筛选、缩放、对比可以;**让用户换配色、换比例尺、关掉证伪行 —— 不行。**
可交互的是**看哪一段数据**,不是**这些记号意味着什么**。
(同一条线在 §玻璃那节已经写过:动效必须回答一个问题。)

---

## 六、回来时从哪儿接

按依赖排:

1. **受众和页面清单**(你的活)—— 定了这个,下面全部有参照
2. **数据契约** —— 谁保证什么、坏了怎么显示。第 5 条张力全挂在这里
3. **wayfinding** —— 页面之间的路
4. 然后才回到视觉:`home.html` 那版三距离要么落地,要么按新架构重画

**别先动视觉。** 那版首页稿假设了「首页只有一个决策」,而那正是第 1 步要定的事。
