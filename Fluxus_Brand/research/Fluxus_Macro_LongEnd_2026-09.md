# 长端利率三变量参考 · 2026-09（Warsh / Bessent / CPI）＋ 8/18 案例

*Marketing Steve 2026-09-10 立档。起因：Andy 问「8/18 市场为什么跌」→「Bessent 和 Warsh 最近的言论和 CPI 会对长端利率有什么影响」→「把这些信息和资源记全了，以后也会有类似的问题」。*
*⚠️ 本档所有 6 月以后的事实**全部来自 09-10 当天抓取**（Fed / Treasury 官网、Yahoo、Reuters、WSJ 标题、Wikipedia 时事页、Bing News RSS），不是训练记忆。每条带日期与源。**结论会过期，引用时看日期。***
*同类问题的用法见 §九「机制速查」。*

---

## 〇、一句话结论（截至 2026-09-10）

**三个变量都指向长端有上行压力，且 Fed 与 Treasury 都在失去对它的控制；明天（9/11）的 8 月 CPI 是唯一能换方向的变量，而它对长端的影响不对称：热 → 狠涨；凉 → 长端基本不动，只帮前端。**

支撑这句话的四个硬事实：
1. Warsh 讲稿**通篇零次**提到 yield / long-term / Treasury / balance sheet / deficit / term premium —— 长端在一篇没提长端的讲话后继续冲高
2. Treasury 回购 $2B → $4B（8/19）→ $6B（9/9）**逐级加码，收益率照涨**（10y 4.841%，2023-11 以来最高）
3. 仓库 `regime_ledger`：**OAS 在 252 日分位 0.8–8%**，VIX 14–16 —— 零信用压力、零恐慌 = 纯利率/期限溢价重定价
4. 传导路径是**油**：USO 一个月 +17.5%；WSJ 9/2 明写「油价上涨推高美国加息预期」

---

## 一、时间线（全部带源）

| 日期 | 事件 | 源 |
|---|---|---|
| **08-18 周二** | **美国 30 年期收益率创 2007 年以来最高**，「战争与油价担忧」；Trump 称不会重启伊朗停火谈判；霍尔木兹货船遇袭 1 死；伊朗向阿联酋射 2 枚导弹 | Reuters 8/18「US 30-year yields hit highest level since 2007 as war, oil worries fester」· TheStreet 8/18 · Wikipedia Current Events 2026-08-18（Al Jazeera / Gulf News） |
| 08-18 | **科技抛售**：「Tech selloff weighs down Wall Street as bond yields climb… multiyear peaks」 | Reuters 8/18 |
| 08-19 周三 | Treasury **长债回购加倍**（标准 $2B → $4B 底），「targets the sensitive longer-duration part」 | CNBC via MSN 8/19 `msn.com/…/ar-AA2at60R`（正文未取，JS 壳） |
| 08-20 | Bessent：回购「could increase further」 | Reuters via MSN 8/20 `…/ar-AA2aAR2T`（正文未取） |
| 08-23/24 | 「Bessent's 'Treasury twist' fails to tame bond yields」；他的 yield-curve-control 设想**延伸到 hyperscalers —— 为 AI 举债的公司** | Bloomberg via Moneycontrol 8/24 `moneycontrol.com/…article-14013416.html` |
| **08-24** | **Druckenmiller WSJ 专栏「Let the Bond Market Speak」** | WSJ `wsj.com/opinion/let-the-bond-market-speak-81529d74`（付费墙） |
| 08-25/27 | 专栏用 AI 写的（Claude / ChatGPT / Gemini / Perplexity）；「These are my ideas」 | Yahoo 8/27 `finance.yahoo.com/technology/ai/articles/stanley-druckenmiller-used-ai-write-114145195.html` |
| **08-28 周五** | **Warsh 首次 Jackson Hole 讲话「In Our Time」** | Fed 官网 `federalreserve.gov/newsevents/speech/warsh20260828a.htm` ✅ 一手 |
| 08-28/29 | 媒体解读「准备加息」；9 月加息概率升至 55.7% | Fox Business / Investopedia / Blockonomi / FINCHANNEL |
| 08-30 | Bessent 会 BoJ 行长 Ueda：**支持日本应对「日元大幅低估」的果断市场与货币行动** | Treasury 读出 `home.treasury.gov/news/press-releases/sb0619` ✅ 一手 |
| 08-31 | Bessent 在 G20（Asheville）对 CNBC：「We are the house. We do have the information, and over time we win」；嘲 Druckenmiller「doesn't like losing money」；称美债「本月最佳主要债市，30 年在跌」；10y 4.73%（2025-01 以来最高） | Yahoo 8/31 `…/bessent-taunts-druckenmiller-over-bond-164801093.html` |
| 08-31 / 09-02 | **JGB 10 年逼近 3%「一代人未见」**；油 > $91；**Bund 10 年 15 年新高**；美 10y「近三年高」 | FMT 8/31 · WSJ 9/2 |
| **09-08 周二** | Bessent SMU 讲话：**「I am the house now… you can bet against me if you want」「it's my dream, I have asymmetric information」** | Yahoo 9/10 `…/treasury-unveils-6b-bond-buybacks-172123799.html` · Yahoo 9/9 `…/bessent-dares-currency-traders-treasury-130441125.html` |
| **09-09 周三** | **首次 $6B 回购**（10–20 年 + 20–30 年，发短债付 = maturity twist）；华尔街预期 $6–10B，落下沿；**10y 冲 4.841%，2023-11 以来最高**；FT「令投资者失望」 | Yahoo / Fox Business / **FT** 9/9 |
| **09-11 周五** | **8 月 CPI 发布**（待出） | Yahoo / Seeking Alpha 9/9 |

⚠️ 日期勘误：AOL 9/9 那篇把 SMU 讲话写成「Tuesday, September 9」—— 2026-09-09 是周三；讲话是**周二 9/8**，Yahoo 两篇一致。Andy 09-10 先说 9/8 后改 9/9，**两个日期都是真的：讲话 9/8，回购 9/9。**

---

## 二、Warsh（Fed）—— 讲稿逐字关键句

**讲稿：「In Our Time」，2026-08-28，Jackson Hole。五节：Preparing for Future Policy Conjunctures / Forward Guidance and Its Stand-ins / Key Principles / The Economy Today / Conclusion。**

### 零命中清单（对长端最重要的发现）

> **0 hits: yield, yields, long-term, longer-term, curve, Treasury, Treasuries, balance sheet, holdings, deficit, fiscal, debt, term premium, tightening, QT, hike, raise, cut, easing**

`supply` 只出现一次，且是「labor supply」。**他没有谈长端、没有谈资产负债表、没有谈财政。** 市场把长端往上打，打的是一篇没提长端的讲话。

### 「The Economy Today」逐字（与长端相关的）

- 通胀：**「The 12-month change in the PCE price index stands at 3.7 percent, while the six-month change is 4.1 percent.」** —— 六个月 > 十二个月 = **在加速**
- **「And while this summer's PCE and CPI readings were better than expected, they do not tell me that underlying trends have meaningfully improved.」**
- 广度：**54% 的 PCE 篮子 12 个月涨幅 > 3%**（疫情前二十年 32%）；6 个月口径 49%
- **「The recent rise in overall commodity prices also bears watching.」** ← 油的通道，他点了
- 信用：**「Credit spreads on corporate bonds and leveraged loans are near the low ends of their historical ranges」**；「I would be hard pressed to describe broad financial conditions as restrictive」 ← 与仓库 OAS 分位 0.8–8% 完全对上
- 就业：失业率 4.1%，「consistent with full employment」
- AI capex：**「More than half of the cap-ex growth this year can likely be ascribed to the buildout related to AI」**；投资四季增速 ~9%，2021 以来最高
- **「We're staying keenly focused on market internals, watching performance across sectors.」** ← Fed 主席在看板块轮动
- 责任：「The responsibility for 65 months of sustained, elevated inflation sits squarely with the central bank.」
- 标准：**「We must be confident that underlying inflation is moving to our objective, clearly and at sufficient speed. Otherwise, we have work to do.」** ← 媒体「准备加息」的全部依据，是条件句
- 姿态：「I stand here today committed to a discipline, not to a decision.」

### AI 段（与 8/18 久期清算相关）
「Will the next generation of AI models demand even greater capital intensity, or will the models themselves help devise a capital-light solution?」「It's not obvious where the returns on capital will land or on what timescale.」「how much of the surplus goes to owners of scarce assets—AI labs, chipmakers, energy producers, and cloud providers?」

### 解读
他对长端**一个字没说**，但他选的数字全指一个方向：通胀 3.7/4.1 且加速、商品在涨、金融条件不紧、充分就业。**前端要更高更久，长端通过 higher-for-longer + 通胀补偿吃到它。** 他没有给长端任何「Fed 会接盘」的暗示 —— 这本身就是对期限溢价的放任。

### Fed 内部对 Treasury 回购的态度
**Waller（Fed Governor）：「I've never believed as an economist, not a policymaker, that these kind of short-run interventions do much.」**（AOL 9/9）—— Fed 公开不看好 Treasury 的 twist。

---

## 三、Bessent（Treasury）—— 供给侧

### 回购参数（官方公告页 09-10 未取到，两次 404；以下为 Yahoo 9/10 报道）
| | |
|---|---|
| 标准规模 | $2B → **$4B 底**（8 月宣布）→ **$6B 首次**（9/9） |
| 期限桶 | 10–20 年 · 20–30 年 |
| 结构 | **maturity twist**：买长债，用**增发短期国库券**来付 |
| 市场预期 | Wrightson ICAP：$5–6B 起步、「不排除更大」；华尔街区间 $6–10B → **$6B 落下沿 = 失望** |
| 效果 | 公告后 10y **+~10bp**；9/9 冲 4.841% |

### 原话
- SMU 9/8：**「I am the house now, so when we intervene with the Japanese yen, I have pretty good insight into what the Japanese, what the Bank of Japan is going to do, what Japanese policymakers are going to do. And you can bet against me if you want.」**
- SMU 9/8：**「Whenever people say, 'Oh, well, Treasury Secretary is taking a risk' – well, it's my dream, I have asymmetric information.」**
- G20 8/31：**「We are the house. We do have the information, and over time we win.」**（语境：伊朗政策）
- G20 8/31：「U.S. Treasuries have been the best-performing major bond market this month, with the 30-year yield down and the 10-year roughly flat」 ← **九天后 10y 4.841%**
- 立场（Yahoo 转述）：**不让交易员把高收益率当成永久趋势**，把注意力拉回基本面
- 对 Druckenmiller：「Stan's a great investor」「changes his mind a lot, and he doesn't like losing money」

### BoJ 读出（8/30，一手）
「expressed strong support for Japan's decisive market and monetary steps to address the **substantial undervaluation of the yen** and noted the role of yen weakness in contributing to domestic inflationary pressures in Japan」；「the importance of sound formulation and communication of monetary policy to anchor inflation expectations and avoid excess exchange rate volatility」。**读出没提美债需求、JGB、债市稳定。**

⚠️ **日元 ↔ 美债的连接是推的，不是读出写的**：日本是美债边际买家；JGB 10y ~3% 意味着日本钱有理由留在国内；Bessent 支持日元升值 = 支持日本收紧 = 加剧这个撤退。**这条逻辑链每一环有源，但没有一个源把它串起来。**

### hyperscaler 框架（Bloomberg via Moneycontrol 8/24）
Bessent 的 yield-curve-control 设想「extends beyond Treasuries. It includes the so-called hyperscalers, companies pouring money into AI and borrowing to do it.」—— Treasury 把 **AI 举债**看成和国债同一个久期问题。这正好接上 8/18 的成分表：久期最长的 AI capex 链被最狠地卖。

---

## 四、反方

| 谁 | 说什么 | 源 |
|---|---|---|
| **Druckenmiller**（Bessent 前老板） | **「Governments defending prices against fundamentals always lose.」** 回购是「price management」不是流动性操作；市场读成「an attempt to suppress yields」；会造成**「an escalating cycle of ever-larger purchases」**；**「deficit reduction, not buybacks」才是唯一可持续的降长端路径** | WSJ 8/24 专栏；Yahoo 8/27 转述 |
| **Ian Lyngen**（BMO） | 30 年期 **5.3% 是 Bessent「effectively drew in the sand」的线**；回购扩张风险在「the credibility of Treasuries as an asset class」 | Yahoo 9/9 |
| **Waller**（Fed） | 「短期干预没什么用」 | AOL 9/9 |

**Druckenmiller 的「越买越多的螺旋」已应验：$2B → $4B → $6B，三步，三周。**

---

## 五、CPI

| | |
|---|---|
| 7 月 CPI（8/12 发布） | **3.4% y/y**，连续第二月降温，「符合预期」（CBS） |
| Warsh 口径的 PCE | 12m **3.7%** · 6m **4.1%** —— 注意 PCE 六个月在加速，和 CPI「降温」标题相反 |
| 8 月 CPI | **9/11 周五发布**；TD 预期核心 **0.19% m/m**；9 月加息概率 **58%**（Forbes 9/9） |

**不对称性**：长端的病是供给 + 油 + 期限溢价，不是 Fed 路径。**热 → 确认 Warsh + 油，长端狠涨；凉 → 加息概率掉、前端受益，长端可能基本不动。**

---

## 六、全球

| | | 源 |
|---|---|---|
| JGB 10 年 | **逼近 3%，「a level not seen for a generation」** | FMT 8/31 |
| Bund 10 年 | **15 年新高** | WSJ 9/2 |
| 美 10 年 | 近三年高（9/2）→ **4.841%，2023-11 以来最高**（9/9） | WSJ / Yahoo |
| 美 30 年 | **2007 年以来最高**（8/18）；5.3% 是 Lyngen 说的「沙线」 | Reuters 8/18 · Yahoo 9/9 |
| 油 | **> $91**（8/31）；USO 月 +17.5%（仓库 09-10） | FMT · `data/output/etf_data.json` |

---

## 七、仓库校验（`data/history/regime_ledger.csv` · `data/output/etf_data.json` @ origin/main 09-10）

| 08-20 → 09-09 | |
|---|---|
| OAS | 2.63–2.75；**252 日分位 0.008–0.29** —— 一年最紧 |
| VIX | 14.3–16.5 |
| USO | 周 +6.2% · **月 +17.5%** |
| TLT | 周 −0.3% · 月 −0.2% · 3 月 −2.6% |
| SMH | **周 +4.3%** —— 半导体从 8/18 已回来 |

**读法**：利差钉最紧 + VIX 没动 + 油飙 = **有序的久期重定价**，零信用、零恐慌，传导靠油。股市至今把 8/18 当一次性久期冲击，不当 regime 变化。

---

## 八、8/18 案例（完整版）

**导火索**：Trump 称不重启伊朗停火谈判（TheStreet 8/18）→ 油 → **30 年期 2007 年以来最高**（Reuters 8/18）→ 科技抛售（Reuters 8/18）。

**三层结构（仓库）**：
1. **广度层**（`groups_archive` 08-18 `perf_1d`）：AI-Datacenters −7.5% · Electronic Components −7.4% · Memory & Storage −7.4% · Semi Equipment −7.0% · Semis Broad −6.6% · Electrical Equipment −6.4% · Quantum −5.8% · **IPP −5.6%** · Optics −5.2%。涨的：Staffing +3.4% · Consulting +1.8% · Drug Mfg +1.7% · Cloud Software +1.5%。**Oil & Gas Drilling −0.8% —— 油股在跌，所以不是 risk-off，是久期**。SPX 只 −0.7%（7,745 → 7,692）；20 日线上占比 63.3 → 56.2 → **49.5%**；涨 4%/跌 4% 511/434 → 349/676 → **320/812**。恶化从周一 08-17 开始（净上涨 −1,583）
2. **盘型层**（`snapshot_SPX_20260818.json` 的 `development`/`facilitation` —— ⚠️ 描述的是 **08-17 那场**）：开盘在前日 value 内 open_auction；double_distribution 在 7,762.5 断开；向下延伸 7 个 bracket 建在 IB 低 7,771 之下，接受到 7,744.88
3. **期权层**（08-18 盘前 07:35 ET）：Regime **NEGATIVE**，净 GEX −9.19B，前一日 neutral → negative（−11.5B, erosion）；现货 7,745 **已在零 gamma 翻转位 7,758 之下**；put wall 7,700；0DTE 预期 7,706–7,785；**收盘 7,691.76 跌穿 put wall、跌出预期区间**。负 gamma = dealer 顺势对冲 = 加速器不是起因

**Andy 当天**（08-23 口述，`case_mrna_2026-08-19/andy_oral_2026-08-23_organized.md` L217）：「8月18号那天大盘是 gap down，我的科技股遭受重创。我觉得我的 sizing 可能太多了，遂把加仓的那 5% 在入场价附近、无亏损卖出……进入 8月18号收盘时，我手上只剩 5%。」**次日 MRNA +176%，+23R。**

**进 8 月月复盘「② 做对的」的写法**：利率冲击日砍久期仓位到保本，是对的动作；它第二天赚 23R 是另一件事。判决策不判结果。

---

## 九、机制速查（以后同类问题直接用）

| 谁动了 | 对长端的机制 | 怎么验证是不是这条 |
|---|---|---|
| **Fed 鹰派**（讲话/点阵/加息） | 双刃：可信度↑→通胀预期↓→长端**降**；higher-for-longer→长端**升**。**看讲话后长端走向**决定哪边赢 | 讲话后 3–5 日 10y/30y 方向；市场加息概率变化 |
| **Treasury 供给**（发行结构/回购/twist） | 买方进场价格还跌 = 需求结构性不足 = 期限溢价。回购规模对市场是**信号不是力量** | 回购公告后 10y 走向；分析师预期区间 vs 实际（落下沿=失望） |
| **通胀数据**（CPI/PCE） | 前端看 CPI；长端看供给+油+期限溢价。**不对称**：热狠涨、凉不动 | 发布后 2y vs 30y 谁动得多（bear steepening = 长端问题） |
| **油 / 商品** | 油 → 通胀预期 → 长端。**是否 risk-off 看油股同日方向**：油股跌 + 长久期跌 = 久期；油股涨 + 全跌 = 地缘 risk-off | `groups_archive` 当日 Oil & Gas 的 `perf_1d` |
| **海外长端**（JGB/Bund） | 海外收益率升 → 海外买家留在国内 → 美债边际买盘撤 | JGB 10y 水位；BoJ 动作；Treasury 与 BoJ 读出 |
| **信用 vs 利率** | OAS 紧 + 收益率升 = 利率故事；OAS 宽 + 收益率升 = 信用故事 | `regime_ledger.csv` `oas_rank252` |

**成分表是最快的判别器**：把当日 `groups_archive` 按 `perf_1d` 排，看跌的是不是按久期排队（Datacenters/Quantum/IPP 在前，Staffing/Consulting 在后）。是 → 利率；不是 → 另找。

---

## 十、缺口（诚实记录）

- **Treasury 官方回购公告页未取到**（`treasurydirect.gov/auctions/buybacks/` 与 `home.treasury.gov/policy-issues/…/treasury-buybacks` 均 404；Bing 未索引）。操作参数来自 Yahoo 9/10
- **CNBC 8/19、Reuters 8/20 正文未取**（MSN JS 壳，真 Chrome 也空）—— 只有标题
- **Moneycontrol 8/24** 只取到导语一句
- **Druckenmiller WSJ 原文**付费墙，论证来自 Yahoo 8/27 转述
- **8/18 当天 10y/30y 的具体 bp 变动**：Reuters 标题只给「2007 以来最高」，没给数
- **Warsh 对期限溢价/资产负债表的看法**：**不是没找到，是他没说**（零命中已核两遍）
- Andy 8/18 的 Discord #live-commentary 不在仓库；Founders Note 08-18/19 为空
