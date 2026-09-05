# X 日调研 · 执行手册(给跑手会话,Opus 5)

*2026-09-06。Andy 定:「先不花钱,Fable 出方案,Opus 5 去跑。然后看看质量、时间和效果,到底需不需要第三方花钱的方式。」*
*方案与目标见 [`2026-09-06_x_daily_watch_plan.md`](2026-09-06_x_daily_watch_plan.md);名单见 [`2026-09-06_x_watch_roster.md`](2026-09-06_x_watch_roster.md)。本文件只讲**怎么跑**。*
*跑手会话名:`MARKETING STEVE · X 日调研跑手`。文件边界:只写 `data/content/x_watch/**`;改本手册要回到 Steve 主会话。*

---

## 〇、免费方案的核心:一张 X List,一页看完所有人

不再逐个账号进主页。**把名单建成一个私密 List,List 时间线是纯时序、无算法、一页滚完。** 一天一次滚 24 小时的量(名单 30 人 · Andy 估总量 <500 条),比逐人访问少 30 次页面加载,也少 30 次 45 秒超时的机会。

工具照旧 `mcp__claude-in-chrome__*`(Andy 的登录态 Chrome)。**不用 headless Playwright**(X 对 headless 回空页,且用他的 cookie 走无头有封号风险)。

---

## 一、一次性准备(第 1 天)

1. **建 List**:x.com → Lists → New。名字 `fx-watch`,**Private 打勾**。⚠️ 这是在 Andy 账号里建东西 —— 开建前在会话里问他一句,他点头再动。
2. **加成员**:按 roster「定稿 v3」的 30 人加(含 @TheOneLanceB / @LindaRaschke,两者都有仿冒号,认精确 handle)。加之前每个进一次主页确认存在、是本人;对不上的记进 README 问 Andy,不猜。加完记下 List URL(`https://x.com/i/lists/<id>`),写进 `data/content/x_watch/README.md`。
3. **建目录**:
   ```
   data/content/x_watch/
     README.md          ← List URL · 名单版本 · 本手册链接
     posts/             ← YYYY-MM-DD.jsonl 原始
     daily/             ← YYYY-MM-DD.md 给 Andy 看的
     mentions.csv       ← 累加表
     runlog.csv         ← 每次运行:date, started, minutes, posts_captured, oldest_post_age_h, timeouts, notes
   ```
4. **抓取器**:沿用 `data/research/README_x_account_scrape.md` §二的 `__xgrab`,加三个字段:`handle`(从 permalink 解析,见 `pipeline/x_bookmarks/extractor.py` 的做法)· `replies`(aria-label 里有)· `is_reply`(卡片顶部有 "Replying to")。**取 `<time>` 前先数该卡片里有几个 `article`/`time` —— 引用帖的时间戳会抢第一个位置**(08-25 Muninn 事故)。

## 二、每天(一次,盘前)

**跑几点:06:30 ET(19:30 JST)。** 覆盖前 24 小时。Andy 若改,改这里。

1. 打开 List URL(`?f=live` 不需要,List 本就是时序)。
2. 初始化 `window.__X`,滚动 + `__xgrab()`,**直到最旧一条早于 24 小时前**,再多滚两屏收尾。每 10 屏导出一次到剪贴板/console,防 45 秒 CDP 超时丢全部(**超时不是失败,继续滚**)。
3. 落盘 `posts/YYYY-MM-DD.jsonl`,一行一条:`id, handle, datetime, text, views, likes, bookmarks, reposts, replies, is_reply, is_qt, has_chart, url`。
4. **机械步(脚本,不许手改数)**:
   - ticker 抽取:`\$[A-Z]{1,5}\b` **加** 不带 `$` 的裸代码 —— 裸代码只认 `data/output/tickers/` 里存在的符号,且排除英文常用词表(A, I, ALL, CEO, IPO, ETF, AI, EPS, PM, AM, US…)。
   - 追加 `mentions.csv`:`date, ticker, handle, post_id, views, bookmarks`(stance 列此步留空)。
   - 榜:提及次数 · 提及人数 · 与昨日对比(新进/掉榜)。
   - 蹭位榜:`views / max(replies,1)`,只算 is_reply=false 且发帖 <20 小时的。
   - 异常:`bookmarks/likes > 0.5` 或 `views > 该 handle 近 7 日中位 × 5`。
5. **判断步(你读 jsonl 后写)**:给前 5 ticker 每条相关帖标 stance,词表**只有六个**:`long / short / watching / exited / recap / mention`;回填 mentions.csv。然后写 `daily/YYYY-MM-DD.md`,六节,每节一屏内:
   1. 今天变了什么(新进/掉榜 ticker · 首次出现的话题。**昨天也在的不写**)
   2. Ticker 榜(表:ticker · 提及 · 人数 · 立场分布)
   3. 他们怎么说的(前 5 ticker 各 2–3 句**原话** + handle + stance。不转述,不加形容词)
   4. 非 ticker 话题(一行一个,谁说的)
   5. 表现异常(帖链接 · 收藏比 · 一句话它讲什么)
   6. 蹭位榜前 5(链接 · 人流密度 · 距今小时)
6. 追一行 `runlog.csv`。
7. **直推 main**(CLAUDE.md 标准动作,临时树,只 add `data/content/x_watch/`),`git log origin/main -1` 看到自己的 commit 才算完。
8. 收工三问照答,写在 daily 文件末尾折叠块里。

## 三、评估 —— 5 个交易日后回答「要不要花钱」

跑到 **09-13** 汇总 `runlog.csv`,给 Andy 四个数,不给形容词:

| 量 | 怎么算 | 花钱的临界 |
|---|---|---|
| **时间** | 每次运行分钟数(中位) | > 25 分钟/天 → 值得 $2–5/月 |
| **覆盖** | 抽 3 个账号,主页数 24h 内帖数 vs jsonl 里抓到的 | < 90% → 数据不可信 |
| **稳定** | 5 天里几次要人介入(登录弹窗、超时后重开、限滚动) | ≥ 2 次 → 无人值守不成立 |
| **用了没** | Andy 从蹭位榜实际回了几条、看了几天 | 0 → 先别谈方法,谈产品 |

**前三条任一过线 → 切 twitterapi.io(方案 §三);都没过 → 免费方案保留,钱省下。**

---

## 四、跑手的禁区

- 不发帖、不回复、不点赞、不关注 —— 只读。蹭位是给 Andy 的建议,不是给你的动作。
- 原话只进 daily 文件,**不进任何对外文案**(SOP「只存不引」)。
- 不改 roster、不改本手册、不改 plan —— 有意见写在 daily 末尾「给 Steve」一行。
- 抓取的数是脚本出的;判断步只加 stance 和文字,**不改任何数字**。
