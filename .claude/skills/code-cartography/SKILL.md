---
name: code-cartography
description: 给越写越乱的文件或目录先画地图再动刀——盘清谁在读它、量出行数与消费者、给出带 file:line 的拆分建议、落地时带正面对照。Andy 说「这里乱了」「加功能不知道改哪」「拆一下」「重构」「组件太大」「整理代码」时用；周检扫到文件超 800 行（py）或 300 行（jsx）时用；改 frontend/src/components/ 里任何东西之前用。产出地图与建议，不产出重写。
when_to_use: 乱、拆、重构、整理、组件太大、加功能改哪、file 太长、周检、消费者、谁在用这个字段。不触发：修一个明确的 bug、加一个明确的字段、纯样式改动。
paths:
  - "frontend/src/components/**"
  - "pipeline/screeners/run_all.py"
  - "pipeline/adapters/yfinance_adapter.py"
---

# code-cartography — 先画地图，再动刀

复制这张单子进回复，做一项勾一项。四项没勾满，不许给结论。

- [ ] 1 盘消费者（每个导出 ≥4 种拼法 grep，加一次整仓搜，加一次路径字符串搜；去重后的文件数才是 M）
- [ ] 2 量（wc -l 行数、export 个数、useState/useEffect 个数、直接 `fetch(` 次数；四个数都要贴命令输出）
- [ ] 3 拆分建议（每条：搬什么 file:line → 搬到哪 → 谁受影响 → 怎么验没坏；先说「拆了省什么」）
- [ ] 4 落地带正面对照（既有测试先跑一遍记下绿/红 + 新加守边界测试 + 注入真 bug 红一次）

产出是地图和建议，不是重写。要不要落地，留给人拍板。

## 每一步要做到什么（RED 基线实测）

### 1a · 每个导出跑 ≥4 种拼法，去重后才算 M

```bash
T=WatchlistPage; D=frontend/src
grep -rn "from.*$T'"    --include='*.jsx' --include='*.js' $D | grep -v node_modules
grep -rn "from.*$T\""   --include='*.jsx' --include='*.js' $D | grep -v node_modules
grep -rn "require(.*$T" --include='*.jsx' --include='*.js' $D | grep -v node_modules
grep -rn "import(.*$T"  --include='*.jsx' --include='*.js' $D | grep -v node_modules
```

堵的是：基线只跑了第一条（单引号 `from`），得到 N=4。四条全跑得到 M=5，漏报 1 个文件，漏报率 20%。双引号版和 `require(` 这次确实 0 命中，但「0 命中」要跑出来才算数，不是假设出来的。

### 1b · 整仓搜一次裸字符串，文档命中逐条打开确认

范围含 `pipeline/`、`data/reference/`、`docs/`。命中不等于消费者：逐条打开看是不是代码 import，不是就明写「查过，是文档提及，不计入 M」。

堵的是：基线的 grep 只覆盖 `frontend/src`。整仓搜会命中 `pipeline/tests/test_federation_board_lane.py`、`data/reference/DATA_CONTRACTS.md`、`docs/ 下四份规划文档，这些确认后全是文字提及、不计入 M。这一步的产出是一句「排除了什么」，不是一个更大的数。

### 1c · 查一次「按路径字符串挂载」

路由表、hash 表、动态 key 比对，这类引用不经过组件名，组件名 grep 天然搜不到。

堵的是：`Rail.jsx:76` 的 `hash: '#/watchlist'` 和 `Layout.jsx:329` 的 `current === 'watchlist'` 字符串比对，基线四次 grep 一次都碰不到。本次拆分不改导出路径所以风险为零，但方法论上的洞是真的：换成搬迁整个页面，这条绑定就会被漏检。

### 1d · 消费者里有整页渲染回归测试的，点名并标为优先验证对象

判据：这个测试是不是 mount 整个页面读渲染输出。是就单独列一行，写清它守的是哪个 bug。

堵的是：漏掉的那个 `provenanceCount.test.jsx` 正是靠动态 `import(` 挂进来的（命中在 43、56 两行），它 mount 整页读句子，守的是一个真出过的「2.1x bug」，文件头注释自陈：不挂载整页的单测在那个 bug 错的四天里会一直是绿的。基线的迁移表下方只点了 `pickRs.test.js` / `gateWords.test.js` / `exHealthExempt.test.js` 三个，它一次都没被点名。13 个文件拆完，最可能因为接线错误而失手的就是它。

### 2 · 三个数现场跑，行数不算数

```bash
F=frontend/src/components/watchlist/WatchlistPage.jsx
wc -l $F                      # 1195
grep -n "^export " $F | wc -l # 7（6 具名 + 1 default）
grep -c "useState(" $F        # 9
grep -c "useEffect(" $F       # 1
grep -n "fetch(" $F | wc -l   # 0（数据经 useWatchlist hook 拿）
```

堵的是：基线唯一的量数动作是 `wc -l` 加 `ls`。它断言「9 个展示组件」「五层不相关的东西」「页面级状态与路由」，一个都没数过。而 9 个 `useState` + 1 个 `useEffect` 全留在壳层，意味着壳层不是纯路由拼装，「瘦身到 ~200 行」这个目标没有配任何计算依据。数字要出现在方案正文里，不是留在脑内印象里。

### 3 · 每条建议先说「拆了省什么」，再说搬哪去

四段固定格式：搬什么 `file:line` → 搬到哪 → 谁受影响 → 怎么验没坏。行号区间要能抽样核对。

参照做法在基线里已经成立：18 段行号区间逐段标去处，抽样 `sed -n '40p;120p;291p;381p;944p'` 全部命中，第 944 行确实是 `export default function WatchlistPage(`。照着做，不要退回散文式建议。

### 4 · 提方案前先跑一遍既有测试，把绿/红写进方案

顺序是：跑 baseline 测试 → 记结果 → 才给方案。落地时再加一次正面对照：新加的守边界测试要注入一个真 bug 让它红一次，只会绿的测试是装饰。

堵的是：基线把「跑一遍现有测试确认全绿」放进了「风险与工作量」那一节的工作量清单，即推给未来的一个步骤，方案正文里没有任何一个 baseline 读数。方案是在「测试现在是什么颜色」未知的前提下给出的。

## 常见借口 → 现实

| 借口 | 现实 |
|---|---|
| 「9 个展示组件」「五层不相关的东西」，读一遍就看得出明显该拆 | 没数过就是印象。`grep -n "^export "` 是 7，`useState` 是 9，这些命令三秒就跑完，跑完再断言 |
| 跑一遍现有测试算在工作量里，落地时一起跑 | baseline 颜色是方案的输入，不是方案的输出。不知道现在是绿是红，就不知道拆完的红是谁造成的 |
| 1195 行摆在这，行数已经能支撑「页面级状态」这个判断 | 行数只说明文件长。撑「状态层」的是 9 个 `useState` + 1 个 `useEffect`，撑「不直接取数」的是 `fetch(` 命中 0 次 |

## 它做对了什么（别在下一版丢掉）

- 带 file:line 的迁移表。18 段行号区间逐段标去处，抽样全部命中，`.orig` 报的 40993 字节也和实际一致。这是基线最扎实的一步，照做。
- 主动报告 `.orig` 遗留，并诚实标注「不属于本次任务范围，是否清理由你定」，没有借题发挥去动它。路过发现的东西就该这样处理。
- 没有直接重写。只读约束下明确说没动任何文件，方案末尾把「要不要落地」的决策点留给人。skill 补的是缺的那几个读数，不是把这三件废掉。

## 单子不许挤掉你临场看见的东西

带这份单子跑的那一轮漏了一个真 bug：`WatchlistPage.jsx:1020` 用了 `view`，而它的 `const` 声明在 `:1025`——不带单子的那一轮反而抓到了（评分记录见 `code-cartography-workspace/iteration-1/scoring.md`）。

所以四项勾完之后，回答里固定加一行 **「顺手看见的」**：读文件时撞见的真问题（TDZ、重复块、死代码、命名对不上），一条一行带 file:line，写完就走，不展开成方案。看见了没写，比没看见更糟。

## 裁决记录

### [2026-09-05] 建 · RED 基线见 code-cartography-workspace/iteration-0/baseline/report.md
