# I4 的阈值不是拍得太松，是拍到了**错的单位**

*2026-08-20 夜，数据端。起因：`DATA_RELIABILITY.md` §六.1「I4 的阈值(0.3×/3×)是拍的，攒一个月 audit_last.json 再校」。*

## 一、先量：这道闸从来没响过，也响不了

`ticker_events.csv` 有 101 个交易日、95,008 行。每日总行数对**前 20 日中位数**的比值：

| | 最小 | p01 | p05 | 中位 | p95 | p99 | 最大 |
|---|---|---|---|---|---|---|---|
| 总行数 / 前 20 日中位 | 0.63 | 0.67 | 0.72 | 1.01 | 1.82 | 2.25 | 2.28 |

96 个可检查的日子里，**0 个**落在 `[0.30, 3.0]` 之外。观测到的极端是 0.63 和 2.28；闸口是 0.30 和 3.0，比数据的实际摆幅宽出约一倍。它不是一道闸，是一句摆设。

按 p02/p98 各放宽 15% 量出来的带是 **[0.58, 2.45]**（`data/reference/i4_bands.json`）。

## 二、但真正漏掉的东西，收紧总行数也拦不住

仓库自己已经写过这个事故（`e8ac440`，2026-08-15）：**Finviz 在 2026-08-07 把 `Change` 列改名成 `Change %`**，`change_pct` 整列变 null，读这列的三个筛选器一行都没写出来，持续到 08-15 才被人发现。

那四天，`ticker_events` 的总行数完全正常：

```
session        rows  x med  旧闸(0.3/3.0)   breadth 当日涨≥4%  I7
2026-08-07      604   0.68    silent            956   VIOLATION: gainers_4pct, vol_up_gainers
2026-08-11      863   1.00    silent            530   VIOLATION: gainers_4pct, vol_up_gainers
2026-08-12      907   1.05    silent            527   VIOLATION: gainers_4pct, vol_up_gainers
2026-08-13     1005   1.17    silent            617   VIOLATION: gainers_4pct, vol_up_gainers
2026-08-14     1221   1.42    silent            511   clean
2026-08-17     1825   2.11    silent            349   clean
2026-08-18     1667   1.88    silent            320   clean
```

（`python data/research/i4_calibration_2026-08/replay.py` 复现；registry 冻结在改名日之前的 94 个 session 上。）

08-11 那天 breadth 数出 **530 只**涨幅 ≥4%，`gainers_4pct` 写了 **0 行**，总行数是中位数的 **1.00 倍**。
`is_plausible_day` 也没响：它只要求 7 个筛选器里 ≥4 个有行，那天正好 4 个。

**旧闸抓到 0/4；I7 抓到 4/4，且 08-14/17/18 三个健康日一个都不误报。**

「涨 4% 的票是 0 只」这件事本身可不可能？breadth 归档 566 个 session，`up_4pct` 最小值 **15**，低于 10 的天数 **0**。所以 `gainers_4pct` 写 0 行是 bug，不是行情。

## 三、所以单位换成**系列**（series），不是文件

每个归档的子系列（ticker_events 的 `screener`、watchlist_hits 的 `panel`、groups_archive 的 `kind`）单独定级：

- **reliable** = 出现率 ≥95% **且** 中位行数 ≥20 → 当天写 0 行 = **违规**（I7，拒 commit）
- **sparse** = 其余（`episodic_pivot` 中位 4 行、若干 preset 本来就常常空） → 空了不说话
- 每个系列还带自己的行数带（经验 p02/p98 放宽 15%），越界只报警（I4s）

用全量 101 天定出来的 5 个 reliable：`ema21_watch`(中位 96) `gainers_4pct`(180) `healthy_charts`(139) `momentum_97`(77) `vol_up_gainers`(46)。
`vcp` 中位 19 行、出现率 100%，差一行没进 reliable —— 门槛调到 15 它就进来，是个可以给 Andy 拍的旋钮。

## 四、registry 必须是**冻结的**，不能滚动重算

这一条是从 `e8ac440` 自己的教训里抄的：「a renamed-away column vanishes from the rows at exactly the moment it should scream, and only history remembers it existed」。

同样的道理对系列成立。用滚动 20 日窗口自动重算的话：08-07 报、08-11 报，然后 08-12/08-13 **不报了** —— 因为窗口里已经装进了两个空日，出现率跌破 95%，故障把基线教成了正常。冻结的 registry 四天全报。

所以 `data/reference/i4_bands.json` 跟 `schema_snapshot.json` 一样：**提交进仓库、只在人显式 `--update` 时才动**。

## 五、落地

| 文件 | 做了什么 |
|---|---|
| `pipeline/tools/calibrate_i4.py` | 新；从归档量出每档带 + 系列定级，写 `data/reference/i4_bands.json`；`--until` 可冻结任意时点 |
| `data/reference/i4_bands.json` | 新；提交的 registry（101 个 session 建的） |
| `pipeline/tools/audit_archives.py` | I4 改用量出来的带（没有就退回 0.3/3.0 并在文案里标 `default`）；新增 **I7**（reliable 系列空 = 违规）与 **I4s**（系列行数越界 = 警告） |
| `pipeline/tests/test_audit_archives.py` | +4 个测试：I7 违规 / sparse 空了不响 / 系列带警告 / 量出来的带确实被用上 |
| `pipeline/tests/test_calibrate_i4.py` | +3 个测试：定级、`--until` 冻结 vs 滚动、带的护栏 |
| `data/research/i4_calibration_2026-08/replay.py` | 事故回放，离线可复现 |

今晚在真归档上跑 `audit_archives`：**0 violations / 3 warnings**（session 2026-08-18）。两条新警告都是 08-18 的 preset：`preset:pp_count` 183 行 = 中位的 3.16×、`preset:weekly_20_gainers` **1 行** = 中位的 0.06×。后者第一晚就值得看一眼。

## 六、还没做的（留给 Andy 拍）

1. **`vcp` 要不要算 reliable**：中位 19 行 vs 门槛 20，出现率 100%。门槛改 15 就进。
2. **I7 违规要不要拒 commit**：现在会（走 §一的 plan B）。冻结回放上 0 误报、breadth 的 566 天下限 15 也撑得住，但这是第一晚，可以先降成警告观察一周。
3. **缺失的整个 session 没人查**：`2026-08-10` 是交易日，`ticker_events` 一行都没有，`universe_quality` 却有那天的行。I5 只看最新一天，中间的洞看不见。补一条 I8（覆盖率：最近 N 个 session 每个都得有行）是下一件。
4. `watchlist_hits` / `leaders_log` / `groups_archive` 现在各只有 1 / 3 / 8 天，攒够 12 天后重跑 `calibrate_i4 --update`，它们才有自己的带和系列定级。
