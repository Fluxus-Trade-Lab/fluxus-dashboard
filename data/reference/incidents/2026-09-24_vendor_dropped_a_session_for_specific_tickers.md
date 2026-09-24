# 2026-09-24 · Yahoo 对少数活跃票丢了 2026-09-22 这一场，闸从两个不同方向抓到了它

**日期**：2026-09-24（alex）
**形状**：厂商（yfinance/Yahoo）对一批**真实交易、未停牌**的票，在某一个交易日的日线里完全没有这一场；
本地 K 线库据此做「回退到该票自己上一根 bar」的容错，把一个真实的 1 日 vs 归档比对，
悄悄变成了一个 2 日累计 vs 归档比对，两条独立的闸（跨厂商比对、EP 计数器绝对重算）各自在
不知道对方的情况下报了红。
**同族**：`2026-09-01_vendor_dropped_a_completed_session.md`（同一形状的第 1 次，SPY/AAPL/MSFT
等 18/18 全中，那次是 `Close=NaN` 而不是整行缺失）；`pipeline/tools/audit_calendar_gaps.py`
（该次事故新增的闸，本次事故命中它的 WARN C1，见下）。

---

## 一、时间线（UTC）

- **2026-09-22 22:03–22:27**：`daily-data-update.yml` workflow_dispatch 运行 `35790198216`。
  `pipeline.tickers.ticker_data_fetcher` 对约 700 只票发起抓取，Yahoo 对绝大多数请求返回
  `YFRateLimitError`；防御性的「no-bars skip」正确跳过了写盘（"no-bars skips (file untouched)"，
  日志列出约 210 只票，含 ACMR/AMBA/MXL/ANET/GPRK/CRD-B 等）。
- **2026-09-23 22:59–23:23**：run `35931311680`。限流缓解，43 只票的 `data/output/tickers/*.json`
  被刷新，含 ACMR/AMBA/MXL（拿到 2026-09-23 的新 bar）。同晚 `delayed_ep_scan --archive`
  用**当时的本地 K 线库**（仍缺这些票的 09-22 bar）写入 `delayed_ep_log.csv` 的 09-23 场次，
  26 行的 `days_since` 因此比日历少 1。
- **2026-09-24 01:13 UTC**：`tests.yml` run `35941983930` 红，三个测试失败（`test_audit_events_vs_bars`
  一个、`test_audit_progress` 两个）。
- **2026-09-24（本次，alex）**：分诊、复现、根因确认、修复。**二分，不是推断**：
  ```
  python3 -m pipeline.tools.failure_class --run-id 35790198216   # → C_gate（首次误判，见下）
  python3 -m pipeline.tools.audit_calendar_gaps --days 10        # → WARN C1 2026-09-22: absent for 2/8 (25%)
  ```
  `failure_class` 把这次归成 C_gate（"抓取正常，是下游的闸不让发"）——**这是误判**，
  真实原因是限流（B_vendor 的一种），不是下游质量闸拦截；`gh run download` 也证实这一点：
  该 run 没有产出任何 `data-output-*` artifact 可供恢复，因为限流当晚根本没有"更好的数据"
  被丢弃，防御性跳过本身就是当晚能拿到的最优结果。

## 二、根因

**`pipeline/tools/audit_events_vs_bars.py::_bar_pct` 的"回退到该票自己上一根 bar"容错，
无法区分"真停牌"和"厂商在一个正常交易日漏发了这只票的 K 线"——两者在本地存量看来长得一模一样。**

- 证据链（三种独立取数路径一致）：`yf.Ticker(t).history(period='2y', auto_adjust=True)`、
  `yf.Ticker(t).history(..., auto_adjust=False)`、`yf.download(t, ...)` 对 ACMR/AMBA/MXL/ANET
  在 2026-09-22 均**完全没有该日的索引行**（不是 `test_the_previous_close_comes_from_the_tickers_own_last_bar`
  假设的"停牌"场景那种"有索引槽、值为空"）。
- 反证"未停牌"：`data/history/ticker_events.csv` 里 ACMR 与 MXL 在 2026-09-22 当天**确实**
  出现在 Finviz 的 `gainers_4pct` / `momentum_97` 等筛子快照里，change_pct 与量都是正常值——
  独立厂商证明这两只票那天真的在正常交易。
- `_bar_pct` 于是把 2026-09-23 的前收错配成 2026-09-21（跳过了缺失的 09-22），
  算出的是两日累计涨幅，与归档里 09-23 当天的 1 日 change_pct 自然对不上。
- `delayed_ep_scan` 的 `days_since` 计数器同样吃**同一份**本地 K 线库（docstring 原话：
  `days_since = len(post)` 是"EP 那根之后帧里有几根 bar"）——缺一根 bar，计数器永久少 1，
  这不是 EP 扫描器的逻辑错，是它的输入本身有洞（`audit_events_vs_bars.py` 文档里明写的
  "盲区 4"：本地 K 线库自己可能是坏的，责任会被闸误推给归档）。
- `pipeline/tools/audit_calendar_gaps.py`（2026-09-01 那次事故新增的闸，专门测"厂商是不是
  丢了一整场"）当场确认：2026-09-22 对样本 8 只票里 2 只（25%）缺失，判 **WARN**（"零星，读作
  停牌/未上市"）——它的判据本来就设计成"稀疏缺失不触发 BAD"，因为它当时假设稀疏缺失=停牌。
  **这次事故说明这个假设不总成立**：稀疏缺失也可能是活跃票被限流/厂商抽样漏发。

## 三、影响

**已确认受影响**（现场量过）：
- `data/output/tickers/{ACMR,AMBA,MXL}.json` 缺 2026-09-22 bar，导致
  `test_audit_events_vs_bars.py::test_the_real_archive_is_clean_...` 判红（2026-09-23 匹配率
  21/24=87.5%，判定线 0.90）。
- `data/history/delayed_ep_log.csv` 里 2026-09-23 场次 **26 行**（26 只票）的 `days_since`
  比正确值少 1，含 1 行因此被误判为落在扫描窗口内（GPRK，修正后 `days_since=16 > --max-days 15`，
  本应是"ghost"行，本不该被写入归档）。
- 命令：`python3 -m pipeline.tools.audit_calendar_gaps --days 10` 复现 WARN；
  `python3 -c "from pipeline.tools import audit_events_vs_bars as A; print(A.audit()['bad'])"`
  复现 `{'2026-09-23': ...}`。

**模式命中、未逐一确认**：
- 2026-09-22 全库限流当晚约 210 只票被"no-bars skip"，这些票的本地 K 线库此后可能还缺
  09-22（部分已在 09-23 那晚的部分刷新中补齐）。本次只逐一核实并修复了造成 CI 红的
  4 只票（ACMR/AMBA/MXL 的 change_pct 恒等式 + GPRK 等 26 只的 days_since 计数器）；
  其余票是否还缺 09-22、是否会在未来某天造成新的 CI 红，**没有逐一核实**，留给日常
  `audit_calendar_gaps` / `audit_events_vs_bars` 巡检继续抓。

## 四、修法

已做（本次 commit，未来引用见 `git log` 里的 sha）：
1. `pipeline/tickers/ticker_data_fetcher.py`：`fetch_ohlc_and_technicals` 的 `tk.history()`
   调用加 `repair=True`（yfinance 官方文档 `advanced/price_repair`，默认关闭）——
   yfinance 用分钟/小时线重建被厂商丢掉的日线 bar。**验证**：对 ACMR/AMBA/MXL/ANET 加
   `repair=True` 后四只票都拿回了 2026-09-22 的重建 bar；重建值与归档里独立厂商
   （Finviz）记的 change_pct 核对，三只(ACMR/AMBA/MXL) 全部落在容差 0.005 内
   （最大偏差 0.0041）。这条测试**改之前是红的**：`pytest pipeline/tests/test_audit_events_vs_bars.py::test_the_real_archive_is_clean_and_the_gap_to_the_frozen_bad_days_is_wide` 改之前失败、改之后通过。
2. `data/output/tickers/{ACMR,AMBA,MXL}.json`：手工补入 repair 重建出的 2026-09-22 bar
   （对齐 `ohlc_2y`/`ohlc_1y` 两个数组）。
3. `data/history/delayed_ep_log.csv`：26 行 2026-09-23 场次的 `days_since` 各 +1，改成
   `_sessions_between(ep_date, as_of)` 应有的日历值（纯日期算术，不依赖任何价格数据，
   无歧义）。改之前 `test_real_archive_ghost_rows_should_have_been_outside_the_scan_window`
   与 `test_real_archive_has_exactly_these_five_violations` 均失败，改之后通过。

**欠条（没做的，交给谁）**：
- 上面"模式命中、未逐一确认"那约 210 只票，没有逐一核实本地 K 线库是否还缺 09-22——
  归 alex 日常巡检（`morning_check` / `failure_triage`），不在本次 CI 修复范围内现场核完。
- `audit_calendar_gaps.py` 的 C1 判据（稀疏缺失=WARN、系统性缺失=BAD）本次被证明有盲区：
  一只活跃票的稀疏缺失不该被自动读作"停牌"。是否要加一条"用归档自己的 Finviz 行反证
  该票当天是否真的停牌"的判据，没有在本次动手改——那是给 `audit_calendar_gaps.py` 的
  一个新能力，需要单独设计与测试，归 alex 但不在本单范围内。
- `pipeline/tickers/run_tickers.py:195`（benchmark 独立的 1y history 调用）与
  `pipeline/content/recap/visual.py:192`（分钟线调用）没有同步加 `repair=True`——
  它们不是本次两个失败测试的输入源，不在本单范围内改动。

## 五、机制升级

**这是"厂商丢一整场"这个形状第 2 次出现**（第 1 次 2026-09-01，`Close=NaN` 而非整行缺失；
本次是整行缺失且发生在"停牌容错"逻辑的盲区里）。**尚未到三次律的机制升级门槛**，
但两次事故已经共享一个具体教训：`_bar_pct` 式"回退到该票自己上一根 bar"的容错，
在"厂商漏发"和"真停牌"之间没有分辨率。第 3 次出现同一形状时，**必须**把这个判据
升级为机制（例如：回退超过 1 个交易日时，交叉核对归档里该票在缺口日是否有独立厂商记录，
有则不判"停牌"，转而标记"厂商洞"并从 change_pct 恒等式里排除该 ticker-day 而不是
静默接受错配的多日回报）。

## 六、教训

- 一个"停牌容错"逻辑，测过"真停牌"这一种情况，就足够正确吗？—— 它默认了"本地库缺一天
  = 那天没交易"，这个默认在厂商丢场次时是假的，而且从**本地数据本身看不出区别**。
- 归档（`ticker_events.csv`/`delayed_ep_log.csv`）比本地 K 线快照更可信吗？—— 本次两条
  归档都是"事后被闸冤枉"的一方：change_pct 归档是对的，是 K 线快照缺了一天；
  `days_since` 归档写错了，但错的原因也是 K 线快照缺了一天，不是归档自己的逻辑错。
- `failure_class` 的分诊结论要不要直接采信？—— 不要。本次它把限流误判成 C_gate，
  按它的建议去下载 artifact 会扑空（因为限流当晚没有"更好的数据"被拦下）；
  分诊结论要用独立证据（`audit_calendar_gaps`、跨厂商核对）复核，尤其当它建议"去 GitHub
  下载 artifact"时，先确认那次 run 到底有没有产出 artifact。
