# Yahoo 调用模式审计 — 2026-09-04（OPS Fable，探查 agent 全仓扫描）

**起因**：Andy 问「dashboard 断更两天，真的是 yfinance 的问题还是我们的问题」。
**结论**：主犯是我们。Yahoo 封 GitHub 机房 IP 是事实，但我们的调用模式把自己送进了封锁名单。

## 一晚的真实请求量：≈14,000–16,000 次，压缩在 ~30 分钟、单个 runner 出口 IP

| # | 拉取 | 规模 | 证据 |
|---|---|---|---|
| 1 | `enrich_universe` 全量 1y 日线 | 5,629 只 | `pipeline/adapters/yfinance_adapter.py:657` |
| 2 | `volume_enrichment` 再整拉一遍 3mo | 又是 5,629 只 | `pipeline/screeners/volume_enrichment.py:74` |
| 3 | VCP 候选 90d（裸 download 无重试） | 100–200 只 | `yfinance_adapter.py:1088` |
| 4 | ETF 1y + 指数逐只串行 | ~150 只 | `yfinance_adapter.py:493,1017` |
| 5 | short_window / name_cards / asset_signals / baskets / macro / correction_risk | 各自再拉 | `run_all.py:814,953,1002,1081` |
| 6 | `run_tickers` 每只打 8 个端点 | 213×8 ≈ 1,700 次 | `pipeline/tickers/ticker_data_fetcher.py:460-480` |
| 7 | delayed_ep_scan 最多 4 轮 | — | `pipeline/tools/delayed_ep_scan.py:275-288` |

关键事实：
- **零增量缓存**。每晚重拉 5,629×252 根 bar，其中 251 根昨晚拉过。`ohlc_store.py:1-27` 的「先查本地」docstring 是空头支票——`enrich_universe` 一次都没调它；`.cache/ohlc/` 被 `.gitignore:60` 忽略，runner 上永远是冷的。
- **同晚 universe 被整拉 ≥2 次**：`enrich_universe` 的 `all_data` 是局部变量，返回时丢弃（`yfinance_adapter.py:648→999`），于是 volume_enrichment 只为算一个 `vol_5d_50d` 又把 5,629 只拉了一遍——这个数用手上已有的 1y 日线就能算。
- **重试是线性硬打**：`yfinance_adapter.py:694-706`，退避 20/40/60/80s；`except Exception` 把 429 和 delisted 混为一谈（`:671`）；无熔断，只要还有零星成功就把剩下的批全部打完。各模块重试互不知情，无进程级共享限流器（全仓 grep `RateLimit|Limiter` 零命中）。
- **失败 = 数据蒸发**：`.github/` 全目录 `upload-artifact` 零命中。审计闸翻红 → commit 跳过 → 刚花 15,000 次请求换来的 `data/output/` 随 ephemeral runner 一起消失。重跑=重打 Yahoo，恰在限流最易复发的时刻。「不发布坏数据」被实现成了「不保留数据」，两者不是一回事。
- session/crumb/UA 用法干净（没踩「自建 session」的坑）；`yfinance>=0.2.31` 上界开放，CI 每晚装最新版（09-02 成功班与 09-03 失败班都是 1.7.0，版本不是这次的凶手，但是不受控变量）。

## 09-03→09-04 断更的完整死因链

1. 09-03 21:30Z 主班被 GitHub 排程丢弃（老毛病）→ 23:28Z backstop 顶上。
2. backstop 班 Yahoo **全程通**（fundamentals 400/400 零失败）→ 死在最后一步审计闸：`shortlist_log.csv` 1 行重复（ABSI dup，C 类，已修 d6fec77e）→ 无 artifact，整晚数据丢弃。
3. 深夜 02:08–04:16Z 连发 6 次 dispatch，每次全量重拉 5,629 只 → GH 机房 IP 被 Yahoo 逐级封锁：429 → `HTTP 401 Invalid Crumb` → tradeable 46→0。
4. 结论：起因是我们的 bug；修复失败是我们的重试策略撞上 Yahoo 对机房 IP 的敏感窗口。

## 优化清单（按性价比排序，归 DATA ALEX 裁量执行）

1. **universe 级日线 store + 增量拉取**（收益最大）：新增 parquet store，接入 `yfinance_adapter.py:648-674`；命中则只补 `period='5d'`。数据量降 ~98%。
2. **`all_data` 交出去，砍 3 次重复整拉**（改动最小当晚见效）：volume_enrichment / VCP / short_window / name_cards 全部从 1y 面板里切，**单这条砍 ~6,000 次请求（≈40% 夜间流量）**，不改任何数字定义。
3. **失败路径加 `upload-artifact`**（`daily-data-update.yml:335` 旁，`if: failure()` 存 `data/output/`，retention 7 天）：把「不发布」和「不保留」分开；修复=重审+提交，不再重打 Yahoo。
4. **进程级共享限流器 + 指数退避 + 429 感知**：新增 `yahoo_budget.py`（token bucket + 全局 backoff_until），接入五个调用点；`sleep(20*attempt)` 改指数带 jitter（`:690-693` 注释已记录线性不够的实测）。
5. **钉死 `yfinance==`** + 评估显式装 curl_cffi impersonate。
6. 顺带：`run_tickers` 的 8 端点里 earnings/quarterly/analyst 是季度数据，套用 `fundamentals_store.pick_due` 的 budget 模式可再省 ~1,000 次。

## 应急通道（已在执行）

- 本机（住宅 IP）在 origin/main 干净树上替跑 `run_all`，Yahoo 对住宅 IP 开门——09-04 本班数据由此落地。
- 数据哨兵小时接力继续盯原生 21:30Z 窗口（历史上该窗口一直通）。
