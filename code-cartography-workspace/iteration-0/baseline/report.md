# RED 基线报告 — WatchlistPage.jsx 整理任务（无 code-cartography skill）

证据源：
- `.superpowers/sdd/2026-09-04-skill-os-v2/red/baseline_toolcalls.txt`（3 次工具调用逐字记录）
- `.superpowers/sdd/2026-09-04-skill-os-v2/red/baseline_final_answer.md`（完整方案）
- 复核环境：worktree `/Users/taolezhu/Documents/AI-Trading-System/.claude/worktrees/skill-os-v2`，`frontend/src/components/watchlist/WatchlistPage.jsx` 现状 1195 行（`wc -l` 实测，与它的判断一致）。

## Step 2 六问逐条作答

### 1. 有没有先盘消费者？
有，但只做了一半。第 2 次工具调用就是消费者扫描：
```
grep -rn "from.*WatchlistPage'" --include="*.jsx" --include="*.js" frontend/src | grep -v "node_modules"
```
在最终方案里它也确实用上了这次扫描的结果——三个 test 文件的静态 import 被列进了"逐段搬迁映射"下方的风险清单。顺序是对的（先扫再答，不是先答后凑证据）。

### 2. grep 了几种拼法？
**只有 1 种**：单引号收尾的 `from ... WatchlistPage'`。没有测试双引号版本、`require(`、动态 `import(`，也没有搜索路由按路径字符串挂载的写法（如 `Rail.jsx` 里的 `hash: '#/watchlist'`）。

### 3. 量了什么数？
第 3 次工具调用是唯一的"量数"动作：
```
ls -la frontend/src/components/watchlist/ && wc -l frontend/src/components/watchlist/*.js frontend/src/components/watchlist/*.jsx 2>/dev/null && ls -la frontend/src/components/watchlist/shortlist/
```
只量了**行数**和**目录清单**。它的方案文字里断言"9 个展示组件""五层不相关的东西"，但从未用命令数过组件个数、`useState`/`useEffect` 个数或直接 `fetch(` 次数——这些断言全靠读一遍代码的印象，没有一条配数字。

### 4. 拆分建议带不带 file:line？
带，而且完整、准确。"逐段搬迁映射"表把 1195 行拆成 18 段行号区间，逐段标去处。抽样核对（`sed -n '40p;120p;291p;381p;944p'` 实测）：第 944 行确实是 `export default function WatchlistPage(...)`，与表格"944-1195"的起点吻合；`.orig` 备份文件的 40993 字节也和它报的数字一致。这是它做得最扎实的一步。

### 5. 有没有直接开始重写？
没有。它在只读约束下明确说"我没有动仓库任何文件"，方案末尾写"如果要我实际动手，告诉我一声我就在这个 worktree……落地"——是在等一句"动手"，不是先斩后奏。

### 6. 找了什么借口？
没找到没有证据支撑的借口。它的核心论断（"五层没有文件边界"）配着三个 test 文件反向 import 私有函数的证据，"shortlist/ 已经验证过的规范"也配着第 3 次工具调用里 `ls shortlist/` 的真实目录结构。唯一站不住脚的地方不是"编借口"，是**证据覆盖面本身不够**（见下一节的 M/N）——它没有为覆盖不足找借口，只是没意识到覆盖不足。

## 消费者扫描漏报实测：N=4，M=5

它那条命令的实际命中：
```
$ grep -rn "from.*WatchlistPage'" --include="*.jsx" --include="*.js" frontend/src | grep -v "node_modules"
frontend/src/components/Layout.jsx:33:import WatchlistPage from './watchlist/WatchlistPage'
frontend/src/components/watchlist/pickRs.test.js:2:import { pickRs, RS_BANDS } from './WatchlistPage'
frontend/src/components/watchlist/exHealthExempt.test.js:2:import { shown } from './WatchlistPage'
frontend/src/components/watchlist/gateWords.test.js:2:import { gateWords, tradeableCount } from './WatchlistPage'
```
N = 4 个文件。

用更宽的拼法重跑：
- 双引号版 `from.*WatchlistPage"` → 0 命中（这条确实没漏，写实）。
- `require(.*WatchlistPage` → 0 命中（这条也没漏）。
- 动态 `import(.*WatchlistPage` → **2 处命中，同一个新文件**：
  ```
  frontend/src/components/watchlist/provenanceCount.test.jsx:43:  const { default: WatchlistPage } = await import('./WatchlistPage')
  frontend/src/components/watchlist/provenanceCount.test.jsx:56:  const { default: WatchlistPage } = await import('./WatchlistPage')
  ```
- 整仓（含 `pipeline/`、`data/reference/`、`docs/`）搜裸字符串 `WatchlistPage`：命中 `pipeline/tests/test_federation_board_lane.py`、`data/reference/DATA_CONTRACTS.md`、`docs/` 下三份规划文档等——逐一打开确认，**全部是文档/规划里的文字提及，不是代码 import**，不构成真实消费者，不计入 M（如果算文档提及也算漏报会虚报数字，这里照实排除）。
- 路由按路径字符串挂载：`frontend/src/components/Rail.jsx:76` 有 `hash: '#/watchlist'`，`Layout.jsx:329` 靠 `current === 'watchlist'` 字符串比对来挂载组件——这条路由不经过组件名，静态 grep 组件名永远搜不到它。本次拆分不改导出路径所以风险为零，但作为**方法论漏洞**它依然存在：如果这次是要拆分/搬迁整个页面（而不只是拆文件内部函数），这条路由绑定就会被漏检。

**M（frontend 代码里真实 import WatchlistPage 的文件数）= 5**（Layout.jsx + pickRs.test.js + exHealthExempt.test.js + gateWords.test.js + provenanceCount.test.jsx）。
**N（它那条命令找到的）= 4**。**漏报 1 个文件，漏报率 20%。**

漏掉的 `provenanceCount.test.jsx` 不是随便一个测试——它的文件头注释写着这是为一个真实的"2.1x bug"写的回归测试："a unit test on a selector the page never calls would have stayed green through the whole four days this was wrong. So this test mounts the page and reads the sentence."，即它专门挂载整个页面组件校验渲染输出，是 13 文件拆分后**最可能因为接线错误而失手却又最容易被忽略**的一个消费者。它的最终方案"逐段搬迁映射"下方只点名了 `pickRs.test.js`/`gateWords.test.js`/`exHealthExempt.test.js` 三个测试文件要改 import，完全没提到 `provenanceCount.test.jsx`（虽然这个文件因为 import 的是 default export、路径不变，理论上不需要改 import，但它也从未被列入需要特别注意的清单——风险小节里提到要跑它，但没提到它是唯一测渲染输出的文件，值得优先跑）。

## 它没量的三个数

```
$ grep -n "^export " WatchlistPage.jsx | wc -l   # 7 (6 具名 + 1 default)
$ grep -c "useState(" WatchlistPage.jsx          # 9
$ grep -c "useEffect(" WatchlistPage.jsx         # 1
$ grep -n "fetch(" WatchlistPage.jsx | wc -l     # 0（数据经 useWatchlist hook 拿，不直接 fetch）
```
它的方案文字里提到"页面级状态与路由"这一层，但从未用命令验证过状态量级（9 个 `useState` + 1 个 `useEffect`）——这个数字直接决定"瘦身到 ~200 行"这个目标是否现实：`useState` 全留在壳层意味着壳层不是纯路由拼装，是有实质状态逻辑的，200 行的估计没有配对任何计算依据。

## 做得对的地方（不要在 skill 里重新发明）

- 先 grep 再下结论，顺序对。
- file:line 迁移表逐段可核实，抽样全部命中。
- 主动指出 `.orig` 备份文件（40993 字节，路过发现），并诚实标注"不属于本次任务范围，是否清理由你定"——没有借题发挥去动它。
- 引用 `shortlist/` 目录规范时先用 `ls` 验证了它真实存在这个模式，不是凭印象断言。
- 只读约束下没有动手，方案末尾明确留了"要不要我落地"的决策点给人类，不是自作主张重写。

## 这份 skill 要堵的是什么

- 消费者扫描必须跑 ≥4 种拼法（单引号 `from`、双引号 `from`、`require(`、动态 `import(`），去重后的文件数才算 M，只跑 1 种拼法得到的数字不能当结论用。
- 消费者扫描必须包含一次整仓搜索（含 `pipeline/`、`data/reference/`、`docs/`），命中的文档提及要逐条打开确认是不是代码 import，不是就明确排除并写清楚"查过，是文档提及"，不能跳过这一步。
- 消费者扫描必须额外检查一次"按路径字符串挂载"的写法（路由表、hash 表、动态 key 匹配），因为组件名 grep 天然搜不到这类间接引用。
- 提出拆分方案前必须先跑一次现有测试确认 baseline 绿或红，并把结果写进方案；不能把"跑测试"只放进"未来工作量"清单里当作分步骤之一。
- 度量拆分依据时必须现场跑三个数（export 个数、`useState`/`useEffect` 个数、直接 `fetch(` 次数），只用 `wc -l` 的行数不能支撑"页面级状态"这类判断；数字要出现在方案正文而不是只存在于脑内印象。
- 消费者清单里如果有测试文件是"挂载整页渲染做回归断言"的（如本例校验一个曾经错了四天的 bug），必须在方案里点名并标记为拆分后优先验证对象，不能和普通单测一起一笔带过。
