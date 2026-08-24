# 文章骨架模板 — 三个栏目各一套

*骨架逐段对标 TSF《Semiconductors Deep Dive》(2,051 字 / 22 图)拆出来的结构。*
*铁律:**标题写结论,不写标签。** 是「You Can't Have True Capitulation Without A Mark Down」,不是「半导体分析」。每个小标题都是一句可证伪的判断。*
*图密度目标:**每 90–120 字一张图。** 他 2,051 字配 22 张。读者在看图,文字是图注。*

---

## 模板 1 —— `Size & Stop`(旗舰,2–3x/周,付费)

```
[块 A:开头免责块]

## <回指上一次的判断,用收据开场>
   例:「Two weeks ago I said I'd stop caring about breadth below X. Here's what it did.」
   [图:当时那张图 + 现在]
   ← TSF 每篇都这么开。这是把「我上次说对了」变成结构而不是吹嘘的唯一方式。
     没说对的时候更要写 —— 那是 Voice Bible 的「always show the losses」。

## <这周的读数,一句结论当标题>
   3–4 句冷句:Herd 在做什么(情绪)· Algo Monkeys 被迫做什么(流)· 我读到什么
   [图:regime / breadth / GEX 任一张]

## <一个日常 toggle>
   低档:菜市场 / 白菜价。高档:艺术市场 / Cattelan 的香蕉。
   ⚠️ 一篇最多一个,且必须为一句朴素的市场道理服务。顶部用艺术,底部用菜价。
   ⚠️ 艺术线还在 4 周试用期(Voice Bible §4)—— 没自然冒出来就先别硬塞。

─────────── PAYWALL ───────────

## <标的一>  <一句结论标题,不是 ticker>
   [图]
   为什么现在:2–3 句
   **The measurement:** entry / stop / trade risk % / port risk %

## <标的二> …
## <标的三> …

## <收尾:一句「什么会让我改主意」>
   ← 这是「收藏闸」的关键。立场只拿赞,**失效条件才被收藏**。

[块 B:结尾持仓块]
[块 C:P.S.]
```

---

## 模板 2 —— `The Weather Report`(每周一,免费引流)

> 你手上 TSF 完全没有的东西:GEX 引擎、breadth v2、signal history、regime 分类。
> 他的「平台」是无代码烤 HTML;这一栏是你唯一能做而他做不到的产品。

```
[块 A:开头免责块]

## <一句市场状态判断当标题>
   例:「Dealer gamma flipped negative on Tuesday and nobody sent a memo.」

## The regime
   [图:regime 仪表盘]
   一句读数 + 一句「这意味着我把仓位放在哪个区间」

## Breadth
   [图:breadth 信号引擎]
   一句读数 + **一句失效条件**

## Dealer gamma
   [图:GEX levels]
   今天的关键价位,以及「价格在这条线上方/下方时,我预期的波动性质不同」

## How to read this
   ← 抄 TSF 平台里的「How To Interpret The Groups」教学块。
     每个数据模块下面配一段怎么读。这既是教育也是降退订。

## <一句 so-what:这周我打算怎么下手>
   不给标的(标的在 Size & Stop 里,付费)。给**姿态和风险预算**。

[块 A 的免责已在顶部]
[块 C:P.S.]
```

**为什么这栏免费:** 这是引流品。它展示测量能力但不给可执行标的 —— 想要标的就得付费去 Size & Stop。TSF 的免费文也是这个逻辑(市场观察免费,个股 setup 付费)。

---

## 模板 3 —— `The Ledger`(每月,付费)

> TSF **完全没有**这个栏目。他连业绩都没公开过就收 $399。
> 这是你最不对称的武器 —— 直接把 `pipeline/portfolio/performance_review.py` 的输出写成刊物。

```
[块 A:开头免责块]

## <这个月的一句话结论 —— 好坏都直说>

## The number
   [图:equity curve vs SPY]
   月度 return · YTD · vs SPY · max DD

## The shape
   [图:R 分布柱状图]
   n trades · win rate · avg winner / avg loser · payoff · profit factor · expectancy
   一句翻译:「我输的次数比赢的多,年份照样成立,因为赢的是输的 X 倍。」

## The three worst trades this month
   ← **这是全栏的心脏。** 每笔:我当时测到什么、错在哪、判据改了没有
   [图 ×3]

## The three best, and how much was luck
   ← 对称处理。Voice Bible:「arrogant in the number, humble in the method」

## What changed in the method
   这个月因为哪笔亏损改了哪条规则。没改就写「没改」。

[块 B:结尾持仓块]
[块 C:P.S.]
```

---

## 发稿前自查 —— 七道闸(`../Fluxus_Brand/ops/Fluxus_Content_Ops.md` §8.5)

发布按钮按下去之前逐条过:

| 闸 | 问自己 |
|---|---|
| **瞄准** | 这篇解决的是读者真在问的问题,还是我想说的话? |
| **事实** | 每个数字都能在 repo 里回溯到源吗? |
| **平庸** | 这句话别人写过一万遍吗? |
| **语感** | 格言密度 ≤ 每段一句?其余是不是在「说话」(hedge、停顿、第一人称具体事)? |
| **品牌** | 用了自有语言(the Herd / Algo Monkeys / Market God / 白菜价)还是通用行话? |
| **收藏** | 说完这句,读者最想问的下一个问题是什么?**答案在帖里吗?** 停在立场 = 停在倒数第二步 |
| **AI 味** | 有没有句句对称双拍?有没有 PPT 式每句一段?编号清单里**每条有没有一根非教科书的刺**? |

**冷幽默判据:** 荒诞必须在材料里,不在表情上。庄重脸 ≠ 冷幽默。
