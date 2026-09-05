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
