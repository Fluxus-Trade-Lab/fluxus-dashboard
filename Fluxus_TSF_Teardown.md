# The Setup Factory 全栈拆解 — 一个业余医生怎么用 4700 粉做出付费社群

*调研于 2026-08-01/02,登录态 Chrome,付费会员视角(Substack $399 档 + Discord + Analytics 平台全部可见)。*
*方法同 `Fluxus_X_Competitor_Teardown.md`。这是快照,不是全史审计。*

---

## 〇、先说结论:三件事推翻了直觉

调研前的假设是「他 X 做得好 → 导流到 Substack → 400 人付费」。**三条数据把这个故事全推翻了:**

| 假设 | 实测 | 含义 |
|---|---|---|
| X 是增长引擎 | 4,691 粉,日更 5 帖,**单帖 600–1,200 views,个位数赞** | X 是**产品陈列柜**,不是漏斗入口 |
| 平台是自研的 | 跑在 **EasyWeb(瑞典无代码建站)**,零 XHR、零 API、3.8MB 纯静态 HTML | 他**没写后端**。K 线图都是烤进 HTML 的 SVG |
| 靠内容自然增长 | Substack **互推 50 出 / 50 入**,名单高度重合 | 真正的引擎是**推荐网络置换**,不是内容病毒性 |

**一句话:他赢的不是流量,是"从很小的流量里榨出极高转化"+ "用最省力的技术栈交付一个看起来很贵的产品"。**

这对你是好消息 —— 你差的不是能力,是**顺序**和**包装**。

---

## 一、基本盘

| 项 | 数据 | 来源 |
|---|---|---|
| **本人** | **Jonas,瑞典人,全职儿科 ICU 医生**,十余年交易经验 | Substack 免费档介绍语 |
| Substack 首发 | **2025-02-14** | archive API |
| 至今文章数 | **355 篇**(17.5 个月) | archive API |
| 发布频率 | **~20 篇/月 ≈ 4–5 篇/周**(自称 3–4x weekly) | 逐月统计 |
| 定价 | **$49/月 · $399/年 · $499/年 (founding)** | plans API |
| X | **4,691 粉 · 9,789 帖 · 2017 年注册** | 主页 |
| Discord | **2025-08-31 建**,`Paid TSF Subscriber` 角色 **54 人** | 服务器首帖 + 成员列表 |
| 宣称社群规模 | **400+ traders** | Substack hero / X bio |
| 平台 | 6 个页面,**53 个自建主题**,~2,900 只股票 | app 遍历 |

> **关于 400 vs 54:** Discord 成员列表(含离线)只有 54 人。这不等于付费用户只有 54 —— 大量付费订阅者从不进 Discord 是常态。但它确实说明:**「400+ 活跃社群」是营销话术,真实同时在线的社群核心大约几十人。** 一个几十人的活跃群完全足够撑起这门生意。这条对你最重要 —— **你不需要 400 人才能开张。**

**收入量级推算:** 若 400 人以年费 $399 为主 → **~$160k/年**;若月费 $49 为主 → 上探 $235k。这是一个兼职医生的副业规模。

---

## 二、时间线:他怎么从 0 到收费的(这是最该抄的部分)

```
2025-02-14  开张日一口气发 6 篇(1 篇 Start Here + 5 篇个股拆解)
2025-02     全月 25 篇,100% 免费  ← 用一个月把货架填满
2025-03-01  第 26 篇开始收费       ← 开张第 15 天就架付费墙
2025-06-22  founding 档上线(Momentum Leaders 模型组合)
2025-08-31  Discord 才建           ← Substack 之后 6.5 个月
2026-04 起  免费文归零,100% 付费
2026-06-22  founding 档独立成第二个 Substack 刊物
```

**逐月免费/付费比例(付费墙是怎么一格格拉上去的):**

| 月份 | 免费 | 付费 | 免费占比 |
|---|---|---|---|
| 2025-02 | 25 | 0 | **100%** |
| 2025-03 | 11 | 10 | 52% |
| 2025-05 | 6 | 14 | 30% |
| 2025-08 | 3 | 14 | 18% |
| 2025-10 | 1 | 17 | 6% |
| 2026-04 | 0 | 18 | **0%** |
| 2026-07 | 3 | 25 | 11% |

**四条可直接搬的规律:**

1. **开张日不能是空货架。** 他第一天发 6 篇,第一个月发 25 篇。新读者点进来看到的是一个「已经运转很久」的档案库,不是一个刚建的空博客。
2. **付费墙架得极早(第 15 天)。** 不是等做大了再收费,是**一开始就确立"这是个付费刊物"的身份**。免费期只用来填货架,不用来养粉。
3. **免费额度是逐月收紧的,不是一刀切。** 从 100% → 52% → 30% → 18% → 6% → 0%,给了市场 14 个月适应。
4. **社群和平台都是后置的。** Discord 晚 6.5 个月,平台更晚。**内容 → 收费 → 社群 → 平台**,这个顺序他走对了,而你现在是反的(平台先做好了,内容和收费都没有)。

---

## 三、Substack:文章模板逐段拆解

拿 2026-07-29《Semiconductors Deep Dive》(2,051 字,**22 张图**)做样本,结构完全可复制:

| # | 段落 | 作用 |
|---|---|---|
| 1 | **固定免责声明块**「What TSF Is / What TSF Is Not」 | 每篇都有,一字不改。合规护栏 + 定位声明 |
| 2 | **回指旧观点**「Remember The "Clock Is Ticking" Post」+「You Were Warned」 | **收据**。用自己上一次的判断证明这次值钱 |
| 3 | **产品公告**「New Tool Launching — TSF Correction Risk Model」 | 把平台新功能塞进 newsletter,免费交叉推广 |
| 4 | **宏观/主题段**(SMH 半导体)+ 明确立场 | 「In Summary My Lean Is A Bounce Very Soon」 |
| 5 | **个股 setup 串烧**(NVEC / NTAP / CBRL / PANW / SAIL / AMBA / ITRI) | 每只 = 一个标题 + 一张图。**这是主菜** |
| 6 | **「Jonas's Swing Portfolio In Order Of Size」** | 每篇结尾公开自己全部持仓,**按仓位大小排序** |

**四个可以立刻抄的写作手法:**

- **标题写结论,不写标签。** 是「You Can't Have True Capitulation Without A Mark Down」,不是「半导体分析」。每个 H2 都是一句可证伪的判断。
- **图密度 = 每 90 字一张图。** 2,051 字配 22 张图。读者是在**看图**,文字只是图注。
- **每篇结尾公开持仓和仓位排序。** 这是他最强的信任装置,成本为零。
- **合规话术:**「I share all of my own trades, but those are my personal trades and journaled thoughts — never a recommendation」。**你的「不喊单、不给信号、只给测量」比他这句更硬,但你没有把它写成每篇都出现的固定块。**

**内容产品线(355 篇聚类后):**

| 产品 | 篇数 | 档位 | 平均字数 |
|---|---|---|---|
| **TSF Focus Stocks**(旗舰,周更) | 48 | 付费 | ~1,900 |
| **The Momentum Leaders Portfolio**(模型组合) | 11 | **founding 独占** | ~450 |
| **TSF - Community Meeting**(社群会议) | 8 | 付费 | ~1,100 |
| 教学长文(Ultimate Guide / 10 Core Concepts) | 少量 | 付费 | 2,000–3,600 |

> **注意 founding 档的设计:$499 vs $399 只差 $100,多给的是「他本人的长线组合 + 每周信号」。用一个几乎零边际成本的东西(他本来就要管的自己的组合)撑起 25% 溢价。** 而且平均只有 450 字 —— 极短。

**最高互动的是什么:** 前三名分别是 Community Meeting(36 赞/19 评)、Ultimate Guide 教学长文(36 赞)、10 Core Concepts 教学长文(28 赞/11 评)。**教学 > 个股。社群活动 > 内容。**

---

## 四、平台:最反直觉的一节

### 技术栈真相

```
托管/建站:  EasyWeb (app.easyweb.se) — 瑞典无代码建站工具
框架:       无 React / 无 Next / 无 Vue / 无 Supabase
数据接口:   零 XHR、零 fetch、零 inline JSON
页面体积:   3.8 MB HTML(全部预渲染,含 274 张 SVG K 线图)
字体:       Plus Jakarta Sans + Clash Display(都免费)
404 页:     瑞典语「Sidan hittades inte」
```

**他没有后端。整个平台是一坨每周生成一次、烤进 HTML 的静态页。** 连个股 K 线图都不是前端渲染的,是提前画好的 SVG 贴进去的。

> **这对你是最大的一条情报:你的 Python pipeline → 静态 JSON → React 架构,比他先进一个代际。你已经有的东西比他"平台"更强。你缺的只是把它开出来 + 加一道登录墙。**

### 六个页面

| 页面 | 内容 | 更新频率 |
|---|---|---|
| **TSF - Market Overview** | 主题涨跌卡 + Leading/Weakening/Improving/Lagging 计数 + **市场 regime 仪表盘**(Defensive/Caution/Tactical bull/Euphoria)+ 主题×滚动 2 周 RS 对比表 | 每周五收盘 |
| **Thematic Focus View** | **53 个主题**任选 3 个对比 RS 走势 | 每周 |
| **TSF - Focus Stocks** | 人工精选名单,标签分层(Weekly Focus / TSF-Leaders / Universe / High Octane)+ **「INSIGHT FROM FOUNDER」栏** | 人工 |
| **Live RS Theme Tracker** | 主题 RS vs S&P 双向条形图 | **每 15 分钟(盘中)** |
| **Theme Leaderboard** | 三张 Top-10 榜:RS 0-2w / RS 加速度 / RS 0-10w | 每周 |
| **Stock Screener** | ~2,900 只股票。列:History(制度色带)· Category · RS 0-2W/0-4W/0-10W · RS Accel · 52W High · Vol Surge · Accumulation · COC · **Score(0–6)**。内嵌 K 线图 + SMA/EMA | 每日 |

### 平台设计上真正聪明的四点

1. **53 个手工主题分类才是护城河。** RS 计算是初中数学,谁都能写。**「哪些股票属于 AI-Datacenters / Rare Earth Metals / High Octane」这份分类表是他一个人攒了一年多的资产。**
2. **应用里嵌了他本人的声音。** Market Overview 页面右侧是一段他手写的解读,**配头像、署名 Jonas**。数据 + 人格,不是冷冰冰的仪表盘。
3. **每个数据模块下面配「How To Interpret」教学块。** 不假设用户看得懂。这既是教育,也是降低退订。
4. **更新频率分层。** 只有一个页面是 15 分钟级的(而且是最容易做的那个),其余全是周更。**他把"实时"这个昂贵的承诺,只给了成本最低的那一页。**

---

## 五、Discord:两层结构 + 一个留存引擎

**建于 2025-08-31。频道树:**

```
📢 Information From TSF(只读广播 — 他的输出)
   ⛔ start-here-rules-of-conduct
   📌 weekly-dashboard
   📊 market-insights
   🧐 jonas-trades          ← 留存引擎,见下
   📕 10-tsf-trading-rules
      tradingview-indicators

💬 TSF - Community(成员互动)
   📈 daily-chat-stocks-and-trading    ← 主战场,他本人天天在
   😎 tsf-members-intro
      tsf's-analytics-broken-or-desired    ┐
      tsf-community-watchlists              │
   🔊 trading-strategy (语音)               │  4 个频道专做
   📊 trading-and-news-resources            │  产品共创
   🤔 feature-requests                      │
      tsf-analytics-planned-updates         │
      tsf-analytics-discussions-and-obs...  ┘
      community-trading-journal

🐋 Unusual Whales(第三方合作)
      tsf-members-use-unusual-whales-here   ← 会员折扣/联盟
      live-unusual-options-flow             ← 机器人喂流
      highest-volume-contracts
```

### `#jonas-trades` 是整个生意的留存引擎

实录格式(2026-07 抽样,约 2–4 笔/周):

> `@Paid TSF Subscriber` Buying BAND @ 69.61, SL day low ~3.6%. Small size risking ver…
> `@Paid TSF Subscriber` BB stop hit. not a recommendation to buy or sell anything…
> `@Paid TSF Subscriber` Selling 1/3 of SIMO @332.20 not a recommendation to buy or sel…

**拆解:**
- **实时**发自己的真实买卖:入场价、止损(同时给 % 和价位)、仓位语言、离场
- **每条都 @ 付费角色** → 推送通知 → 打开 App → 留存
- **每条都带免责尾巴** → 法律上是「交易日志」,体验上是「信号服务」

**这是他把 $399/年 变成"每周都有理由打开"的机制。** Substack 是每周 4-5 次的内容,Discord 是每天的存在感。

### 另外三点

- **4 个频道专门做产品共创。** 实录里可见成员提需求(要 stage 1/2 识别、均线斜率、距均线 %),他当场回路线图。**用户帮他定义产品,同时被这个过程锁定。**
- **他明写「这是无人值守服务器」+「我不会总在」** —— 提前把自己的劳动预期压下去。但实际他周六晚上还在群里回「Complete crap」「Breadth not good」。**低承诺 + 高实际在场 = 惊喜感。**
- **Unusual Whales 合作** —— 用别人的产品补自己的短板(期权流),很可能还有联盟返佣。零开发成本。

---

## 六、X:他其实做得不好(这是给你的好消息)

| 指标 | 他 | 你 |
|---|---|---|
| 粉丝 | **4,691** | **273** |
| 帖数 | 9,789 | 871 |
| 注册 | 2017-03 | 2009-11 |
| 单帖 views | **600–1,200** | — |
| 单帖赞 | **1–8** | — |
| 置顶帖 | 产品说明书「Understanding How TSF-Analytics Works」(10.6K views) | — |

**他的 X 现状,对照你 7 月那份 10 账号拆解:**那份里最小的 @FranVezz 都有 22.3K 粉、体系长文 215K views。**TSF 的互动量是那个梯队的 1/50。**

**他的 X 打法:**
- 日更 4–6 帖,几乎全部带图
- 大量是**自家 App 的截图**(「This is one of the most awesome things I have ever made tbh」)
- 部分是**排版好的文字卡片截图**(米色背景衬线字体)+ 图表
- 短评盘口(「Anyone noticing the bitcoin puke $BTC」)
- 简介三行硬广:4x weekly publication · 400+ Discord · Analytics 平台 + 链接

**结论:X 对他是产品陈列柜和信任存档,不是获客渠道。** 他不追爆款,不玩梗(对比你 7 月的发现:段子触达是分析的 10–40 倍 —— 他一条都不玩)。

### 那 400 人从哪来?—— Substack 推荐网络

```
他推荐别人的刊物:  50 个
别人推荐他的刊物:  50 个
两份名单高度重合  ← 互推置换
```

重合名单包括 The Daily Market Roadmap®、美股送分題、SaltStack、Rebound Capital、Algomatic Trading、Smart Money Talk、Crack The Market、Freedom Trades、Quanta 72、Grey Rabbit Finance、The Rogue Quant…

**Substack 的推荐位会出现在对方每一个新订阅者的注册流程里。** 50 个互推伙伴 = 50 条持续的、免费的、精准的引流管道。**这才是他的获客引擎,而且几乎不花时间 —— 是一次性搭好的结构。**

> 顺带:他还把 founding 档的 Momentum Leaders Portfolio **单独开成了第二个刊物**,自己推荐自己,吃第二个推荐位。

---

## 七、你 vs 他:优势、差距、该做什么

### 你现在手里的牌(客观比他强的部分)

| 维度 | 你 | 他 |
|---|---|---|
| **数据引擎** | Python pipeline + 12 个 JSON + React 19,GEX 引擎、breadth v2、ticker events、sequence mining、options structure engine | EasyWeb 无代码,静态烤 HTML,零后端 |
| **真实业绩** | 7 年真实回报,H1 2026 +90.5%,已有公开 Track Record 页面 | **未见任何业绩披露** |
| **投入** | 全职 | 兼职(全职 ICU 医生) |
| **声音资产** | Voice Bible、43 条视觉库、Fluxus 品牌系统、13k Discord 语料 | 无品牌系统,文风朴素 |
| **合规姿态** | 「不喊单、不给信号、只给测量」 | 同样定位,但靠每篇复制粘贴的免责块 |
| **量化深度** | 做过 null result 诚实披露(sequence mining 42 个组合 0 个跑赢) | 「backtested, data backed」但未见方法披露 |
| **双语** | EN + 中文,能吃中文圈 | 只有英文 |

**你最大的、他完全没有的牌:7 年真实业绩 + 一个已经建好的 Track Record 页面。** 他连业绩都没公开过就收 $399。

### 你的差距(按致命程度排序)

| # | 差距 | 严重度 | 说明 |
|---|---|---|---|
| **1** | **没有 Substack** | 🔴 致命 | 他的**收款台、内容库、获客引擎全在这一个东西上**。你零。这是唯一真正的阻塞项。 |
| **2** | **没有推荐网络** | 🔴 致命 | 他 50 出 50 入。这是他获客的全部。而这**不需要粉丝、不需要爆款,只需要开号 + 主动去谈**。 |
| **3** | **Dashboard 没开放** | 🟠 高 | 你的东西更好,但对外等于不存在。 |
| **4** | **没有定价 / 没有付费墙** | 🟠 高 | 他开张第 15 天就架墙。你做了一年多产品,一分钱没收。 |
| **5** | **没有固定内容产品线** | 🟡 中 | 他有 TSF Focus Stocks(48 篇)这种**有名字、有节奏、可预期**的栏目。你的输出是项目制的,不是刊物制的。 |
| **6** | **X 粉丝 273** | 🟢 低 | **看起来最刺眼,实际最不重要** —— 他 4,691 粉且互动稀烂,照样做成。别把力气花在这。 |

### 建议动作(按顺序,不要跳)

**第一优先 —— 开 Substack,一个月内。**
- 别等内容完美。**开张日发 5–8 篇**(你手上现成的:Track Record 故事、GEX 方法论、breadth 信号引擎、sequence mining 的 null result、options 分析方法论 —— 这些全都是已经写好的资产,改写即可)
- 第一个月填满 ~20 篇,全免费
- **第 15–30 天架付费墙**,定价 $39–49/月 · $299–399/年。别定低了,他 $399 卖的东西你比得过

**第二优先 —— 立刻搭推荐网络。**
- Substack 开号当天就可以设置推荐。**去谈 30–50 个互推**,优先中文圈(他完全吃不到的市场)+ 你 7 月普查过的 46 个 fintwit 账号里有 Substack 的
- 这件事和粉丝数无关,是纯结构性红利,而且做一次管一年

**第三优先 —— 把 dashboard 加一道登录墙开出来,作为付费权益。**
- 不需要重构。你的架构已经比他好。加 auth + 付费校验即可
- **抄他三点:**(a) 页面里嵌你本人的解读 + 头像署名;(b) 每个模块配「怎么读」教学块;(c) FAQ + 视频教程页
- **别抄他的更新频率承诺** —— 只给一个页面实时,其余周更

**第四优先 —— 定一个有名字的旗舰栏目。**
- 他是「TSF Focus Stocks」,每周一篇,1,900 字 + 20 张图,结尾公开全部持仓
- 你的版本应该建在你的独有优势上 —— 业绩透明 + 量化诚实。**「每篇结尾公开全部持仓 + 仓位排序」这一条直接抄,成本为零,信任回报极高**

**第五 —— Discord 先别动。** 他晚了 6.5 个月才建,而且真实活跃只有几十人。你已经有 Discord 了,等 Substack 有付费用户再把它接成权益。

**不要做的事:**
- ❌ 不要去追 X 粉丝。他 4,691 粉、单帖 600 views 就做成了。X 是陈列柜
- ❌ 不要再往 dashboard 加功能。它已经超过他了。**问题不在产品,在于它没有价签也没有门**
- ❌ 不要等"准备好了"。他开张第 15 天就收费,那时候他只有 25 篇免费文和零社群

---

## 八、一句话总结

> **他用一个无代码建站工具、4,700 个僵尸粉、和 50 个互推伙伴,做出了 ~$160k/年的副业。**
> **你有更强的引擎、更真的业绩、更好的品牌和全职时间 —— 但你没有收款台。**
> **差的不是能力,是那一个 Substack,和架墙的胆子。**

---

*受据存于 `Fluxus_Receipts/tsf/`。数据抓取时间 2026-08-01 ~ 08-02。*
