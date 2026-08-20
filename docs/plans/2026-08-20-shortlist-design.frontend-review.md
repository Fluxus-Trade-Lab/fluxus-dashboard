# Short List 对照页 · 前端意见（2026-08-20）

回 `2026-08-20-shortlist-design.md` §三的两个问题，外加四条我认为会真正打断学习回路的东西。
**C 是 schema 的**——数据端说 schema 不等前端答案，那请至少先看 C。

## ① tab 还是独立路由：两个都要

Andy 明说「在 Today's List 页面加一个 tab」，那就是 tab，形不改。但用现成的 subRoute 兜底：
[`Layout.jsx:254`](../../frontend/src/components/Layout.jsx:254) 已经在传 `zone={subRoute}`，
[`WatchlistPage.jsx:173`](../../frontend/src/components/watchlist/WatchlistPage.jsx:173) 的 `go(zone)`
已经在写 `#/watchlist/<zone>`。所以 `#/watchlist/shortlist` 零新基建就有真 URL——刷新不丢、
状态可链接、可以单独钉起来。

要说清的代价：Today's List 顶部已经有五步条。tab 压在步骤条上面就是两排 chrome。
做法是 **tab 切整个 body**——Short List tab 里步骤条整个不在，两个选择器不会同时活着，
所以不违反 DESIGN.md 的「同一组对象上不放两个选择器」。

## ② 图：自绘 SVG，不用 lightweight-charts

不是偏好，是三件查过的事：

1. **lightweight-charts 读不了 CSS 变量。** 仓库里四处用它（`OhlcvChart` / `TradingGym` /
   `HealthChart` / `useBreadthChart`），每一处都得把 token 解析成字面量，注释写着
   「a theme flip re-resolves on chart rebuild」。20 张卡就是主题一切换重建 20 个图。
   SVG 直接吃 `var()`，明暗互换零成本。
2. **20 个 canvas + 20 个 ResizeObserver**，为的是 130 根的缩略图。不值。
3. **它自带一套视觉语言和配色系统**，会和 DESIGN.md 的图表文法打架（三条规则不是七条、
   `vectorEffect="non-scaling-stroke"`、文字标签放在 SVG 外面，因为 `preserveAspectRatio="none"`
   会把 SVG 里的字拉变形）。信号标记叠在图上恰恰是 SVG 的本行；lightweight-charts 的 marker
   是一套固定形状词汇，我们四种 kind 未必套得进去。

分界线：lightweight-charts 留给 Model Books 和 Breadth 那种十字光标/交互撑得起重量的大图。
series 130×20 ≈ 60KB 前端接受。

---

## 会打断回路的四条

### A. `feedback.csv` 缺分母 —— 这条最要命

「哪个席被否率高」现在算不出来。六席的基础曝光率完全不同：①在烧每天都有名字，
③入场在没有 EP 的日子是空的。只记 veto 的话，一个天天出现的席天然会积累更多 ✗，
而这跟它选得对不对无关。

要的是**每席每天一行**，不是每次否一行：

```
date, seat, ticker|null, shown(bool), outcome(vetoed|starred|ignored|empty), <当时的全套 readings>
```

`ignored`（看见了没动）和 `empty`（没名字可给）是两个不同的分母，都得记。

这正是我们栽过的那个形状——按结果排序的名单没有分母。方案 §四 自己写了
「选法内的排序依据是便利选择」，那就更需要分母才验得动。

### B. ✗ 是三个标签挤在一个按钮里

「不合适」可以是：今天不合适 / 这只票本身不行 / 这个席选错了人。学习端把三种当一种，
30 个打岔全是噪声。

保住一次点击的最省做法：**把 ✗ 的定义钉死成「不是这个，今天」**，写在按钮自己的 tooltip 上，
别的意思一律走 `note`。分析端不许假设按钮说了它没说的话。不改代码也行，但要写进 schema 注释。

### C. 空席需要三个空状态，不是一个（schema，急）

§二.2 写「空席就空着，空着本身是读数」——但空着有三种，页面必须能分：

- 喂它的那格**今晚没跑**（未测量）
- 跑了，**一个都没有**（found none）
- 有人，但**被闸挡了**（blocked by threshold）

这三个在 DESIGN.md 里是必须长得不一样的（未测量 ≠ 0 ≠ 被闸挡）。请加：

```
seat.empty_reason: "not_measured" | "none_found" | "all_excluded"
seat.excluded_n:   int   // all_excluded 时挡掉了几个
```

没有这个字段，页面只能把三种都画成同一个灰框，那就是撒谎。

### D. ✗/★ 不能骑现有的 push

[`sheetsSync.js:35`](../../frontend/src/components/portfolio/services/sheetsSync.js:35) 的
`pushToSheets` 发的是 `action: 'sync_all'`，带 `stockTrades` + `optionsTrades` + `meta`
**整包覆盖**。一次 ✗ 点击要驮着整个组合状态过去，而且两个标签页同时开着会互相盖掉。

要一个自己的 GAS action：`shortlist_upsert`，**append-only、按 `(ticker, added_date)` 幂等**，
只发这一条记录。GAS 侧归数据端，前端照这个契约写。

---

## 两条小的

**E.** `readings` 里 `rs_1m` 和 `rs_line_pctl_21` 同时在——好，别合并。这是不同的量，
我们在 Today's List 上栽过一次（三百个数字挂着没人说它们是什么，
[`pickRs.test.js`](../../frontend/src/components/watchlist/pickRs.test.js) 整个文件就是那次的墓碑）。
卡片显示哪个都行，但必须带名字显示。

**F.** 判词是确定性模板很好，意味着前端能对它做快照测试。请随引擎发
**3–4 张 golden card 当 fixture**（含一张六席全满、一张有空席、一张 `flags.chase=true`），
前端拿它锁文案渲染，模板一改测试就响。

---

顺序同意：数据端先出 `shortlist.json`，前端等文件就位再渲染。C 请在 schema 定稿前塞进去，
其余不挡动工。
