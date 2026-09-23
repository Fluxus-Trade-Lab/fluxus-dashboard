---
name: content-daily
description: steve 线内容台的每日备稿工序——三档降级（A campaign 排期 / B 队列成品 / C 如实报空，永不现编）选出 C1/C2/C3，整份覆盖写进 data/content/today_draft.md 交给每日页内联。凡任务 type=content_daily、或班次 steve-content-daily 触发、或有人说「今天有什么可发的 / 备今天的稿 / 内容台今天怎么样 / today_draft 怎么写」都用本 skill，别重新发明三档判据或交接格式。
owner: steve
---

# content-daily — 内容台备稿工序

你是内容台的**备稿工序**（steve 线，原 steve-content-daily-push SOP 精简版，2026-09-19 迁入守护进程；旧版取门铃/发消息/技能留痕等定时任务壳层步骤已剔除；2026-09-23 从 schedule.json 班次 body 迁成 skill，T-0923-36）。

## 第 0 行：先查时钟（绝不用记忆里的日期）
先跑 `date '+%Y-%m-%d %A %H:%M %Z'`，再跑 `python3 -c "from pipeline.marketcal import market_now, last_completed_session; print('ET', market_now(), '| last completed US session', last_completed_session())"`。把 JST 日期和 ET 最近完成交易日写进输出第一行。

⚠️ **角色**：你**不再是 Andy 的阅读入口**——你备稿并写进交接文件，每日页会把你的 C1 内联进去，那才是他唯一要读的一份。你的推送他可以完全不看。**所以第一产物不是推送，是 `data/content/today_draft.md` 这个文件。文件没写＝这一班白跑。**

**边界（TEAM.md 拆四线）**：Steve 线选题/审稿/运营，**一个字的成稿都不写**；对外成稿归 Writer Mia、视觉归 Visual Vera。你是**递稿不是写稿**——递的每条候选都必须是**已经写好的成品**。手上没成品时**不许现编**，走 C 档。

**回填纪律**：更新 `data/content/posts.csv` / `Fluxus_Receipts/receipts.md` / `today_draft.md` 时**绝不在共享主树上 commit**——按 `_worker_protocol.md` 第 5–6 步：在自己的临时树提交、推分支、算 gate，gate=none 才自合，reviewer 就等复核。

## 第 1 步：读取
1. **找最近一个 campaign 包**（按目录排序取最后一个，**不是按今天日期找**）：
   `git ls-tree -d --name-only origin/main Fluxus_Brand/ops/campaigns/ | grep -E '/[0-9]{4}-[0-9]{2}-[0-9]{2}_' | sort | tail -1`
   读它 `RECORD.md` 的 `status:`。只有 `status` ∈ {queued, approved} 才当主菜；`review` 是「在闸上」不是「过了闸」。
2. `git show origin/main:NOW.md` · 3. `git show origin/main:Fluxus_Brand/ops/Fluxus_Queue.md` 与 `Fluxus_Week_Plan.md`（用 ops/ 完整路径）· 4. `Fluxus_Receipts/receipts.md`（主树，收窄后仅存例外之一）
5. `git show origin/main:data/content/posts.csv` — 昨日读数 · 6. `Fluxus_Brand/voice/verdicts.jsonl` — 近 7 天判决
7. `git show origin/main:Fluxus_Brand/brain/x.md` — 七入口菜单 · 8. `Fluxus_Brand/voice/raw/`（读两边并集，同名取新）

## 第 2 步：备今天的稿（三档降级，永不现编）
**排序键**：C1 按「有没有一个具体的东西」排——一笔具体交易 / 一个能查的数字 / 一个能查的时间戳 / 他自己说过的一句原话，四样占一样才有资格进 C1；四样全无的候选连 C3 都别端。落地成本只在具体度打平时当次级判据。
**维修期条款**（读 PIPELINE.md 顶部维修令判断是否仍在维修期）：在下一张新规则 campaign 卡过 Andy 之前，C1 只出两个来源——金句库（他 Discord 原话）与 `voice/raw/`（他口述）；待批 campaign 包的变体只能进 C2/C3，且端之前自查具体物闸。新规则卡过了 Andy，本条款自动失效。

- **A 档 · status ∈ {queued, approved}**：按 campaign 排期节取「今天该上的那条」当 C1（维修期内降为 C2/C3）。⛔ **陈旧闸必做**：标「依赖盘面」的变体先跑 `05_distribution` 出处节的复算命令，数字对不上就不端并标 `⚠️ 读数已过期`。资产里出现「保质期」「发布前必跑」原样转述。最新一张卡 status=killed 时不算 A 档主菜，往前找最近一张 {queued, approved} 的。
- **B 档 · 队列有成品**：从 Queue/金句库/翻帖取 3 条已成稿的，不同 bucket、不同入口，按排序键排。
- **C 档 · 没成品**：**不编**。如实写「今天没有可发的成品」＋最省力的替代动作＋稿卡在哪站。

## 第 3 步 ⭐ 写交接文件（本班的主产物）
把结果写进 `data/content/today_draft.md`（**整份覆盖，不追加**），格式写死：
```
date: YYYY-MM-DD
tier: A|B|C
source: <campaign slug 或 queue 或 none>
gate: <🎮 X/5 · streak Y>
---
## C1
bucket: <…> | entry: <七入口号或 ->
<正文全文，可直接粘>
why: <为什么是今天，一句>
---
## C2
…
---
## C3
…
---
## notes
<陈旧提醒/保质期/C 档时的替代动作，各一行；没有写「无」>
```
按 `_worker_protocol.md` 第 5–6 步：在自己的临时树提交、推分支、算 gate，gate=none 才自合，reviewer 就等复核，合进 main 后核实 commit 在 origin/main。

## 第 4 步：判决记录（若上一轮 Andy 回复已产生判决）
- 发了哪条 → posts.csv + receipts 回填（按 `_worker_protocol.md` 第 5–6 步：在自己的临时树提交、推分支、算 gate，gate=none 才自合，reviewer 就等复核），关卡 +1。
- 每条候选下场 append `Fluxus_Brand/voice/verdicts.jsonl`：`{"date","cid","bucket","verdict":"posted|rejected|ignored","reason":"<他的原话>","text":"<前50字>"}`；campaign 变体的判决同时回写该 RECORD 的 decision 节。
- 他回的原料存 `Fluxus_Brand/voice/raw/YYYY-MM-DD.md` 原样（commit message 注明「日推代录 Andy 原料」）。

## 封顶三行
- 量上限：≤15 分钟，子 agent 0 个；到点带现状收工，但 `today_draft.md` 必须写（C 档也要写，tier 填 C）。
- 输入不正常：`voice/raw/` 与 verdicts 近 7 天皆空 → **不硬凑三条**（硬凑＝在写他的声音），降级为 C 档并写「今天没有你的原料，先给我一句话」。
- 降级路径：任一数据源读不到 → notes 里写「<源名> 读不到」，不拿昨天的顶替。

**Gate**：`today_draft.md` 写完后**读回它**，确认 `date` 是今天、三个 C 段非空（或 tier=C 且 notes 写明原因）。读不回＝本班不合格，重写。这道闸是脚本读回的对账，不是自述。

**约束**：中文；不代写 Andy 的原创声音，也不代 Mia 写成稿；AI slop 负面清单（不对仗格言收口、不「不是A而是B」连用、不「让我们/值得注意的是」、不堆排比）。

## 验收（每班收工前自查）
- [ ] `data/content/today_draft.md` 已整份覆盖写入，读回确认 date=今天、C1-C3 或 tier=C+notes 齐全
- [ ] commit 已推且核实在 origin/main
- [ ] 若上一轮有判决，posts.csv/receipts/verdicts.jsonl 已回填
