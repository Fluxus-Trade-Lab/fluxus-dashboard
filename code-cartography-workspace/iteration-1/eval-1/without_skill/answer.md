# WatchlistPage.jsx（1195 行）整理

结论：这一个文件塞了三样东西——① 一堆与 React 无关的纯函数（配色数学、RS 口径、过滤排序），② 六七个展示组件，③ 顶层页面的状态和路由。加功能九成情况不用读完 1195 行，按下面的地图跳到对应段落就够；顺手体检发现一个会炸的 bug 和一个死文件，一并列在最后。

---

## 一、文件地图（按出现顺序，行号为当前版本）

| 段落 | 行号 | 是什么 | 是否是 React 组件 |
|---|---|---|---|
| 文件头 JSDoc | 1–38 | 页面设计哲学（为什么不是 Screener、为什么是卡片不是长页、三条禁止事项） | 否，纯注释 |
| `ZONE_ORDER` / `HIDDEN_ZONES` | 40–60 | 六个分区的顺序和隐藏名单 | 否 |
| `STEPS` / `DEFAULT_STEP` | 62–120 | 五步流程的配置（每步的 find/with/dont/wants/panels/switches） | 否 |
| `nf` / `tr` | 122–128 | 格式化 + i18n 兜底 | 否 |
| `gateWords` | 130–158 | 把 gate 对象拼成一句话文案 | 否，纯函数，**已被 `gateWords.test.js` 直接 import** |
| `tradeableCount` | 160–176 | 取 universe 计数，带新旧字段兜底 | 否，纯函数，**已被 `gateWords.test.js` 直接 import** |
| `pickRs` | 178–200 | 决定这批行用哪个 RS 口径（`rs_1m` vs `rs_line_pctl_21`） | 否，纯函数，**已被 `pickRs.test.js` 直接 import** |
| `go` | 202 | 路由跳转（改 `location.hash`） | 否 |
| `RS_BANDS` / `rsInk` | 204–254 | RS 数字的染色阈值 | 否，`RS_BANDS` 被 `pickRs.test.js` import |
| **ATR 配色数学** | 256–404 | `ATR_STOPS`、`ATR_INK`、`hexToRgb`、`mix`、`relLum`、`contrast`、`lStar`、`toLightness`、`atrFill`、`useDarkTheme`、`atrTitle` | 只有 `useDarkTheme` 是 hook，其余全是纯色彩计算，与 React/业务完全无关 |
| `Name` | 406–453 | 一个 ticker 格子（代码 + 主题圆点 + RS 数字），用到上面的 ATR 配色 | React 组件 |
| `Names` | 455–473 | 网格布局包一层 `Name` | React 组件 |
| `Switch` | 475–502 | 一个通用开关按钮 | React 组件 |
| **过滤/排序核心** | 504–569 | `RS_FLOOR`、`FLOOR_EXEMPT`、`floorApplies`、`rsOf`、`EX_HEALTH_EXEMPT`、`exHealthApplies`、`shown()` | 否，纯函数，**`shown` 被 `exHealthExempt.test.js` 直接 import**——这是全文件业务逻辑最核心的一段 |
| `Count` | 571–607 | 显示"过滤后/全部"两个数字 | React 组件 |
| `ScanCard` | 609–734 | **首页**卡片：折叠/展开、recipe、chase 分组、复制按钮 | React 组件 |
| `Panel` | 736–798 | **详情页**（`#/watchlist/<zone>`）里一个 panel 的展示 | React 组件，逻辑与 `ScanCard` 大量重叠（见下面「体检」） |
| `ZoneDetail` | 800–844 | 一个分区的详情页整体布局 | React 组件 |
| `StepBar` | 846–914 | 五步选择条 + 当前步骤的三行说明 | React 组件 |
| `Tabs` / `MORNING` / `SHORTLIST` | 916–942 | 「晨报 / Short List」两个 tab | React 组件 |
| `WatchlistPage`（默认导出） | 944–1195 | 顶层：state（四个开关+step）、路由分发（shortlist tab / zone detail / 首页）、首页布局组装（provenance、开关行、StepBar、卡片网格、cross-zone、脚注） | React 组件（页面根） |

一句话版本：**1–404 行是"数据怎么算、怎么上色"，406–942 行是"一个个积木组件"，944–1195 行是"顶层怎么拼"。** 三层分得很清楚，只是物理上写进了同一个文件。

---

## 二、加功能对照表——不知道改哪就查这张表

| 你想加/改 | 去哪段（行号） | 备注 |
|---|---|---|
| 新增一个开关（像 exHealth/pool3m 那种） | `Switch` 组件（475）定义样式；state 声明在 963–969；渲染在 1081–1088；真正生效要接进 `shown()` 的过滤逻辑 548–569 | 四步都要碰，别漏了 `shown()` |
| 新增/调整五步流程里的一步 | `STEPS` 数组 82–119 | 纯配置，改完 `StepBar`（846）和顶层 `stepCounts` 计算（1042–1049）自动跟着变 |
| 改 ATR 位置的配色规则/阈值 | `ATR_STOPS` 291–299 及其下方色彩数学 300–404 | 这块和 React 无关，改完在浅色/深色两套主题里都要肉眼过一遍（文件注释里写了 contrast 实测值） |
| 改一个 ticker 格子上显示什么（加个角标/字段） | `Name` 组件 406–453 | 首页卡片（`Names`→`ScanCard`）和详情页（`Names`→`Panel`）共用这一个组件，改一处两处都变 |
| 改「哪些行会被藏起来」的口径（RS floor、healthcare 排除等） | `shown()` 548–569 及其上方的 `floorApplies`/`exHealthApplies`/`rsOf` 504–546 | 这是唯一决定"某行是否上屏"的地方，`Count`/`ScanCard`/`Panel`/顶层 `stepCounts`/`emptied` 全部依赖它 |
| 加一个新 panel 类型的展示方式（比如首页卡片和详情页样式要不一样） | 首页卡片逻辑在 `ScanCard` 609–734；详情页逻辑在 `Panel` 736–798 | 这两个组件几乎是同一份东西抄了两份（recipe 折叠、复制按钮、rows 判空），加字段容易只改一边漏另一边，见下面体检 |
| 改分区（zone）顺序、新增/隐藏一个分区 | `ZONE_ORDER`/`HIDDEN_ZONES` 40–60；`zones` 的 `useMemo` 974–982 | |
| 改 RS 数字用哪个口径、染色阈值 | `pickRs` 199–200；`RS_BANDS` 237–246；`rsInk` 248–253 | |
| 改 provenance 那行文案（universe 计数、gate 说明） | `gateWords` 143–158；`tradeableCount` 175–176；渲染在 1073–1080 | |
| 改 cross-zone（跨榜）那块折叠区 | 顶层 1149–1184 | |
| 加一个新 tab（现在只有「晨报」「Short List」两个） | `Tabs` 916–942；顶层 `routeZone` 分发 1007–1022 | |
| 改 Short List 本身 | 不在这个文件——`ShortListPage.jsx`（`frontend/src/components/watchlist/shortlist/`），本文件只在 1007–1015 挂了个入口 | |

---

## 三、顺手体检（没动手改，只是看出来的）

1. **一个会炸的 bug：`view` 在声明前被用到（TDZ ReferenceError）。**
   [`WatchlistPage.jsx:1017-1025`](frontend/src/components/watchlist/WatchlistPage.jsx#L1017-L1025)：
   ```js
   const at = zones.findIndex((z) => z.key === routeZone)
   if (at >= 0) {
     return (
       <ZoneDetail zone={zones[at]} index={at} total={zones.length} view={view} />   // ← 1020 行用了 view
     )
   }

   const cross = data.cross_zone || []
   const view = { highOnly, floor, pool3m, exHealth }                                 // ← 1025 行才 const 声明
   ```
   `view` 用 `const` 声明在 1025 行，但 1020 行的分支在它声明**之前**执行到，处在 JS 的 temporal dead zone 里——只要访问 `#/watchlist/<zone>`（点开任意一个分区详情页）这条路径，理论上会直接抛 `ReferenceError: Cannot access 'view' before initialization`，`ZoneDetail` 拿到的也从来不是真正的开关状态。没有去跑测试/浏览器核实是否被某种打包器优化掩盖了，但从代码本身看这是一个真实缺陷，建议找前端线确认后修（把 `const view = {...}` 挪到 1017 行之前即可，一行搬家）。

2. **`ScanCard`（609–734）和 `Panel`（736–798）高度重复。** 两者都做「取 `shown()` 的行 → recipe 折叠按钮 → 复制到剪贴板 → rows 为空时的文案」，字段名和结构几乎一致，只是外壳（卡片 vs 详情条）不同。以后任何一条过滤/展示规则的改动都要小心两边都改——这也是为什么上面的对照表里把它们并排列出来。如果以后要拆文件，这是第一个该合并成"共享 hook + 两个薄壳组件"的地方。

3. **`WatchlistPage.jsx.orig` 是个死文件。** [`frontend/src/components/watchlist/WatchlistPage.jsx.orig`](frontend/src/components/watchlist/WatchlistPage.jsx.orig)，866 行，早于当前版本，`git log` 显示它是在 `c166c974`（"the five steps..."）那次提交里被一起提交进仓库的，像是合并冲突时留下的 `.orig` 备份文件误提交。全仓库搜索没有任何 import 引用它，纯粹占地方、还会让人误读成"另一个版本的真实实现"。不在这次任务范围内改，但值得单独清理。

4. **纯函数已经被测试当成独立模块在用，但物理上仍嵌在组件文件里。** `gateWords.test.js`、`pickRs.test.js`、`exHealthExempt.test.js` 都是直接 `import { xxx } from './WatchlistPage'`——测试早就把 `gateWords`/`tradeableCount`/`pickRs`/`RS_BANDS`/`shown` 当作独立的逻辑单元对待，只是它们至今仍和十来个 React 组件挤在同一个 1195 行文件里。

---

## 四、如果以后要真正拆分文件（建议，未执行）

同目录下的 `shortlist/` 子目录已经在用这个模式——`ledger.js`/`manualCards.js`/`scales.js`/`sync.js` 各自是纯逻辑 + 对应的 `*.test.js`，和 `ShortListPage.jsx`/`NameCard.jsx`/`CardChart.jsx` 这些视图分开放。`WatchlistPage.jsx` 可以照抄这个已经验证过的结构，照当前测试文件的 import 边界拆：

- `watchlist/atrColor.js` ← 256–404 行的配色数学（`ATR_STOPS`/`atrFill`/`toLightness`/…），与 React 无关，最容易搬、影响面最小
- `watchlist/scanFilters.js` ← 504–569 行的 `shown`/`RS_FLOOR`/`floorApplies`/`exHealthApplies`，`exHealthExempt.test.js` 的 import 路径改一行就行
- `watchlist/format.js` ← `gateWords`/`tradeableCount`/`pickRs`/`RS_BANDS`/`nf`/`tr`，对应 `gateWords.test.js`、`pickRs.test.js`
- `watchlist/steps.js` ← `STEPS`/`ZONE_ORDER`/`HIDDEN_ZONES` 纯配置
- 组件层（`Name`/`Names`/`Switch`/`Count`/`ScanCard`/`Panel`/`ZoneDetail`/`StepBar`/`Tabs`）留在 `WatchlistPage.jsx`，或者进一步按"首页积木"/"详情页积木"拆成两个文件

这样拆完 `WatchlistPage.jsx` 本体大概能从 1195 行降到 400 行左右（组件 + 顶层拼装），纯函数各自可测、可复用。但这是后续动作，本次任务只读不改，未执行。
