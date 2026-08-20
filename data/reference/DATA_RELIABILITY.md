# 数据层的可靠性机制（data reliability / data quality engineering）

*2026-08-19，Andy：「这在数据处理层面叫什么？我们有没有已经创立了数据维护的机制，保证数据的干净，plan b 等等。如果没有，需要设计一套，实施。现在这类小毛病太多了，还有定时清洗维护。」*

业内叫法：**data reliability engineering / data quality gates / data observability**；口语 data plumbing。三件事：**契约**（每个文件长什么样、谁写谁读——`DATA_CONTRACTS.md`）、**闸门**（写之前拒掉坏数据）、**巡检**（写之后定期重读整套归档）。我们之前有前两件的零件、没有第三件，也没有把零件连成一条线。这份文档是那条线。

## 一、一次 cron 的生命周期（每一层守什么）

```
[时钟] market_now(ET) ─ 交易日 04:00–16:15 拒跑(FORCE_INTRADAY_RUN 才放)      ← 08-19 加
   │   所有归档行的 session 标签 = last_completed_session(),一次算,处处用      ← 08-19 统一(breadth 原用 last_trading_day)
[抓取] Finviz 主 · yfinance 备
   │   bar_consistency:过期 K 线 / 拆股尺度 → 该票派生列置空、不发假数         (08-14)
   │   429 四轮重试 + stale 单补前歇 30 s                                        ← 08-19
   │   fundamentals:40 连败=撞墙,提前停、不打时间戳                            (08-18)
[写输出] universe.json
   │   quality.py:每列缺失率对自己的 20 天基线;severe → 整份不写,昨天的留着   (08-09)
   │   sparse-by-design 白名单(稀疏是构造使然的列不报警)
   └ breadth_archive:check_quality(池子大小、缺失率、pct200 跳变、**spx_close 与上一交易日相同=过期 K 线拒收** ← 08-19)
   └ ticker_events:is_plausible_day(行数下限、≥4 个筛选器、momentum_97 对滚动中位数的倍数);预设行在核心行判定之后再加 ← 08-19
   └ baskets:按日期合并,不再"拒收更短的响应"                                 (08-18)
   └ 按交易日幂等:同一 session 重跑 = 覆盖不是追加(watchlist_hits / leaders_log / groups_archive / ticker_events)
[巡检] audit_archives(I1–I5,见下)→ 有违规 → **job 失败 → 不 commit**          ← 08-19
[发布] commit + push(rebase 重试 ×3)→ Vercel
[通知] Discord 成败;周六 weekly-data-audit 报告                               ← 08-19
```

**Plan B 就是"不 commit"**:main 上永远是上一份通过闸门的数据,Vercel 跟 main。universe/breadth 自己还有第二层 plan B(severe 时服务上一行)。

## 二、归档不变量(`pipeline/tools/audit_archives.py`)

对 `data/history/*.csv` 每晚 commit 前、每周六整套重读:

| 不变量 | 含义 | 违反时 |
|---|---|---|
| I1 | date 是真实交易日,且 ≤ 最近完成的 session | **违规**(拒 commit;`--repair` 删行) |
| I2 | 主键无重复(date[+ticker+panel…]) | **违规**(`--repair` 留最后一行) |
| I3 | breadth 的 spx_close 不与上一交易日相同 | **违规**(`--repair` 删行) |
| I4 | 事件类归档每日行数在滚动中位数的 [0.3×, 3×] 内 | 警告(半截抓取 / 坏富集的签名,人看) |
| I5 | 每晚写的归档最新 session = 最近完成的 session | 警告(某个写入者悄悄停了) |

首跑就逮到真货:08-19 盘前误跑写进的 `2026-08-19` 行同时触发 I1 + I3。

## 三、谁来跑

| 频率 | 什么 | 在哪 |
|---|---|---|
| 每晚(cron 内) | 所有闸门 + audit_archives(失败=不 commit) | `daily-data-update.yml` |
| 每周六 22:00 JST | audit + universe_quality 近 7 天 + 近 7 天 cron 成败 → Discord | `weekly-data-audit.yml` |
| 人工 | `--repair`(先看 .bak)、backfill 工具、`oratnek_diff`/`scanner_event_study` 这类研究 | 本地 |

## 四、手工操作的规矩

1. 重跑 cron 只在 **16:30 ET → 次日 04:00 ET**(JST 05:30–17:00);pipeline 自己会拒,别 FORCE。
2. 共享工作树上**不 stash**;验 HEAD 去 `scratchpad/wt-main`。
3. 更新本地数据只用 `git fetch && git checkout origin/main -- data/output data/history`。
4. 改任何归档的写入者,先跑 `python -m pipeline.tools.audit_archives`,再跑 `pytest pipeline/tests`。
5. 新归档 = 在 `audit_archives.ARCHIVES` 登记一行(date 列、主键、是否算行数、是否每晚)。

## 五、08-19 晚补齐的三件

- **运行台账** `data/history/run_ledger.jsonl`(`pipeline/run_ledger.py`):每次 run 一行——session、起止 UTC、代码 sha、触发方式、每个闸门的判定(universe_quality 状态/缺 K 线数/stale 数、breadth stale 与分数、ticker_events、fundamentals、watchlist 各格计数、site_quality、各筛选器计数)、错误。同一 session 重跑 = 两行(都发生过)。周报读最近 7 行。
- **Schema 快照** `data/reference/schema_snapshot.json`(`pipeline/tools/schema_snapshot.py`):26 个 output 文件每层的字段集;cron 里 `--check` 只报不拦,改动在 DATA_CONTRACTS 写明后 `--update` 接受。
- **对账 I6**(在 audit_archives 里):watchlist.json 各格 count == watchlist_hits 行数;七个筛选器 JSON 的行数 == ticker_events 当日行数;breadth universe_size ≈ universe.json 行数。前两条不等 = 违规(两个写入者对不上)。

## 六点五、事故复盘

严重事故做成 case study 存 `data/reference/incidents/`;首篇 [2026-08-19_breadth_blackout.md](incidents/2026-08-19_breadth_blackout.md)(else 重绑、四道闸为何都没拦、五条行为规则)。新事故照它的结构写:影响/时间线/五个为什么/防线对根因/行为规则。

## 五点五、跨会话交接:问被留下,答被丢掉(2026-08-20 发现)

数据的闸门齐了,**交接**没有闸门。一次完整的失败链,08-20:

1. 数据端某会话写了 `docs/plans/2026-08-20-shortlist-design.md`,征求前端意见,然后**会话结束**。
2. 前端会话写了意见 `docs/plans/2026-08-20-shortlist-design.frontend-review.md`,commit `39a2def`,**没 push**。
3. 它想把意见发回去,但收信会话已经不在了(`ListAgents` 里点不到),于是**群发给三个不相干的会话**,三个都不是这件事的主人。
4. 与此同时 Short List 引擎 `9ca7037` **已经合进 origin/main**。

**这条链的形状是不对称的:问活下来了,答没有。** 方案本体在 `origin/main` 上(87012d0),意见只存在于一台机器的本地 commit 和三份会掉的会话记录里。`DATA_CONTRACTS` §七 就是为这件事设的耐久信道("跨会话消息会丢,2026-08-17 就丢过一封"),而这次**没人往里写**——§七 至今只有 08-17 那一条,还全是 ✅。

**已经付出的代价(核过,不是推测)**:

- 意见里最急的一条(C:空席三种成因要 `seat.empty_reason: not_measured|none_found|all_excluded` + `excluded_n`,说"schema 定稿前塞进去")**到得比代码晚**。已上线的 `pipeline/screeners/name_cards.py:193` 空席只发 `{"seat", "ticker": None, "why": <中文一句话>}`;`why` 是给人看的字符串,页面没法可靠地按它分支,`excluded_n` 根本不存在。全仓 grep `empty_reason|excluded_n|all_excluded|none_found|not_measured` = 0 命中。
- 顺带查出的第二件(与交接无关,但同一次核对里发现):`name_cards.py:211` 的 `entry` 席在没有 EP 时回落到**「第一波(4%×ATR≤4×RS新高)」**,而同一晚的研究 `72d79eb` / `data/research/scanner_validation_2026-08/b4_gates.md` 测出这个叠加是 **NULL**(样本砍 35–47%、中位一个都没抬)。这不等于该席坏了——挑一个名字填席位比"该组能跑赢基准"弱得多——但**选人规则和刚测完的结论对不上,值得复看**。

**建议交给 data plumbing 的三条不变量**(和 I1–I6 同一风格,都是可机器判的):

| | 含义 | 违反时 |
|---|---|---|
| H1 | `docs/plans/*.md` 若有 `*.frontend-review.md` 兄弟文件,两个都必须在 `origin/main` 上 | 违规(答没送到) |
| H2 | 计划文档里点名"schema 定稿前要加"的字段,必须能在 `schema_snapshot.json` 里找到,或在 `DATA_CONTRACTS` §七/§八 有一行未结的记录 | 违规(要求蒸发了) |
| H3 | 任何工作树上有**未 push** 且早于 N 小时的本地 commit | 警告(活儿卡在一个可能已经死掉的会话里) |

H3 最便宜也最通用——这次的意见就是被它逮的那个形状。H1/H2 要不要做取决于 `docs/plans/` 是不是长期信道。

## 六、还没有的(按优先级)

0. **run_all.main() 端到端 smoke**(小夹具宇宙跑全链、断言输出块齐全)——08-19 breadth 全黑暴露的最大盲区,编排器 900 行零测试。
1. I4 的阈值(0.3×/3×)是拍的,攒一个月 audit_last.json 再校。
2. universe 行数 vs Finviz 宣称总数(adapter 现在不存那个数)。
3. run_ledger 攒满一个月后:429 频率、各闸触发频率的月报。
4. 交接不变量 H1–H3(见 §五点五)——**新增 08-20**,目前一条都没有。
