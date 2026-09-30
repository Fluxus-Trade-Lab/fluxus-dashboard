# 把两场行情的计数相减，报成「两个写入端不一致」

`audit_archives` I6b / I6c · 2026-10-01 · linda（T-1001-30）

09-29 那轮（[`audit_calendar_gaps_threshold_2026-09-29.md`](audit_calendar_gaps_threshold_2026-09-29.md)）
修完 `check()` 与 `reconcile()` 在边界上互相打脸之后，末行留的下一件事是：
**把「两个函数不许对同一件事给相反答案」拿去问其余的闸。** 今晨先查，没有先动手。

## 一、先把「该问谁」缩到 2 个

按名字找共享阈值（20 个 `audit_*` 模块的 AST 扫描）能列出 11 处多读者常量，
但逐个读下来 **全是「参数穿透到底」的干净写法**：

| 闸 | 共享阈值 | 两个读者 | 判定 |
|---|---|---|---|
| `audit_universe_freshness` | `LOW`/`HIGH`/`MIN_NAMES` | `check` → `classify` | 干净：`check` 把判词整个委托给 `classify`，单判官 |
| `audit_events_vs_bars` | `OK_RATE`/`VOL_OK_RATE`/`MIN_N` | `audit` / `_fmt` | 干净：`rate < X` 与 `rate >= X` 精确互补，且都读模块常量、无参数化 |
| `audit_regression_gate` | `PANEL_TOL` | `audit_outputs` → `compare_panels` | 干净：`tol` 穿透，`render_outputs` 读结果里的 `tolerance` 不读常量 |
| `audit_universe_population` | `SMALL_CAP`/`FACTOR` | `check` → `share_small` | 干净：`line` 穿透；`1 / factor` 在判据与文案里逐字相同 |
| `audit_deploy_cost` | `STALE_DAYS`/`STALE_MIN_MB` | `stale_shipped` → `walk` | 干净：同一条调用链 |

**按名字找共享阈值是个弱判据**——它找得到 09-29 那个 bug，但那次的真形状不是「共享一个名字」，
是**同一个量被两个不同表达式问**（`missing >= u` 对 `present >= 1.0 - u`）。
补扫一遍补数表达式（`1.0 - x` / `1 / x`）：全仓只 2 处命中，都是判据与文案逐字一致的同一行。

换一把更锋利的尺子——**这个闸有几个会吐 violation 的入口？** 两个入口才可能对同一件事给相反答案：

```
20 个闸，2 个有 >=2 个 violation 生产者
  audit_archives.py        ['audit_one', 'reconcile', 'ticker_shells']
  audit_calendar_gaps.py   ['check', 'reconcile']      ← 09-29 已修
```

**`audit_archives` 是仅剩的那一个**，也正是 09-29 末行点名的那个。

## 二、复现（先复现，没先动刀）

`ticker_events.csv` 落后一场（最新行 08-17），今天（08-18）的 screener payload 已在盘上。
在 `origin/main` 的 `8c059cf00` 上跑：

```
I5   ticker_events  newest session 2026-08-17 < last completed 2026-08-18    WARNING
I5   breadth_archive 同上                                                    WARNING
I6b  gainers_4pct.json 3 rows vs ticker_events 2                             VIOLATION
I6c  breadth universe_size 100 (2026-08-17) vs universe.json rows 103        WARNING

ok = False | violations = 1 | exit code 1
```

**同一个事实，两个答案。** I5 说对了（归档落后一场），只报 warning；
I6b 把账记到我们自己的写入端头上——说 **08-17 少了一行**，而 08-17 那天是干净的——
并以这句话让 nightly job 在 commit 前失败。

而 `reconcile()` 的 docstring 自己写着：

> Reported as violations only when the dates line up (a stale file is I5's job).

**I6a 照办了**（`hits[hits["date"] == wl["date"]]`，不齐就降 warning）；**I6b 和 I6c 没有。**

根因：`extract_events(scr, payload, newest)` 的 `date_iso` 是**盖上去的戳，不是过滤条件**
（`pipeline/screeners/ticker_events.py:89`，只有退役 screener 才按它裁）。
所以 `n_json` 永远是**今天** JSON 的行数，`n_csv` 是**归档最新那场**的行数——
归档一落后，这个减法量的就是隔夜行情。

### 被同时盖住的那一半：假阴

老代码只在 `n_json != n_csv` 时才说话。**昨天的计数恰好等于今天 JSON 的计数时，它一个字都不说**，
而归档正整整落后一场。所以它连「静默漏归档」这个闸都算不上——**恰好在两个数撞上时失灵**。

## 三、修法

判据照 09-29 那条：**让两处问同一个量、同一把尺子、同一个方向。**

- **每一次比较都发生在一场之内。** I6b/I6c 在归档最新一场 ≠ `last_done` 时不再比计数，
  改报**错位本身**；`run()` 把它已经算好的 `last_done` 传进 `reconcile()`——
  那正是 I5 读的同一个量。
- **各自保持原有严重度**：I6b 仍然 fatal（今天的 payload 躺在一个没拿到今天行的归档旁边，
  必须拦下 commit，plan B 不变），I6c 仍然 warning。**退出码在复现场景里一个字没变**，
  改的只是 CI 打印的那句话。
- **不造第三份 `et_session`**：`watchlist.json` 有 `date` 字段所以 I6a 能按共享键对齐；
  screener payload 与 `universe.json` 只有 `timestamp`，把它折成 ET 交易日就是
  `et_session` 的**第三份拷贝**（已经躺在 `audit_universe_population` 与
  `audit_universe_freshness` 里各一份）。所以 I6b/I6c 对齐到 `last_done`。
  这条不对称写进了 docstring，不留给下一个人猜。

修后同一个复现：

```
I6b ticker_events newest session 2026-08-17 is not the session under audit 2026-08-18
    -- today's screener payloads have no archive rows to reconcile against
       (the archive never got this session; see I5)            VIOLATION（严重度不变）
I6c breadth_archive newest session 2026-08-17 is not the session under audit
    2026-08-18 ... not comparable (see I5)                     WARNING（严重度不变）
ok = False | exit code 1（不变）
```

## 四、顺手修掉的两处漂移

模块 docstring 第 28 行写着 **「Exit code 1 when any I1/I2/I3 violation exists」**——
而 `run()` 从来是 `sum(len(r["violations"]) for r in reports)`，**I6a / I6b / I7 也一直是致命的**。
那句话是在 I6/I7 加进来之前写的，之后没跟上。已改成代码实际做的事，
并写明 I4/I5/I6c 为什么是 warning（I5 管的归档由好几种不同节拍写入——`regime_ledger`、
`delayed_ep_log`——对其中任何一个落后就让 nightly 失败，等于为 nightly 修不了的原因让它失败）。

## 五、测试

新增 10 条（85 通过，此前 75）。**按「能坏的方式」分类造，不只造一个方向**：

| 测试 | 钉的是哪个坏法 | 在 `origin/main` 上 |
|---|---|---|
| `..._inside_the_session_under_audit_still_fires` | 别把闸弄瞎：对齐 + 真漏行，计数差必须照旧报 | 🟢 绿（本来就对） |
| `..._never_reported_as_a_count_delta` | 本体：错位时不许说成计数差 | 🔴 红 |
| `..._whose_counts_happen_to_match_is_not_silent` | 假阴那一半：两个数撞上时不许沉默 | 🔴 红 |
| `..._for_a_session_other_than_last_done[k]`，k=0..5 | 不变式，扫描而非点测 | 🟢 k=0 / 🔴 k=1..5 |
| `..._i6c_reports_the_misalignment_not_a_size_delta` | warning 那一半：改句子，不改严重度 | 🔴 红 |

**8 红 2 绿**，绿的两条正是 k=0 对齐点与那条防自残的对照——
扫描形状（1 绿 5 红）是 09-29 那次（10 绿 1 红，只在边界破）的镜像：
那次只在边界坏，这次**除了对齐点处处坏**。形状本身就是定位证据。

期望值写死在测试里，不从被测模块读回来（09-25 的教训：
`assert bool(w) is bool(spec["counts"])` 那种写法看着滴水不漏，19 个存活点一个没死）。

变异核对四个方向全死：

| 变异 | 结果 |
|---|---|
| I6b 判据翻转 `!=` → `==` | 13 failed |
| I6c 判据翻转 | 3 failed |
| I6b 错位降级成 warning | 2 failed |
| 忽略传进来的 `last_done`，改读 `last_completed_session()` | 9 failed |

## 六、没做的，和为什么（留给复核员/ALEX 判，不自决）

1. **I6a 错位时是 warning，I6b 是 violation** ——底下是同一个事实（已发布的输出旁边缺归档行）。
   统一它们要动 `test_hits_from_another_session_do_not_count_as_this_one` 这条现有测试，
   是**硬发布闸上的严重度改动**，不在本轮的诊断范围内。
2. **I5 该不该对 nightly 自己写的那几个归档升成 violation** ——现在「静默漏归档」在 CI 里
   只剩 I6b 的错位 violation 兜着（本轮把它兜得可靠了，但它只覆盖 `ticker_events.csv`）。
   升 I5 会牵到别的线写的归档节拍，是跨线决定。

## 七、这轮学到的方法

**「两个函数不许对同一件事给相反答案」这条戒律，找它的尺子不是「共享阈值名」。**
按名字扫出 11 处，11 处全干净；按「有几个 violation 生产者」扫，20 个闸里只剩 2 个，
其中 1 个就是 bug 所在。**判据要问「谁有权吐判词」，不是「谁读了同一个数」。**
