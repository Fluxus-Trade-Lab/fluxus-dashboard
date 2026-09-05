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

## 二点五、闸的三档严重度（2026-08-28 立，来自连续五晚的事故）

**为什么有这一节**：08-24 到 08-28 五次运行挂在**四道不同的闸**上（Schema snapshot / Audit
archives I6a / Audit run ledger / 加上一次 GitHub 直接丢弃排期），每次都是**整晚一个字发不出去**。
数据每次都算对了，每次都没能出门。plan B（宁可不发也不发错）是对的，但它当时只有**两档**：
阻断，或者沉默。一周里天天触发一次不同的闸时，缺的那一档就暴露了。

| 档 | 语义 | 实现 | 什么时候用 |
|---|---|---|---|
| `block` | 不修好就不该发 | 步骤失败 → `Commit and push` skip | 会让**前端展示错数**的（schema 丢字段、归档串日期、台账证据与状态词不符）|
| **`loud`** | **发，但必须有人看见** | `--fail` + `continue-on-error: true` → **红步骤 + 注解，任务继续** | 副产物退化、覆盖不全、外部依赖降级——**主数据没坏** |
| `silent` | 只记不喊 | 写 ledger/日志，不改退出码 | 例行波动、预算内的部分覆盖 |

**判据一句话**：问「这个问题会让 Andy 早上**看到错的东西**，还是只会让他**少看到一点东西**？」
错的 → `block`；少的 → `loud`。**「少的」以前被当成「没问题」，这就是 ticker 库能冻五天没人管的原因。**

已按此归档的闸：
- `block`：audit_archives · audit_ledger（L1/L3–L6）· schema_snapshot（仅 removal）· claim_registry
- `loud`：**ticker staleness**（08-28 起，`--fail` + `continue-on-error`）· tvdatafeed 安装失败 ·
  **ticker 刷新凭证缺失**（08-28 起发 `::error`——在此之前它 `exit 0` 静默跳过了五晚）
- `silent`：Delayed-EP 归档 · 交易复盘（外部 GAS 冷启动）

⚠️ **配套铁律：失败的夜晚也要留下记录。** 到 08-28 为止，任何触发 `block` 的运行都会跳过
`Commit and push`，于是**它的 run_ledger 行随 runner 一起消失**。08-28 查「fundamentals 撞墙多久
一次」时，committed 历史里 `walled: true` **零次**——不是没发生过，是**发生的那些夜晚正是没有
commit 的夜晚**。现在有一个 `if: failure()` 的步骤只提交三个记账文件（run_ledger + 两个 audit
json），不碰 `data/output`。**台账若只记成功，它记的就不是历史。**

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

## 六、还没有的(按优先级)

0. ~~run_all.main() 端到端 smoke~~ **08-22 已建**(`pipeline/tests/test_run_all_smoke.py`):只造假网络(一个合成 yf.download+夹具 Finviz),其余全真跑进临时树,断言 breadth 四块/台账证据/必备块/审计零违规;10 秒跑完。**首跑就抓了三只真虫**:shortlist 在无归档的处女树上整块崩(已修)、审计器遇 0 行归档崩(已修)、必备块把「空集合」误判成「缺失」(语义改为键在即可)。
1. I4 的阈值(0.3×/3×)是拍的,攒一个月 audit_last.json 再校。
2. universe 行数 vs Finviz 宣称总数(adapter 现在不存那个数)。
4. **测试跑完仓库必须还是干净的**——CI 在 pytest 之后加一句 `git diff --exit-code data/history data/output`。08-23 夜间组发现 `test_quality.py::TestRequiredBlocks::test_missing_block_grades_severe` 每跑一次就把 `data/history/quality/breadth_last.csv` 的 08-19 基线行改写成近乎全 1.0(=空值率 100%,方向是让守卫**变迟钝**);根因是 `check_site(output_dir, date, history_dir=QUALITY_DIR)` 的第三个参数默认指向真仓库,测试只沙箱了第一个。origin/main 干净,但主工作树此刻就带着这个改动。事故档 `data/reference/incidents/2026-08-23_test_writes_into_the_real_archive.md`;**修法归数据端**(一行传参只堵这一个洞,建议同时上 conftest autouse fixture 或上面这句 CI 断言)。
3. ~~run_ledger 没人读~~ **08-23 已建**(`pipeline/tools/audit_ledger.py` + `pipeline/tests/test_audit_ledger.py`,10 例):台账的读者。L1 上个交易日没有行(=当晚根本没跑,任何归档检查都看不见,因为没跑的 run 哪儿都不写)、L2 闸门状态非 ok、**L3 说 ok 的闸门拿不出自己的证据**、L4 errors 非空、L5 上一场在这场消失的闸门(警告)、L6 同 session 重跑与数值漂移(只报)。**L3 就是 08-19 blackout 的形状**——拿真台账回放,当晚那行 `breadth: ok / regime_score: null / 无 enriched` 被判违规,四小时后修好的重跑行放行。月报=`--window 30`(现在只有 3 个交易日,攒够再看 429 频率)。**未接进 CI**:`weekly-data-audit.yml` 现在仍只原样打印最近 7 行,把那步换成本工具需要动 workflow(不属夜间组文件边界),等 Andy 点头。

5. **⚠️ 上面第 4 条的诉求没有落点：CI 从来不跑 pytest。**（Nighty Zac 实测，2026-09-02）
   第 4 条写的是「**CI 在 pytest 之后**加一句 `git diff --exit-code data/history data/output`」——
   而现场核对 `.github/workflows/` 全部 **6 个** workflow
   （`content-reminder` / `daily-content-threads` / `daily-data-update` / `gas-probe` /
   `premarket-digest` / `weekly-data-audit`）：**没有任何一个执行测试**，
   也没有 `.pre-commit-config.yaml`、`Makefile`、`.husky`。
   ```bash
   grep -rniE "pytest|unittest|make test|tox" .github/workflows/     # 唯一命中是 "diag(nose)d" 这个词
   ```
   **也就是说：这 1,302 条测试没有任何自动触发点，全靠会话自己想起来跑。**
   §五.4 那句「改任何归档的写入者，先跑 …，再跑 pytest」是**人的纪律，不是闸**。
   → 第 4 条要真正落地，需要的不是「加一句断言」，是**先有一个跑测试的 workflow**。
   `.github/workflows/` 不属夜间组边界，**本行只记事实不动文件**；归属见门铃（晨报 2026-09-02）。

   **本行同时销掉第 4 条的代码那半**：`test_quality.py::test_missing_block_grades_severe`
   现在显式传 `history_dir`（`test_quality.py:313`），且有一条元测试
   `test_no_test_calls_check_site_without_a_history_dir` 用 AST 扫全套测试、带具名豁免清单钉住它。
   实测：本夜在干净树上跑完 1,302 条测试后 `git status --short` 为空；
   该检查的**阳性对照已做**（往 `data/history/quality/breadth_last.csv` 注射一行，`git status` 立即报出）。

6. **⚠️ 第 5 条的缺口只关了一半：CI 现在跑测试了，但它跑不到 614 个。**（Nighty Zac 实测，2026-09-05）

   `tests.yml` 于 09-04 落地，`audit_wiring.tests_have_ci()` 从 False 变 True。
   **那是个 bool，而缺口住在集合里。** 它跑的是
   `pytest pipeline/tests -q -m "not slow"`，在一个 depth-1 的 checkout 里 ——
   按 ast 计，仓库 **1,988** 个测试函数中 **614 个不在任何自动运行里**：

   | 漏掉的原因 | 条数 | 里面有什么 |
   |---|---|---|
   | 只指了 `pipeline/tests` 一个测试根 | 607 | 整个 `tests/` 根，**其中一条是红的** |
   | `-m "not slow"` | 3 | 含 `test_run_all_end_to_end` —— 就是上面第 0 条记着「首跑抓了三只真虫」的那条 |
   | `actions/checkout` 无 `fetch-depth` = depth 1 | 4 | 唯一用真实事故数字复现 08-27 覆盖事故的四条 |

   那次运行自己说了 —— `1327 passed, 4 skipped, 3 deselected`，然后 exit 0。
   **钉着我们最严重那次数据事故的检查，不在我们读它绿的那次运行里。**

   被漏掉的根里那条红的是 `tests/test_no_naive_clock.py`，
   自 `6f66f5f9`（2026-08-27 16:18 JST）起红到今天（**8 天 12 小时**，日历日跨 9 天；父提交 `494f4689` 绿，二分出来的）。
   事故档 [`2026-09-05_the_green_run_did_not_run_them.md`](incidents/2026-09-05_the_green_run_did_not_run_them.md)。

   **已建**：`pipeline/tools/audit_ci_test_coverage.py`（+41 条测试，commit `aabf4d98`），
   把那个 bool 换成集合，按 `audit_wiring` 的棘轮形状声明今天的 614 条（带 owner／理由／日期），
   今天绿、任一变化就红；整工具的阳性对照＝喂一个修好的 workflow 后 excluded 归零且三条 T2 全响。
   它自己无自动触发，已登记进 `audit_wiring.KNOWN_UNWIRED`。

   **仍欠**（四条都要动 `.github/workflows/tests.yml`，不属夜间组边界）：
   `fetch-depth: 0` · 目标加 `tests` · slow 另开 job · 把本工具挂进 `audit_wiring (reported)` 旁边。
   ⚠️ **顺序**：先合修复分支 `auto/night-20260905-805da3-fbclock`（`f0899fac`，修那条红的），再改 workflow ——
   反过来 CI 首日就红。实测：修复分支上 `pipeline/tests + tests`（除 `tests/gex`，本机缺 jinja2/ib_async）
   **2004 passed / 6 skipped 全绿**；`origin/main` 上单跑 `tests` 是 **1 failed / 528 passed**。

7. **⚠️ 归档能自证自相矛盾，而此前没有任何闸在看这条。**（Nighty Zac 实测，2026-09-06）

   `ticker_events.csv` 的同一天同一只票常被多个筛子同时记下 —— 归档里有 **72,189** 个
   这样的「字段 × 日期 × 票」可比组。它们来自同一份当日快照，**在物理上必须相等**。
   这条恒等式的价值：**它不需要任何外部真值**。计数类检查（行数够不够、字段缺不缺）
   对一份内部自相矛盾的快照**全部是绿的**（§六.5 那条与 `pitfall_having_a_row_is_not_having_data` 同形）。

   实测有**两天**不等，两种不同的坏法：

   | 日期 | 打架的 (字段,票) | 占当日可比 | 机制 |
   |---|---|---|---|
   | 2026-08-17 | 78 | 6.7% | `65bbb080`「manual pipeline run 2026-08-17 **(08-14 bars)**」→ `e2554467` 的预设回填按 git 快照逐日读，该日 604 行 `preset:*` 携带 08-14 读数。**7/7** 有 08-14 对照的票逐位相等 |
   | 2026-08-14 | 12 | 2.4% | Finviz 08-07 改名 `Change`→`Change %`（`e8ac440e`），08-07~08-13 三个 gainers 筛子**零行**；**08-14 是复活第一天**，当日 `gainers_4pct` 中位 volume = **987 股**，110 个交易日里的最小值，比次低那天小 **290 倍** |

   **08-14 那条 `change_pct` 看不见，只有 `volume` 看得见** —— 那次修复盯的是大声死掉的那一列，
   旁边安静退化的那一列没有人验收。**空值检查看不见错值。**

   **已建**：`pipeline/tools/audit_event_agreement.py`（+21 条测试，6 个变异体全部被杀，commit `2793493d`）。
   查四个跨筛子必须相等的字段 `change_pct` `volume` `sector` `atr_ext`
   （后两个全库 26,108 / 18,558 例可比、**0 例不一致**，是干净对照）；
   明确**不查** `group`(28.5% 分歧) 与 `rel_volume`(42.4%) —— 它们的分歧散布在每一个日期上，
   是定义不同不是快照坏了，放进来闸会天天红然后被人学会跳过。棘轮形状，两天已具名声明，E2 逼人修好后删声明。
   ⚠️ 第一版只查 `change_pct` 时有 **3 天（08-11/12/13）完全看不见**，扩到四字段后盲区 **0/114** ——
   闸自己报覆盖面，因为「有闸」之后还得问「盖住了多少」。

   **仍欠（归 DATA ALEX，本线不碰 `data/history/`）**：①重算或撤下 08-17 的 604 行 `preset:*`；
   ②重算或撤下 08-14 gainers 家族的 `volume`，并判**当天的成员资格是否也受影响**
   （`vol_up_gainers` 的入选含 `rel_volume ≥ 1.5`，若快照是盘前的，那天进榜的是谁也可疑）；
   ③真正的生产接线 = `pipeline/screeners/ticker_events.py` 写完归档后自查一次
   （现在只挂在 `pipeline/tests` 里靠 tests.yml 执行，`audit_wiring` 因此仍记 known-unwired）。
   事故档 [`2026-09-06_two_days_the_archive_contradicts_itself.md`](incidents/2026-09-06_two_days_the_archive_contradicts_itself.md)。
