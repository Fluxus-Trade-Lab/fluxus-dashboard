# 审查站 · 第 2 轮（重过闸）· 2026-08-30

> 本轮审查站是**全新上下文**，没参与任何一稿的写作，所有数字**从 `data/output/universe.json` 原始字段独立复算**，未读稿子的自述表来验稿子。
> 口径源：`universe.json` timestamp `2026-08-29T03:18:17.230043+00:00`（count 5634）· `quality.json` date `2026-08-28` status `ok` · 每行 `bar_date=2026-08-28`。

## 判定：**退回 —— 旗舰站 1 句 · 分发站 V2 1 句 · V3 1 句 · 不毙**

上一轮两处拦路**都真修好了**。本轮的三处是**新的**，全部是一句话（合计约三行文本）能改完的。
V1、V4 直接过闸，V4 仍是四条里最强的一条。

---

# 〇、上一轮两处拦路是否已修好（逐条对账）

| 上一轮的拦路 | 当时的判词 | 本轮实测 | 结论 |
|---|---|---|---|
| 🔴 **① 旗舰 `my convention`** | 把「止损放 50 日线」这个我们自己的假设，用第一人称写成 Andy 的既定规则；与 `PUBLISHED_X:115` 的 0.73 ATR 结构止损冲突 | `grep -n "my convention" 04_flagship.md` → **仅命中 §三 的引述与禁令行（180、192），正文块零命中**。正文改为 `Call it the 50-day`（一个被点名的选择）。全篇零处宣称 Andy 用 50 日线做止损 | ✅ **已修好** |
| 🔴 **② V3 `any name, any volatility` → 44–55** | 真实池 11.2% 的可交易票落带外，是一条会被读者正确证伪的公开声明 | 我独立复算：`tradeable=true` n=**2,556**，全池 ext=10 真实带 **40.5993–67.8583**，落 44–55 之外 **285 只（11.15%）**；收进 ATR% 2–8 后 n=**2,091（81.81%）**，实测带 **44.4497–54.5416**，落带外 **0**。新版正文写的正是这个限定 | ✅ **已修好（限定范围正确）**，但**换来一个新问题，见 §6(d)** |
| 🟡 V1 `60 to 67` 内缩 | 真值上界 67.5325 | 已改 **`60 to 68`**（外扩，安全） | ✅ 已修好 |
| 🟡 V2 `You only ever ask it` 教训感 | 对读者习惯的断言，零数据支撑 | 已改 **`It only ever gets asked after the move.`** | ✅ 已修好 |
| 🟡 旗舰 `This was never a rule about being careful.` | 与 08-24 被亲手删掉的 `The news is never in the chart` 同形 | 已删，换成 `Same arithmetic, opposite sign. All it ever reads is…` | ✅ 已修好 |
| 🟡 旗舰散文里裸写 `186%` | ext=2 全带 175.76–192.59 | 已改 `about 186%`，并在 §二 注明理由 | ✅ 已修好 |
| 🟡 排期倒过来（说破恒等式的先行） | V4 被排到下周 | 已改 **V4（或含新止损因果的旗舰）→ V1 → V3 → V2** | ✅ 已采纳 |
| 🔴 数据陈旧两场 | 08-27 收盘 + 08-28 全天缺 | `quality.json` date=**2026-08-28**，是仓库里最新一场收盘；周日无新数据；周一盘前发 = 口径成立 | ✅ **已推进，口径日说对了** |

**并且**：v1 的支柱句「49.8 / 50.4 — Half, both times」被本轮自己作废了，作废理由（恒等式的产物，两票 ext 本来就几乎相等）与上一轮审查站的判词一致。这是本轮最好的一件事——**它自己把自己的支柱推翻了，而不是等我来推。**

---

# 一、无出处主张 —— **通过（一处数字须外扩）**

我用 Bash 从原始字段独立复算，**没有读稿子的自述表**。逐个核对稿里每一个数字：

## 1.1 CRM / VEEV 主读数（08-28 收盘）

| | ATR%（`atr/close`） | ext 复算（`sma50_dist ÷ ATR%`） | 文件 `atr_from_sma50` | 止损%（`d/(1+d)`） | 比值 vs ext=4 | 稿子写的 |
|---|---|---|---|---|---|---|
| **CRM** | 4.2685% | **9.7275** | 9.7275 | **29.3395%** | **49.7073%** | 9.73 / 29.34% / 49.7% ✅ |
| **VEEV** | 3.9865% | **8.3460** | 8.346 | **24.9651%** | **55.0888%** | 8.35 / 55.1% ✅ |
| OKTA | 5.5121% | 3.2668 | 3.2668 | 15.2591% | 118.3898% | 正文未用 ✅ |
| OOMA | 5.8721% | 2.0815 | 2.0815 | 10.8913% | 174.6414% | `tradeable=false`，正文未用 ✅ |

`change_pct`：CRM **+1.57%**、VEEV **−1.93%**、OKTA −3.86%。close：CRM 256.00、VEEV 276.69。
→ V3 的 *"Then Friday happened to one of them. Not a crash."* 与 *"The other barely moved"* 都成立 ✅。

> 🟡 **§二 那句「逐位吻合（非自证）」是假的，改掉。** `atr_from_sma50` 不是独立第二实现——`pipeline/screeners/atr_enrichment.py:52` 的 `atr_multiple_from_sma50(close, atr, sma50_dist)` **就是** `sma50_dist / (atr/close)`，同一个函数、同一批输入。docstring:22 自己写着「so the badge and the screener column are **one number**」。这是**一致性检查**，不是独立验证。数字我另行复算过，全对；但这句方法学表述会让下一个人跳过真正的复算，删掉或改成「与存储列一致（同一实现，非独立验证）」。

## 1.2 08-27 快照（V3 的「周四那两个数」）

`git show 03761dc8:data/output/universe.json`（ts `2026-08-28T05:36:00Z`，bar_date 2026-08-27）：
CRM ext **9.6822** 比值 **49.7979** · VEEV ext **9.4029** 比值 **50.4463** · OKTA 4.4012 / 92.4994 · OOMA 2.4059 / 154.1307
→ V3 写 **49.80 / 50.45** ✅（注：上一轮我方写的 50.44 是截断，50.45 才是四舍五入正确值，本轮分发站是对的）
→ 分发站 §出处表的 OKTA `92.50→118.39`、OOMA `2.406→2.081` ✅

## 1.3 21EMA 换参照（V4 的 +49.8 / +92.5）

CRM：stop50 **29.3395%** → stop21 **19.5846%**，size 0.85209 → 1.27651，**+49.8088%**
VEEV：stop50 **24.9651%** → stop21 **12.9672%**，size 1.00140 → 1.92794，**+92.5243%**
→ V4 写 **49.8 / 92.5** ✅（上一版的 43/71 是 08-27 读数，已正确作废）

## 1.4 纯函数带宽（`f(4a)/f(ma)`，`f(x)=x/(1+x)`，ATR% 扫 2→8）

| | 我的复算 | 稿子写的 | |
|---|---|---|---|
| ext=2 | **175.7576 – 192.5926** | V2 `176 to 193` | 🟡 **下界内缩**（175.76 < 176） |
| ext=7 | **60.3175 – 67.5325** | V1 `60 to 68` | ✅ 外扩，安全 |
| ext=10 | **44.4444 – 54.5455** | V1/V3 `44 to 55` | ✅ 外扩，安全 |
| 减半点 | **8.6957 – 11.7647** | V2 `8.7 and 11.8` | ✅（下界内缩 0.004，可忽略） |

> 🟡 **V2 的 `176` 是上一轮 `60 to 67` 的同一个病，只是换了个地方**：向内取整＝把带说窄了。同一份稿子里 V1 已经改成外扩的 68，V2 这处没跟上。改 **`175 to 193`**。

## 1.5 读数表 20 格（配图）—— **逐格复算，20/20 吻合** ✅

| ext ＼ ATR% | 3 | 4 | 5 | 6 |
|---|---|---|---|---|
| 2 | 189.2857→**189** | 186.2069→**186** | 183.3333→**183** | 180.6452→**181** |
| 4 | 100→**100** | 100→**100** | 100→**100** | 100→**100** |
| 6 | 70.2381→**70** | 71.2644→**71** | 72.2222→**72** | 73.1183→**73** |
| 8 | 55.3571→**55** | 56.8966→**57** | 58.3333→**58** | 59.6774→**60** |
| 10 | 46.4286→**46** | 48.2759→**48** | 50.0000→**50** | 51.6129→**52** |

「纯函数、与盘面无关、不用重做图」——**属实** ✅。散文的 `about 186%` 对应 ATR%=4 那格 ✅。

## 1.6 真实池 ext=10 带宽与落带外比例

`tradeable=true` **n=2,556**（全库 5,634）· 全池带 **40.5993–67.8583** · 落 44–55 外 **285 只 = 11.15%**
ATR% ∈[2,8] 子集 **n=2,091 = 81.81%** · 实测带 **44.4497–54.5416** · 落 44–55 外 **0**
→ 分发站写的 2,091 / 81.8% / 44.45–54.54 / 0 例外 / 全池 40.60–67.86 / 11.2%（285）**全部吻合** ✅
→ `tradeable` = 市值 ≥ 门槛 且 成交额 ≥ 门槛（`pipeline/quality.py:142-158`），叫 "liquid tickers" **成立** ✅

## 1.7 posts.csv 三个判据基线

n=**14** 帖 · 总收藏 **1**（唯一一条：2026-08-24 LONGFORM，1 收藏 / 5 赞 → 收藏赞比 **0.20**）
ARC n=**8**，views 中位 **180**，最高 **421**（也是全库最高）· REPLY 唯一一条 2026-07-30，**81** 曝光
→ 分发站三个判据基线**全部吻合** ✅。「收藏/赞 >0.5 从没达到过」**属实**，两级判据的建议是对的，请采纳。

## 1.8 其余

`date(2026,8,27)`=**Thursday**、`date(2026,8,28)`=**Friday**、`2026-08-30`=Sunday、`2026-08-31`=Monday ✅
CRM `high_52w_dist` **−4.39%**、`days_since_52wh` **167** → 全篇零处写「新高」「龙头突破」✅
天真算法 `4.00/9.7275` = 41.12% → **两稿正文均不存在 41%** ✅
`grep -nE '\$[0-9]|million|billion|万美元'` 对两份文件的**正文块** = 空（cashtag 不触发）✅
0.25% 的出处 `PUBLISHED_X:19`「0.25% for 23R」+ `:115`「0.25% ÷ 4.34% ≈ 5%」**逐字核对属实**，且确实是**规则值**而非 MRNA 那笔的 0.217%（`:104`）✅
4/7/10 归属：`pipeline/screeners/atr_enrichment.py:66`「The Jacobs/Jeff Sun bands (0-4 entry / 5-7 hold / >=7 scale-out)」**真实存在**；`JeffSun_Wiki/wiki/entry-rules.md:30`「No entry if ATR% from 50-MA exceeds 4x」✅；`atr-extension-signals.md:63`「At the individual stock level, he uses 10x ATR% for profit-taking」✅。**三条引用全对，V1 的 Entry/Trim/Take profit 映射准确。** ✅

---

# 二、重复 hook —— **通过**（一处跨站撞车，不拦路）

四条变体的**第一拍动作**确实各不相同：

| | 第一拍**做的动作** | 落点 |
|---|---|---|
| V1 | 拿起读者手里已有的那把尺，说他只读了一半（翻译） | 尺的背面 |
| V2 | 先替读者说出最狠的反驳，再邀请他反向跑一遍（预先反驳） | 反向那一半 |
| V3 | 给两个数，然后让其中一个当着读者的面动掉（时间序列） | 可证伪带 |
| V4 | 先拆自家可信度（自伤） | 整个品类 |

🟡 **但旗舰和 V1 现在是同一个动作**：旗舰 *"you already know what everyone is going to tell you. It's extended."* 与 V1 *"Everyone reads it as a temperature."* 都是「立人群共识 → 一句推倒」。上一轮旗舰的第一拍是「把一个词换成可下单的数」，本轮重写后向 V1 靠了一步。
**不拦路**（六项审的是四条变体之间），但**排期上别让旗舰和 V1 挨着发**——分发站建议的 V4 → V1 → V3 → V2 里，若旗舰当周发，把 V1 放在离旗舰最远的位置。

---

# 三、变体是否只是缩写 —— **不通过（V2 一处）**

- **V1 独立成立 ✅ 且是四条里最干净的一条**：零 ticker、零日期、零盘面，而且**它自己交代了基准**（`4 — call this one full position.`）——这一点旗舰反而没做到，见 §6(e)。
- **V2 ❌ 它现在站不住**：正文第二段写 `Same risk budget, same stop convention **as before**` —— **as before 在这条帖子内部没有先行词**，帖子从头到尾没提过任何 stop convention。同理第一句的 `Before you decide **this** is a rule for cowards`，`this` 也没有对象。稿子声称它「不含 ticker，同样常青、能独立存在」，**但它实际上是在向旗舰稿借上下文**——正是本项要防的那件事。**三个词能修好。**
- **V3 独立成立 ✅**（重写后靠自己的时间序列站住了，不再依赖旗舰的 49.8/50.4）
- **V4 独立成立且最强 ✅**（靶子是整个「晒仓位百分比」的品类，没见过 CRM 也中枪）

---

# 四、AI 腔 —— **逐条点名，共五条；标准连接词零命中**

`grep -nEi 'moreover|furthermore|delve|crucial|ultimately|not only|it's worth noting|in conclusion|dive into|landscape|realm|tapestry|underscore|pivotal|robust|leverage|navigate|testament|game.chang|unlock|seamless|meticulous|nuanced|multifaceted|it is important|serves as|plays a (vital|key|crucial)'` → **对两份文件的正文块全部零命中**，仅命中稿子自己的自查行与 grep 命令行。✅

按风险排序的五条（全部**不拦路**，但要让 Andy 拍）：

1. 🟡 **V2 中段**：*"Below that you're being paid to be early. Above it you're paying to be late."* —— 教科书级对仗（paid/paying × early/late 双轴）。上一轮已点名，本轮**未换，只备了替代版**。记忆里那条「他删了我评分第一的收口句」形状完全一致，**这仍是最可能被划掉的一句**。备选 `Under that number the same risk buys more shares than your normal size. Over it, fewer.` 是对的方向。
2. 🟡 **V4 收口**：*"That part isn't a convention. / That part is division."* —— 排比＋对仗双段收口。已备非对仗版 ✅。
3. 🟡 **V1 收口**：*"The trim line isn't where the stock turns dangerous. It's where the division already had you at two thirds."* —— 「不是 A，是 B」镜像句。已备非镜像版 ✅。
4. 🟡 **旗舰收口**：*"Conviction doesn't change the division."* —— 抽象名词 × 抽象名词 + 头韵，「要回味的巧话」家族。已备两个重话版 ✅。
5. 🟢 **旗舰段 4**：*"Same arithmetic, opposite sign."* —— 不是 AI 腔，是**数学上不对**：186% 与 49.7% 不是「相反的符号」，它们是同一个乘数落在 1 的两侧（互为倒数量级）。这稿全部的卖点是「算术精确」，一个懂数的读者会在这里绊一下。改 **`Same arithmetic, the other side of one.`** 或 **`Same division, the other direction.`**

> **豁免（不算 AI 腔）**：旗舰 *"Your stop isn't a line on a chart. It's rent."* —— 与 `PUBLISHED_X:111` 的 *"Position size is not risk. Stop distance is risk."* 是同一个**他已经公开用过**的句法。这是他的声音。上一轮的豁免继续有效。

🟡 **顺带：`rent` 链在该收账的地方断了。** 段 2 建了 `rent → same square footage → you don't set the rent → the rent is 29.34%`，链是干净的（租金/坪＝止损距离，预算固定 ⇒ 面积＝仓位），但段 3 该兑现的时候写的是 `buys 49.7% of the position` —— 喻体消失，换回了内部词。§4.8 第 4 条「比喻要连成一条链」，把 `position` 换成 `square footage` 就闭合了，且顺手解掉 §6(e) 的一半。

---

# 五、语气漂移 —— **通过**

对照 Voice Bible §1 **Calm Monk / 天气预报员（报概率、不下命令、对预报无自我）**：

- **零方向、零买卖、零持仓、零预测**：`grep -nEi '\b(buy|sell|long|short|target|forecast|predict|expect)\b'` 对四条变体代码块 = **空**；旗舰里 `buy` 只出现在 *"You can still buy it. You just can't buy as much of it."*——那是**许可**不是**指令**，反而是 anti-dopamine 的正面表达 ✅
- V3 *"one of us did the arithmetic wrong, and I'd want to know which"* 与 V4 *"Including mine"* 仍是本轮最好的两句天气预报员 ✅
- 上一轮点名的 V2 教训感**已修好** ✅

🟢 **一处要主动澄清，免得下一轮误伤**：旗舰开头 *"You've had that chart open all weekend"* 是**断言读者做了什么**，形状上像上一轮被判漂移的 V2。**但它不是同一件事**：V2 那句是把「读者只在事后才算」当成**论证前提**（零数据支撑）；旗舰这句是 Voice Bible §4.8 第 1 条**明确要求**的开场（「开头不许是我……今天在读这条的人正盯着一只已经飞了的票犹豫要不要追——从那里开口」）。**判通过，并记进案，别下一轮又拿它当漂移。**

🟢 V4 *"Including mine, which is why the stop convention is written into every one of these."* —— 我查了：这是一条**对外的方法承诺**，但它有据 —— Voice Bible §3「**the risk ledger** — 'x% trade risk, y% port risk' as the fixed footer of **every public trade**」是已登记的自有 tic。**不算代写立场** ✅。

---

# 六、诚实边界 —— 🔴 **不通过（两处，都是新的）**

## (a) 口径日 —— **通过，而且这轮说对了** ✅

- `quality.json` date=**2026-08-28**，全部 5,634 行 `bar_date=2026-08-28`，是仓库里最新一场收盘。今天 08-30（周日）无新数据。**周一 08-31 盘前发，08-28 仍是最新一场，口径成立。**
- `date(2026,8,28)` = **Friday** ✅。旗舰段 2/3 两处 `Friday's close`、V3/V4 的 Thursday/Friday 全部对得上。
- 上一轮点名的「`since Thursday` 在周一发会漏掉整个周五」**已修好**：改成 `all weekend` ✅。上一轮点名的 V4「Same day 没说哪天」**已修好**：改成 `Friday's close` ✅。
- 失效表（§四「口径日与失效条件」）写得**准确且可执行**，`about 186%`/读数表/0.25% 标为不失效 ✅ —— 我复算证实这三项确实与盘面无关。

> 🟡 **一处例外：选择 4 的备选 A 自带一个口径错误。** *"How much of it stopped being your call on **Thursday morning**."* —— 全篇口径日是**周五**，正文从头到尾没建立过「Thursday」这个时间点（它指的是 CRM 08-27 那根 +22.58%，但读者看不到）。周一发时这是四天前。**若 Andy 选备选 A，必须同时把它改成 `on Friday's close` 或把段 2 里补一句 Thursday 的跳空**——否则收口指向一个正文没提过的日子。请把这条一起递给他，别让他挑到一个带故障的选项。

## (b) 有没有把我们的假设写成 Andy 的立场或方法承诺 —— **通过（上一轮的翻车点已修好）** ✅

- `my convention` 在**正文块零命中**；50 日线以 `Call it the 50-day` 出现——一个被点名的选择，不是他的惯例 ✅
- V1/V2/V3/V4 一律用 `one stop convention` / `same stop convention` / `the 50-day, say` ✅
- 唯一引用他的是 0.25%，是**已公开的规则值**（`:19`、`:115`），不是 MRNA 那笔的 0.217% ✅
- V3 的 §纪律③ 明文写死「不许滑成 `my convention`」，V4 的注也写了 —— 这条纪律在稿内被制度化了 ✅

> 🟡 **但替换句自己带了一条无出处的因果法则，请降调。** 旗舰段 2：*"you put the stop where the chart lets you, and **a bar this far from its base doesn't let you put it close**."* —— 这是一条**关于图表的普遍规律**，我们没有任何数据支持它，而且仓库自己的字段就在旁边打脸：CRM 的 `sp_stop` = **200.10（距收盘 21.84%）**、VEEV 的 `sp_stop` = **236.19（距收盘 14.64%）**，都比我们用的 50 日线止损（29.34% / 24.97%）**近得多**；而 Andy 公开那笔用的是 **0.73 ATR ≈ 3.12%**（按 CRM 的 ATR% 折算）。
> 这不是上一轮那种归属错误（那个真修好了），**是把一个假设从「他的习惯」改写成了「图表的法则」——归属对了，举证还是零。** 而且句子里有个逻辑折返：先说「止损由图决定」，下一句又「Call it the 50-day」（一个我们自己挑的线）。读者会看见这个切换。
> **不拦路**（措辞含糊，`close` 未定义，严格说不可证伪），但**建议改**，见回退清单 🟡-1。

## (c) 有没有发出会被读者正确证伪的公开声明 —— **通过** ✅

上一轮的 44–55 已收进 ATR% 2–8，我实测该子集 **0 例外**。这条声明现在**是真的**。上一轮那个最难看的失败模式（读者拿低波票算出 41%，紧贴我们全程警告的天真算法 41.1%）**已经消失**。

## (d) 🔴 **有没有把恒等式包装成实证发现 —— 这是本轮的头号拦路，在 V3**

> **原句**：`Here's the part you can break. Any name that moves between 2 and 8 percent on an average day — four out of every five liquid tickers — ten ATRs out, same stop convention: 44 to 55. **I ran all 2,091 of them that qualify and not one landed outside.**`

**这句话在数学上不可能有反例，所以「2,091 只无一例外」不是证据，是同义反复。**

比值只是 ATR% 的一元函数：
```
ratio(a) = f(4a)/f(10a),  f(x)=x/(1+x)
         = 0.4 · (1+10a)/(1+4a)
d/da = 0.4 · 6/(1+4a)² > 0   ← 在 a>0 上严格单调递增
ratio(0.02) = 44.4444%   ratio(0.08) = 54.5455%
```
**一个严格单调函数在闭区间上的值域，就是两个端点。** 只要一只票的 ATR% 落在 [2%, 8%]，它的比值**必然**落在 [44.44, 54.55]——这与它是哪只票、什么行业、什么价格、有没有财报**完全无关**。筛选条件（ATR% 2–8）和被检验的结论（44–55）是**同一件事的两种说法**。

- 「我跑了 2,091 只」提供的信息量 = **0**（超出「它们的 ATR% 在 2–8 之间」之外，一个 bit 都没有）
- `Here's the part you can break.` 是**假的证伪邀请**：这一段没有任何东西可以 break
- 这**恰好是上一轮我方标红的那条更深一层**（止损定在 50 日线后，ext 与止损距离是同一个量）在新版里的**复发**，只是从 CRM/VEEV 的「巧合」换成了 2,091 只的「普查」。**同一个形状，第二次。**
- 后果不是被证伪，是**被看穿**：这稿的全部信用来自「我们把算术做对了」。一个懂数的读者两分钟就能看出这是循环论证，而他正是我们最想要的那个读者。

> 相比之下，**V3 同段里那个 `four out of every five liquid tickers`（81.81%）是真的实证结果** —— 那是关于**我们股票池的经验事实**（2,091/2,556），跟函数值域无关。它才是这一段值得报的数。

**必改。**见回退清单 🔴-2。

🟡 **同族的轻症（不拦路）**：V1 *"Those ranges are the entire contribution of volatility, **measured across** names that move 2 to 8 percent on an average day."* —— `measured across` 同样暗示实测，实为函数值域。但 V1 的句子重心在「这就是波动率贡献的全部」（**这句是对的且有价值**），且没发出证伪邀请。**建议**把 `measured across` 换成 `across`，一个词。

🟡 **另一处轻度过度归因（不拦路）**：旗舰段 3 *"**Neither company did anything to those two numbers.** The distance did."* 我做了反事实分解：49.71 → 55.09 的 5.382pp 缺口里，**距离贡献 +5.814pp，波动率贡献 −0.433pp（约 8%，方向相反）**。ATR% 是公司自己的价格属性，它确实动了那个数。改成 **`Almost none of that gap is the companies. It's the distance.`** 就从「几乎对」变成「精确对」，而且更像天气预报员。

## (e) 🔴 **额外拦路：旗舰的核心数字，分母在正文里从未出现，而且 "the base" 在相邻两段是两个意思**

旗舰段 2：*"a bar this far from **its base**"* —— 这里 `its base` = **50 日线本身**（距离为 0）。
旗舰段 3：*"it buys 49.7% of the position it would have bought **at the base**"* —— 这里 `the base` = **ext = 4**。
旗舰段 4：*"the same rule buys about 186% of what it buys **at the base**"* —— 同样是 ext = 4。

**同一个词，相邻两段两个所指，而且其中一个所指会把算术变成不可能。** 若读者照段 2 的用法把「the base」读成 50 日线本身，那里的止损距离是 0，仓位无穷大，49.7% 无从谈起。

**更要紧的是：`4` 这个数在整篇正文里一次都没出现。** 全文提到的 ATR 倍数只有 9.73、8.35、two。基准只写在配图的表里（`4 ATRs — the base`）和图注（`at 4 ATRs from the 50-day`）。X 长推的正文必须自己站得住——**这稿最重要的一个数字（49.7%）在正文里是一个没有分母的分数。**

对照之下 **V1 做对了**：`4 — call this one full position.` 一句话把基准立了。旗舰反而漏了。

**必改。**见回退清单 🔴-3。两个词。

---

# 回退清单（逐句可执行；原句 → 问题 → 改法文本）

## 🔴-1 · 退回分发站 · V3 —— 把伪证伪邀请换成真实证结果

**原句**（05_distribution.md:107-111）：
> `Here's the part you can break. Any name that moves between 2 and 8 percent on an average day — four out of every five liquid tickers — ten ATRs out, same stop convention: 44 to 55. I ran all 2,091 of them that qualify and not one landed outside. If yours does, one of us did the arithmetic wrong, and I'd want to know which.`

**问题**：44–55 是「ATR% 落在 2–8」这个筛选条件的**代数后果**（`ratio(a)=0.4(1+10a)/(1+4a)` 严格单调，端点即 44.44 / 54.55）。「2,091 只无一例外」在数学上不可能有别的结果，它是同义反复不是证据；`the part you can break` 是一个没有东西可 break 的证伪邀请。**它是上一轮标红的恒等式问题的第二次复发。**

**改法（A，推荐——把真正的实证部分留下，把算术部分说成算术）**：
> `Here's the part that isn't an opinion. Ten ATRs out, same stop convention, the answer lands between 44 and 55 percent — and the only thing that moves it inside that range is how volatile the name is. That's not a survey, it's a division you can do on the back of a receipt. What is a survey: four out of every five liquid tickers move between 2 and 8 percent on an average day, so for four out of five, that's the whole range. Run yours. If you land outside it with a name in that band, one of us did the arithmetic wrong, and I'd want to know which.`

**改法（B，短版——只删掉那半句）**：
> 把 `I ran all 2,091 of them that qualify and not one landed outside.` **整句删掉**，把 `Here's the part you can break.` 换成 `Here's the part that isn't an opinion.`，其余不动。
> （删掉那句后，2,091 这个数消失，但 `four out of every five liquid tickers` 保留——那个 81.81% 才是真实证结果。）

⚠️ **两种改法都不要保留 `I ran all 2,091 of them`**。若 Andy 想留一个大数字撑场面，唯一诚实的写法是把它绑到它真正证明的那件事上：*"Four out of five liquid names — 2,091 of the 2,556 I can trade — move between 2 and 8 percent on an average day."*（这句我复算过，**属实**。）

---

## 🔴-2 · 退回旗舰站 —— 给 49.7% 一个分母，并解掉 "the base" 的一词两义

**原句 A**（04_flagship.md:17）：
> `Same 0.25% of risk. Out there it buys 49.7% of the position it would have bought at the base.`

**原句 B**（04_flagship.md:19）：
> `two ATRs off the 50-day, the same rule buys about 186% of what it buys at the base.`

**问题**：`the base` 在段 2 指 50 日线本身、在段 3/4 指 ext=4；而 `4` 这个基准在整篇正文里一次都没出现，只活在配图里。X 长推的正文必须独立可读——现在最重要的那个数是一个没有分母的分数，而且照段 2 的用法读会得到一个无穷大。

**改法（两处替换，共四个词）**：
> A → `Same 0.25% of risk. Out there it buys 49.7% of the square footage it would have bought four ATRs out — the top of the entry zone.`
> B → `two ATRs off the 50-day, the same rule buys about 186% of what it buys four ATRs out.`

（A 顺手把 `position` 换回 `square footage`，把段 2 建起来的 rent 链在该兑现的地方闭合——§4.8 第 4 条。若不想用比喻，写 `49.7% of the position it would have bought four ATRs out` 即可，分母问题一样解掉。）

⚠️ 段 2 的 `its base` **不用改**——它在那里指 50 日线是自然的；只要段 3/4 不再用「the base」当 ext=4 的代称，一词两义就消失了。

---

## 🔴-3 · 退回分发站 · V2 —— 三个词，让它真的能独立站住

**原句**（05_distribution.md:62）：
> `Same risk budget, same stop convention as before, two ATRs above the 50-day instead of ten`

**问题**：`as before` 在这条帖子里**没有先行词**——V2 全篇从没提过任何 stop convention。稿子声称它「零 ticker、零日期，常青、能独立存在」，实际是在向旗舰稿借上下文，正是本项（变体≠缩写）要防的那件事。

**改法**：
> `Same risk budget, one stop convention — the 50-day, say — two ATRs above it instead of ten`

**顺带同一条**：第一句 `Before you decide **this** is a rule for cowards` 的 `this` 也悬空。若上面那处改了，`this` 由下一段的内容回指，勉强能读；想彻底干净就写 `Before you decide that sizing by stop distance is a rule for cowards, run it the other way.`

---

## 🟡 不拦路，但建议同一轮改掉（六条，全是一句话）

| # | 位置 | 原文 | 改法 |
|---|---|---|---|
| 🟡-1 | 旗舰段 2 | `you put the stop where the chart lets you, and a bar this far from its base doesn't let you put it close.` | 无出处的图表法则，且仓库自己的 `sp_stop` 给 CRM 21.84% / VEEV 14.64%，都比我们用的 29.34% / 24.97% 近。改成把它当**公开的选择**：`And you don't get to pick it for free — pick one line and hold it, or the number means nothing. Call it the 50-day:` |
| 🟡-2 | V2 | `176 to 193 percent` | 真值 **175.7576–192.5926**，下界向内取整＝把带说窄了（与上一轮 `60 to 67` 同病）。改 **`175 to 193 percent`** |
| 🟡-3 | 旗舰段 4 | `Same arithmetic, opposite sign.` | 186% 与 49.7% 不是相反符号。改 **`Same arithmetic, the other side of one.`** |
| 🟡-4 | 旗舰段 3 | `Neither company did anything to those two numbers. The distance did.` | 反事实分解：5.382pp 缺口里距离 +5.814、波动率 −0.433（≈8%）。改 **`Almost none of that gap is the companies. It's the distance.`** |
| 🟡-5 | V1 | `Those ranges are the entire contribution of volatility, measured across names that move 2 to 8 percent…` | `measured across` 暗示实测，实为函数值域。删一个词：**`…the entire contribution of volatility, across names that move 2 to 8 percent…`** |
| 🟡-6 | 04 §二 出处表 | 「文件独立存储的 `atr_from_sma50` … **逐位吻合（非自证）**」 | `atr_from_sma50` 就是 `sma50_dist/(atr/close)` 的同一实现同一输入（`atr_enrichment.py:52`，docstring:22 明写「one number」）。改成 **「与存储列一致（同一实现，非独立验证）；独立复算见审查站 06 §1.1」** |

## 🟡 选项本身有故障，请连同修法一起递给 Andy

- **选择 4 备选 A**：`How much of it stopped being your call on Thursday morning.` —— 正文口径是**周五**，全篇从未建立 Thursday。若他选这条，同步改成 `on Friday's close`，或在段 2 补一句 CRM 周四那根跳空。
- **选择 2 备选**（`$VEEV printed the same 50% on Thursday…`）—— 稿子自己已标明代价，判断正确，**默认版更好**，我同意不用它。
- **上一轮点名、本轮只备选未改的两句**（V2 `paid to be early / paying to be late`、V4 `That part isn't a convention / That part is division`）：备选都写得对，**但它们已经被点名两轮了**。若 Andy 这次也不表态，建议默认走非对仗版，别让同一句第三次进闸。

---

# 流程项（不影响发布，但下一站要补）

- 🟡 **`RECORD.md` 停在第 1 轮**：`status:` 仍写「退回旗舰站」，flagship 节仍写「~150 词」（实为 **219 词**，我实测），distribution 表仍标 V3 🔴 退回、hook 仍写「独立复现钩」（已作废）。PIPELINE §Campaign Record 要求「一张卡走全程」。**我不写它**（本轮只许写 06），请旗舰站/分发站回填。
- 🟡 **`verdicts.jsonl` 仍是零判决**（`wc -l` = 1，只有 `_header`）。两稿都如实登记了缺件 ✅，做得对。**Andy 对本轮的取舍应成为第一条真记录**——尤其是上面那两句「被点名两轮仍未定」的对仗句，它们正是这本账要防的形状。

---

# Andy 发布前必须知道的 6 条

1. 🔴 **V3 里「我跑了 2,091 只，一只都没落在带外」是一句同义反复，不是证据。** 44–55 是「ATR% 在 2–8 之间」这个条件的代数后果，不可能有反例。留着它，最懂数的那批读者会两分钟看穿——而他们正是我们要的人。删那半句（回退清单 🔴-1），保留 `four out of every five liquid tickers`（81.81%，那个是真实证）。

2. 🔴 **旗舰最重要的那个数「49.7%」，在正文里没有分母。** 基准是「4 个 ATR」，但 `4` 只出现在配图里，正文一次没写；而且 "the base" 在相邻两段一个指 50 日线、一个指 ext=4。加四个词就好（🔴-2）。

3. 🔴 **V2 不能独立发**：`same stop convention as before` 的 "before" 在那条帖子里不存在。它现在只有跟旗舰一起读才通。三个词能修（🔴-3）。

4. ✅ **上一轮的两处拦路真修好了，数据也真推进了。** `my convention` 正文零命中，50 日线现在是被点名的选择；44–55 收进了实测范围（我复算：ATR% 2–8 子集 2,091 只 0 例外，全池 2,556 只 11.15% 落带外）；口径日 08-28 = **Friday** 说对了，`quality.json` status=ok。**周一（08-31）盘前发，口径成立。**

5. ⚠️ **这稿的保质期是周一盘前，而且比想象的短。** VEEV 一根 −1.93% 的 K 就把 ext 从 9.403 打到 8.346、比值从 50.45 推到 55.09 —— **这类读数的半衰期就是一个交易日**。周一收盘后（cron ≈ 09-01 03:1x UTC）旗舰段 1/2/3、V3、V4 全部作废；V1/V2 与配图那 20 格是纯函数，**永远有效**。发前跑 04 §二 的命令 ① 和 05 的命令 ①⑤。

6. ⚠️ **「收藏/赞 > 0.5」这个判据我们从没达到过**——我现场复核 `posts.csv`：全库 **14** 帖，**总收藏 1**（08-24 LONGFORM，1 收藏 / 5 赞 = **0.20**），ARC 中位 180 / 最高 421，REPLY 基线 81。分发站建议的两级判据（一级 = 出现任何收藏，基础率 1/14）**是对的，请采纳**，否则四条会被全判失败。

---

**本轮审查站未 commit、未 push、未发布、未发任何消息，未替任何人执行替换，除本文件 `06_gate_review.md` 外未写仓库任何文件。** 复算全部在 `data/output/universe.json`、`data/output/quality.json`、`data/content/posts.csv` 原始字段与 `git show 03761dc8:` 快照上现场跑出。

---
---

# 第 4 轮审查（终轮）· 2026-08-31 · 独立新上下文子 agent

> **本轮权限被轮数上限缩到二选一**（`PIPELINE.md` 断点续跑节 / `roles/06_gate.md` done-when）：本卡 `rounds: 3`，
> 第 4 轮**只能放行或标 killed，不产生第 5 轮，「退回某站」不是本轮可选输出**。

## 判定

**放行（子集）** —— 进包：**旗舰 · V1 · V4**；下架：**V2 · V3**。**不毙。**
理由：进包三件逐个数字独立复算无一处错；V2/V3 的问题是**打包问题与两句话的问题，不是整卡的问题**。

---

## 0. 入口号登记（Gate 独立复判；先读 `brain/x.md` 自己判，判完才看 RECORD 文末的 OPS 外部审计——结论相同）

| | 入口 | 理由 |
|---|---|---|
| **V1** | **2** 架构/机制 | 主语是规则，完整讲清一个区分（热度 vs 剂量），独立成立。认真考虑过判 **4**（载荷确实是一张三行查询表，x.md 明写「同一张读数表可以既出 4 也出 7」），但入口 4 的形状是**判据帖**（我要看到什么才动），V1 不给行动判据，给的是对一把已有尺子的重读。**为了让撞车消失而改判＝第二次犯「文体不同≠入口不同」那个错。判 2。** |
| **V2** | **2** 架构/机制 | 同一条比值曲线的另一半；靶子是**我们自己的规则**，没挑战任何流行工作流 → 不是 5。 |
| **V3** | **2** 架构/机制 | 同一把尺隔一个交易日的两个读数。**不是 3**（票根＝我们自己的判断/成交，V3 零成交零持仓）；**不是 6**（反馈环＝我们自己的表现数据，V3 报的是市场数据）。 |
| **V4** | **5** 批判常见做法 | 靶子是整个「晒仓位百分比」品类；`Including mine` 使它不是嘲讽对手盘。干净的 5。 |

**⛔ 硬闸触发：三撞入口 2。** 按 `roles/06_gate.md` 本该直接退回分发站，但轮数上限禁止退回 → 改用**席位处置**：入口 2 只留一个，留 **V1**，下架 V2、V3。
下架顺序理由：V2 有实错（§1、§3）；V3 无错，但（a）保质期只到周一盘前，（b）它的四个盘面数（9.73 / 49.7 / 8.35 / 55.1）**旗舰里全有**——对读过旗舰的读者，V3 剩下的新东西只有周四那两个数和 81.81%，是四条里**最接近「缩写而不是重建」**的一条；V1 常青、四轮零拦路、自己交代了前提。
> 若 Andy 更想要 V3 那句 `Run yours.` 的证伪邀请，**V1 ↔ V3 是一行互换**，代价＝失去常青、必须周一盘前发。

**包内入口覆盖：旗舰=1（长推载体成立）· V1=2 · V4=5。三个入口，无重复。**

---

## 1. 第 3 轮两个 🔴 的复核

### 🔴-A（V3）—— ✅ 真修好了
> `take a name that moves 2 to 8 percent on an average day. Ten ATRs out, one stop convention, and the answer lands between 44 and 55 percent … That isn't a survey I ran. It's a division you can do on the back of a receipt, and **inside that band** it can't come out anywhere else.`

前提在同一句出现一次、收口再限定一次（`inside that band`），与下一段「四分之五的票在带内」不再自相矛盾。**这句现在是真的。**

### 🔴-B（V2）—— ⚠️ 只修好了一半，且暴露出紧挨着的第二处同病
基座确实立起来了：
> `Against **a full position at four ATRs — the top of the entry zone** — the arithmetic hands you 175 to 193 percent.` ✅

但**下一段那两句在新基座下变成明确的假话**：
> `The halving point — where the same budget buys half of that four-ATR position — sits between 8.7 and 11.8 ATRs … **Under that number the same risk buys more shares than a full position. Over it, fewer.**`

减半点是 8.7–11.8；`under that number` 包含 ext=6，那里比值是 **70–73%**，**少于**一个 full position，不是多于。正确说法是 more than **half** a full position。该句只在 ext<4 时成立。

> **这不是第 3 轮改坏的。** `more shares than your normal size` 从第 2 轮的备选就带着这个病；**第 3 轮把基座钉死之后它才从「含糊」变成「可判假」**。
> 即：第 3 轮**亲自诊断出的根因**（回退清单驱动的修订只修被点名那句，同族不扫）**在修 🔴-B 的那一次修订里第四次复发，而且同族就在相邻的那一句。**

### 有没有修坏别的 —— 没有
旗舰四处第 3 轮改动（`four ATRs out` / `the other side of one` / `Almost none of that gap is the companies` / 止损句）逐句核过，都成立且无牵连伤。🟡-2/-5/-6/-7 与 §三陈旧告示已执行。词数 221 与自述一致（实测 `wc -w` = 221）。

---

## 2. 独立复算（不核对上一轮清单，从原始字段与 `ratio(m,a)=(4/m)(1+ma)/(1+4a)` 现场重算）

| 稿里写的 | 复算 | |
|---|---|---|
| 旗舰 CRM ext **9.73** | 9.7275 | ✅ |
| 旗舰 CRM 止损 **29.34%** | 29.3395% | ✅ |
| 旗舰 CRM 比值 **49.7%** | 49.7073% | ✅ |
| 旗舰 VEEV ext **8.35** | 8.3406（稿内注 8.346） | ✅ 舍入后同 |
| 旗舰 VEEV 比值 **55.1%** | 55.1196（稿内注 55.09） | ✅ 舍入后同 |
| 旗舰 **about 186%** | ext=2 全带 175.7576–192.5926；ATR%=4 格 186.21 | ✅ `about` 用法正确 |
| 读数表 20 格 | 189/186/183/181 · 100×4 · 70/71/72/73 · 55/57/58/60 · 46/48/50/52 | ✅ **20/20** |
| V1 **60 to 68** | 60.3175–67.5325 | ✅ 外扩安全 |
| V1 **44 to 55** | 44.4444–54.5455 | ✅ 外扩安全 |
| V2 **175 to 193** | 175.7576–192.5926 | ✅ 数对，**缺前提** → §3 |
| V2 **8.7 and 11.8** | m=4/(0.5−2a) → 8.6957–11.7647 | ✅ 数对，**缺前提** → §3 |
| V2 `under that number … more than a full position` | ext=6 → 71%，**少于** | ❌ **不一致** |
| V3 周四 **49.80 / 50.45** | 08-27 快照 49.7979 / 50.4463 | ✅ |
| V3 **2,091 / 2,556 = 81.81%** | 一致 | ✅ |
| V4 **+49.8% / +92.5%** | CRM 0.852095→1.276514 = +49.81%；VEEV 1.001398→1.927937 = +92.52% | ✅ |
| 天真算法 41% | 4/9.7275 = 41.12%，**两稿正文零命中** | ✅ |

⚠️ **口径提醒（新，不改任何已写的数）**：`universe.json` 当前 timestamp 是 **2026-08-30T17:45:49Z**，不是两稿引的 `2026-08-29T03:18:17Z`——周日又跑了一次（`quality.json` 仍 `date=2026-08-28 / ok`）。VEEV 的 ATR% 从 3.9865 微动到 3.9891（ext 8.346→8.3406、比值 55.09→55.1196）。**四舍五入后稿里每个数都没变**，但两稿自述的 timestamp 已不是当前值。

---

## 3. ⭐ 同族扫描（本轮强制：每定一条问题必答「其余资产里还有没有」，哪怕答案是「没有」）

| 形状 | 其余资产里还有没有 |
|---|---|
| **S1 数字没有分母/基座错配** | **有，只有一处，就是 V2 那句。** 旗舰两处（`four ATRs out` ×2）、V1（`4 — call this one full position` + `of it`）、V3（`compared to what it would have bought back at 4 ATRs`）、V4（`Move the stop from the 50-day to the 21-day`，基座在同句）——**全部就地点名基座。V2 是唯一漏网，且它自己上半段点了名、下半段又丢掉。** |
| **S2 可被正确证伪的无条件带** | 🔴 **有，就在 V2，第三次复发。** V2 全篇从未出现 ATR% 2–8 前提，却写死 `175 to 193` 与 `8.7 and 11.8`。实测全池 n=2,556：ext=2 真实带 **153.57–199.00，352 只（13.77%）落带外**；减半点真实带 **8.08–60.03，472 只（18.47%）落带外**。与第 1 轮毙掉 V3 `any name, any volatility` **同形状同量级**（当时 11.15%）。**邻居 V1 与 V3 都写了这个限定，只有 V2 从第 1 轮活到现在。** |
| **S3 恒等式包装成实证** | **没有。** V3 自写 `That isn't a survey I ran. It's a division…` 并把真普查单列；V1 已删 `measured`；旗舰无此形状。三次律的第 3 次被拦住后未回潮。 |
| **S4 散文里向内取整把带说窄** | **没有。**（60→68 外扩、176→175 外扩、44–55 外扩；仅 8.696→8.7 内缩 0.004，可忽略。） |
| **S5 借来的刻度不标出处** | **有三处**：旗舰 `four ATRs out — the top of the entry zone`、V2 同句、V1 `draws its lines at 4, 7 and 10`。三处都**没有**宣称是我们的分档（05 纪律满足）✅，但也都没交代是 Jacobs / Jeff Sun 的刻度。🟡 不拦路。 |
| **S6 对仗格言收口** | 三处（V1 收口、V2 中段、V4 收口）**默认已全走非对仗版，巧话降为备选** ✅；**旗舰收口 `Conviction doesn't change the division.` 仍是默认的巧话**（备选 A/B 已备）。被点名三轮仍未定的唯一一处。 |
| **S7 相邻两段复述** | **有一处残留**：V4 结尾 `Further from your stop, smaller position — every convention, every time.` 与 `Direction is the only part that survives…` 互相复述。🟡 不拦路。 |

---

## 4. 常规清单

**BRAIN《每个 campaign 必须包含》五条**
1. 读者结果 ✅
2. 单一 thesis ✅（不许两个，本卡只有一个）
3. 主张逐条带出处 ✅（04 §二 / 05 出处表逐数字带命令；独立复算全对；散文里零手打数字）
4. 一个可复用物 ⚠️ **半交付**——5×4 读数表存在且 20 格全对，**但它只作为「旗舰配图」存在，而那张图不存在**（Vera 无 routine）。目前只有 V1 的三行是它的文字缩影。
5. 每个变体独立成立 ✅ V1 / V3 / V4；V2 独立成立但含错 → 下架。

- **hook 查重** ✅ 四类（翻译 / 反面先行 / 对照 / 自拆）互不重复；进包三件＝翻译 + 自拆 + 旗舰。
  🟡 门铃：`brain/hooks.md` 类型登记里「对照钩」的定义写的是**已作废的旧 V3**（两个标的同读数不同待遇的并置）。现 V3 是「同一把尺两天两读数」。**周报直接转正会让 store 带着作废定义入库。**
- **AI 腔** ✅ 负面清单全表对正文块零命中（实跑 grep，只命中稿子自己的自查行）。镜像/对仗句状态见 S6。
- **语气漂移** ✅ 零方向、零买卖、零持仓、零预测。`buy` 只出现在旗舰 `You can still buy it`——许可不是指令。
- **CTA** ✅ **零 CTA**（`subscribe / whop / membership / lifetime / link` 全零命中）。**不触发冻结线，不构成毙。**
- **立场红线** ✅ `my convention` 正文零命中；50 日线一律以 `one stop convention — the 50-day, say` 的明示选择出现；唯一引用 Andy 的是已公开的 1R 规则值 0.25%。
- ⚠️ **一处必须 Andy 拍**：V4 的 `Including mine, which is why the stop convention is written into every one of these.` 是一条**面向读者的新方法承诺**。上一轮以 Voice Bible §3「the risk ledger — 'x% trade risk, y% port risk' as the fixed footer of every public trade」豁免；**核对原文后判定：那条 tic 承诺的是每笔公开交易带风险台账页脚，不是每条仓位帖带止损约定——同族，不同句。** 对外承诺是 BRAIN §八 的人批边界，AI 不替他新立。
- 🟡 V3 `2,091 of the 2,556 I can trade`——第一人称把 screener 的 `tradeable` 池说成「我能交易的」。随 V3 下架，不处理。

---

## 5. 缺口与风险

**Mia / Vera 缺件——如实记，按契约不构成退回。** `writing` / `visual` 两节各有「暂缺执行者」占位，正是 PIPELINE〈过渡条款〉与 `roles/06_gate.md` 过渡期例外要求的写法；两条规矩都明写「此时按毛坯审，**不因缺这两节退回**」。**但 Andy 必须知道他看到的是毛坯，不是成稿。**

⚠️ **一个不能糊过去的实质缺口**：旗舰自述载体是「X 长推 + 一张读数表图」，visual 节写「本卡不配图」——**两句直接打架，而那张图正是本卡唯一的可复用物**。现在发＝221 词长推裸发、读者拿不走那张表；等图＝错过唯一发布窗口。**这条由 Andy 定，Gate 不配图不改稿，不替他解。**

**保质期（05 契约要求：复算命令 + 保质期）—— 写全了 ✅**
05 有「每个数字的出处 + 复算命令」（①①′②③④⑤⑥）与置顶第 3 条「08-31 盘后 cron 一跑，V3 的 8.35/9.73 与 V4 的 49.8/92.5 全部作废，发布前必跑命令 ① 和 ⑤」；04 有独立的「口径日与失效条件」表。
- 旗舰段 1/2/3 与 V4：**只在 2026-08-31（周一）ET 盘前有效**，周一收盘后 cron（≈09-01 03:1x UTC）即作废。
- V1 与那 20 格读数表：**纯函数，永远有效**。
- 🟡 04 §二 的复算命令块开头写死 `cd /var/folders/ck/…/wt-campaign`——一棵已蒸发的临时树，**照抄跑不动**；05 写的「命令均在仓库根目录跑」才是对的。

**流程缺口**：RECORD review 节把第 3 轮判定链到本文件，但**本文件此前只有第 2 轮**（第 3 轮判定从未落盘，只活在 RECORD 摘要里）。第 4 轮判定即本节，已落盘。

---

## 6. 给 Andy 的审批队列行

已按 `APPROVAL_QUEUE.md` 格式追进「待批」节，含终稿路径 / 平台 / 入口 / 毛坯告示 / 发布窗口 / **需他定的 2 件事**。

## 7. 留给 performance 与下一卡的教训

1. **第 3 轮自己诊断出的根因，在修第 3 轮 🔴 的那一次修订里第四次复发**——修 V2 的 `175 to 193` 时钉死了基座，紧挨着的下一句用同一个基座却算反了；同族的第二种病（缺 ATR% 2–8 前提）在同一个变体里从第 1 轮活到现在。**「同族扫描」不能只是 Gate 判定里的一节，必须是修订方交稿前的一步**：改完被点名那句，回答「这一段里还有几句共用同一个基座 / 同一个前提」。
2. **变体之间的相互抄写没发生**：V1 和 V3 都写了 ATR% 2–8 的限定，V2 一直没有。同一份文件里已有正确写法而另一条没跟上——最便宜的抓法是**跨变体同关键词对齐**（`grep '2 to 8'` 数几条有几条没有），比逐句审快得多。
3. **入口号必须在分发站产出时就写死，不能等 Gate 补标**：四条稿的文体 / hook 四项全不重复，撞车在旧校验下完全隐形，而三撞一意味着一整卡的力气只覆盖了 2 个入口。角度站 §六 那张 5×4 读数表（**入口 4**）和 §七 那条 `atr_enrichment.py:48` 的自有口径 bug 收据（**入口 6**）一直躺着没人捡——**这卡缺的从来不是弹药。**
4. **`brain/hooks.md` 的「对照钩」定义写的是已作废的旧 V3**，Steve 周报回填前必须更正，否则 store 会带着作废定义转正。

---

**本轮审查站未 commit、未 push、未发布、未发任何消息、未用 ListAgents、未跑管线、未改数据文件，未写仓库任何文件**（本节由工头落盘）。复算全部在 `data/output/universe.json` / `quality.json` 原始字段与纯函数 `ratio(m,a)=(4/m)(1+ma)/(1+4a)` 上现场跑出。
