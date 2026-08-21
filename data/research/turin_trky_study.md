# Turin / TRKY 模型逆向研究 —— @turintrader 的 correction risk + breadth washout timing

*2026-08-20 采集与复现。来源：X（@turintrader 主号 + @bcrossleypy 副号）+ TradingView（bcrossley）。*
*下游：逆向 + 回测方案见 [turin_trky_replication_plan.md](turin_trky_replication_plan.md)。*
*所有引用素材遵守「只存不引」；本文是结构拆解，不是转载。*

---

## 〇、账号地图（名字都是同一个人）

| 身份 | 说明 |
|---|---|
| **@turintrader**（主号，"Turin"） | 方法论 thread 都在这。前一个号 2022 年被封（他自称 "for providing too much alpha"），所以 2022-03-14 起有一波「怕被封先把 regime filters 公开」的泄露期——**那批帖是逆向的主矿** |
| **@bcrossleypy**（副号，13 帖） | "spam account"。bio: TRKY updates · VIX ETP projections · **1990+ VIX 3m6m data sheet + calc** · custom TV libraries。SPXL-V3 每日 plot 将由 claude bot 自动发这里 |
| **TradingView: bcrossley** | 9 ideas + 5 scripts。核心策略全部 invite-only（Discord @toropirlo 收费开权限），但 **release notes 泄露大量机制**；初版 Turkey 1001（旧号 TLEZspXT）的描述几乎是完整规格 |
| TRKY = Turkey | 塔勒布火鸡：第 1001 天感恩节。整个产品就是「火鸡日探测器」= correction risk 模型 |

## 一、模型谱系

```
Turkey-1001-Day (2022-02, 初版, 描述公开)
  → 6-TRKY-1001-DAY (2022-03-31 定版, invite-only; 2024-09 更新)   ← 资产配置层 (0/1 oscillator)
  → O-VIX-TS-SPXL-v3 (2022-03-30, "main trky strat")               ← 执行层: SPXL 短线（他叫 scalp，**实为日线图策略**：源码注释 APPLY ON A DAILY CHART，bot 每日一张 plot；持仓周期=数日，非日内）
  → g-VIX-TS-HA-WEEKLYVERSION = turin_LT (weekly, live since '22)   ← 长线层: SPY 周线 HA
  → z-C-Ind-strat (2024-01, "401k 版" trend following)
```

自评业绩口径：turin_LT "outperforms SPX B&H, min 14.58% DD since '07, 4 年 forward test"；TRKY 替代 DBMF 进 60/40 → "1.42 Sharpe"（自述，无审计，当广告看）。

## 一·五、现行版（2026-08）的组合与使用方式 —— 从 release notes 全时间线拼出（tv_pages 快照 + 近期推文）

**三层现行规格：**

| 层 | 脚本 | 现行部件（含最近更新） | 输出/用法 |
|---|---|---|---|
| **中期资产配置** | TRKY-1001-DAY | VIX-TS（自制 1990+ 3m:1m，2023-06 从 credit 换回："stick with what's been working"）· NHNL 比率调整线（2023-08）· **R3TW 条件（2024-08-26 重新加回）**· **Kerb 的 VIX/VVIX/GLD 相关指标（2024-08-26 加回）**· credit 喂 FRED（2024-09 换源）· 底部箭头 = NYSE A/D **成交量**比（不是家数）· HMA 交叉入场（2023-08 修过 crossover bug） | **Osc 三档**：+1 = 最激进成长股/LETF、避债；0 = 减仓+现金+短债；−1 = 避股、持现金等 countertrend、买长债 |
| **日线执行** | SPXL-V3 → 改名 **turintrend** | 2026-07-14 indicator→strategy 大改：LONG-ONLY，入场 = ADR thrust / NDQ-QQQ trend cross / filtered Williams VIX Fix；出场 = z-score divergence sell / regime 红退出 / 硬止损；**还修了一个 lookahead 未来函数泄漏**。**2026-08-16 最新：trend filter "Reverted back to the original AQR"** —— 即 R2 底图上那段动量因子代码（linregress 年化斜率 × R²），并注明 "Pair this with Turkey1001 Day Indy" | TRKY 定 regime 门，turintrend 管进出；regime 三色：红=STFR 做多 vol、深绿=low-vol grind-up（动量/趋势跑赢、便宜 vol 更便宜）、浅绿=mean-revert |
| **周线长线（401k）** | turin_LT（vix_ts_weekly） | 单一 Nas+NYSE breadth 指标出信号 + 自定 hi/lo z-score 定 LT regime（**默认符号 BAML/VIX/DXY**，可换 SPX/NDQ/IWM 需反色）· vol 分位条件阈 45 · **2026-08-20 用 Fable 重建 entry/exit**：%>MA / Adv-Decl / 252d rvol | SPY 周线 HA；**每年 3–6 笔**；对普通人的推荐姿势 = 60/40 + 这个 trend 策略，他本人 "rip my strat raw" |

**现行使用姿势（2026-08 当周）**：08-17 判 regime = **low vol grind up（2016-18 类比）→ "max long semis/tech w 2-3x lev and leave it for a year. Don't over complicate"** —— 正是他自家 regime 色标里深绿档的操作语义。标的按 Andy 情报为 SPXL/TQQQ/SOXL 配比。SPXL-V3 每日 plot 即将由 bot 发副号。

**与我们检验的三处呼应（旁注）**：① 底部条件其实是 A/D **量能**口径（UVOL/DVOL 家族）——我们 N6 测的表切 NULL，但他当**事件箭头**用不当表切；② Kerb 的 VIX/VVIX 相关 = 我们 N9 家族——他 2024-08 加回，而我们测得 36 年完美单调但**方向与他的警告语义相反**；③ 执行层 08-16 起的 AQR 动量因子正是 R2 底图泄露的那段代码——复刻时可直接用。

## 二、TRKY 1001 逆向出的架构

**三层：regime filter → top conditions（correction risk 侧）→ bottom conditions（washout 侧）。**

### 1. Regime filter（定牛熊背景，决定信号方向权重）
- 初版：**NYSE cumulative AD line + z-score**（红底 = bear regime）
- 定版（2024-09 notes）：**HMA on 自制 HY credit total return index** + **52w NHNL line**
- 他单独公开过的最爱：**Nasdaq cum AD：100d SMA 上/下，或 252d z-score > −1**（2022-03-14）
- 信条（2023-03 thread）：先于每个熊市的只有两样——**数月级 breadth divergence + credit spread 走阔**；"vol 是 credit 的兄弟，vol regime 转换由 credit cycle 驱动"

### 2. Top conditions ×4（顶部/自满探测 = 他的 correction risk）
1. CBOE **SKEW**
2. CBOE **total equity put/call (PCCE)**
3. **VIX 期限结构陡峭度**——公开代理：**VIX/VIX3M 的 3EMA**，`<0.8` 自满区、`1.0–1.1` 恐慌/投降区（2022-03-28，给了确切阈值）
4. **WMT/XLY z-score**（防御/可选消费轮动——沃尔玛跑赢可选消费 = 自满破裂前兆）

红三角 = 全对齐的 sell（"get to the bunker"）；黄三角 = swing high 警告。

### 3. Bottom conditions ×2（washout/底部探测）
1. **NYSE advance/decline ratio**
2. **Russell 3000 % above 20dma**

绿箭头 = 全对齐（大底）；橙箭头 = NYSE A/D + VIX 条件先行的激进买点。

### 4. 输出形态
0–1 oscillator：1 = 满仓成长、0 = 减仓加现金短债、−1 = 空仓等 countertrend buy。数据底座 1990+（FRED + 自算 VIX3M——TV 的 VIX3M 只有 2009+，他自己算回 1990，就是 bio 里那张 3m6m sheet）。

## 三、Breadth washout timing（用户问的第二个 study）

他公开过的可直接复刻的规则，按重要度：

**R1 · 买点确认（2022-03-10）**：当前 regime 里每个 buyable low 都出现 **NYSE cum AD line 的 21d z-score 上穿 0**；z<0 时抄底 = bagholder。
**R2 · regime 闸（2022-03-14）**：Nas cum AD 在 100d SMA 上方，或 252d z > −1。
**R3 · VIX TS 区间（2022-03-28）**：VIX:VIX3M 3EMA，0.8 / 1.0 / 1.1 三档，配 R3K breadth 用来定 short-vol / 加减 hedge 时机。
**R4 · 自制 washout 复合（2026-07-30，副号）**：把 risk-on 系指标（DXY、JPY、CHF、R3TW、GLD…）聚合成 **smoothed 5d cumulative hi/lo line + 252d z-score**；个股侧用 barchart 的 NHNL（$MALN）和 R3TW，poly reg 或 EMA 平滑。
**R5 · 教学版策略（2023-03-09 thread）**：smoothed SPX cum AD line × **50w MA**，穿越买卖，"60+ 年回测"。设计意图 = 不对称：熊市反弹 → MA 没时间偏离 → 很快反穿 → 小亏出局；真底 → AD line 一路向上直到下个熊市。**两条 MA 的偏离度**本身再当 complacency/risk-off 读数（上极端处看 60d forward return）。信用版（credit stress index 替换 AD line）更钝但**领先**熊市。

## 四、在我们数据上的复现（2026-08-20）

脚本：scratchpad `turin_replication.py`；数据：`data/history/breadth_archive.csv`（我们 ~2,500 名池，567 个交易日 2024-05-15→2026-08-19；**注意不是 NYSE 口径**）。

**R1 的三次大底全部按剧本走**（低点 → z21 上穿 0 的确认滞后）：

| SPX 低点 | 确认 cross | 滞后 | cross 后 21d |
|---|---|---|---|
| 2024-08-05 (5186) | 2024-08-16 | +9 | +1.4% |
| 2025-04-08 (4983) | 2025-04-23 | +10 | +8.7% |
| 2026-03-30 (6344) | 2026-04-01 | +2 | +10.0% |
| **失败样本** 2025-03-13 | 2025-03-24 | +7 | **−6.8%**（随后 4 月崩盘）|

2025-03-24 正是他 thread 里预写的「bear rally cross」分支——该信号的定位是**带止损的策略入场**，不是一次性预测。无条件口径下无优势：cross 日均 21d 前瞻 +0.92% vs 全样本 +1.46%（n=33 vs 546）——**价值在闸（z<0 不抄底）与确认结构，不在均值抬升**。这与我们 [[project-b4-gates-null]]「闸分得开、过闸不跑赢」的形状一致。

**R2 复现**：2.3 年 40 次翻转，噪音大（他的用法配合快速止损，噪音是设计的一部分）。当前读数（08-19）：**RISK-ON**，z21 +0.28，z252 +0.64，AD line 在 100d SMA 上方。

**口径警告**：我们的 z 是打在 cum AD 线的水平值上（非平稳序列），窗口内趋势主导；他大概率同款（原话就是 "add a z score to it"）。换池即换答案（[[pitfall-the-universe-chose-the-answer]]）——NYSE 口径与我们自选池的 AD line 行为不同，正式采用前要用 NYSE 数据重跑。

## 五、与我们停摆的 correction_risk 的对照

| | 我们（08-17 停摆） | 他 |
|---|---|---|
| 形态 | 条件基准率表 P(5%/21d)，VIX 五分位 × 200dma | 多条件阈值 regime + oscillator，无概率输出 |
| VIX 用法 | 水平分位（唯一 OOS 幸存者之一） | **期限结构阈值**（0.8/1.0/1.1），当状态机不当特征 |
| 我们已证伪的 | 9 特征 logistic OOS 输给基准率；VIX term 作为概率特征弱（AUC 0.55） | —— 他从不出概率，绕开了我们踩的坑 |
| 他有我们没有的 | —— | SKEW、PCCE、WMT/XLY 轮动 z、credit TR index HMA、NHNL regime、washout 确认结构 |

**可直接接到停摆项目开放问题 #2 的动作**（新维度必须以表切入 + 半样本单调检验，不进模型参数）：
1. **NYSE AD 21d z 的正负**作为第三个表切维度测一次（我们有 advances/declines，NYSE 口径需补数据源）
2. **WMT/XLY 63d z** —— 数据免费（yfinance），从没测过，最便宜的新信息
3. VIX/VIX3M 已知概率上弱，但**阈值化当第三切**（<0.8 / 中性 / >1.0）与他的用法同构，值得一测
4. credit：他用自制 HY total return index 的 HMA 趋势，我们上轮用 HYG/IEF 比价进 logistic 失败——**趋势化 vs 特征化是两种用法**，不算已证伪

## 五·五、Fixtures 落盘（2026-08-20）

全部图表/数据帖已存 `data/research/turin_fixtures/`（**180 帖 / 238 图 / 43MB，未 commit——是否入库等 Andy 拍板**）：`tweets.jsonl`（元数据+全文）· `images/`（`<date>_<id>_<n>.jpg`，name=large）· `tv_pages/`（5 张脚本页 HTML 快照，含 release notes）· `INDEX.md`（方法帖标注索引）· `_downloader.py`（可复跑，syndication API，零登录）。按年：2022:47 帖（泄露期主矿）· 2023:104 · 2024:14 · 2025:10 · 2026:5。

**R2 底图（`2022-03-14_1503166211701497859_0.jpg`）比推文本身多出的规格：**
- 卖出纪律：**多次 z<−1 打印 = 100% 现金/risk-off；单次 <0 打印不卖**（"major tops take time"）
- z>−1 区间的用法：可上 3x 杠杆 ETF / portfolio margin / 90d 动量高分股
- 证据形态：252d z 两侧的 **SPY 60 天前瞻收益分布对比**（>−1 侧左尾显著收窄）——他的验证方法就是我们表切法的分布版
- 附送动量因子代码：`linregress(arange, log(price))` 的 `((1+beta)**252) * r²`（年化斜率×拟合度）
- 自注："z-score to mimic SMA"——z 版和 100d SMA 版是同一 filter 的两种写法；"Turkey 1001 signals to perfect execution, this is just a filter"

## 六、来源索引（tweet id / script）

- 主号：1501947016867299336（R1）· 1503166211701497859（R2）· 1508257418387599361（R3+阈值）· 1633713947730669568 起的 2023-03-09 thread（R5）· 1911817860801847300（"5 行代码 breadth thrust"）
- 副号：2090285236185616393（turin_LT 条件）· 2082702882407621033（R4 配方）· 2082710972066615731（KY 免费套件——注意作者是 KaibaraYuzan 不是他）
- TV：`ZCGLFf86-TRKY-1001-DAY` · `upR4KgUO-VIX-TS-SPXL-v3` · `HbgASFRg-VIX-TS-HA-WEEKLYVERSION` · `Z3yf3sxz-C-Ind-strat` · 初版 `TLEZspXT-Turkey-1001-Day-Indicator`（六条件规格在此）
