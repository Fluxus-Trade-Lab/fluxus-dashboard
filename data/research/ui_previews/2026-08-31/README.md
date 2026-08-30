# UI 预览稿 · 2026-08-31

**页面**：Breadth · **一处**：`MarketStateSummary.jsx` 的四格摘要
（`frontend/src/components/breadth/MarketStateSummary.jsx:22-52`）。
**⚠️ 不动 dashboard 与 groups 两页；`frontend/` 一个字节没改。**

---

## 一、为什么是这一处 —— 页面正在显示数据端自己判定为反向误导的那个数

08-31 数据端把新高/新低换成了**标准普通股口径**（`b1c7d907`，Andy 亲定「先找口径，别自己造」）。
但前端仍然读**原始计数**：`ClassicBreadth.jsx:16` 与 `BreadthTable.jsx:78` 都是 `new_highs`。

**同一天（2026-08-28）两个口径的读数（`git show origin/main:data/output/breadth.json` 现读）**：

| 口径 | 新高 | 新低 | 净 | Record High Pct |
|---|---|---|---|---|
| 原始（页面现在显示的） | **68** | 19 | **+49** ← 读起来偏多 | — |
| 标准普通股（数据端新口径） | **8** | 18 | **−10** ← 偏空 | **30.77** |

**符号翻转。** 而 `Market State Summary` 那四格里**根本没有这一项**——
最该被看见的一格，恰好是唯一不在摘要里的。

⚠️ **n=1**：归档 100 行里**只有 08-28 一行**有标准口径读数（回填还没铺开）。
所以「翻转」是**一次观测，不是一个规律**。本预览要解决的是「页面该显示什么」，
这个问题的答案不依赖 n。

### ⛳ 顺带一条**不归前端**的发现（已列门铃 → DATA ALEX）

`pipeline/screeners/breadth_signals.py:125` —— `votes['nh_nl'] = _sign_vote(row.get('new_highs'), row.get('new_lows'))`，
用的是**原始计数**。08-28 因此投出 **`nh_nl = bull`**；标准口径下（8 vs 18）它该是 **bear**。
`percentile_context()` 第 729 行的 `nh_nl_net` 同样取原始计数（该格今天报 98th pctile）。
**`pipeline/screeners/` 不在我的 safe-merge 白名单，我只报不改。**

---

## 二、四稿 + 两轮迭代

| 稿 | 文件 | 一句话 |
|---|---|---|
| v0 | [`v0_current.html`](v0_current.html) | 现状（对照组，摘要里根本没这一格） |
| v1 | [`v1_replace.html`](v1_replace.html) | 加一格，只显示标准口径的 8 / 18 |
| v2 | [`v2_flip.html`](v2_flip.html) | 把口径与旧数一起写进格子 |
| v3 | [`v3_rhp.html`](v3_rhp.html) | 主角换成 Record High Percent，计数退成出处 |
| **v4** | [`v4_merge.html`](v4_merge.html) | 迭代①：v2 的披露 + v3 的克制，压回一行 |
| **v4b** | [`v4b_tighten.html`](v4b_tighten.html) | 迭代②：把「往哪个方向改」用一个词说清 |

### 评分（Andy 六条，各 0–2；触「新增颜色 / 鸡汤 / 动效」直接判负）

| | 简洁整齐 | 反多巴胺 | 只留交易内容 | 不新增颜色 | 让推理被看懂 | 决策优先 | 合计 |
|---|---|---|---|---|---|---|---|
| v0 现状 | 2 | 2 | 2 | 2 | **0** | **0** | **8** |
| v1 | 2 | 2 | 2 | 2 | **0** | 1 | **9** |
| v2 | **1** | 2 | **1** | 2 | 2 | 2 | **10** |
| v3 | 2 | 2 | **1** | 2 | 1 | 2 | **10** |
| v4 | 2 | 2 | 2 | 2 | **1** | 2 | **11** |
| **v4b** | **2** | **2** | **2** | **2** | **2** | **2** | **12** ✅ |

**扣分理由**（不写「感觉」，写具体那一处）：
- v0/v1 的「让推理被看懂」= 0：**昨天看过页面的人今天看到 8，会以为市场塌了**——数变了但没人说口径变了。
- v2 的「简洁」= 1：note 行两行，比另外四格高，破了对齐；「只留交易内容」= 1：`shells` 是内部词。
- v3 的「只留交易内容」= 1：`Record high pct` 读者第一次见，格子里没解释它是 0–100 的比值；
  「让推理被看懂」= 1：说了 below 50，没说这个数刚换过口径。
- v4 的「让推理被看懂」= 1：`counting changed` 没说**往哪个方向**改，读者不知道 8 是更严还是更松。

### 胜者 v4b · 读者比 v0 多知道三件事

1. 新高/新低**第一次进摘要**（此前只在下面的 Classic 表里）；
2. 它今天是**偏空**的——v0 上那个 `68 / 19` 会被读成偏多；
3. 这个数**刚被收严过**（`stricter count from Aug 31 · was 68 / 19`），所以昨天的 68 不是错觉。

**零新增颜色**：四稿的 HTML 里 `grep -oE "#[0-9a-fA-F]{3,6}"` 命中 **0**；
所有色值只在 `_shared.css` 里，逐个抄自 `frontend/src/index.css`。

### ⚠️ 没量的东西

**对比度没测**（`--color-text-muted #655e55` on `--color-bg #e2e0d6` 那一行是最小字号 10px）。
本轮没有跑对比度断言，**记成「未测量」而不是「通过」**。

---

## 三、给 UI Claire 的可执行版（纯前端，零新字段）

`breadth.json` 的 `history.rows[-1]` **已经带**了 `new_highs_common` / `new_lows_common` /
`record_high_pct` / `common_universe`（实测 08-28 行：8 / 18 / 30.77 / 5292）——**不需要数据端先加字段**。
在 `MarketStateSummary.jsx` 的 `grid` 里加第五格，`lg:grid-cols-4` 改 `lg:grid-cols-5`，内容照 v4b。

⚠️ **兜底**：99/100 行的 `new_highs_common` 是 `null`（回填未铺开）。
拿不到标准口径时**这一格不要退回原始计数**——那正是本预览要修的病。
**没有标准口径就不显示这一格**，或显示 `—` 并在第三行写 `standard count not backfilled`。
