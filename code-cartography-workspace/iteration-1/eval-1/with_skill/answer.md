# WatchlistPage.jsx 地图（只读，不重写）

- [x] 1 盘消费者
- [x] 2 量
- [x] 3 拆分建议
- [x] 4 baseline 测试颜色

目标文件：`frontend/src/components/watchlist/WatchlistPage.jsx`（1195 行）

---

## 1 · 消费者（M=5，含 1 个整页挂载回归测试）

### 1a · 四种拼法 grep（去重前）

```
T=WatchlistPage; D=frontend/src
grep -rn "from.*$T'"    --include='*.jsx' --include='*.js' $D | grep -v node_modules
grep -rn "from.*$T\""   --include='*.jsx' --include='*.js' $D | grep -v node_modules
grep -rn "require(.*$T" --include='*.jsx' --include='*.js' $D | grep -v node_modules
grep -rn "import(.*$T"  --include='*.jsx' --include='*.js' $D | grep -v node_modules
```

命中：

| 拼法 | 命中数 | 文件 |
|---|---|---|
| `from '...'` | 4 | `Layout.jsx:33`、`gateWords.test.js:2`、`pickRs.test.js:2`、`exHealthExempt.test.js:2` |
| `from "..."` | 0 | — |
| `require(` | 0 | — |
| 动态 `import(` | 2 处（1 文件） | `provenanceCount.test.jsx:43,56` |

单跑第一条只得 N=4，四条全跑去重后 **M=5**（漏报 1 个用动态 `import()` 挂载的测试文件）。

### 1b · 整仓裸字符串搜（`WatchlistPage` 全仓命中，逐条核实）

命中 `pipeline/`、`docs/`、`data/reference/`、`data/research/` 共 16 个文件，逐条打开确认：**全部是文档 / 规划 / 事故记录里的文字提及（多数带 `file:line` 引用当时的行号，如 `WatchlistPage.jsx:142`），没有一处是代码 import**，不计入 M。列出以便交叉核对：

- `pipeline/tests/test_federation_board_lane.py:50` — 断言用的是一个**假想路径字符串** `"frontend/src/pages/WatchlistPage.jsx"`（注意是 `pages/` 不是真实的 `components/watchlist/`），测的是联邦看板的「路径→线名」映射函数，不是真实引用，不计入 M。
- `data/reference/DATA_CONTRACTS.md:713`、`data/research/night_reports/INBOX.md:288`、`data/research/repo_health/2026-08-24.md`、`2026-08-31.md`、`data/research/ui_previews/2026-08-26|27|29/README.md`、`2026-08-29/build.py:64` — 均为运营/回顾文档里点名 `file:line` 描述当时代码状态，非 import。
- `docs/plans/2026-08-20-shortlist-design.frontend-review.md`、`docs/superpowers/plans/2026-09-04-skill-os*.md`、`docs/superpowers/specs/2026-09-04-skill-os-v2-design.md`、`.claude/skills/code-cartography/`、`code-cartography-workspace/` — 都是这次「建 code-cartography skill」本身的规划/评测语料，提到 WatchlistPage 是把它当例子讲，不是消费者。

### 1c · 路径字符串挂载（组件名 grep 搜不到的绑定）

```
grep -rn "watchlist" frontend/src/components/Rail.jsx frontend/src/components/Layout.jsx
```

- `Rail.jsx:76` — `{ key: 'watchlist', short: 'WCH', hash: '#/watchlist' }`：左侧导航靠这个 key/hash 驱动 `current` 状态，不直接 import 组件名，四次 grep 天然搜不到。
- `Layout.jsx:329` — `{current === 'watchlist' && <WatchlistPage zone={subRoute} />}`：真正的挂载点，字符串比对 + 已在 1a 的 import 里数过。

本次只是「拆文件内部结构」不改导出名/挂载方式，这条绑定风险为零；但若以后要**搬迁整个页面文件**，Rail.jsx:76 这个 key 字符串必须跟着核对，组件名 grep 不会提醒你。

### 1d · 消费者里的整页渲染回归测试（优先验证对象）

**`provenanceCount.test.jsx`**（靠 1a 的动态 `import(` 挂进来，最容易被基线漏掉的那个）—— 用 `render(<WatchlistPage/>)` 挂载整页、读 `screen.getByText(...)` 实际渲染出的句子，不是测某个被导出的选择器。文件头注释自述：它守的是「provenance 行印错数字」的 2.1x bug——`tradeableCount()` 算对不等于渲染处真的调用了它，bug 曾经四天里让一个只测选择器的单测保持全绿。**任何拆分动作只要触碰 943-1195 行的渲染逻辑，第一个要跑的就是这个文件**，其余三个（`gateWords.test.js` / `pickRs.test.js` / `exHealthExempt.test.js`）测的是被导出的纯函数本身，改动小范围时次要。

---

## 2 · 量（现场跑，贴命令输出）

```
F=frontend/src/components/watchlist/WatchlistPage.jsx
wc -l $F                      # 1195
grep -n "^export " $F | wc -l # 7（6 具名 + 1 default）
grep -c "useState(" $F        # 9
grep -c "useEffect(" $F       # 1
grep -n "fetch(" $F | wc -l   # 0（数据经 useWatchlist hook 拿，不在本文件发请求）
```

`useState` 9 处的位置：`387`（`useDarkTheme` 内）、`629`/`630`（`ScanCard` 内 `openRecipe`/`opened`）、`740`（`Panel` 内，同名不同作用域）、`963`/`964`/`965`/`969`/`972`（默认导出的壳层：`highOnly`/`pool3m`/`exHealth`/`floor`/`step`）。**唯一的 `useEffect`（389 行）在 `useDarkTheme` 里**，不在壳层——这条对第 3 节「壳层瘦身到多少行」的估算是硬约束，不是印象。

顶层声明全景（`grep -n "^const \|^function \|^export \|^class "`）：

```
40   const ZONE_ORDER
60   const HIDDEN_ZONES
79   const STEPS
120  const DEFAULT_STEP
122  const nf
125  const tr
143  export const gateWords
175  export const tradeableCount
199  export const pickRs
202  const go
237  export const RS_BANDS
248  const rsInk
291  const ATR_STOPS
313  const ATR_INK
315  const hexToRgb
316  const mix
321  const relLum
325  const contrast
330  const lStar
344  function toLightness
365  export function atrFill
386  function useDarkTheme
398  const atrTitle
406  function Name
464  function Names
482  function Switch
525  const RS_FLOOR
526  const FLOOR_EXEMPT
527  const floorApplies
533  const rsOf
545  const EX_HEALTH_EXEMPT
546  const exHealthApplies
548  export const shown
577  function Count
627  function ScanCard
738  function Panel
800  function ZoneDetail
857  function StepBar
916  const MORNING
917  const SHORTLIST
922  function Tabs
944  export default function WatchlistPage
```

已有的姊妹目录 `frontend/src/components/watchlist/shortlist/`（`ShortListPage.jsx` + `NameCard.jsx`/`CardChart.jsx` 组件 + `scales.js`/`ledger.js`/`sync.js`/`manualCards.js` 纯逻辑，逐个配 `*.test.js`）已经是本仓库对「页面拆成组件 + 纯逻辑 + 各自测试」这个模式的现成先例，第 3 节照这个先例分组，不是发明新规范。

---

## 3 · 拆分建议（每条：搬什么 → 搬到哪 → 谁受影响 → 怎么验没坏）

拆了省什么，先说一遍：现在改「ATR 热力图配色算法」和改「五步导航条文案」要打开同一个 1195 行文件、在里面滚动定位；拆开后两件事分别落在两个 <100 行的文件里，找不到该改哪的问题直接由文件名回答。9 个 `useState` 目前混在 3 个不同层级（工具 hook / 卡片组件 / 页面壳层）里，拆开后每层的状态数量才对得上它该有的职责。

| # | 搬什么 (file:line) | 搬到哪 | 谁受影响 | 怎么验没坏 |
|---|---|---|---|---|
| A | `gateWords` 143-174、`tradeableCount` 175-198、`pickRs` 199-201 | `watchlist/gates.js`（纯函数，无 React 依赖） | `gateWords.test.js`、`pickRs.test.js` 的 import 路径要从 `./WatchlistPage` 改成 `./gates`；`WatchlistPage.jsx` 内部改成 `import { gateWords, tradeableCount, pickRs } from './gates'` | 跑 `gateWords.test.js` + `pickRs.test.js`，两个都应保持绿；`provenanceCount.test.jsx` 间接用到 `tradeableCount`，一并跑 |
| B | `RS_BANDS` 237-247、`rsInk` 248-290 | `watchlist/rsColor.js` | 内部消费者：`Name`（406-463，读 `rsInk`）、壳层第 1191 行 legend 文案（读 `pickRs` 不读这俩，无关）；外部：`pickRs.test.js` 里 `import { pickRs, RS_BANDS } from './WatchlistPage'` 要跟着改成从 `./rsColor` 拿 `RS_BANDS` | `pickRs.test.js` 绿；人工核对 `Name` 组件渲染出的颜色没变（无既有测试覆盖这条，落地时应补一个) |
| C | `ATR_STOPS` 291-312、`ATR_INK` 313-314、`hexToRgb` 315、`mix` 316-320、`relLum` 321-324、`contrast` 325-329、`lStar` 330-343、`toLightness` 344-364、`atrFill` 365-385 | `watchlist/atrColor.js`（纯数学，零 React，本文件里最独立的一坨；`atrFill` 保留 `export`） | 内部：谁调用 `atrFill` 需要在文件里另查——**导出的 `atrFill` 目前在全仓没有任何外部消费者**（1a 四种 grep 都是 0），只在本文件内部用；外部无 import 需要改 | 无外部测试覆盖这条链路，落地时人工截图对照 ATR 徽章配色前后一致，或补一个针对 `atrFill` 输入输出的单测（当前是空白） |
| D | `useDarkTheme` 386-397（含唯一的 `useEffect`）、`atrTitle` 398-405、`Name` 406-463、`Names` 464-481、`Switch` 482-524 | `watchlist/primitives.jsx` | 壳层第 944 行往下会调用 `Names`/`Switch`；`ScanCard`(627-737)/`Panel`(738-799) 会调用 `Name`/`Names` | 无专用测试；`provenanceCount.test.jsx` 挂载整页会间接渲染这些组件，是目前唯一的回归网 |
| E | `RS_FLOOR` 525、`FLOOR_EXEMPT` 526、`floorApplies` 527、`rsOf` 533、`EX_HEALTH_EXEMPT` 545、`exHealthApplies` 546、`shown` 548-576 | `watchlist/visibility.js`（纯函数，`shown` 已有专属测试） | `exHealthExempt.test.js` 的 `import { shown } from './WatchlistPage'` 改成 `./visibility`；壳层多处调用 `shown(...)` 需改 import 来源 | 跑 `exHealthExempt.test.js`，应保持绿 |
| F | `Count` 577-626、`ScanCard` 627-737（含 2 个 `useState`）、`Panel` 738-799（含 1 个 `useState`） | `watchlist/ScanCard.jsx`（这三个组件耦合最紧，`Panel` 直接渲染 `ScanCard`，`ScanCard` 渲染 `Count`，拆开单个意义不大，整组一起搬） | 壳层第 1155-1163 行 `<ScanCard .../>` 的渲染循环 | 无专用单测；`provenanceCount.test.jsx` 会挂载到这层，落地后必须跑一遍看还绿不绿 |
| G | `ZoneDetail` 800-856 | `watchlist/ZoneDetail.jsx`（本来就是 `#/watchlist/<zone>` 下钻的独立路由目标，和卡片网格是两条渲染路径，边界最干净） | 壳层第 1015-1019 行 `at >= 0` 分支调用它 | 无专用测试，人工核对某个 zone 的下钻页 |
| H | `StepBar` 857-915 | `watchlist/StepBar.jsx` | 壳层第 1130 行渲染它 | 无专用测试 |
| I | `MORNING`/`SHORTLIST` 916-921、`Tabs` 922-943 | `watchlist/Tabs.jsx` | 壳层 1010、1024 行渲染 `Tabs`，`SHORTLIST` 常量还在壳层第 1010 行的 `if (routeZone === SHORTLIST)` 分支里被读，需要跟着 import | 无专用测试 |
| J（保留） | `ZONE_ORDER` 40、`HIDDEN_ZONES` 60、`STEPS` 79-119、`DEFAULT_STEP` 120、`nf` 122、`tr` 125-128、`go` 202、默认导出 944-1195 | 留在 `WatchlistPage.jsx` | 这就是拆完之后的壳层本体 | 上面 A-I 全部落地后跑一次全量 `frontend` 测试套件 |

行号抽样核对（本节表里引用的边界）：

```
sed -n '40p;120p;143p;199p;237p;291p;365p;386p;406p;482p;525p;548p;577p;627p;738p;800p;857p;916p;922p;944p' \
  frontend/src/components/watchlist/WatchlistPage.jsx
```

已在第 2 节的「顶层声明全景」逐行核对过，每一行都命中对应的声明关键字，不是抽象区间。

**J 组瘦身到多少行，算一遍不猜**：doc 注释(9-38，30 行) + imports(1-8，8 行) + `ZONE_ORDER`/`HIDDEN_ZONES`/`STEPS`/`DEFAULT_STEP`(40-120，81 行) + `nf`/`tr`(122-128，7 行) + `go`(202，1 行) + `MORNING`/`SHORTLIST`(916-921，6 行) + 默认导出本体(944-1195，252 行) ≈ **385 行左右**，不是「瘦身到 ~200 行」这种整数目标——252 行的默认导出本体（状态 + 路由分支 + JSX 组装）本身就没被 A-I 任何一组动到，它是页面真正的壳层职责，A-I 省的是「找 ATR 配色数学该改哪个 300 行区间」，不是让壳层本身变短。

**关于 `WatchlistPage.jsx.orig`**：目录里还躺着一个 `WatchlistPage.jsx.orig`（866 行，40993 字节，mtime 09-04 22:28），不在本次盘点范围内、也不在四种 grep 的任何命中里（没人 import 它）。是否清理留给你定，本次没有动它。

---

## 4 · baseline 测试颜色（提方案前的输入，不是工作量清单里的一步）

尝试执行：

```
cd frontend && npx vitest run src/components/watchlist
```

结果：**跑不起来**——`frontend/node_modules` 在这个 worktree 里不存在（`find . -maxdepth 2 -name node_modules` 空），`vitest.config.js` 连 `vitest/config` 都 resolve 不到。装依赖（`npm install`）会在仓库里新建 `node_modules`，违反本次任务「只读、只许新建这一个 answer.md」的限制，所以没有执行。

**如实报告：baseline 颜色现在是「未知」，不是绿色。** 落地前必须先在一个允许装依赖的环境里把 `gateWords.test.js` / `pickRs.test.js` / `exHealthExempt.test.js` / `provenanceCount.test.jsx` 这四个跑一遍、记下真实颜色，再按第 3 节的表逐组搬；落地时每组之后至少再跑一次 `provenanceCount.test.jsx`（它是唯一挂载整页的回归测试），并对新拆出的纯逻辑文件（`gates.js`/`rsColor.js`/`atrColor.js`/`visibility.js`）补齐当前完全没有测试覆盖的部分（B、C 两组尤其空白）。

---

## 结论

不重写，只给地图。M=5 个真实消费者（1 个页面挂载 + 3 个纯函数单测 + 1 个动态 import 的整页渲染回归测试），后者是拆分时最先要跑的那个。1195 行里 7 个导出、9 个 `useState`（分布在 3 层）、1 个 `useEffect`（在可独立抽走的 `useDarkTheme` 里）、0 次直接 `fetch(`。建议按 A-I 十组搬（对照仓库里 `watchlist/shortlist/` 已有的「组件+纯逻辑+测试」拆分先例），壳层留下的是路由分支和页面级状态本身，算出来约 385 行，不是感觉上的整百数字。baseline 测试因环境缺 `node_modules` 跑不了，如实标注为「未知」而非默认绿色，落地前必须先补跑。要不要落地、先落哪一组，留给你拍板。
