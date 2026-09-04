# 给 ScreenerPage 加一列 —— 改哪

一句话结论：ScreenerPage.jsx 本身不画表格，列都在 `StockTable.jsx` 里定义并渲染；要加一列，主要改 `StockTable.jsx`，数据源头再看是否要补 `ScreenerPage.jsx` 的行构建。

## 涉及文件（按改动顺序）

1. **`frontend/src/components/screener/StockTable.jsx`** — 列在这里，改动最多，分五处：
   - **表头**（约 336-359 行）：加一个 `<th>`（不可排序，如 `Sector`）或一行 `<SortTh k="xxx" ...>`（可排序数值列，仿照 `RS 1M`/`Rel vol` 那几行）。
   - **`SORTS` 映射表**（237-248 行）：若新列要支持点击排序，在这里加 `xxx: { get: (r) => r.xxx }`（字符串列加 `str: true`）。
   - **行渲染 `RowPair`**（379-451 行）：在对应位置插入一个 `<td>`，取值 `r.xxx`，参照已有单元格的空值处理（`== null` 一律显示 `—`，别让 `undefined` 直接渲染成空白——这页所有列都遵守"未测量 ≠ 零/空"这条规矩，看 5-70 行的大注释）。复杂列可以抽成独立组件（参照 `RsCell`/`AlignDots`/`GroupTrendCell`/`HeatCell` 的写法）。
   - **`EvidenceFold` 的 `colSpan={15}`**（207 行）：加列后这个数字要 +1，否则展开行的证据条会错位。
   - 文件顶部的**列注释块**（13-34 行）：这页有约定俗成的"列即约束"文档习惯，新列如果带任何隐含规则（比如空值含义、单位、口径来源），照着 Heat/Align/Group trend 的格式补一段。

2. **`frontend/src/components/screener/ScreenerPage.jsx`** — 只有当新列要展示的数据**还没进入行对象**时才需要碰：
   - 数据组装在 `preState` 这个 `useMemo`（180-242 行），每行对象目前从 `universe`(`u`)、`groups.stocks`(`s`)、`heatByTicker`、`industryState`、`ribbonByHome` 拼出来。想加的字段如果已经在 `u`（`universe.json` 的行，参见 `frontend/src/hooks/useUniverse.js`）或 `s`（`groups.stocks`）上，只需在 209-239 行的 `out.push({...})` 里补一行 `xxx: u?.xxx ?? null`。
   - 如果字段来自一个新的 JSON/数据源（不在 `universe.json` / `groups.json` / 现有 `market` 里），还要先确认管线（pipeline）那边有没有产这个字段——这页的宪法性注释反复强调"前端不自己发明口径"，缺数据源就先去 `data/output/` 或 `DATA_CONTRACTS.md` 查，不要在前端算。

3. **`frontend/src/i18n/translations.js`**（387-397 行英文，782-792 行中文）——如果新列标题想走 `tr('scr.col.xxx')`（像 `ticker`/`heat`/`align` 那样双语），要在两处都加键值对；简单列也可以像 `RS 1M`/`Rel vol` 那样直接硬编码英文字符串，页面里两种写法并存。

## 顺带要看一眼（不一定要改）

- `frontend/src/components/screener/heatMark.test.jsx` —— 现有测试文件，如果新列有值得测的逻辑（比如 `HeatCell` 那种带条件标记的），可能要照着加测试，但不确定这仓库要求"新列必测"，需要问一下。
- `frontend/src/components/screener/ScanBar.jsx` —— 不管列，是过滤器/开关那一条控制栏，除非新列同时想加一个对应的过滤开关（比如新增一个 gate），否则不用碰。

## 关键约束（这个文件里的强规矩，改的时候别踩）

- **列不随筛选变化**：ScreenerPage.jsx 顶部注释写死"changing a scan or a state changes the row set and nothing else — no column appears, disappears, or re-encodes"。新列必须在所有 scan/state/theme 组合下都稳定存在、含义一致，不能只在某个 scan 下才显示。
- **空值语义**：未测量（`null`/无数据）和测量出来是零，是两个不同的东西，全表统一用 `—` 表示"未测量"，别用 `0` 或空字符串顶替。
- **颜色只能用 CSS 变量**（`var(--color-...)`），不要写死颜色值，要兼容亮暗主题。
