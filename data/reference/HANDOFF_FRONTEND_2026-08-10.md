# 数据端 → 前端 交接 · 2026-08-10

*字段全部从当天的活文件抽取。完整契约见 [DATA_CONTRACTS.md](DATA_CONTRACTS.md),这份只讲**这一轮变了什么、你能做什么**。*

---

## 一、可以立刻做的三件

### ① 主题色带 —— 16 个有数,58 个 `null`

`groups.json` 的主题行新增 `ribbon`,值是 **5 个 `{state, level, accel}`**,由旧到新:

```json
"ribbon": [{"state": "Improving", "level": -0.080283, "accel": 0.19308}, … ×5]
```

**和 `rotation.json` 里 `baskets[].ribbon` 是完全同一种对象、同一套窗口**(level 63 交易日 / near 21 交易日),
`shared/StateRibbon.jsx` 直接复用,不用改。

| 主题类型 | 数量 | `ribbon` |
|---|---|---|
| `method="proxy"` | **16** | ✅ 有值 |
| `etf` / `industry` / `rule` | 58 | `null` 到 **2026-10-19** |

**不要为这个分岔写分支。** `StateRibbon` 对 `null` 已经画虚线空框;10 月归档满了那 58 行自己会有值,**契约不变、代码不用二次改**。

> 为什么 58 个要等:基金每天有一个收盘价,供应商永远存着,所以任意过去窗口今天就能算。
> 主题的读数是「某一刻对一组股票取中位数」,不写下来就没有 —— 而归档从 2026-08-09 才开始。
> 倒推补不了:成分名单本身在变(今天就删了 7 个主题、给 Quantum Computing 加了 IBM、市值地板 3 亿→10 亿),
> 拿今天的名单套 6 月的价格,算的是「今天这批票当时的表现」,是另一个问题。

### ② ThemeMembers 的口径统一 —— 数据早就在手上

[ThemeMembers.jsx:62](../../frontend/src/components/groups/ThemeMembers.jsx) 已经在做 `found.push({ ...u, rs: stocksByTicker?.[t] })`,
每一行都挂着 `r.rs`,来自 `groups.json.stocks`(2991 条),字段和组层**完全同口径**:

```
excess_3m · rs_accel · state · rs_0_1w · rs_1w_1m · rs_1m_3m · rs_3m_6m
persistence · persistence_of · group_pctile · top_quartile
```

组件**已经在用** `r.rs.state`(119 行)和 `r.rs.persistence`(126 行)。只有 RS 那两列和排序还在读百分位:

```jsx
121:  {num(r.rs_21d)}      ← universe 百分位 0–99
122:  {num(r.rs_63d)}      ← 同上
 66:  sort((a,b) => (b.rs_63d ?? -Infinity) - ...)
```

而表头 84 行印的是 `theme.excess_3m`(pp)。**同一张表,表头一把尺、表身另一把尺。**

四条注意:

1. 换成 `r.rs.excess_3m` 后表头表身才可比 ——「这只票季度超额 21.4pp vs 主题整体 47.4pp」才是一句能读的话
2. 两套都留可以,**但必须各自标注口径**;不能标注就只留一套
3. **`group_pctile` 还没被渲染过** —— 它是三把尺里唯一回答「这只票在这个主题里算强还是弱」的,而这正是点进来的人最想问的
4. 排序键换了之后 `top_quartile` 才对得上 —— 它按主题内算,现在按 `rs_63d` 排,榜首那只未必带标记,看着像 bug

### ③ Regime 分数 —— 已在 `breadth.json.regime`,前端尚无消费方

`score`(0–100)· `band` / `band_label`(damaged / mixed / healthy / extended)· `bands[]`(画刻度)· `measured` / `of` · `strong[]` / `weak[]` · `evidence`

⚠️ **三个字段是许可证不是装饰,省掉页面就会说数据没说过的话:**

- `caveat` —— 必须显示
- `predicts_return`(恒 `false`)/ `separates_tail`(恒 `true`)—— 它对**下月均值收益无信息**,对**左尾单调**(−5% 回撤频率 Damaged 27.2% → Extended 5.8%)。**画成红绿灯就是替它做一个它做不到的声明**,它是仓位预算的输入,不是方向的输入
- `measured` / `of` —— 8/9 和 6/9 不是同一个声明

档位边界 47 / 63 / 75 是 **558 个交易日的经验四分位**,不是拍的整数。

---

## 二、字段改名 —— 旧名仍可用,但请换

`universe.json` 每行现在同时有:

| 新名(请用) | 旧别名(将来会删) | 实际窗口 |
|---|---|---|
| `rs_1m` | `rs_21d` | **1 个日历月**(Finviz `Perf Month`) |
| `rs_3m` | `rs_63d` | **1 个日历季** |
| `rs_6m` | `rs_126d` | **半个日历年** |

旧名字写着交易日,底下是日历口径 —— 实测 129 只,与交易日复算吻合率 **< 4%**,`perf_6m` 中位偏差 **7.83pp**。
新旧是同一个 Series,**换名字不改数值**。

受影响文件:`ResultsTable.jsx` · `screenerFilter.js` · `TickerStats.jsx` · `ThemeMembers.jsx` · `WatchlistTab.jsx`

> **ETF 侧相反,而且保持不变**:`etf_data` 没有 Finviz 来源,它的 `perf_1w/1m/3m` 真是 **5/21/63 交易日**。
> 所以 Dashboard 的「1M」和 Screener 的「1M」差几天 —— 现在只有一边会撒谎了。

---

## 三、修掉的数据缺陷(会改变你看到的排名)

| 缺陷 | 影响 |
|---|---|
| `rank_tradeable` 的 `na_option='bottom'` | pandas 的 "bottom" 是**名次最大**=分数最高。27 只没有 `perf_3m` 的票 `rs_63d` **全是 99**(中位 49),61 只 `rs_126d`=98,并按 0.4 权重流进 `rs_ibd`。**「我们对它一无所知」曾是 IBD 榜首的唯一理由。** 已改 `'top'`,那些行现在是 0–1 |
| `rrs_rank` 吞掉 0.0 | `if rs_score else None` 把最弱读数删了。8 只(XTN EWY EWT TAN EEM ICLN WGMI BLOK)全是真值 0、各有 251 根 bar。已修 |
| `avg_volume` 富集塌方 | 8.2% 缺失让 **RKLB($49.5B)** 被判不可交易。已重跑修复(1.99%),并加了 null-rate 闸 |

**`rrs_rank` 本身没改,但它不是你以为的那个东西** —— 它是「今天在**这只基金自己**最近 21 天里排第几」,
和同侪强弱几乎无关(vs RRS 绝对水平 Spearman **+0.075**),对 `perf_3m` 甚至是负相关(−0.193)。
XLK 是周内最强板块却拿最低档 5,就是这个原因。**它唯一的消费方是 `EtfSection.jsx:14` 那一列,那一列的排序信不过。**

---

## 四、新增可读字段

`universe.json` 顶层多了 `quality`:

```json
{"status": "ok", "runs_in_baseline": 0,
 "tradeable": {"tradeable": 2535, "excluded": 2971, "unmeasurable": 112},
 "fields": {"avg_volume": {"rate": 0.0199, "baseline": null, "status": "ok", "evidence": "…"}, …}}
```

`unmeasurable` 是新的第三态 —— 以前它藏在 `excluded` 里,**一只 495 亿的票和一只真没量的壳股读数完全一样**。
如果要在页面上标注数据质量,这是来源。`status` ∈ `ok` / `degraded` / `severe`。

---

## 五、分类学变动(主题列表会短)

**74 个主题 · 121 个行业 · provisional 0 · skipped 0** —— 第一次没有任何主题卡在半途。

删了 7 个:

- **4 个通不过共动性**(全是 Finviz 行业标签,不是策展):Packaged Foods +0.0092 · Telecom Services +0.0042 · Computer Hardware +0.0005 · Industrial Metals **−0.0161**(比随机还不同步)。**它们仍在 121 个行业层里**,删的是「报表分类 = 一笔交易」这个主张
- **3 个连检验都进不去**:GLP-1 两半各剩 2 个成员($1B 地板削的),2 个成员只有 1 对,没有可比对象;Microcaps 归零,地板按定义删掉了它要追踪的东西

**IBD 50 改成 proxy 追踪 FFTY** —— 榜单是 IBD 付费订阅内容不能抓,yfinance 只给前 10(十只票挂五十只招牌),
而基金价格是公开的、榜单调整时基金自己跟。当前 **−17.5% 对 SPY(季度),Lagging**。

---

## 六、不要动的

**Market State 页(`#/breadth`)** —— 轮动面板和 regime 这一轮不碰。

---

## 七、时间线

| 何时 | 会发生什么 |
|---|---|
| 每个交易日 21:30 UTC | 归档 +195 行;`universe_quality.csv` +1 行 |
| 满 5 次运行后 | 质量闸开始真正打分(在那之前诚实地说 "no baseline yet") |
| **2026-10-19** | 那 58 个主题的 `ribbon` **自己出现**,前端无需改动 |
