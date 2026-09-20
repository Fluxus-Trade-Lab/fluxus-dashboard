---
name: x-watch
description: X（Twitter）调研两班——主班（ET 00:30 起抓前一 ET 日历日完整 24h + @jfsrev 订阅区 + mood → 七节日报 + ticker 看板）与睡前速报（ET 13:00，只出蹭位榜 + 圈外主题起量，两屏）。凡任务 type=x_watch / type=x_nightcap、或有人说「跑一下 X 调研 / 今天 X 上谁在说什么 / 蹭位榜 / 出日报 / 刷一下看板 / 圈外主题起量」都用本 skill；抓取窗口、清单帖、stance、mood 词表那几条坑全在里面。
owner: steve
---

# x-watch — 两班一本账

把 Andy 关注的 34 个交易者说了什么，变成他能用的一页。两班制（Andy 2026-09-07 定：「用2班制,早班推迟到到13:30 JST」）：

| 班 | 跑点 | 产出 | 目录 |
|---|---|---|---|
| **主班** | 13:30 JST = ET 00:30 | 七节日报 + ticker 看板 | `data/content/x_watch/daily/<ET 日>.md` |
| **速报** | 02:00 JST = 前一日 13:00 ET | 蹭位榜 + 圈外主题起量，两屏 | `data/content/x_watch/nightcap/<ET 日>.md` |

仓库：`/Users/taolezhu/Documents/AI-Trading-System`。只写 `data/content/x_watch/**`。

## 开工前必读（读权威版，不读主树副本）

```bash
git -C /Users/taolezhu/Documents/AI-Trading-System fetch origin
git show origin/main:Fluxus_Brand/ops/briefs/2026-09-06_x_daily_watch_runbook.md
git show origin/main:data/content/x_watch/README.md
git show origin/main:data/content/x_watch/subs/README.md
git show origin/main:data/content/x_watch/scoring/2026-09-07_time_window.md
```

**手册是设计理由的权威，本 skill 是节目单和操作步骤的权威**（09-13 定）。冲突时：节目与步骤听本 skill，「为什么这样设计」读手册。名单 34 人在 `members.json`。

⭐ README 末尾「📮 给 Steve 取件账」是前几班的回执，开工先看：✅ 的别再提 · ⛔ 的读理由 · 🟡 的看是不是轮到你。同一条建议没回执、又想提，照提并注明「第 N 次」。

---

# 主班

## 一、抓公开区

⛔⛔ **永远不要用 `--days 1`。** 它是 `until=now(ET)` / `since=now−24h` 的**滚动窗口，跨两个 ET 日历日各切一截**。09-13 之前落盘是 `"w"` 覆盖，它曾**每天把前一天的 jsonl 砍成只剩 20:00–24:00 的四小时残片**；09-13 起日归档按 `id` 并集，它不会再毁数据，但**抓到的仍是两个半天，不是一个整天**。用明确的日历日边界：

```bash
cd /Users/taolezhu/Documents/AI-Trading-System
D=$(TZ=America/New_York date -v-1d +%F)      # 昨天(ET)
N=$(TZ=America/New_York date +%F)            # 今天(ET)
.venv/bin/python Fluxus_Brand/ops/tools/x_watch/fetch.py --since $D --until $N --max-pages 60
```

`--until` 被解析成那天的 00:00 ET，判定是 `since <= dt <= until`，所以这正好圈住 ET 日历日 `$D`。**同一天被抓两次（速报 + 主班）时按 `id` 并集**：同一条帖整行换成本轮的（曝光/收藏是新值），旧文件有、本轮没返回的留着。

✅ 跑点是 13:30 JST（= ET 00:30），`$D` 的 24 小时全部已经发生，不缺尾部。**别再在日报里写「本窗口止于 ~20:00 ET」**（那条旧警告在任务书里滞留了五天，每班都读到一次不再成立的话）。

key 在仓库根 `.env` 的 `TWITTERAPI_KEY`（别读值、别打印、别写进任何文件）。限速每 5 秒 1 请求，**60 页约 5–6 分钟，别以为它卡住了**。

### ⛔ 跑完必做的四条核对

1. **翻到底了吗** —— `runlog.csv` 最后一行的 `oldest_raw_utc` 必须**早于** `since_et` 的 00:00 ET。没早于就是没翻到底，加 `--max-pages` 重跑。
   ⚠️ 首跑 25 页只翻到 09-04 11:33 ET，周五被砍掉 42%（**连着的前半天**）。**当时每个闸都是绿的**——条数没有「该等于多少」的先验。那条警告当时打印过。**闸响了没人读，所以现在把读它写成动作。**
2. **文件只增不减吗** —— `wc -l data/content/x_watch/posts/*.jsonl` 对比 origin/main，任何一天都不该变小。09-13 起 `fetch.py` 按 `id` 并集落盘，**它自己不会让文件变小**：变小了说明是别的东西动过它，`git checkout origin/main -- <该文件>` 恢复并查是谁。抓取打印的 `posts/<日>.jsonl: 旧 N · 本轮 M → 并集 K` 那行抄进第 7 节窗口行。
3. **名单没被覆盖吗** —— `members.json` 必须还是 34 人。脚本会拿 API 成员接口结果覆盖它，而私密 List 的成员接口**永远返回空**。被写成 `[]` 就 `git checkout origin/main -- data/content/x_watch/members.json` 恢复，**永不提交 `[]`**。
4. **额度还在吗** —— `HTTP 402 Credits is not enough` 就在日报里报「无数据」，**别拿旧 jsonl 冒充新的一天**。

`mentions.csv` 由 `fetch.py` 按 `(date,ticker,handle,post_id)` upsert，**重跑不会产生重复行**。下面这条 `awk` 留作双保险，**不是验证动作**，别在日报里当核对写：

```bash
awk -F, 'NR==1||!seen[$1","$2","$3","$4]++' data/content/x_watch/mentions.csv > /tmp/m && mv /tmp/m data/content/x_watch/mentions.csv
```

## 二、抓 @jfsrev 订阅区

⛔ **twitterapi.io 拿不到订阅内容**（实测：搜索 0 条，单帖端点返回空壳）。**只能用 Andy 登录态 Chrome。**

`mcp__claude-in-chrome__*` 打开 `https://x.com/jfsrev/subs`，注入 `__xgrab`（handle 从 permalink 解析，**排除内嵌引用帖的 `<time>`**），然后：

⚠️⚠️ **必须用 `computer` 的真实鼠标滚轮**：`{action:"scroll", coordinate:[700,500], scroll_direction:"down", scroll_amount:10}`，每 2 次滚动等 2 秒再 `__xgrab()`。**JS 的 `scrollBy` 和派发的 `WheelEvent` 都不触发 X 的无限加载**——实测滚 6 条就"到底"，那是假阴性。基线约 10 次真实滚动拿到 15 条。

落 `data/content/x_watch/subs/jfsrev/<日期>.jsonl`：`id · dt · et · kind · tickers · proxy · stats · text`。`kind` 用他自己的词：`Stalk` / `Focus` / `Update` / `WeekendSeries` / `Groups` / `Note` / `Plan` / `Educational`。
  ⚠️ 后三个是 09-20 周结补进来的（取件账 09-14·1 数到第 4 次）：库里存量早就有 `Note` 21 条、`Plan` 4 条，跑手每班照实写、每班又超纲，超的是词表不是跑手。**这张表以本行为准，别再按五个词自检。**

⛔ **付费内容，原话只存不引，永不进任何对外文案**；只抓 Andy 本人已订阅的，**目前只有 @jfsrev，不扩**。
⛔ 浏览器工具不可用时：日报里写「订阅区未取 · 原因」，**不静默跳过，也不拿昨天的顶替**。

## 三、算 mood 指标

抓完公开区、确认 coverage 之后：

```bash
.venv/bin/python data/content/x_watch/scoring/mood_index.py --date $D
```

它自己做三件事：①算七个**比例型**指标写进 `scoring/mood_daily.csv`（幂等，同日重跑=覆盖那一行）· ②读 `runlog.csv` 判 `coverage` · ③判「圈外主题起量」，过闸就自动追 `scoring/theme_events.csv`。

**把它打印的两样抄进日报**：那一行 mood 摘要 · 有没有 `⭐ 圈外主题起量` / `⚠️ 庆功不是起量`。

- ⛔ **不手打 CSV 里的任何一列。** 09-07 手抄第一版时 `index_people` 等四列没算过就填了 0，重算后 08-17 是 6 不是 2。
- ⛔ **不改 `DEF`/`OFF` 词表和 `OUT_THEME`。** 改了老行新行就不可比（删一个 `wait` 就让同日 `defensive_share` 从 0.037 变 0.030）。真要改：升 `CALC` 版本 + 用 `--from` 把全部历史行重算，并在日报里说明。
- ⛔ **不出情绪读数。** 到 20 个交易日（约 10-06）之前，日报里只登记数字、不写「今天偏空」这种话。
- `coverage` 不是 `full` 时照写那一行，但日报里注明，画基线时要排除。

## 四、写（判断活）

读 `posts/$D.jsonl`，写 `daily/$D.md`。日期一律 ET（`pipeline.marketcal`）。

标 stance 回填 `mentions.csv`（**只改 stance 列，行数不许变**），词表只有六个：`long / short / watching / exited / recap / mention`。

⚠️ **recap 和 long 分不清，第 1、2 节全废。** 讲**已发生的涨幅**=recap；讲**还没发生的入场条件**=long。同条两者都有按结尾那句算。
⚠️ **stance 只给第 1、2 节的判断用，不进任何打分/权重链**（Andy 09-07：「我只需要有人提醒到这个 ticker 就可以了,不需要方向」）。所有计分一律纯计数。

**七节，每节一屏内（第 7 节带回复方向可到一屏半）：**

1. **明天的候选 —— 还没跑的。** ≥2 人提 · 立场 long/watching · 不在昨天榜首。⭐ 判据是「新鲜」不是「热」。
   ⭐⭐ **算人数时把 @jfsrev 墙后那票算进去**——09-06 的 `$HNGE` 被判成「单人票够不上闸」，而 Jeff 09-04 就标了 Focus，算上他正好过闸。**只看得见半边场地的计数会把真候选判出局。**
   ⚠️ **清单帖会把人数抬虚。** 单条挂 6 个以上代码的组合帖/周榜/晨报，对每只票都没给一句自己的话；09-11 剔掉 13 条这类帖后 `$HOOD` 从 5 人掉到 0。**这把尺子只能报阳性（这只票只活在清单里），不能报阴性**——表按原人数走，剔完的数当红旗列在旁边。
   每条帖挂几个代码 = `posts/*.jsonl` 那行 `tickers` 数组的长度，**从那里算，不往 `mentions.csv` 加列**。
   闸空了就报空，但要说清是样本太小还是真没人看好。
2. **已经跑完的 —— 别追。** recap/exited 占多数的。**拦 FOMO，和第 1 节一样重要。** mood 脚本报的「⚠️ 庆功不是起量」写进这一节。
3. **接下来的走势。** 大盘/板块，不带个股。**分歧比共识值钱。** ⭐ 谁写了「什么情况算我错」单独点出来。
   **⭐ 3a. 圈外主题起量** —— 直接用 mood 脚本的判定（人数 ≥3 **且**该主题代理当日 α 在 ±2% 内）。过闸的**置顶到第 3 节最前面**。
   ⛔ **不给人加权重系数。** 已验证：黄金那波和比特币那波看着 20 张票、胜率 80%，但同日同标的 α 完全相同，独立信息**只有 2 条**（n=2 符号检验最小可能 p=0.25）；同一批人同期讲的其他 547 票中位 α **−0.6%**、胜率 **43%**。**他们不是「准的人」，是在那两次里对了。** 见 `scoring/2026-09-07_theme_weight.md`。台账到 **n≥10** 才谈权重。
4. **圈内人在聊什么（非 ticker）。** 一行一个，谁说的。
5. **⭐ 墙后 vs 墙外（@jfsrev 专节）。** 他今天 Stalk/Focus/Update 了什么 · 哪些**公开区零提及** · 有没有从 Stalk 升到 Focus · 代理票和杠杆。
   **墙外是「我在看什么」，墙后是「我在做什么」。** 基线：墙后 11 只票有 7 只公开区零提及（64%）。
   ⚠️ **他的一天不按 ET 日历日过**——「明天计划」常在前一晚 22:xx ET 发。按日历日切会把最可执行的那截切掉；**按「计划簇」整块收**，跨日的在节里注明。
6. **选题候选（给 Andy 发 X 用）**：A 高收藏样本（收藏比 >0.5 或曝光 >该账号 7 日中位 5×；⚠️ **该 handle 库内 <8 帖时不出倍数、只出收藏比**——09-08 @Muninn 算出 147×，分母只有两条帖的中位；曝光与收藏**一律读 `posts/*.jsonl`**，`mentions.csv` 里的是首次抓到时的快照），每条写清**戳中什么卡点 · 我们有没有弹药 · 一句我们的角度**；只列「我们答得比他好」的。B 圈子的空白。同一卡点两条帖算一发子弹。⛔ **订阅区原话不进这一节。**
   ⚠️ **「本周最高」「全库第一」这类形容词必须跑过数才写。** 09-11 把「全天收藏第一」顺手写成「也是本周第一」，而 09-08 Muninn 那条更高。**算过的那个量可以写，没算过的更响的说法不许顺口加。**
7. **蹭位榜 + 窗口与 mood 一行。** 曝光÷回复前 5，非回复且发帖 <20 小时，附链接和距今小时数。见下面「蹭位榜与回复方向」（两班共用）。
   末尾两行：本窗口的 ET 起止 · mood 脚本那行摘要（只登记，不解读）。

✅ 09-13 起 `fetch.py` 只在裸大写词分支拦指标名（SMA EMA RS PPI MA VWAP ATR MACD PCE），带 `$` 的照认——`RS`（Reliance Steel）`SMA`（Summit Materials）`MA`（Mastercard）是真代码。⚠️ **09-12 及以前的 posts/mentions 里仍有这批假行**，跨到那几天比人数时要人工剔。撞上新的指标名写进「给 Steve」，别手改 `fetch.py`。

## 五、刷新 ticker 看板（Andy 2026-09-18 要回来的「以票为主体」阅览）

日报是营销编排视角（谁说了什么、我该发什么）；看板是交易视角（按票检索、看热点）。**两个都要。**

在送到用的同一棵临时树里、commit 之前跑：

```bash
.venv/bin/python data/content/x_watch/tools/build_board.py   # 用主树的 .venv 绝对路径
```

- `ticker_daily.csv` 随本班一起 `git add`（Excel 用的宽表，入库）；`board.html` / `board_data.json` **不提交**（各 2.5MB，未进 .gitignore）：`git add data/content/x_watch/` 之后必须跑 `git -C "$WT" reset -q -- data/content/x_watch/board.html data/content/x_watch/board_data.json`，再看 `git diff --cached --name-only` 里没有它俩。
- 发布到同一个 Artifact（URL 见 `data/content/x_watch/README.md`「📇 每日看板」节）：先 `Artifact action:"read"` 这个 url（不 read 会被拒），再 `Artifact publish url:<同上> file_path:<临时树>/data/content/x_watch/board.html label:"数据到 ET $D"`。**不 publish 不带 url**（那会新建一个 URL，Andy 收藏的那个就又停了）。
- 发布前核一眼：`board_data.json` 的 `dates` 末项必须 = `$D`。不等就是没用新数据，别发。
- Artifact 工具不可用时：日报末尾写「看板未刷新 · 原因」，不静默跳过。

---

# 睡前速报

跑在 **13:00 ET**，Andy 2AM JST 睡觉，这一班是他躺下前能动手的最后一次机会。**只做两件事，两屏以内交付。完整日报归主班，不要在这里重复它。**

## 为什么有这一班

蹭位榜是日报里**唯一会过期**的东西。实测：**52% 的蹭位候选发在 13:00 ET 之前**。这一班看到它们时只隔几小时，还能蹭；主班看到时已隔 11 小时以上，**窗口关了**。

其余内容不要在这里做——第 1 节「明天的候选」和第 3 节「走势」的原料在 **16:00–20:00 ET（占全天 21.2%）**，那时这一班还没发生，物理上拿不到。

## 一、抓（30 页就够，只覆盖半天）

```bash
cd /Users/taolezhu/Documents/AI-Trading-System
git fetch origin
S=$(TZ=America/New_York date +%F)        # ET 当日（进行中）
U=$(TZ=America/New_York date -v+1d +%F)  # ET 次日
.venv/bin/python Fluxus_Brand/ops/tools/x_watch/fetch.py --since $S --until $U --max-pages 30
```

⛔ **永远不要用 `--days`。** 理由同主班。
⚠️ 本班在 13:00 ET 跑，`$S` 这一天才过了 45%——**这是设计，不是缺陷**。主班 11.5 小时后会用同一个 ET 日期重抓全天，**按 `id` 和这份并集**。
`HTTP 402 Credits is not enough` → 写「无数据」，**不拿旧 jsonl 顶替**。`members.json` 被写成 `[]` → `git checkout origin/main -- data/content/x_watch/members.json` 恢复，**永不提交 `[]`**。

## 二、写 `data/content/x_watch/nightcap/<$S>.md` —— 两屏以内，两节

### 1. 蹭位榜（本班的正题）

曝光 ÷ max(回复,1) 前 5，**只算非回复帖**且发帖 **<8 小时**（比主班的 20 小时更严——要的是还热着的）。每行：密度 · ET 时刻 · 距今几小时 · @谁 · 曝光/回复 · 链接 · **一句话说他在讲什么**（不引原话超过一句）。

⭐ 密度高 = 一屋子人在看、没人说话。**这是给 Andy 的动作建议，不是你的动作。**

### 2. 圈外主题起量（有才写，没有就写「无」）

非美股个股的主题 —— 贵金属 · 加密 · 能源 · 债 · 外汇 —— 在本窗口内被 **≥3 个不同的人**提起。

⚠️ **表头必须写一句「速报口径：宽词表、半天窗口，不与 mood 台账比」。** 09-10 实测：速报报「债 11 人、能源 9 人」，主班 mood 脚本同一天报 fx_rates 3 人、energy 4 人——词表不同，数差三倍，读者会以为有一边算错了。**别去对齐两边的数，标清口径就够。**

**判据不是他们准，是这批人平时不讲这些，注意力从个股移开这件事本身罕见。**

⚠️ **过了人数闸还要看当日 α**：该主题代理标的（金→GLD · 币→IBIT · 能源→XLE · 债汇→TLT）当日相对 SPY 的涨跌若 **超过 ±2%**，那是**庆功不是起量**，写成「⚠️ X 人在讲 Y，但 Y 今天已经涨了 Z% —— 是复盘不是机会」。09-03 实测：11 个人讲加密，IBIT 当日 α +4.8%，全是庆功帖，T+1 IBIT −2.0% / COIN −3.8%。

⛔ **不要在这一班记 `theme_events.csv`** —— 那是主班用全天数据记的，半天数据记进去会污染台账。这里只提醒。

## 三、⛔ 这一班不做的

- ❌ 不标 stance、不写 `mentions.csv` 的 stance 列（主班做）
- ❌ **不跑 `mood_index.py`** —— 半天数据会污染基线
- ❌ 不碰 @jfsrev 订阅区（主班做，且要浏览器）
- ❌ 不写 `daily/` 下的任何文件
- ❌ 不写第 1/2/3/4/5/6 节 —— 那些的原料还没发生
- ❌ 不发帖、不回复、不点赞、不关注

---

# 蹭位榜与回复方向（两班共用）

⭐⭐ **每行下面给 2–3 个回复方向，Andy 自己挑一个写。**
Andy 2026-09-14 原话：「继续出，我每天都在看。关键是ai能够给出蹭帖的几个回复选择方向，我自己选就可以，减少摩擦。而首先我们得先有能发的专有内容（课程，系统，平台等等），这个得先有，再去蹭别人。」

每个方向一行，**三样齐才算数**：

- **角度**：一句话 —— 接他哪一点、往哪边推（补数 / 补反例 / 补失效条件 / 补一个他没问的问题）
- **挂哪份自有内容**：课程哪一课（`~/Documents/SwingMasterclass/` 的课名）· 每日复盘 · dashboard 哪一页 · `data/research/` 哪个结论。**挂不上自有内容的方向不出** —— 蹭的目的是把人带回我们的东西，不是替别人热场
- **能不能放链接**：课程 **09-25 上架前不能链接**（Andy 09-19 把发布日从 09-20 改到 09-25，$1,499 / Whop），只能用课里的观点；dashboard / Substack 已公开可链。⚠️ 仓库是 PUBLIC，课程原文不进仓库，方向里只写课名

⛔ **只给方向，不写成品回复。** 字由 Andy 写（对外永不代笔）。英文帖也只用中文写方向。
⛔ 说「我们有 X」之前**现场核实 X 存在**（grep 前端/数据文件），核不到就不许写进方向。
那一屋子没有话题的（纯链接、玩笑、生活帖）写「跳过：无可接的点」，**不硬凑**。
五行里一个方向都出不来，照实写「今天没有挂得上自有内容的蹭位」——这本身是给 Steve 的信号：弹药缺在哪。

# 送到（两班同法）

宪法「直推 main 标准动作」，临时树，**只 add `data/content/x_watch/`**（主班含 `ticker_daily.csv`，不含 `board.html` / `board_data.json`）：

```bash
export WT=$(mktemp -d)/wt-xw
git -C /Users/taolezhu/Documents/AI-Trading-System fetch origin
git -C /Users/taolezhu/Documents/AI-Trading-System worktree add "$WT" origin/main
# 在 $WT 里跑抓取/mood/写报告（.env 用 set -a; . 主树/.env; set +a 带进来）
git -C "$WT" diff --cached --name-only   # 多出来的先 restore --staged
(cd "$WT" && python3 data/content/x_watch/tools/check_mentions.py)   # 公箱自检，退出码必须 0
git -C "$WT" commit -F <消息文件> && git -C "$WT" push origin HEAD:main
git -C "$WT" log origin/main -1 --oneline  # 看到自己的 commit 才算送到
git -C /Users/taolezhu/Documents/AI-Trading-System worktree remove --force "$WT"
```

⚠️ **自检用 `check_mentions.py`，不再用 `grep '^-'`**（09-13 升机制：grep 在有 stance 回填的日子必然报红，数的是改行不是丢行）。脚本按 `(date,ticker,handle,post_id)` 比对，**丢行 / 非 stance 列被改 / 已有 stance 被改**三个失败分支在 CI 里各有注射测试。退出码非 0 → 看它列出的前 5 个键，**修掉再提交，不许绕过**。

收尾同步进主树让 Andy 点得开：`git checkout origin/main -- data/content/x_watch/daily/`（速报是 `nightcap/`）后 `git restore --staged` 同路径（**别污染主树暂存区**）。

⛔ **耐久文件里永不写占位值。** 09-11 订阅区抓取被截断时先用自造 id（`2098208312brk1` 这种）往下走，差一步就进了 main——行数/字段/schema 全绿，只有「id 必须纯数字」这种内容形状断言报得出来。**拿不到真值就重抓，不用假的先跑通。**

# 写作纪律

中文。**散文里不出现手打的数字** —— 全部从脚本产出的 jsonl 来，表格里给。原话只存不引。昨天也在的不复述。**多天比较前先确认每天覆盖是同一把尺子**；**跨天比计数一律先换成比例**。不写「值得关注」这类空话。写之前读 `.claude/skills/fable-voice/SKILL.md`。

速报的**两屏就是上限** —— 蹭位榜连回复方向一屏半，圈外主题半屏；超过说明在做主班的活。末尾一行：本窗口 ET 起止 + 条数/人数，让 Andy 知道这是半天的量。

# 禁区

- ⛔ 不用 `--days`。
- ⛔ 不发帖、不回复、不点赞、不关注。
- ⛔ 不碰任何 X List。成员变了只在日报末尾记一行。
- ⛔ 不改 roster / 手册 / 方案 / `fetch.py` / mood 的词表。有意见写日报末尾「给 Steve」。
- ⛔ 不改脚本产出的任何数字，不手打 CSV 的任何一列。
- ⛔ 只写 `data/content/x_watch/**`。

# 收工三问（日报末尾折叠块）

①这轮什么做成了、方法值不值得固化 ②哪条规矩帮了/碍了 ③下轮第一件事。

# 📌 测试窗口（09-08 · 09-09 · 09-10 · 09-11 · 09-14 —— ✅ 已结束，留作记录）

09-14 那班已出评估节（`daily/2026-09-13.md`，commit `c13279f5`）。结论：60 页不花钱；墙后 T+5 窗口内一批未满（09-07 休市），**B 账 09-20 周结补算**；A 账「用了没」蹭位榜 0/25 → **Andy 09-14 裁：继续出，加回复方向**。本节不再每班执行。

- **A. 60 页值不值** —— `minutes` 中位（>25 分钟/天 → 太贵）· 每天 `oldest_raw_utc` 是否早于 `since_et` · 五天里几次要人介入 · Andy 从蹭位榜实际回了几条（0 → 先别谈方法，谈产品）。
- **B. 墙后值不值** —— 墙后点的票 T+5 表现 vs 墙外那批 · 墙后独有的票（基线 64%）里有几只后来在公开区被别人提起 · 抓取成本。
- **C. mood 台账** —— 只报「攒到第几天、有没有 partial 行、触发过几次圈外主题起量」。**不做解读，20 个交易日之前不画基线。**
