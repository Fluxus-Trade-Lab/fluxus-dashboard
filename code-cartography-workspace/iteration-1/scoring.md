# code-cartography — with_skill vs without_skill scoring (iteration-1)

Six answers scored:
`eval-{1,2,3}/{with_skill,without_skill}/answer.md`, judged against `/tmp/cc_skill.md`.

All six answers were spot-checked against the actual files in this worktree
(`.claude/worktrees/skill-os-v2/{frontend,pipeline}/...`). Every line-count / def-count /
try-count number quoted by `with_skill` matched the real files exactly (`WatchlistPage.jsx`
1195 lines / 7 exports / 9 `useState` / 1 `useEffect` / 0 `fetch(`; `run_all.py` 1258 lines,
`main()` at 486, 32 `try:`; `ScreenerPage.jsx` 490 lines, 5 `useState`, 2 `useEffect`;
`StockTable.jsx` 451 lines). No fabricated numbers found in either condition — `without_skill`
just supplies far fewer numbers to check.

---

## Eval 1 — WatchlistPage.jsx, "整理一下"

### with_skill

**A — consumer scan breadth: PASS.**
Shows all four grep spellings as literal commands plus a repo-wide pass:
> ```
> grep -rn "from.*$T'"    --include='*.jsx' --include='*.js' $D | grep -v node_modules
> grep -rn "from.*$T\""   --include='*.jsx' --include='*.js' $D | grep -v node_modules
> grep -rn "require(.*$T" --include='*.jsx' --include='*.js' $D | grep -v node_modules
> grep -rn "import(.*$T"  --include='*.jsx' --include='*.js' $D | grep -v node_modules
> ```
> "命中 `pipeline/`、`docs/`、`data/reference/`、`data/research/` 共 16 个文件，逐条打开确认…没有一处是代码 import"

**B — three measured numbers: PASS.**
> `grep -n "^export " $F | wc -l # 7（6 具名 + 1 default）` / `grep -c "useState(" $F # 9` /
> `grep -c "useEffect(" $F # 1` / `grep -n "fetch(" $F | wc -l # 0`
All four confirmed correct against the actual file.

**C — file:line split proposals: PASS.**
Ten-row table (A–J), each with source `file:line`, destination file, affected consumers, and
a verify step, e.g. row A: "`gateWords` 143-174…→ `watchlist/gates.js`… `gateWords.test.js`、
`pickRs.test.js` 的 import 路径要从 `./WatchlistPage` 改成 `./gates`…怎么验没坏: 跑
`gateWords.test.js` + `pickRs.test.js`…"

Extra facts: no rewritten code produced (explicit "只读，不重写" / "未改动仓库任何文件").
States test status explicitly: attempted `npx vitest run`, it failed (`node_modules` missing
in the worktree), and it says so plainly: "**baseline 颜色现在是「未知」，不是绿色。**"

**Miss worth flagging**: it never finds the real bug in this file — see below.

### without_skill

**A — FAIL.** Zero grep/bash commands anywhere in the file (only one `js` code block, which is
a quoted bug snippet, not a search). Consumer claims are asserted inline in a table
("已被 `gateWords.test.js` 直接 import") with no command or repo-wide pass shown.

**B — FAIL.** No export count, no `useState`/`useEffect` count, no `fetch(` count anywhere.
Only line-range subtraction in the map table ("609–734", "736–798" etc.), which is the
line-count the skill explicitly says doesn't count.

**C — FAIL.** Section 四 ("如果以后要真正拆分文件") lists five bullet targets with rough line
ranges and a destination file, but none of the five states who is affected or how to verify,
e.g.: "`watchlist/atrColor.js` ← 256–404 行的配色数学…与 React 无关，最容易搬、影响面最小" —
no consumer list, no verify command. (Section 二's "加功能对照表" is a where-to-edit map, not
a split proposal, and also carries no verify step.)

**What it found that with_skill missed**: a real TDZ bug —
> "`WatchlistPage.jsx:1017-1025`…`view` 用 `const` 声明在 1025 行，但 1020 行的分支在它声明
> **之前**执行到，处在 JS 的 temporal dead zone 里"

Verified in this worktree: `WatchlistPage.jsx:1020` reads `view={view}` inside the
`ZoneDetail` early-return branch, and `const view = { highOnly, floor, pool3m, exHealth }` is
declared at line 1025 — five lines later, same function scope. This is a genuine bug the
skill-driven checklist run never surfaced. `without_skill` also flagged the duplicated
`ScanCard`/`Panel` logic as a merge candidate; `with_skill` never mentions that duplication.
Neither answer ran a test.

---

## Eval 2 — run_all.py, "太长了，能不能拆"

### with_skill

**A — PASS.** Four import-style greps (all 0 hits, correctly explained: the repo always writes
`from pipeline.screeners import run_all` / `from pipeline.screeners.run_all import X`) plus a
dedicated wide search:
> `grep -rln "run_all" . --include='*.py' --include='*.md' --include='*.yml' …` — "命中 50+
> 个文件，逐类核对…全部是事故记录/规划文档…不计入 M"
Plus the path-string-mount step (1c) that the other five answers don't formalize as a search:
finds two AST-based tests that read the file as text (`test_no_downgrade_is_wired.py`,
`test_run_all_breadth_structure.py`) and the CI cron line
`.github/workflows/daily-data-update.yml:133`.

**B — PASS.** Six separate measured counts with commands and output, not just `wc -l`:
> `wc -l` → 1258 · `grep -n "^def ..."` → 4 top-level defs · `awk 'NR==486,NR==1258' | wc -l`
> → 773 (main() share) · `grep -c "^\s*try:"` → 32 · write-call grep → 18 · import-line grep
> → 20
All confirmed exact against the worktree file.

**C — PASS.** Three graded proposals (A low-risk / B medium / C "don't do yet"), each with
`file:line`, destination module, named affected consumers, and a verify command, e.g. proposal
B: "搬什么 `run_all.py:157-486`…谁受影响: `test_derived_fields.py:22`、
`test_tradeable_scoring.py:10`、`test_score_all_rows.py:14`、`oratnek_diff.py:81`…怎么验:
`test_derived_fields.py test_tradeable_scoring.py test_score_all_rows.py`…（本次已跑）".

Extra facts: no rewritten code. Actually **ran** the test suite and pasted the result:
> `python3 -m pytest … -q` → `76 passed in 4.42s`; `test_run_all_smoke.py` → `2 passed`;
> `test_group_history.py` → `18 passed` — "**Baseline 全绿（96 passed）**"

### without_skill

**A — FAIL.** No consumer scan of `run_all.py` at all — never mentions
`test_derived_fields.py`, `test_tradeable_scoring.py`, `test_score_all_rows.py`,
`oratnek_diff.py`, or the CI cron line that actually invokes it. It does independently find
the two AST-locked tests (`test_run_all_breadth_structure.py`,
`test_no_downgrade_is_wired.py`), which is genuinely useful, but the file contains zero grep
commands or repo-wide search evidence (`grep -c '```'` on this file returns only pseudocode /
target-directory blocks, never a search command) — the claim is asserted, not shown.

**B — FAIL.** The only quantified table is line-range subtraction per top-level def
("~74", "~15", "~329", "~773") — restating line count, not new measurements. "20 个阶段"
is a stage count arrived at by reading comments, not a grep'd/counted number; no `try` count,
no I/O-call count, no import count anywhere.

**C — FAIL.** Proposes 8 target files (`run_all_fetch.py` … `run_all_market_layers.py`) with
approximate line ranges and one-line descriptions of what moves, but "谁受影响"/"怎么验" is
given only in general terms in the Action Plan (run smoke test every 2-3 stages; keep the AST
test's `SRC` path in sync for the one breadth stage) — not per proposal. Seven of the eight
target files carry no affected-consumer note and no per-item verify step at all.

Extra facts: no rewritten code. Discusses both guard tests in real depth (arguably the
without_skill answer's strongest showing across all three evals) but never actually executes
pytest or states a pass/fail baseline color anywhere.

---

## Eval 3 — ScreenerPage, "加一个新列，改哪"

### with_skill

**A — PASS.** Four spellings, all shown as commands with literal output, plus repo-wide and
path-string passes:
> `grep -rn "from.*ScreenerPage'" …` → 1 hit (`Layout.jsx:32`); the other three → 0 hits;
> "整仓裸字符串搜…命中的其余 8 处逐条打开确认，全部是文档/计划/评测提及，不计入 M";
> "`Rail.jsx:73` 有 `{ key: 'screener', ... hash: '#/screener' }`…不经过组件名 grep"
Also explicitly checks whether any test mounts the full page and reports the negative result
as a finding: "**没有找到 mount 整个 ScreenerPage 的测试**".

**B — PASS.** Measures both the page shell and the file that actually renders the table:
> `wc -l ScreenerPage.jsx` → 490 · `useState(` → 5 · `useEffect(` → 2 · `fetch(` → 0 ·
> `wc -l StockTable.jsx` → 451 · exports → 2
All six numbers confirmed correct against the worktree.

**C — PASS.** Four lettered "落点" (A–D), each with `file:line`, what to add, who's affected,
and how to verify, e.g. 落点 C: "`StockTable.jsx:379-436`…谁受影响: 只有这一个文件内部…怎么验:
新 `<td>` 插入的位置必须和 B 里新 `<th>` 插入的位置一致…错位不会报错，只会让数据显示在错的表头
下面". It also catches a real risk with no other answer names: adding a `<th>` without bumping
`colSpan={15}` on the evidence-drawer row.

Extra facts: no rewritten code. States test status: attempted `npx vitest run … heatMark.test`,
got `ERR_MODULE_NOT_FOUND` (no `node_modules`), and says so plainly: "**没有可用的绿/红基线**".

### without_skill

**A — FAIL.** Zero code/command blocks in the entire file (confirmed: no fenced block at
all). No consumer search is attempted for either `ScreenerPage` or `StockTable` — the file
list is produced by reading, not searching.

**B — FAIL.** No export/useState/useEffect/fetch counts anywhere; only line ranges quoted from
reading (e.g. "表头（约 336-359 行）").

**C — FAIL.** Names file:line targets (StockTable header/SORTS/RowPair/colSpan/i18n) but gives
no verify step anywhere in the document — the closest it gets is a list of "关键约束" (rules
not to violate), not a check to run after editing. No consumer/affected note beyond "改动最多"
framing.

This is the shortest of the six answers (29 lines) and the only one with no code fences of any
kind — noted below as a possible outlier rather than a stable trait of "without_skill" as a
method.

---

## Scoreboard

| Eval | Assertion | with_skill | without_skill |
|---|---|---|---|
| 1 | A consumer scan breadth | PASS | FAIL |
| 1 | B three measured numbers | PASS | FAIL |
| 1 | C file:line split proposals | PASS | FAIL |
| 2 | A consumer scan breadth | PASS | FAIL |
| 2 | B three measured numbers | PASS | FAIL |
| 2 | C file:line split proposals | PASS | FAIL |
| 3 | A consumer scan breadth | PASS | FAIL |
| 3 | B three measured numbers | PASS | FAIL |
| 3 | C file:line split proposals | PASS | FAIL |

**with_skill pass rate: 9/9 = 1.0. without_skill pass rate: 0/9 = 0.0. Delta: +1.0.**

Neither condition ever produced rewritten code in any of the six answers — all six stayed at
the map/proposal level, matching what both prompts (only one told to read the skill) and the
underlying tasks asked for. The one place conditions diverge sharply on process, not just on
scoring: all three `with_skill` answers explicitly attempted to run the existing test suite and
stated the resulting color (two attempts failed for environment reasons — missing
`node_modules` — and said so instead of assuming green; one attempt actually ran pytest and got
"96 passed"). None of the three `without_skill` answers ran or attempted to run a test, and
none states a baseline color anywhere.

## Does with_skill beat without_skill?

Yes, on the letter of these three assertions, uniformly — 9/9 vs 0/9, and the gap is the same
3-0 shape in every eval, so there's no eval where the skill "changed nothing." But the reason
for the uniform gap is narrower and more mechanical than "better answers": in every one of the
six files, the discriminating signal was almost entirely *whether the answer pastes actual
command output* (a `grep`/`wc`/`pytest` invocation with its result) versus *asserting a
conclusion from having read the file*. `with_skill` pastes commands in all three; `without_skill`
pastes zero commands in eval 1 and eval 3, and only pseudocode/target-listing blocks (no
searches, no counts) in eval 2. That is very plausibly the skill's doing — its checklist
literally says "四个数都要贴命令输出" (paste command output for all four numbers) and gives the
exact four grep commands to run — so this is a difference I'd expect the skill to cause, not
one that would have happened anyway.

Two things temper that conclusion. First, `with_skill` answers are also longer in every eval
(172 vs 91, 155 vs 135, 115 vs 29 lines) and read more confidently ("**baseline 颜色现在是
「未知」**", bolded verdicts throughout) — length and confidence alone would inflate a
holistic-quality judgment, but assertions A/B/C here were graded on a narrow, checkable
signal (is there a command, is there a number, is there a four-part row), which is harder to
fake by being verbose, and I could verify the with_skill numbers against the real files, which
they matched. So I don't think the 9-0 result is merely a length/confidence illusion, but the
eval-3 gap (115 vs 29 lines) is wide enough that I'd want a second without_skill sample before
trusting it as a stable effect size — that run may simply have been a shallow pass rather than
what "without the skill" reliably produces, given that the eval-1 and eval-2 without_skill
answers are comparably thorough in prose (they just don't show their search process).

Second, and more important: on raw usefulness rather than the three procedural assertions,
`without_skill` eval 1 is not worse — it is the only one of the six answers that found a real
bug (the TDZ `view`-before-declaration crash at `WatchlistPage.jsx:1020` vs `:1025`, confirmed
present in this worktree) and the only one to flag the `ScanCard`/`Panel` duplicate-logic
smell. `with_skill` eval 1, despite running every checklist item, missed both. A checklist that
directs attention to "scan consumers, count exports, propose file:line moves, check test color"
can crowd out the kind of open-ended reading that catches an unrelated live bug sitting a few
lines away from the exact code being mapped. So: the skill reliably wins on the evidence
discipline it explicitly mandates (which is what it's designed to enforce and what this
benchmark measures), but that is not the same claim as "with_skill produces the better answer
for Andy to act on" in every case — on eval 1 specifically, a reader who only wants to know
"what will break if I touch this file" arguably got more value from the answer that failed all
three assertions.

skill-none: 本轮无适用 skill
