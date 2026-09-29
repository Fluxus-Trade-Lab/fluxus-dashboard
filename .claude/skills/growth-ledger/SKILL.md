---
name: growth-ledger
description: gary 线的增长周记账工序——采集 X 周浏览量/followers/Substack/Whop/Discord/MRR 六项，追加进 data/growth/metrics.csv 并写 data/growth/weekly/YYYY-MM-DD.md 小结，每个数都带来源与日期，量不到留空标「未测量」，永不估、永不结转装新。凡任务 type=growth_ledger、或班次 gary-growth-ledger 触发、或有人说「增长周记账 / 这周的 growth 数字记了吗 / metrics.csv 怎么填 / Whop 会员数怎么取 / discord_members 口径」都用本 skill，别重新发明采集流程或口径判据。
owner: gary
---

# growth-ledger — 增长官周记账工序

你是增长官（gary 线）的周记账班（原 growth-weekly-ledger SOP 精简版，2026-09-19 迁入守护进程；旧版取门铃/发消息/技能留痕等定时任务壳层步骤已剔除；2026-09-29 从 schedule.json 班次 `gary-growth-ledger` 的 body 迁成 skill，T-0929-34）。唯一写入区 `data/growth/`；改动按 `_worker_protocol.md` 第 5–6 步：在自己的临时树提交、推分支、算 gate，gate=none 才自合，reviewer 就等复核（合进 main 后核实 commit 真在 origin/main）。**铁口径：每个数带来源与日期；量不到留空标「未测量」，永不估、永不结转装新。**

## 流程

1. 读 `git show origin/main:data/growth/README.md`（口径）与 `metrics.csv` 上一行。
2. 采集本周值：
   - **`x_week_views`（必填，别再留空）**：读 `data/content/posts.csv`（权威版 `git show origin/main:`）本周各行 views 求和，notes 标「来源：posts.csv 聚合 · <日期>」。
   - `x_followers`：抓 Andy 的 X 公开主页 follower 数；抓不到留空标「未测量」。
   - **`substack_subs`：不抓公开页。** 08-28 已实测证伪——`/about`、`/`、`/archive` 三处公开页都不暴露订阅数（见 `data/growth/README.md` 取数 SOP）。照那份 SOP 的方法取；取不到就留空标「未测量 · 公开页不暴露（08-28 已证伪）」，不要每周重试已知不通的路。
   - **Whop（T-0922-110 起）**：在你的代码仓临时树里跑 `python3 data/growth/scripts/fetch_whop_members.py --write --date <本行日期>`（只读 key 由脚本从钥匙串 `-a fluxus -s whop-readonly-key` 读进内存；**你自己不要取 key、不 echo、不写文件**）。脚本按游标读全量 memberships/members，把 status 分布、口径 A 人数、试用与到期不续人数写进本行 notes；**`whop_members` 本列由脚本按口径 A 填**（Andy 09-22 原话「A 在档订阅付费人：18 (推荐)」：三个订阅产品、status∈active|past_due、按人去重；试用单列不计），人工盘点不再写本列；人工盘点的身份合并人头另记在 weekly/。脚本把 Whop 段追加在本行已有 notes 后面，同日重跑只替换自己那段——**先写 x_followers 等列与 notes，再跑脚本**。脚本输出「Whop key 不可用，本周空」或报错时：notes 写「Whop key 不可用，本周空」，不硬凑、不抄旧数。push 前跑 `python3 data/growth/scripts/fetch_whop_members.py --leak-check ~/.fluxus-ops-daemon`（脚本在内存里比对 key，只打印「key 命中条数」，必须为 0；非 0 就不 push、报 P0）。
   - `discord_members` / `mrr_usd`：**只抄** `data/growth/weekly/` 里最近一次人工实地盘点的数，并在 notes 标「(盘点日期)」；没有新盘点就留空。这两列的新值只能来自人在场的实地盘点。
     ⚠️ **discord_members 口径陷阱**：metrics.csv 08-24 行的 `39` 是含 9 个 bot 的数（该行 notes 自己写着「discord真人30+bot9」），KNOWLEDGE.md 权威表「取最后一个非空值」的读法会静默取到这个混口径的数。**真人口径的最新实读是 46**（`data/growth/weekly/2026-08-25-growth-diagnosis.md`）。本周填真人口径并在 notes 写死「真人口径（不含 bot）· 来源 <文件>」。
3. 追加一行到 `metrics.csv`。**每个填了值的列，notes 里必须带它的来源与日期**——稀疏表按「最后非空值」读会静默混龄。
4. 写 `data/growth/weekly/YYYY-MM-DD.md` ≤10 行：各读数 + 环比变化 + 一句判断（流量期只评流量列：发布数/views/followers；不催落地）。**每个数后面跟 `(来源 · 日期)`。**
5. **顺手核一次口径漂移**（≤3 分钟）：`data/growth/` 下有没有哪个数与权威链对不上。已知待清的两笔，本周若还没清就在小结里列出来：
   - `data/growth/weekly/2026-08-25-*.md` 里出现的 **MRR $1,572 是孤儿数**——全仓唯一出处，对不上权威链任何一环（权威链：08-24 $1,139【作废】→ 08-25 反解 $1,435【作废】→ 08-25 实读 $1,671 含取消 / $1,478 前瞻；metrics.csv 铁口径只记已测量的 **$1,052**）。
   - **Lifetime 人数差 1**：`members.csv` 里 tier=lifetime 且 status=active 是 **10** 条，而下游三处（metrics.csv 08-25 notes、`Fluxus_Brand/brain/offers.md`、paypal-reconcile.md）一致写 **9**。先判 10 里哪一条不该算，判清后把三处同步；判不清就在小结里如实列出「差 1，待人工判」（有需要用 `taskboard.py needs-andy` 转交）。
6. 全部按 `_worker_protocol.md` 第 5–6 步：在自己的临时树提交、推分支、算 gate，gate=none 才自合，reviewer 就等复核；三轮失败把内容留在汇报标「未投递」。

10:07 的每日页会读你这份小结——你写的就是 Andy 周一看到的增长栏。

## Gate（本 routine 的闸）

记账完 `python3 -c` 读回刚写的 metrics.csv 最后一行，逐列打印「值 + notes 里的来源日期」；**任何填了值却没有来源日期的列＝本次记账不合格，补齐再 push**。这道闸是脚本读回的对账，不是自述。

## 红线

不发消息、不登录任何收费平台。NOW.md 不约束你。

## 验收

- [ ] metrics.csv 已追加本周一行，x_week_views 已用 posts.csv 聚合填值
- [ ] Gate 读回检查通过：每个填值列 notes 都带来源与日期
- [ ] `data/growth/weekly/YYYY-MM-DD.md` 已写且各数带 (来源 · 日期)；口径漂移已核并如实记录
