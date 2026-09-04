# `pipeline/screeners/run_all.py` 拆分方案

**结论**：能拆，而且该拆——1258 行里 773 行全在 `main()` 一个函数里，是 20+ 个「各管各失败域」的阶段硬串成一条线；但拆之前必须先看懂两处已经焊死在这个文件上的回归测试，不然拆完当场变绿变红两条测试都可能挂掉。

**Action Plan**：
1. 先把 `main()` 里目前用注释分隔的 ~20 个阶段，按「取数 / 计算 / 存盘防覆盖 / 派生图层」四组切成同目录下的 `run_all_*.py` 兄弟文件，每个导出一个函数；`main()` 收缩成阶段调用清单。
2. 唯一的硬约束：breadth/signals/state_board/regime/verdict/replay 那段 try/except/else（第 579–663 行附近）要整体搬，且 `pipeline/tests/test_run_all_breadth_structure.py` 里写死的 `SRC = .../screeners/run_all.py` 路径要跟着改，否则这条防「else 静默重绑」事故的测试会测一个空文件。
3. `pipeline/tests/test_run_all_smoke.py` 端到端跑 `run_all.main()`，monkeypatch 打在 adapter/marketcal/breadth_signals 等底层模块上、不打在 `run_all` 自己身上——只要 `main` 这个名字还在 `pipeline.screeners.run_all` 里、还按原顺序调用同一批底层函数，这条测试天然兼容拆分，不用改。建议按此测试逐阶段验证：每挪 2–3 个阶段就跑一次 smoke test，不要一次性搬完再验。

---

## 一、现状拆解

文件只有 4 个顶层定义：

| 定义 | 行号 | 行数 | 性质 |
|---|---|---|---|
| `build_fallback_universe()` | 68–142 | ~74 | 纯函数，yfinance 200 支兜底池 |
| `_json_serializer()` | 142–157 | ~15 | JSON 序列化工具 |
| `compute_universe_scores()` | 157–486 | **~329** | 纯函数（df in → df out），F/I/H 分、ATR 矩阵、百分位排名等全部打分逻辑 |
| `main()` | 486–1258 | **~773** | 整条夜间管线的编排 |

`main()` 内部按注释标号走了 8 个「official」阶段（1 取数 ~ 8 存盘），但第 8 步「Save outputs」本身又吞了 12+ 个子阶段（质量闸、回归闸、basket、group 层、五级主题梯、watchlist、shortlist、rotation、correction risk、regime ledger、tick cycle、site quality……），实际是 20 个阶段挤在一个标号里：

```
1.  Fetch universe (Finviz→yfinance fallback)         ~513
1b. Fundamentals (F score)                            ~529
2.  Fetch ETF data                                     ~550
3.  Fetch MA signals                                   ~555
4.  Run 9 screeners                                    ~563
5.  Stockbee ratio                                     ~574
5b. Breadth metrics + signals/state_board/regime/...   ~579  ← try/except/else，被 AST 测试焊住
6.  VCP detection                                       ~663
7.  ATR enrichment                                      ~671
7b. Ticker event archive + heat                         ~683
8.  Save screener JSON outputs                          ~774
    Save signals / breadth / market_health / replay     ~782-840
    Save ETF data                                       ~842
    Asset-layer signals (~26 ETF)                        ~848
    Save full universe + quality gate + regression闸     ~878-985
    Basket refresh                                       ~987
    Group layer (industries + themes)                    ~1000
    groups_history 投影                                  ~1021
    五级主题梯 (2W/4W/6W/8W/10W)                          ~1033
    Nightly watchlist                                    ~1054
    Short List (六席)                                    ~1092
    Shortlist feedback pull                              ~1154
    Library index                                        ~1167
    Style rotation                                       ~1178
    Correction Risk                                      ~1189
    Regime ledger                                        ~1201
    LBR TICK cycle                                       ~1219
    Site-wide quality grading                            ~1230
    Summary log                                          ~1243
```

每个阶段几乎都带一句「own failure domain」注释——这是有意为之的设计：一个阶段炸了不能拖垮后面的阶段，所以每段都自带 try/except，日志记警告后继续往下走。**拆分不能破坏这个语义**，也就是说抽出来的每个阶段函数最好保留自己的 try/except（返回 None/部分结果），而不是把异常甩给 `main()` 里统一 catch——现在的写法本来就是这个模式，只是全挤在一个函数体里。

## 二、两处焊死在这个文件上的测试（拆分前必读）

### 1. `pipeline/tests/test_run_all_breadth_structure.py`（AST 结构测试）

这条测试是 2026-08-19「else 静默重绑」事故（CLAUDE.md pitfall `pitfall_else_rebinding_in_orchestrator.md` 同一案例）之后补的：它直接 `ast.parse` 源码文件，断言「调用 `run_breadth_metrics` 的 `try` 恰好只有一个，且它的 `else:` 分支里必须调用 `run_signals`」。硬编码路径：

```python
SRC = Path(__file__).resolve().parents[1] / "screeners" / "run_all.py"
```

拆分时如果把 5b 那段 breadth/signals/state_board/regime/verdict/replay 的 try/except/else 挪到新文件（比如 `run_all_breadth.py`），**这条测试必须跟着改 `SRC`**，且挪过去之后 try/except/else 的语法结构本身要原样保留（不能拆成两个函数分别调用，否则「else 绑定在同一个 try 上」这个不变量就没了检测对象）。这是整个拆分里唯一「测试文件也要跟着动」的地方。

### 2. `pipeline/tests/test_run_all_smoke.py`（端到端冒烟测试）

这条测试的文档字符串把动机写得很直白：

> `run_all.main()` is ~900 lines of control flow whose failure domains had never been walked as one path. This test walks it.

它在临时目录里跑真实的 `RA.main()`（只 fake 掉网络：`FinvizAdapter.fetch_universe`、`yfinance.download`、`marketcal.market_now`、`breadth_signals` 的几个阈值常量），断言 breadth.json 带全 regime/state_board/verdict/conditions、universe 行数、`audit_archives` 零违规等——覆盖的正是「模块各自测试都绿、但没人测过接线」这个坑（CLAUDE.md pitfall `pitfall_tested_the_module_not_the_wiring.md`）。

好消息：它 monkeypatch 的都是底层依赖（`FinvizAdapter`、`marketcal` 模块、`yfinance` 库、`breadth_signals` 模块常量），**没有一处 patch 在 `run_all` 模块自己头上**，只是最后 `import pipeline.screeners.run_all as RA; RA.main()` 调一次。这意味着只要：
- `main` 这个名字还在 `pipeline.screeners.run_all` 里能被调用，
- `main()` 内部仍然按原顺序、原语义调用同一批底层函数（不管这些调用是直接写在 `main()` 里还是转手调了 `run_all_fetch.fetch_stage()`），

这条测试天然兼容拆分，**不需要改**。它是检验「拆完之后管线整体行为没变」的现成安全网，应该在每次挪动 2–3 个阶段后就跑一次，而不是等全部拆完才跑——CLAUDE.md 里「接线在，接的是自伤指令」「测试对、没人调用」这两条坑都提醒过：验证要验证「真的按原顺序接上了」，不能只验证「新文件能 import」。

## 三、建议的目标结构

沿用仓库里 `pipeline/screeners/*.py` 「一文件一 `run()`」的既有风格（`breadth_metrics.py`、`gainers_4pct.py` 等都是这个模式），不新开嵌套包，直接在同目录加几个 `run_all_*.py` 兄弟文件，按「取数 / 计算 / 存盘防覆盖 / 派生图层」四组切：

```
pipeline/screeners/
  run_all.py            # 瘦身后的编排入口：intraday 闸 + ledger 初始化 + 依次调用下面几个阶段
  run_all_fetch.py       # 1 universe(Finviz/yfinance) · 1b fundamentals · 2 ETF · 3 MA signals
  run_all_screen.py      # 4 跑 9 个 screener · 5 stockbee ratio
  run_all_breadth.py     # 5b breadth + signals/state_board/regime/verdict/replay
                          #   ⚠ try/except/else 整体搬迁，AST 测试的 SRC 路径同步改
  run_all_enrich.py      # 6 VCP · 7 ATR enrichment · 7b ticker events + heat
  run_all_persist.py     # 8 存盘：screener JSON / signals / breadth / market_health / replay /
                          #   ETF / asset-layer signals / universe 落盘 + quality 闸 + regression 闸
  run_all_groups.py      # basket 刷新 · group 层 · groups_history 投影 · 五级主题梯
  run_all_watchlist.py   # nightly watchlist · shortlist(六席) · shortlist feedback · library index
  run_all_market_layers.py  # rotation · correction risk · regime ledger · tick cycle · site quality
```

`compute_universe_scores()`（329 行，纯函数、无副作用、已经和 `main()` 解耦）也值得挪进 `run_all_persist.py` 或独立成 `universe_scoring.py`——它是目前文件里唯一一段已经天然可单测的大块逻辑，挪出来能顺手补一条不依赖网络/文件系统的单元测试，但这不是本次拆分的强制项，优先级低于上面的阶段拆分。

`main()` 拆完之后大致长这样（伪代码，说明编排关系，不是最终实现）：

```python
def main():
    # intraday 闸 / OUTPUT_DIR·HISTORY_DIR / ledger 初始化，原样留在这里
    ctx = RunContext(...)  # 或继续用普通局部变量传递 universe/etf_data/results/breadth_result

    run_all_fetch.fetch_universe_and_context(ctx)
    run_all_screen.run_screeners(ctx)
    run_all_breadth.breadth_stage(ctx)      # try/except/else 整块内部保留
    run_all_enrich.enrich_stage(ctx)
    run_all_persist.persist_core_outputs(ctx)   # 含 quality 闸 + regression 闸
    run_all_groups.groups_stage(ctx)
    run_all_watchlist.watchlist_stage(ctx)
    run_all_market_layers.market_layers_stage(ctx)

    logger.info(f"Done. {len(ctx.results)} screeners completed. Universe: {len(ctx.universe)} stocks.")
```

跨阶段共享的状态（`universe` df、`etf_data` df、`results` dict、`breadth_result`）建议用一个轻量 `dataclass`（或继续用一个普通 dict）显式传递，而不是让各阶段函数互相读写模块级全局变量——现状是局部变量天然作用域清晰，拆分时最容易踩的坑就是「某个后面阶段读的变量，原来是前面阶段 try 块里才赋值的，抽函数时忘了在 except 分支也给它一个默认值」。第 8 步里「Save breadth metrics (skipped when the breadth step failed — the previous breadth.json stays in place)」这类判断，本质就是靠 `breadth_result is None` 这个哨兵值，拆分时要把这个哨兵显式搬进 context，不能丢。

## 四、值得注意的低耦合红利

`main()` 里从「Group layer」往后的阶段（basket、group、theme ladder、watchlist、shortlist、rotation、correction risk、regime ledger、tick cycle、site quality）有个共同特点：注释里反复出现「reads universe.json off disk」「own failure domain」——它们大多不依赖内存里的 `universe` df，而是重新从磁盘读 `data/output/universe.json`（这是刻意设计：08-27 的「不覆盖健康副本」裁决要求下游阶段读盘上文件而不是内存对象，这样第 8 步的 regression 闸拒绝覆盖时，下游还能吃到昨天健康的数据）。这意味着这批阶段之间的**真实数据依赖是文件系统而不是变量**，拆成独立函数/独立文件的风险最低、可以最先动手；反而是前 7 步（取数→算分→存盘）因为都在同一批 df 上原地改列，耦合更紧，应该放在拆分计划的后半段、更谨慎地做。

## 五、不建议做的事

- 不要把 20 个阶段一次性搬完再跑测试——两条测试（尤其 smoke test，~1-2 分钟一次）就是为了在这种大范围重排里及时报警，应该按前面 Action Plan 第 3 条边挪边跑。
- 不要为了「面向对象」把 `main()` 改成一个大 pipeline 类/注册表框架——现有的「一文件一 `run()` 函数」是仓库里 9 个 screener 共用的既有约定，`run_all_*.py` 按同样风格拆最省认知成本，不需要引入新抽象。
- 不要顺手把 try/except 的「失败不致命，继续往下跑」语义改成统一的异常处理装饰器——这是过去几次事故（08-27 覆盖健康数据、08-19 else 重绑）之后一条条吃回来的设计决定，拆分只是搬家，不是重新设计容错策略。
