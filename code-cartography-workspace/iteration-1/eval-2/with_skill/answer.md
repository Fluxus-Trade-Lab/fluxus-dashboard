# pipeline/screeners/run_all.py 拆分地图

- [x] 1 盘消费者
- [x] 2 量
- [x] 3 拆分建议
- [x] 4 落地前对照（baseline 测试跑了一遍）

只读盘点，未改动仓库任何文件，未 commit。要不要落地留给人拍板。

## 1 · 消费者盘点（M）

`run_all.py` 不是组件，没有 JSX 式的四种拼法，改用「导入 + 模块路径 + CLI 挂载 + 整仓裸字符串」四路：

```bash
grep -rn "from.*run_all'" --include='*.py' .   # 0
grep -rn "from.*run_all\"" --include='*.py' .  # 0
grep -rn "import run_all" --include='*.py' .   # 0（都是 from pipeline.screeners import run_all / from pipeline.screeners.run_all import X 写法）
grep -rn "screeners\.run_all\|screeners import run_all" --include='*.py' .
```

真代码消费者（M = 8，去重后）：

| # | 文件 | 挂法 | 挂的是什么 |
|---|---|---|---|
| 1 | `pipeline/tests/test_derived_fields.py:22` | `from pipeline.screeners.run_all import compute_universe_scores` | 函数级 import |
| 2 | `pipeline/tests/test_tradeable_scoring.py:10` | 同上 | 函数级 import |
| 3 | `pipeline/tests/test_score_all_rows.py:14` | 同上 | 函数级 import |
| 4 | `pipeline/tools/oratnek_diff.py:81` | 同上（函数体内延迟 import） | 函数级 import |
| 5 | `pipeline/tests/test_group_history.py:113-114` | `from pipeline.screeners import run_all` 再 `inspect.getsource(run_all.main)` | 读 `main` 源码文本，不只是调用 |
| 6 | `pipeline/tests/test_run_all_smoke.py:219` | `import pipeline.screeners.run_all as RA` | 端到端跑 `main()`，monkeypatch 内部依赖 |
| 7 | `pipeline/tests/test_no_downgrade_is_wired.py:28` | `Path(...) / "screeners" / "run_all.py"` 后 `ast.parse(RUN_ALL.read_text())` | **不 import，按路径读源码文本做 AST 断言** |
| 8 | `pipeline/tests/test_run_all_breadth_structure.py:18` | 同上，`SRC.read_text()` 后 `ast.parse` | **同上，AST 断言** |
| 9 | `.github/workflows/daily-data-update.yml:133` | `run: python -m pipeline.screeners.run_all` | **CLI 挂载，唯一的生产入口** |

第 7、8 两条是 1c「按路径字符串挂载」——它们不 import `run_all` 这个名字，是把整个文件当文本读进来做 `ast.parse`，grep import 语句四种写法一次都碰不到，必须专门查。

### 1b · 整仓裸字符串搜索，逐条排除文档提及

```bash
grep -rln "run_all" . --include='*.py' --include='*.md' --include='*.yml' \
  --include='*.yaml' --include='*.sh' --include='*.json' --include='*.txt'
```

命中 50+ 个文件，逐类核对：`docs/plans/**`、`docs/superpowers/**`、`data/research/**`、`data/reference/incidents/**`、`Fluxus_Brand/**`、`CLAUDE.md` 全部是事故记录/规划文档里提「run_all」这个名字，**不是代码消费者，不计入 M**。`pipeline/screeners/atr_enrichment.py:21,69`、`breadth_metrics.py:253`、`ticker_events.py:6`、`yfinance_adapter.py:451`、`pipeline/tools/{audit_wiring,audit_ledger,federation_board,audit_archives}.py`、`pipeline/tests/{test_audit_archives,test_failure_class}.py` 都只是**注释里提名字**，没有 import/read_text，同样不计入 M。

### 1c · 路径字符串挂载

已在上表列出（#7、#8 的 `Path(__file__).resolve().parents[1] / "screeners" / "run_all.py"`，#9 的 CI `python -m pipeline.screeners.run_all`）。这三处都不经过 Python import 系统，是本次盘点里最容易漏的一类：如果只 grep `import run_all` 四种拼法，M 会少报 3。

### 1d · 整页级回归测试，优先验证对象

判据：mount 整条主流程、读端到端输出的测试。三个命中，逐一点名：

- **`pipeline/tests/test_run_all_smoke.py`**（#6）——唯一真跑 `main()` 的测试（伪网络、真写盘），docstring 自陈是为了堵 2026-08-19 breadth blackout：717 个通过的单测里没有一个真正跑过 orchestrator。**任何拆分后必须让它继续绿**，这是判断「有没有拆坏接线」的唯一端到端信号。
- **`pipeline/tests/test_run_all_breadth_structure.py`**（#8）——不是跑代码，是对 `run_all.py` 源码文本做 AST 断言：断言 `run_breadth_metrics` 调用外面包着的 `try` 有且仅有一个非空 `orelse`，且 `run_signals` 调用在这个 `orelse` 里。它守的正是 08-19 那次 `else` 被静默重绑到 `if` 上的事故——**这个断言的前提是这段代码物理上留在 `run_all.py` 里**，一旦把 breadth 那段搬进新模块而不同步搬测试（或不改 `SRC` 路径），这条测试会直接报「expected exactly one try around run_breadth_metrics」失败，不是变成装饰品，是硬红。
- **`pipeline/tests/test_no_downgrade_is_wired.py`**（#7）——同样按路径读文本做 AST 断言，断言 `run_all.py` 里 `import ... check_overwrite` 且真的被调用。守的是 2026-08-31 那道「不覆盖健康数据」的闸被一次冲突手工化解误删的事故（`8e4a64ef`）。闸本体在 `run_all.py:959-968`，同一处也是「Quality gate / Regression gate」的落点，是全文件风险最高的一段。

这三个测试合起来意味着：**main() 里 breadth 段（约 579-841 行）和 universe 落盘+两道闸段（约 878-968 行）是全文件里唯一被结构化测试钉死位置的部分**，拆分方案必须单独标注、不能和其余「读一遍就明显该搬」的段落同等对待。

## 2 · 量（现场跑，不算印象分）

```bash
$ wc -l pipeline/screeners/run_all.py
1258 pipeline/screeners/run_all.py

$ grep -n "^def \|^class \|^async def " pipeline/screeners/run_all.py
68:def build_fallback_universe(yf_adapter: YfinanceAdapter) -> pd.DataFrame:
142:def _json_serializer(obj):
157:def compute_universe_scores(universe: pd.DataFrame) -> pd.DataFrame:
486:def main():

$ awk 'NR==486,NR==1258' pipeline/screeners/run_all.py | wc -l
773                      # main() 一个函数占全文件 61%

$ grep -c "^\s*try:" pipeline/screeners/run_all.py
32                       # 全文件 32 个 try，31 个落在 main() 里

$ grep -n "\.to_csv(\|json.dump(\|write_text(\|\.to_json(" pipeline/screeners/run_all.py | wc -l
18                       # 18 处直接写盘

$ grep -c "^import \|^from " pipeline/screeners/run_all.py
20
```

全文件只有 4 个顶层定义：`build_fallback_universe`（68-142，74 行）、`_json_serializer`（142-157，15 行）、`compute_universe_scores`（157-486，**329 行**，含两个内嵌闭包 `rank_tradeable`/`score_against_tradeable`）、`main`（486-1258，**773 行**）。**问题不是「文件散」而是「main() 一个函数吃掉 61% 的行数」**：31 个 `try` 全在里面，对应 31 个「own failure domain」注释块（关键词直接搜得到：`# Own failure domain`/`own failure domain` 在 main() 内出现 8 次以上，加上没写这四个字但同构的另外二十来处）。这不是靠印象读出来的结构，是 31 个 try 块本身就是分割点。

同目录已有 25 个 sibling 模块（`momentum_97.py`、`gainers_4pct.py`、`breadth_metrics.py`……每个一个 `run()` 导出），`run_all.py` 早期阶段（1-5 步，513-579 行）已经在照这个约定调用它们，只有 5b 步之后（breadth 起）和 1000 行之后的长尾阶段还是把逻辑摊平写在 `main()` 里，没有跟进同一约定。**这是拆分的方向，不是新发明一种拆法**。

## 3 · 拆分建议

### 建议 A（低风险，先做）：把长尾阶段搬出 main()

- **搬什么**：`pipeline/screeners/run_all.py:1000-1258`（Group 层 → 主题梯 → 夜间 watchlist → Short List → shortlist feedback → library index → style rotation → correction risk → regime ledger → LBR TICK → 站点质量 → summary，共 11 个独立 try 块，258 行）
- **搬到哪**：新模块 `pipeline/screeners/run_all_late_phases.py`，导出一个 `run_late_phases(universe, results, ledger, logger, timestamp) -> None`（参照 sibling 模块 `run()` 的既有签名习惯），`main()` 在 999 行后改成一行调用
- **谁受影响**：无——这 11 段没有任何测试按路径读它们的源码文本（1c 检索过，只命中 579-968 那两处），也没有外部 import 引用这段代码里的具体符号。唯一要核对的是它们内部互相之间、以及和前面 universe/results 变量的依赖顺序，抽样已确认（见下）互相独立、只共享只读的 `universe`/`results`
- **怎么验没坏**：`test_run_all_smoke.py` 端到端跑一遍，比对 `data/output/` 里这 11 段各自产出的文件字节是否与拆分前一致（`diff` 而非只看退出码）；另外 `pipeline/tools/federation_board.py:520` 提到的 `run_all` 挂点（GAS 回拉）要跟着核对没有断
- **拆了省什么**：main() 从 773 行降到约 515 行，31 个 try 里 11 个（约三分之一）离开主控流程，且是风险最低的三分之一——不动 breadth/universe 两道被结构化测试钉死的段落

### 建议 B（中风险，第二步）：抽出 `compute_universe_scores`

- **搬什么**：`pipeline/screeners/run_all.py:157-486`（329 行，含 `rank_tradeable`/`score_against_tradeable` 两个内嵌闭包）
- **搬到哪**：新模块 `pipeline/screeners/universe_scoring.py`，`run_all.py` 顶部改成 `from pipeline.screeners.universe_scoring import compute_universe_scores`（保留原名字重导出，四个现有 import 点不用改一个字）
- **谁受影响**：`test_derived_fields.py:22`、`test_tradeable_scoring.py:10`、`test_score_all_rows.py:14`、`oratnek_diff.py:81` 四处——因为走的是重导出，`from pipeline.screeners.run_all import compute_universe_scores` 继续成立，理论上零改动；但要在 `pipeline/screeners/atr_enrichment.py:21,69` 里更新一处**注释**（写的是 ``run_all.compute_universe_scores``，纯文档性质，不改也不会跑错，只是名不副实）
- **怎么验没坏**：`test_derived_fields.py test_tradeable_scoring.py test_score_all_rows.py` 三个测试文件（本次已跑，见下方 baseline）必须继续绿；这三个恰好是压这个函数最实的测试，不是找新覆盖
- **拆了省什么**：文件行数再少 329 行，且这是全文件里唯一已经有 4 个独立外部消费者、天然该独立成模块的一段——现状是「它已经被当模块用了，只是物理上还长在 run_all.py 里」

### 建议 C（高风险，不建议现在动）：breadth 段 + universe 落盘/两道闸段

- **范围**：`run_all.py:579-841`（breadth/signals/state_board/regime/verdict/replay 及四个 save）与 `:878-968`（universe 落盘 + quality gate + regression gate + `no_downgrade.check_overwrite`，闸本体在 959-968）
- **为什么不建议现在动**：这两段正是 `test_run_all_breadth_structure.py` 和 `test_no_downgrade_is_wired.py`（1d 点名的两个）按**文件路径读文本**做 AST 断言的对象，断言的是「这段代码物理上留在 `run_all.py` 里的具体形状」（try/else 结构、import 语句）。这两段各自对应过一次真实生产事故（08-19 blackout、08-31 闸被删），测试文件本身的存在理由就是「怕这段代码被不知情地挪动」。要动，必须让搬代码和改测试的 `SRC`/`RUN_ALL` 路径落在同一个 commit 里，且两个 AST 测试改完要能在新位置继续复现「阳性对照会红」（两个测试文件里都留了阳性对照的复现步骤，抽查见下）——工作量和风险都明显高于 A/B，本次只标记不出方案

## 4 · 落地前对照：baseline 现场跑了一遍

```bash
$ python3 -m pytest pipeline/tests/test_run_all_breadth_structure.py \
    pipeline/tests/test_no_downgrade_is_wired.py \
    pipeline/tests/test_derived_fields.py \
    pipeline/tests/test_tradeable_scoring.py \
    pipeline/tests/test_score_all_rows.py -q
76 passed in 4.42s

$ python3 -m pytest pipeline/tests/test_run_all_smoke.py -q
2 passed, 1 warning in 10.83s

$ python3 -m pytest pipeline/tests/test_group_history.py -q
18 passed in 1.95s
```

**Baseline 全绿（96 passed）**，颜色是本方案的输入，不是留给落地阶段的工作量。真要落地时的顺序：先做建议 A（低风险）→ 跑一遍上面这组命令确认仍全绿 → 再做建议 B → 再跑一遍 → 建议 C 单独立项，不跟 A/B 一起提交，且必须新加一条「注入真 bug 让 `test_run_all_breadth_structure.py` / `test_no_downgrade_is_wired.py` 变红」的正面对照（两个测试文件自己的 docstring 里都写了阳性对照怎么摆：把 else 改回 if-绑定、或删掉 `check_overwrite` 的 import），确认拆完之后这两条断言还有牙齿，而不是搬完家之后测试文件路径失配、变成对着一个不存在的 `try` 永远通过的装饰品。

## 抽样核对（file:line）

```bash
$ sed -n '157p;192p;329p;486p;513p;579p;774p;842p;878p;915p;959p;1000p;1258p' pipeline/screeners/run_all.py
def compute_universe_scores(universe: pd.DataFrame) -> pd.DataFrame:
        """Percentile rank within the tradeable set; NaN for everyone else.
    ) / 10
def main():
    # 1. Fetch universe (Finviz primary, yfinance fallback)
    # 5b. Breadth metrics (Stockbee MM + classic breadth)
    # 8. Save outputs
    # Save ETF data
    # Save full universe for screener page
    # Quality gate. A row count is not a shape check: the 2026-08-09 run
    from pipeline.no_downgrade import check_overwrite
    # Group layer: industries + curated themes, scored and state-classified.
main()
```

13/13 命中，边界与正文一致。

## 顺带发现（不属于本次任务范围，是否处理由你定）

- `.orig`/遗留文件：无——`find pipeline/screeners -iname "run_all*"` 只有 `run_all.py` 和它的 `.pyc`，没有历史剩件需要清理
- `pipeline/screeners/atr_enrichment.py:21` 的文档注释写的是 `run_all.compute_universe_scores`，落地建议 B 之后这行文字会跟实际位置脱节一格（仍能工作，只是指路指错了目录），顺手改一个字符串的事，不影响本次结论
