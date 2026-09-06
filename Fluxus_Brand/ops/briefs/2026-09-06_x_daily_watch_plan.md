# X 日调研 —— 方案与困惑

*2026-09-06(JST)。Andy 原话:「我需要让你每天对 X 进行调研,账户就是我们说的那几个。但我需要看到调研方向和目标,每天他们在聊什么,哪些 ticker 被提到很多次,是怎么说他们的。以及你需要扩展寻找一个更好的调研方式,现有的上浏览器截图不是不行,但实在不方便。」补充:「我不打算不花钱」「50 个核心人物,每天总共不到 500 条」。*
*本文件是方案,不是已建成的东西。下面凡是数字都标了来源;没查到的写「未验」。*

---

## 一、目标(三个,按重要性排)

| # | 目标 | 每天回答的问题 | 给谁用 |
|---|---|---|---|
| **1** | **他们在看什么** | 哪些 ticker 被提得多 · 谁提的 · **怎么说的**(进 / 出 / 观望 / 嘲讽 / 复盘)· 和 Andy 自己 watchlist 的重叠与独有 | Andy 盘前 |
| **2** | **蹭位窗口** | 过去 24h 里人流密度(曝光 ÷ 回复数)最高、还能回的帖 | Andy 发帖 |
| **3** | **积累后可测的问题** | 圈子提到一只票,是在涨之前还是之后?—— 我们有本地 OHLC(`data/output/tickers/`),提及表可以直接 join 价格 | Zac / 研究 |

副产品:收藏比 >0.5 的帖自动进选题库(已有机制,Swipe File「高收藏样本 = 选题库」)。

⚠️ **目标 3 是把「调研」变成「研究」的唯一出口。** 前两个是每天消费掉的;只有第三个会越积越值钱。但它要 60+ 个交易日才有统计意义,前两个月别看它。

---

## 二、每日产出长什么样

```
data/content/x_watch/
  posts/2026-09-08.jsonl        ← 原始:每条帖全字段(id/handle/text/时间/views/likes/bookmarks/replies/reposts)
  mentions.csv                  ← 累加:date, ticker, handle, post_id, stance, views, bookmarks
  daily/2026-09-08.md           ← 给 Andy 看的那页
```

**那页只有六节,每节一屏内:**

1. **今天变了什么** —— 新进榜 / 掉榜的 ticker、第一次出现的话题。**昨天也在的不复述**(没变的状态没有信息量)
2. **Ticker 榜** —— 提及数 · 提及人数 · 立场分布(几个说进、几个说出)
3. **他们怎么说的** —— 每只前五 ticker 配 2–3 句原话,标 handle 和立场。原话**只存不引**(SOP),不进对外文案
4. **非 ticker 话题** —— 大盘判断 / 心态 / 互相怼 / 圈内事
5. **表现异常** —— 收藏比 >0.5 或曝光 >该账号中位 5× 的帖 → 选题库候选
6. **蹭位榜** —— 人流密度前 5,附链接和发帖距今小时数

**立场标注(第 2、3 节)是判断活,由 Claude 读 jsonl 后写;提及计数是机械活,由脚本算。** 两步分开,脚本的数不许被改写。

---

## 三、方法 —— GitHub 和市场都查过了(09-06)

> ✅ **Andy 09-06 定:「先不花钱,Fable 出方案,Opus 5 去跑。然后看看质量、时间和效果,到底需不需要第三方花钱的方式。」**
> → 第一版走**免费方案:私密 X List + Claude in Chrome**,执行手册 [`2026-09-06_x_daily_watch_runbook.md`](2026-09-06_x_daily_watch_runbook.md);5 个交易日后按手册 §三的四个数决定是否切付费源。下表保留,是备选不是现行。

**量:50 人 × <500 条/天 ≈ ≤15,000 条/月。** 按这个量算钱:

| 方法 | 月费(我们的量) | 拿得到 views / bookmarks? | 无人值守? | 风险 | 判 |
|---|---|---|---|---|---|
| **twitterapi.io**(第三方 API) | **≈ $2–5**(公开价 $0.15/1k 条) | ✅ `viewCount` `bookmarkCount` 在返回字段里(官方字段表) | ✅ | **非官方**,靠它们爬 X;可能一夜断供。**不动 Andy 的账号** | ⭐ **主源** |
| **官方 X API**(pay-per-use) | **≈ $75**($0.005/条读取;$200 Basic 档 2026-06 起对新用户关闭) | `public_metrics` 含 like/reply/repost/quote;**bookmark / impression 对他人帖是否开放 —— 未验** | ✅ | 稳定;要开发者账号 + 绑卡 | **备胎**(账号先申请着) |
| twscrape / Scweet(GitHub 开源) | $0 | ✅ | ✅ | **用账号 cookie 走 GraphQL,违 ToS,封号风险**。绝不能用主账号 | ✗ 不用 |
| 现状:Claude in Chrome | $0 | ✅ | ❌ 要人在、45s CDP 超时、X 限滚动 | 无 | 保留做单帖核对 |
| GitHub 上的 X MCP servers(x-mcp / twitter-mcp 等) | 同底层源 | 同 | — | 它们只是把上面两种源包成对话工具;**批处理不需要 MCP**,直接 HTTP 更稳 | 参考不装 |

**推荐:twitterapi.io 主源 + 官方 API 备胎。** 两个都花钱,都少;**真正的成本不是钱,是断供** —— 所以原始 jsonl 每天落盘进仓库,数据在我们手里,不在源那边。

**架构两段:**
- **抓**:Python 脚本(无 LLM,幂等,可重跑),launchd 每天定点跑 → 写 `posts/*.jsonl` + `mentions.csv` + commit
- **读**:Claude 定时任务读当天 jsonl → 写 `daily/*.md`(第 1、3、4 节要判断,第 2、5、6 节直接从 csv 出)

已有可复用的骨架:`pipeline/x_bookmarks/`(2026-07 建,Playwright + 持久登录态,但只跑出过一个空目录)—— 它的 extractor 字段设计可以搬,浏览器部分不用了。

---

## 三之二、⭐ 09-06 实测把方法选择改了:**问题不是用哪个爬虫,是这个账号被限速了**

Andy 让查 `xcrawl`。查了,顺带把这一类都查了 —— **结论是这一类工具解决不了我们的问题。**

**当晚实测(同一个登录态 Chrome,三次):** 30 人的 List 拿到 9 条帖 / 5 个作者 · 34 人的 List 拿到 **5 条 / 2 个作者** · following 533 人只吐 16 个 · 五张 List 的成员弹窗**一次都没出过人**(直接 URL、从列表页点、Edit List → Manage members,四条路同一个空弹窗)。**重开 session 无效**,数字还在往下走。

> ### 🔑 **驱动浏览器的库换十个,用的还是同一个被限的账号,撞的是同一堵墙。**
> **限速挂在账号上,不挂在工具上。** 这决定了下面这张表怎么读。

| 工具 | 它是什么 | 对我们的问题 |
|---|---|---|
| **x-crawl**(`coder-hxl/x-crawl`,1.9k★) | **通用** Node 爬虫库 + AI 元素分析 + 指纹/代理轮换。README 里**没有一个字提 X/Twitter**,也没有鉴权与限速的处理 | ❌ **它驱动的还是浏览器。** 我们卡的不是「不会写选择器」,是账号被限。换它 = 换一个更麻烦的方式撞同一堵墙 |
| **twscrape**(`vladkens/twscrape`) | 走 X 的 GraphQL,**明确支持 List 成员 + List 时间线**(正是我们要的两个),多账号轮换 + SQLite 会话 + 内建限速处理 | ⚠️ **功能最对口,风险也最实**:要账号池(cookie 的 `auth_token`+`ct0`),README 自己写着「X 的 ToS 不鼓励多账号,自行承担」。**用 Andy 的主账号 = 拿 @Fluxus_Z 冒险**,而这个账号是全部生意的入口。另外**收藏数在不在返回字段里,文档没写明** —— 而收藏比是我们最重要的那个量 |
| Scweet / X-Tweet-Scraper / proxidize | Selenium/Playwright 驱动 | ❌ 同 x-crawl,同一堵墙 |
| **twitterapi.io** | 第三方**托管** API,不用我们的账号 | ⭐ **仍是推荐**:`viewCount` / `bookmarkCount` 在官方字段表里;按我们的量约 $2–5/月;**@Fluxus_Z 零风险** |

**判定:**
- **`xcrawl` 不采用** —— 类别不对,它解决的是「怎么写爬虫」,我们的问题是「账号被限」。
- **twscrape 只在一种情况下考虑**:用一个**和生意无关的小号**,且先花十分钟验它返不返回 `bookmark_count`。返不回来就没意义。
- **主推仍是 twitterapi.io。** 它唯一的缺点是非官方、可能断供 —— 这个缺点用「原始 jsonl 每天落盘进仓库」对冲掉。

⚠️ **一条得写下来的教训:** 我今晚为了找名单反复拉列表,亲手把这个 session 打限速了,然后又用这个被我打坏的 session 去量「免费方案行不行」。**测量工具和被测对象是同一个东西的时候,读数是我自己造的。** 那三个数(9 / 5 / 16)方向没错,但别把它们当成 X 的固有上限报出去。

## 四、三件套(不写不开工)

| | |
|---|---|
| **发布物** | ⚠️ **要 Andy 答**:日报本身是内部的。候选:每天 1 条蹭位回复(第 6 节直接产)+ 每周日 1 条「这周圈子在聊什么」 |
| **截止日** | **09-13(下周日)**:连续 5 个交易日的日报跑出来,含真数 |
| **到期规则** | 到期没跑通 → 退回浏览器法只盯 13 个拆解过的账号;不再扩 |

---

## 五、困惑(真的困惑,不是修辞)

1. **50 个人是哪 50 个。** 我手上有两堆:拆解过的 13 个(wey_how / Shake / Muninn / JGBanks / jfsrev / TraderLion 五人 / ohiain / ZaStocks / TSF / Hrundel75)+ Fintwit Top 100 扫过的 46 个。**需要你给名单或批我从这两堆里凑。** 名单决定一切:50 个人的 ticker 榜**不是 fintwit 的 ticker 榜**,它只是这 50 个人的 —— 别把它读成市场情绪。
2. **twitterapi.io 的 `bookmarkCount` 真的有值吗。** 字段表里有,不等于填了。**先花 $0.1 免费额度拉 3 个账号各 20 条看看**,5 分钟的事,做完再定主源。
3. **定时任务要 App 开着才跑**(已知约束)。抓取放 launchd 不依赖 App;读报告放 Claude 定时任务 —— **App 没开的那天,数据不缺、报告缺**。这个断法对吗?
4. **「怎么说的」最容易写成 AI 味**:复述 + 形容词。守法是第 1 节只报变化、第 3 节只放原话不放我的转述。够不够,要看头两份。
5. **代码放哪。** 抓取脚本是代码,不是内容;Steve 的边界是 `Fluxus_Brand/` + `data/content/`,没有 `pipeline/`。候选:`Fluxus_Brand/ops/tools/x_watch/`,或问 OPS 开一格。
6. **跑几点。** 一天一次,06:30 ET(19:30 JST)覆盖前 24h,你盘前能看到 —— 还是盘前盘后各一次?

---

## 六、来源

- X API 定价:[Postproxy](https://postproxy.dev/blog/x-api-pricing-2026/) · [TweetStream](https://tweetstream.io/blog/twitter-api-pricing) · [twitterapi.io 对比文](https://twitterapi.io/blog/x-api-cost-breakdown-2026)
- twitterapi.io 定价与字段:[官网](https://twitterapi.io/) · [字段参考](https://twitterapi.io/blog/twitter-tweet-metadata-fields-api-reference)
- GitHub:[vladkens/twscrape](https://github.com/vladkens/twscrape) · [Altimis/Scweet](https://github.com/Altimis/Scweet) · [armatrix/twitter-mcp](https://github.com/armatrix/twitter-mcp)(读走 twitterapi.io)· [DataWhisker/x-mcp-server](https://github.com/DataWhisker/x-mcp-server) · [Infatoshi/x-mcp](https://github.com/Infatoshi/x-mcp)
