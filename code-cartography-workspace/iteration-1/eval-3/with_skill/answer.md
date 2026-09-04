# 给 ScreenerPage 加一个新列，改哪

- [x] 1 盘消费者
- [x] 2 量
- [x] 3 拆分/落点建议
- [x] 4 落地带正面对照（baseline 测试状态）

## 1 · 消费者盘点（M）

`T=ScreenerPage`，四种拼法 + 整仓裸字符串 + 路径字符串挂载，全跑：

```
$ grep -rn "from.*ScreenerPage'"  --include='*.jsx' --include='*.js' frontend/src | grep -v node_modules
frontend/src/components/Layout.jsx:32:import ScreenerPage from './screener/ScreenerPage'

$ grep -rn 'from.*ScreenerPage"' --include='*.jsx' --include='*.js' frontend/src | grep -v node_modules
(0 命中)

$ grep -rn "require(.*ScreenerPage" --include='*.jsx' --include='*.js' frontend/src | grep -v node_modules
(0 命中)

$ grep -rn "import(.*ScreenerPage"  --include='*.jsx' --include='*.js' frontend/src | grep -v node_modules
(0 命中)
```

**M = 1**：唯一代码消费者是 `frontend/src/components/Layout.jsx:32`（import）+ `Layout.jsx:328`（`{current === 'screener' && <ScreenerPage />}`，条件渲染挂载点）。

整仓裸字符串搜（含 `pipeline/`、`data/reference/`、`docs/`）命中的其余 8 处逐条打开确认，全部是文档/计划/评测提及，不计入 M：
- `docs/plans/2026-03-17-dark-mode-plan.md:247`、`docs/superpowers/plans/2026-07-31-ticker-events.md:1140,1398,1433`、`docs/superpowers/plans/2026-09-04-skill-os-v2.md:802` — 历史/在建规划文档提及
- `.claude/skills/code-cartography/evals/evals.json:6` — 本次评测集自身
- `Fluxus_Brand/visual/2026-08-09_WHAT_TO_SHOW.md:115` — 品牌侧笔记提及
- `frontend/src/components/watchlist/WatchlistPage.jsx:552` — 注释里提到 `ScreenerPage GATES.exHealth`，不是 import

路径字符串挂载检查：`frontend/src/components/Rail.jsx:73` 有 `{ key: 'screener', short: 'SCR', hash: '#/screener' }`，是导航路由绑定，不经过组件名 grep，但不影响列改动（不用碰这行）。

测试消费者：`frontend/src/components/screener/heatMark.test.jsx` 是唯一一个 screener 目录下的测试文件，但它只 `import { HeatCell } from './StockTable'` 单独渲染 `<HeatCell>`，**不 mount 整个 ScreenerPage 或整个 StockTable**，不是整页渲染回归测试，不用单独标为优先验证对象。**没有找到 mount 整个 ScreenerPage 的测试** —— 这意味着加列之后没有自动化测试会替你确认新列真的渲染出来，要靠手动跑页面核对。

## 2 · 量（现场跑，命令输出）

`ScreenerPage.jsx` 只是壳层，真正渲染表格的是它 import 的 `StockTable.jsx`（`ScreenerPage.jsx:15,453`）。两个文件都量：

```
$ wc -l frontend/src/components/screener/ScreenerPage.jsx
490 frontend/src/components/screener/ScreenerPage.jsx

$ grep -n "^export " frontend/src/components/screener/ScreenerPage.jsx
79:export default function ScreenerPage() {
（1 个，只有 default）

$ grep -c "useState(" frontend/src/components/screener/ScreenerPage.jsx
5
$ grep -c "useEffect(" frontend/src/components/screener/ScreenerPage.jsx
2
$ grep -n "fetch(" frontend/src/components/screener/ScreenerPage.jsx | wc -l
0   （数据经 useUniverse/useGroups/useMarketData/useHeatingUp 四个 hook 拿）
```

```
$ wc -l frontend/src/components/screener/StockTable.jsx
451 frontend/src/components/screener/StockTable.jsx

$ grep -n "^export " frontend/src/components/screener/StockTable.jsx
176:export function HeatCell({ heat }) {
268:export default function StockTable({ rows, defaultSort = 'rs3', onChart }) {
（2 个：1 具名 + 1 default）
```

结论：加一个新列**不改 ScreenerPage.jsx 本体**（它只负责拼行数据、不画表格），要改的是它下游的 `StockTable.jsx`（表头/数据行）+ `ScreenerPage.jsx` 里拼行对象的那一段（如果新列要的字段还没进 row）。

## 3 · 改哪：四个落点，每条「搬什么 → 到哪 → 谁受影响 → 怎么验」

### 落点 A — 行数据要不要新字段
文件：`frontend/src/components/screener/ScreenerPage.jsx:209-236`（`out.push({ ticker: t, ... })` 这个对象字面量，字段来源于 `u = byTicker.get(t)`（`useUniverse`）和 `s = groups.stocks[t]`（`useGroups`））
- 新列如果要展示的数据 **已经在 row 里但没渲染成列**（比如 `perf1w`、`sector`、`cap`、`vol` 这四个字段现在只进了 row 对象，没有对应的 `<th>`/`<td>`，`ScreenerPage.jsx:232-235`），跳过这一步，直接去落点 B/C。
- 如果字段还不存在，在这个对象字面量里加一行 `xxx: u?.xxx_field ?? null`（参照 `relVol: u?.rel_volume ?? null` 这行的写法，`ScreenerPage.jsx:234`）。若 `u`/`s` 上游（`useUniverse`/`useGroups` 读的 `data/output/` JSON）本来就没有这个原始字段，那是数据管线的活，不在这次前端改动范围内，需要先确认数据端已经产出这个字段。
- 谁受影响：只有 `StockTable` 消费这个 row 形状（`ScreenerPage.jsx:453` 把 `rows` 传给它），改字段名不影响 `Layout.jsx`。
- 怎么验：加完字段后，浏览器里打开 Screener 页任意展开一行的 evidence 抽屉，或临时 `console.log(rows[0])` 确认新字段有值。

### 落点 B — 表头（新增一个 `<th>`）
文件：`frontend/src/components/screener/StockTable.jsx:335-359`（`<thead>` 里那一串 `<SortTh>`/`<th>`）
- 要排序的列用 `<SortTh k="xxx" sort={sort} onSort={clickSort} align="right">{tr('scr.col.xxx')}</SortTh>`（跟 `relVol` 那行长一样，`StockTable.jsx:353`）；不需要排序的列用裸 `<th>`（跟 `align`/`state` 两列一样，`StockTable.jsx:341-343`）。
- 如果要排序，还要在 `SORTS` 对象里加一行 `xxx: { get: (r) => r.xxx }`（`StockTable.jsx:234-246`）。
- 谁受影响：`<thead>` 加一列后，展开抽屉那行的 `colSpan={15}`（`StockTable.jsx:207`）要同步 +1，否则展开的 evidence 行宽度会跟表头错位。当前列数是 15（# / ticker / heat / align / state / groupTrend / rs1 / rs3 / rs6 / accel / h52 / relVol / vol5050 / tq / caret），加一列后改成 16。
- 怎么验：跑起来后目测表头和抽屉行是否对齐；抽屉行错位是最容易漏掉的坏法，因为它默认收起、光看表格第一眼看不出来。

### 落点 C — 数据格（新增一个 `<td>`）
文件：`frontend/src/components/screener/StockTable.jsx:379-436`（`RowPair` 函数体，`<td>` 序列跟 B 的 `<th>` 序列必须一一对应、顺序一致）
- 纯数值列照抄 `h52`/`relVol` 那两个 `<td>` 的写法（`StockTable.jsx:420-425`：null 显示 `—`，否则格式化数字）。
- 有图形/复合渲染的列（如 `AlignDots`、`GroupTrendCell`、`Squares`）抽成独立小组件，照抄 `AlignDots`（`StockTable.jsx:407`）或 `Squares`（`StockTable.jsx:433-434`）调用方式，不要把渲染逻辑堆进 `RowPair` 主体。
- 谁受影响：只有这一个文件内部；`ScreenerPage.jsx` 不用动（它不关心 `StockTable` 内部怎么画）。
- 怎么验：新 `<td>` 插入的位置必须和 B 里新 `<th>` 插入的位置一致（第几个 `<SortTh>`/`<th>` 对应第几个 `<td>`），错位不会报错，只会让数据显示在错的表头下面——这是最隐蔽的坏法，肉眼看列头文字和列里数字是否对得上来验。

### 落点 D — 双语列名
文件：`frontend/src/i18n/translations.js:387-397`（英文块）+ `frontend/src/i18n/translations.js:782-792`（中文块，两块结构一一对应、行号错开 395 行）
- 加一对 `'scr.col.xxx': 'XXX'`（英文）+ `'scr.col.xxx': '中文名'`（中文），两处都要加，漏一处会在切语言时显示 key 本身（`scr.col.xxx` 原样出现在表头上）。
- 参照：`relVol` 在两块里分别是 `'scr.col.relVol': 'Rel vol'`（`translations.js:394`）和 `'scr.col.relVol': '相对量'`（`translations.js:789`）。
- 已有先例但没上表格的：`scr.col.indPct`（`translations.js:397,792`）——`indPct` 字段（`ScreenerPage.jsx:225`）目前只在展开抽屉里当证据文案显示（`StockTable.jsx:216-217`），没有对应的 `<th>`/`<td>`。如果新列想要的效果是「抽屉里的一行文字」而不是「表格新增一整列」，改的地方是 `StockTable.jsx:210-220`（抽屉证据块）而不是落点 B/C——先确认 Andy 要的是「新列」还是「抽屉多一行证据」，两者落点完全不同。

### 附注：文件头的设计意图
`ScreenerPage.jsx:18-22` 的注释写着「row set 随筛选变化，columns never change」——说的是同一张表在切换 scan/state/theme 时列不变，不是「禁止给这张表加列」的规矩，不构成阻碍，仅供改动时理解原设计意图。

## 4 · 落地前的测试基线

按 skill 要求，方案落地前应先跑一遍现有测试、把绿/红写进方案（不能推到"落地时再跑"）。本次尝试：

```
$ cd frontend && npx vitest run src/components/screener/heatMark.test.jsx
Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'vitest' ...
```

**baseline 状态：未跑通**，原因是这个 worktree（`skill-os-v2`）没有装 `node_modules`（vitest 本身找不到），不是代码问题。如实记录：**没有可用的绿/红基线**，落地前必须先在装好依赖的环境里跑一遍 `npm test`（或至少 `heatMark.test.jsx` 所在的 screener 目录）确认现状全绿，再动落点 B/C，改完再跑一遍确认还是全绿——因为没有 mount 整个 `StockTable`/`ScreenerPage` 的回归测试（见第 1 节），列错位这类问题现有测试**验不出来**，唯一的核对手段是跑起页面肉眼看表头和数据对不对得上。

## 结论（先说这句）

不改 `ScreenerPage.jsx` 本体，改 `frontend/src/components/screener/StockTable.jsx`（表头 `:335-359` + 数据行 `:379-436`，两处顺序必须对应，抽屉 `colSpan={15}→16` 别忘）+ `frontend/src/i18n/translations.js`（英中各一行 `:387-397` / `:782-792`）；只有当新列要的字段 row 里还没有时，才需要回头碰 `ScreenerPage.jsx:209-236` 加一行取值。没有整页渲染测试兜底，落地后要手动核对列头和数据对齐，别只信"没报错"。
