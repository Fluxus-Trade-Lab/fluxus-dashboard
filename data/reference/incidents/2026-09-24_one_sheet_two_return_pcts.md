# 一份 Sheet 印出两个 return%：GAS 没有「数量自洽」这道闸

**日期**：2026-09-24（ops；查因 UI Claire）
**形状**：同一份源数据被两条产线用**两个不同的派生量**读持仓——两个量本该恒等，而没有任何闸检查这个恒等式，于是一次手改让两个产品各印各的数，两边都显示健康。
**同族**：
- [`2026-09-18_the_universe_changed_populations_and_nobody_logged_it.md`](2026-09-18_the_universe_changed_populations_and_nobody_logged_it.md)——共有的那句话：**闸都长在数量维，源头沿成分维被换掉时满分通过**。
- `method_read_the_upstream_quantity_not_the_symptom`（ops/linda 方法层）——共有的那句话：**被解释清楚的症状会终止对成因的追问**。

---

## 一、时间线

- **2026-09-24 15:57 JST** Andy 在会话里报症状（原话）：「每日复盘里面出现的 ytd return 计算和我们在 dashboard 上面的 return% 不一样，确认计算方式差异。另外就是我这几天有一些记录做错了就去 portfolio GAS 里面自己更改了，是 ARM 最近两笔交易里的，都在一星期内的。所以确认下是否是造成问题的原因。」
  他在同一句里给了症状**和**根因假设。假设是对的。
- **15:58 JST** UI Claire 落契约行 `e0e7f3c9`：两个公式**代数等价**，差异不出在算法。展开后逐项相同，**前提是 `currentQty == originalQty − Σtrims`**。390 笔里 1 笔破了这个前提。
- **15:59 JST** 开单 T-0924-100（ops），要的是机制不是这一次的数据修复。
- **16:05–16:13 JST** ops 用实时 GAS 数据二分（**二分，不是推断**）：
  ```
  build_pack._qty_mismatch(to_trades(gas_pull()["stockTrades"]))
  → [{"ticker": "ARM", "entry_date": "2026-09-18", "gap_pct_of_position": -13.3, ...}]   # 390 笔里 1 笔
  book_block("2026-09-23", <实时 GAS>)["return_pct"] → 136.51
  ```
  与 09-23 当天复盘 pack 印的 136.5 逐字对上；Claire 实测 dashboard 口径 135.64，把那一笔补成自洽后回到 136.51。

## 二、根因

**恒等式 `currentQty == originalQty − Σtrims` 不在任何闸的眼里。**

GAS 把两份数量各自维护：`currentQty` 是表里手记的一个数，`originalQty − Σtrims` 是从减仓记录派生的。
复盘 [`build_pack.py:534`](../../../pipeline/content/recap/build_pack.py) 读派生的那份，dashboard `PortfolioLayout.jsx:103-105` + `calculations.js:67` 读手记的那份。
两份一致时两条产线逐项相同；**一次手改只改一份，两份就分叉，而两边都没有第二个量可以对账**——每条产线内部自洽，各自的闸（`closes_stale`、`M1`、`schema_snapshot`）全绿。

再往下一层：**这是一个只有跨产线才能看见的缺陷**。任何单产线的测试都测不出它——因为单产线读一份数量，一份数量永远自洽。

## 三、影响

**已确认受影响**：
- 1 笔（ARM，入场日在管线口径下读作 2026-09-18；Claire 记作 09-17）· 390 笔中的 1 笔 = 0.26%
- 复盘 YTD return 与 dashboard return% 相差 **0.86pp**（136.51% vs 135.64%，同一份 GAS 数据、同一组 yfinance 收盘价、09-23 收盘，Claire 实测）
- 产品面：09-18 之后每一期复盘 PDF 的 book 页与 dashboard Portfolio 页对不上。**没有一期因此被拦下**——这是本条的要点。

**模式命中（未逐条确认）**：任何「Andy 直接在 GAS 里手改一行」的操作都能重造同一个分叉；`currentQty` 与减仓记录是两个可独立编辑的格子，没有任何 UI 约束它们同步。本次事件的 390 笔里只发生 1 次，不代表以前没发生过——**09-18 之前没有任何闸能报出它，所以历史发生率无从测量**，只能从今天起有读数。

**不在影响内**：`data/output/`、`data/history/` 与 dashboard 的其它页——组合数据走 GAS + localStorage，不进公开仓库。

## 四、修法

**已做（本轮，ops 边界内）**：
1. `pipeline/content/recap/build_pack.py` 新增 `_qty_mismatch()`，`book_block()` 返回 `qty_mismatch`——逐笔比 `currentQty` 与 `originalQty − Σtrims`。
   **全部减仓都算，不按 T 切窗**：`currentQty` 是活数，每一笔已记录的减仓都已从它里面扣掉，按窗口比会在任何回溯重出上凭空造出违规（一个会喊狼来了的闸等于没有闸）。
   **永不报股数**（Andy 2026-09-13「管线只做 R 和 %，不写股数和美元」）：差额报成**占原始仓位的百分比**。
2. `run.py` 新增 **Q1** 闸：`run_check` 读 `pack["book"]["qty_mismatch"]`，非空则 `ok=False`（`check` 退出码 2，`render` 在出片前停），`print_check` 与 `delivery.md` 逐笔点名 ticker + 入场日 + 差额%。
   **旧 pack 没有这个字段就保持绿**，历史期次照旧能重出。
3. `pipeline/tests/test_recap_book_qty.py` 12 条。**修之前这条测试是红的**——对 `origin/main` 跑 10 红 2 绿（2 绿是绿路径守卫，不是探测器）；按 `method_positive_controls_by_failure_mode` 造第二个方向的阳性对照（**算了但没接进 `ok`**）：`test_check_goes_red_on_a_split_row` 单独转红。
4. 端到端实跑：把 09-23 期次拷进临时 `FLUXUS_RECAP_ROOT`，用实时 GAS 重建它的 book，真跑 CLI `python3 -m pipeline.content.recap.run check --date 2026-09-23` → 打出
   `Q1 ARM (2026-09-18): ... differ by -13.3% of the position ... — recap and dashboard would print different return%`，`EXIT=2`。
   同一条命令对**未改的**原 pack 跑：Q1 行 0 条（同时出现的 16 条 I1/I2 是原 pack 早于 i1/i2 两道闸留下的既有漂移，原 `check.json` 连 `i1` 键都没有——**不是本次改动造成的**）。

**还欠什么**：
- **dashboard Portfolio 页同一检查**（页面上标出不自洽的笔）——`frontend/` 归 **UI Claire** 的白名单，ops 不代合；已开单转交。
- **GAS 端（`Interactive Portfolio Tracker/gas/Code.gs`）写入时校验**——最省事的一道，堵在源头；`pipeline/portfolio/` 归 **DATA ALEX**（TEAM.md 2026-09-22 裁），Code.gs 的归属需一次裁定；已开单。
- **本次那一笔的数据修复归 Andy**——只有他能改 Sheet。Q1 从此把它变成一条会喊的红，不再是静默分叉。

## 五、机制升级

**升级物**：`run.py` 的 **Q1 闸**（可机器判：`rep["q1"]` 非空 → `ok=False` → `render` 退 2）。这是**第 1 次**，不是三次律触发——但它升级成机制而不是一条 memory，因为根因是「没有闸」，记忆治不了没有闸。

**判据留给下一个人**：**两条产线读同一份源数据的两个派生量时，那个恒等式本身必须有一道闸。** 不是「两边都测一遍」——两边都会通过。

## 六、教训

1. **两个产品印出两个数时，先问「它们读的是同一个量吗」，再去对公式。** 本轮公式对账是必要的（它排除了算法），但结论出在数据层：公式等价 ≠ 输入相同。
2. **一个恒等式，只要没有任何代码检查它，就不是恒等式，只是一个巧合。** 它会一直成立到第一次手改。
3. **单产线的测试测不出跨产线的分叉**——每条产线读一份数量，一份数量永远自洽。缺陷在缝上，闸也得装在缝上。
4. **Andy 报症状时常常一起给了根因假设**（本次「是不是我手改造成的？」——是）。先验证他的假设，比先从零查便宜。
5. **报一个违规不等于能报出股数**：privacy 闸和数据完整性闸能同时满足——把差额报成占仓位的百分比。
