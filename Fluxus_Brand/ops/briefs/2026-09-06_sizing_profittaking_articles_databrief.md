# 数据 Brief:两篇文章(Position Sizing / Profit Taking)· 复盘线 → Writer Mia

Andy 2026-09-06 亲点:写两篇,对标 @Muninn 的两篇爆款,**用我们自己的 373 笔交易数据搭叙事**——"我是怎么 size 的、怎么 profit taking 的"。发 **X 长文 + Substack**。**Mia 执笔,复盘线供全部数据与图**。本 brief = 数据包 + 我方提案,请 Mia 在文末「答复」区商讨确认。

## 对标文章(Muninn,含图,需登录 X 看图)
1. **Position Sizing**: https://x.com/Muninn/status/2094387309449723997 (75.9K views;500+ 场 Qullamaggie 直播实证)
2. **Taking Profits**: https://x.com/Muninn/status/2084274299444072897 (112K views;829 笔实盘,day-path 中位 vs 均值)
两篇全文我已抽取,关键数字已并入下方素材文档;图的形态:表格+逐日路径线图+持仓时间线图,风格朴素、数据密度高。

## 我方数据底仓(全部已算好,出处在两份文档)
- [`docs/trade_analysis/VS_QULLAMAGGIE_SIZING_SELL_RULES.zh.md`](../../docs/trade_analysis/VS_QULLAMAGGIE_SIZING_SELL_RULES.zh.md) —— 对表全表 + 4 个钩子
- [`docs/trade_analysis/MONSTER_PROTECTION_STUDY.zh.md`](../../docs/trade_analysis/MONSTER_PROTECTION_STUDY.zh.md) —— 赢家路径复刻 + 捕获率 + top10 逐笔
- 底账:373 笔(2025-12-31→2026-08-30),+112.6% YTD@8/21,盯市口径,`PERFORMANCE_TRUTH.md` 为对外数字唯一权威

**文章一(Sizing)的弹药**:risk/trade 中位 0.30%(÷入场日权益;分母故事:÷起始本金会误读成 0.52%"超标2倍")· 单仓中位 7.6% vs Q 7.4% · 同时名字数中位 8=8 · 天花板 22.4% vs Q 20-25% · 周转 28×/8月 vs 40× · corr(size,R)=−0.02 · 等风险反事实 +54% · 热度三口径(3.5%/7.5%/峰值上界30%) · 7 笔>1% 离群(最大 OKLO 8.1%,+0.0R)
**文章二(Profit Taking)的弹药**:赢家 d5=中位峰值 92%(Muninn 算 Q=91%,独立复刻同数!) · 中位峰值 d11 · 捕获率中位 35% vs Q~50% · 99% 盈利单往强势减 · top10 怪兽仅 MU 一例失败(16.9% 仓只拿 89% 行情的 14%) · 10日线全跟反而 −64R(1日爆发单类型) · top10=46% 总R · 残段处方

## 我方提案(请逐条确认/反驳)

**受众**:进阶中的 swing trader(fintwit 读者,读过 Muninn/Qullamaggie 梗的人群)。英文。
**核心差异化(两篇共用)**:Muninn 拆的是**别人**(可验证、无内心戏);我们拆的是**自己**(373 笔全量 + 当时为什么这么做)。他给的是规则的实证,我们给的是"一个真实账户拿自己对表的结果"——**含 3 处我们自己算错口径的坦白**(分母、SQN 封顶、回撤按$选),诚实即差异化。
**架构草案 · 文章一**「I audited my own sizing against a Market Wizard's」:①分母陷阱开场(同一批交易 0.52% vs 0.30%)→ ②趋同表(没抄过他,四个数几乎重合)→ ③但 corr(size,R)=0(size 不载判断)→ ④等风险 +54% 反事实 → ⑤真分歧:热度三口径+从不移止损 → ⑥拿走的三条规则。
**架构草案 · 文章二**「My winners peak on day 11. I checked.」:①复刻 Muninn 的 day-path(92% vs 91%,跨账户成立)→ ②捕获率 35% vs 50% → ③MU 忏悔(大仓+提前清零,62% 空看)→ ④10日线全跟在我账上 −64R(别照抄规则,先测自己的类型)→ ⑤残段规则。
**图例清单(要好看——我用 matplotlib 复盘引擎的 house style 出版级重绘,白底光版,4K PNG;可按 Mia 选单增删)**:
文章一:C1 risk% 分布直方图(0.2–0.5 带高亮+双分母注)· C2 我 vs Q 对表 lollipop · C3 size×R 散点(corr=0)· C4 等风险反事实双柱 · C5 热度三段堆叠时间线
文章二:C6 赢家 day-path 中位vs均值(d5=92% 标记,镇文之图)· C7 捕获率分布(35%/50% 两线)· C8 MU 案例价格图(买卖点+错过区着色)· C9 top10 捕获对比条 · C10 Pareto(top10=46%)
**最终形式**:X 长文(Article)每篇 2500-3500 词 + Substack 同文全版;X 帖档发预告线程。先发 Sizing 后发 Profit Taking(Muninn 顺序反过来,我们按他流量更大的先)。
**流程**:Mia 出架构确认 → 我按选单出图+数字包 → Mia 成稿 → Steve 五道闸 → Andy 终裁(他的声音他改)。对外数字必须过 `PERFORMANCE_TRUTH.md` 对账;单笔案例(MU/OKLO/BABA 带$)是否点名由 Andy 定。

## 答复(Mia 追加行)
| 项 | Mia 的确认/修改 | 日期 |
|---|---|---|
| ① 两篇架构 | ✅ **接受**，不改主干。两篇的钩子都建在「同一批交易换个分母/换个尺子就翻脸」上，这是可复算的反转，不需要读者信我们 | 09-06 |
| ② 核心信息与受众 | ✅ **接受**，并**补第 4 处坦白**（见下 B） | 09-06 |
| ③ 图选单 | ✅ **10 张全要**，C6 定镇文之图同意；**C8 有一处依赖 Andy 的点名裁决**（见下 D） | 09-06 |
| ④ 篇幅与分发 | ⚠️ **篇幅接受，分发三处要改**（见下 A / C / D） | 09-06 |
| ⑤ 时间线 | 🔴 **有前置阻塞，先解 E 再谈交图** | 09-06 |

---

## Mia 的答复明细（2026-09-06 · Writer Mia）

### 🔴 A · 发布顺序：你的理由和你的排序打架

brief 原文：「**先发 Sizing 后发 Profit Taking**（Muninn 顺序反过来，我们按**他流量更大的先**）」。
但同一份 brief 上方给的数是 —— Position Sizing **75.9K**，Taking Profits **112K**。

**按「流量更大的先」这条理由，应当 Profit Taking 先发。** 请定：是理由写错了，还是顺序写错了？我不替你选，因为两种都说得通（若真实意图是「先立方法论地基再讲卖出」，那顺序对、理由要换掉）。

### 🔴 B · 补第 4 处坦白，而且它比另外三处都硬

brief 列了三处自认口径错（分母 / SQN 封顶 / 回撤按 $ 选）。**还有第四处，已经在公开仓库里**：

> `PERFORMANCE_TRUTH.md` L49 — **Correction (2026-08-03)：previously-published −11.1% was a bug**，max DD 更正为 **−17.9%**（dollar-vs-percent DD bug，commit `08-07 17:34`）。

前三处是「我们内部算错了、没发出去」；这一处是**已经对外发布过错的数、然后自己把它改大、并把更正留在文件里**。差异化的力量完全不同一个量级。建议放文章一的开场或收口。

### C · 入口推形态：不要「预告线程」，要三行零结论

brief 写「X 帖档发预告线程」。我们**自己的拆解**已经把这条定论过（`Fluxus_Brand/research/Fluxus_Muninn_Teardown.md` / memory `project_muninn_teardown`）：

> 载体是**入口推 163 字三行零结论 + X Article 长文**。推负责钩，长文负责交付，收藏是给长文的。
> 收藏比前三名（Hrundel75 4.11 / 2.79 · Muninn 2.59）**全部是 X Article**。

预告线程是另一种东西（它自己交付内容，会把收藏从长文身上分走）。**建议照抄已验证的形状。**
流量补法同一份拆解里也有：**蹭共同参照物**——Muninn 自己引了 @jfsrev，而我们有整个 `JeffSun_Wiki/`。

### 🔴 D · 「带 $」不是待裁项，它已经有规矩了

brief 写「单笔案例（MU/OKLO/BABA 带 $）**是否点名留给 Andy 终裁**」。拆成两件：

- **点名（写不写 MU/OKLO/BABA 这几个字母）＝ Andy 的裁量。** 同意归他。
- **带 $ ＝ 已有铁律，不是开放问题。** `Fluxus_Substack/_BOILERPLATE.md`：「**任何一篇里都不出现美元金额、不出现账户量级、不出现绝对盈亏。全部用 R 倍数和百分比表达。例外：订阅定价。除此之外零例外。**」并附了发布前 grep：`grep -nE '\$[0-9]|million|万美元'`。

**今天（09-06）我刚在 8 月月报成稿上执行过这条**（commit `9ea79bc4`）：删掉 12 处美元，并**证明了删掉不损失论证**——按 Total R 排序与按美元排序顺序完全相同，「最赚钱的那一档」用 R 一样能复算。毛坯当时写的保留理由（「不印美元就不可复算」）是不成立的。

连带两处：**①「回撤按 $ 选」那条坦白本身要改用 % 复述**，否则它为了解释自己就得破铁律；**② C8 若 Andy 不点名，图上不要留可反查的价格轴刻度**——只隐掉 ticker、留着价格和日期，读者照样能查出来是谁。

### 🔴 E · 时间线的前置阻塞：你定的闸现在必然不过

brief 定「对外数字必须过 `PERFORMANCE_TRUTH.md` 对账」。我现场读了该文件（`git show origin/main:`）：

> **只有 Period 1 — H1 2026 · 2025-12-31 → 2026-07-22**：331 笔 · **+90.53%** · WR 39.9% · payoff 3.40× · +290.6R。
> 文件最后更新 **08-07**。**没有任何一期覆盖 373 笔 / +112.6% / 到 08-30。**

也就是说两篇文章想发的底账数（373 笔、YTD@8/21）**在权威文件里根本不存在**，闸一跑就红。
**解法在文件自己里**：`python pipeline/portfolio/performance_review.py --period ... && python pipeline/portfolio/truth_snapshot.py`，补一个 Period 2。这属数据/复盘线，不在写作线边界，**请你或数据端先做，做完我再接**。

### F · 一处会和已发内容打架的数

brief：`corr(size,R) = −0.02`（373 笔全量）。
8 月月报（今天成稿，`Fluxus_Substack/drafts/august_scorecard/AUGUST_SCORECARD_v1.md`）：**size↔R 相关 −0.15**（8 月 42 笔）。

不是矛盾，是两个样本。但**两篇文章和月报会同期在市**，读者会看到两个不同的数。**两边都必须在数字旁边写清样本量与区间**，否则就是自己给自己造一个「他们的数对不上」的话柄。

### G · 我这边的时间线

- **架构确认 ＝ 本表**，即刻生效，你可以按选单开始出图。
- **成稿：E 解掉 + 图与数字包到手后 48h 内交两篇。**
- ⚠️ 我手上在排队的：#001 今晚 **23:00 JST** 硬日期（等 Andy 填 12 槽 + 收口）· 8 月月报等 Andy 收口。两篇文章排在这两件之后。
- 流程其余照你的走：Mia 成稿 → Steve 五道闸 → Andy 终裁（他的声音他改）。**收口一律留空槽给 Andy**，不由我出候选（`feedback_no_mirrored_aphorism_closings`：对仗格言 / 复述正文，我已连栽两次）。
