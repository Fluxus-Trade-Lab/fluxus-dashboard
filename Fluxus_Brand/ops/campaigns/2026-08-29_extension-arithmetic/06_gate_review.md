## 判定：**退回旗舰站**（V3 同时退回分发站）· 不毙

角度、算术、出处体系都是干净的——**四条变体里三条可以直接进 Studio Q**。但旗舰稿有一句把一个我们自己编的止损约定写成了 Andy 的既定规则，V3 向公众发出了一个**在真实股票池里约十分之一会被证伪**的可证伪声明。两处都是一句话能修好，但都不能带着发。

---

## 1. 无出处主张 —— **通过（两处越界除外）**

我用 Bash 从 `data/output/universe.json` 原始字段独立复算，**没读稿子的自述表**：

| | ATR% | ext 复算 | 文件存储 `atr_from_sma50` | 止损% | 仓位@R.25 | 稿子写的 |
|---|---|---|---|---|---|---|
| CRM | 4.2254 | **9.6822** | 9.6822 ✅ | 29.0334 | 0.8611 | 9.68 / 29.03% ✅ |
| VEEV | 3.9877 | **9.4053** | 9.4053 ✅ | 27.2756 | 0.9166 | 9.41 ✅ |

比值：CRM **49.80%**、VEEV **50.44%** → 稿写 49.8 / 50.4 ✅。21EMA 替换：**+42.93% / +71.36%** → V4 写 43 / 71 ✅。减半点 **8.7–11.76** → V2 写 8.7–11.8 ✅。ext=2 带宽 **175.8–192.6** → V2 写 176–193 ✅。读数表 20 格逐格复算 ✅。天真算法 41.31% 全篇不存在 ✅。`grep -nE '\$[0-9]|million|万美元'` 全文 **空** ✅（cashtag 不触发）。Andy 三句原话在 `PUBLISHED_X_2026-08-24_en.md:104,111-113,115` 逐字核对 ✅，副标「0.25% for 23R」在 `:19` ✅。

**两处不通过：**

- 🔴 **V3「44 to 55」是在 ATR% 2–8 上算的，但正文写的是「any name, any volatility」。** 实测：ATR%=1 → **42.31%**，ATR%=12 → **59.46%**，都在带外。放到真实股票池：5,555 只里 **1,790 只（32.2%）** 的 ATR% 落在 2–8 之外；只算 `tradeable=true` 的 2,561 只，仍有 **16.6%** 在外。全池 ext=10 的真实带是 **40.6–68.0**，44–55 只覆盖 **90.5%**。
  > 最难看的是失败模式：真实下界 40.6% 紧贴我们全程警告的「天真算法 41.3%」。读者拿 KO 那类低波票算出 41%，我们会回他「你用错公式了」——而他是对的。
- 🟡 **V1「ext=7 → 60 to 67」的上界实为 67.53**（ATR%=8）。散文里手工把 max 向内取整＝把带宽说窄了，正是角度稿自己禁的那条「散文不许手打数字」。

「没有人写这个角度」的依据 = `2026-08-28_today_x_options.md:21-30`，**n=5、单日、`grep -rln "firesidealpha"` 只命中 brief 自身＝无留存原始数据**。四条成稿正文里都没有搬这个断言，✅ 边界守住了。

---

## 2. 重复 hook —— **通过**

不是同一句式换词，四条第一拍的**动作**都不同：

| | 第一拍 | 落点 |
|---|---|---|
| 旗舰 | 替读者说出人群会说什么，然后要求他把它换成可下单的数 | 订单框 |
| V1 | 拿起读者已有的那把尺，说他只读了一半 | 尺的背面 |
| V2 | 先替读者说出最狠的反驳（「懦夫规则」） | 反向那一半 |
| V3 | 两个不相干输入撞出同一个数 | 可证伪带 |
| V4 | 先拆自家可信度 | 整个品类 |

`Fluxus_Swipe_File.md` 里 #6 Ariel(:199)、#18 TSF(:文体 I「先自己说反面」)、#37 Muninn(:869) 三个骨架引用**真实存在且对得上**。V2 的骨架描述与 #18 的实录（「主动先说反面 → 条件句」）一致。

---

## 3. 变体是否只是缩写 —— **通过（V3 有条件）**

- **V1 独立成立** ✅ 论证对象换成 4/7/10 分档尺，零 ticker、零日期，是真常青弹药。
- **V2 独立成立** ✅ 回答的是相反的问题（这会不会让我变胆小鬼），情绪极性是进攻。
- **V3 半独立** ⚠️ 去掉旗舰它仍读得通，但它和旗舰共用 CRM/VEEV + 49.8/50.4，是四条里最接近「旗舰的另一种切法」的。
- **V4 独立成立且最强** ✅ 靶子是整个「晒仓位百分比」的品类，没见过 CRM 也中枪。

---

## 4. AI 腔 —— **不是零条，六条**（按风险排序）

1. 🔴 **V2**：*"Below that you're being paid to be early. Above it you're paying to be late."* —— 教科书级对仗格言（paid/paying × early/late 双轴对称）。记忆里那条「他删了我评分第一的收口句；要一读就懂的重话，不要要回味的巧话」，形状完全一致。**最可能被 Andy 划掉的一句。**
2. 🟡 **V4 收口**：*"That part isn't a convention. / That part is division."* —— 排比 + 对仗双段收口。
3. 🟡 **V1 收口**：*"The trim line isn't where the stock turns dangerous. It's where the division already had you at two thirds."* —— 「不是 A，是 B」镜像句。
4. 🟡 **旗舰**：*"This was never a rule about being careful."* —— 「X was never Y」正是 Andy 08-24 亲手删掉的 *"The news is never in the chart"* 的同一形状（文件头注明「别再产同一个形状」）。
5. 🟢 **旗舰收口**：*"Conviction doesn't change the division."* —— 抽象名词 × 抽象名词 + 头韵，属于「要回味的巧话」家族。稿子已备了替代版，让 Andy 选。
6. 🟢 **V2**：*"Nobody ever feels the first half. Nobody runs the number when they're early."* —— anaphora，轻度。

**豁免不算 AI 腔的一处**：旗舰 *"Your stop isn't a line on a chart. It's rent."* —— 这与 `PUBLISHED_X:111` 的 *"Position size is not risk. Stop distance is risk."* 是**同一个已公开的句法**，是他的声音不是机器的。

标准 AI 连接词全清：`moreover / furthermore / delve / crucial / it's worth noting / ultimately / not only` **零命中**。

---

## 5. 语气漂移 —— **一处**

Voice Bible §1：**Calm Monk / 天气预报员 —— 报概率、不下命令、对预报无自我**。四条全部零方向、零买卖、零「我预测对了」——变体 B 的收据开场没有任何一条偷偷复活 ✅。V3 的 *"one of us did the arithmetic wrong, and I'd want to know which"* 和 V4 的 *"Including mine"* 是这一轮最好的两句，完全是天气预报员。

🟡 **唯一漂移 —— V2 最后两段**：*"They run it after they've already missed it… conclude the rule is timid. / The rule isn't timid. **You only ever ask it after the move.**"* 主语从「他们」滑到「你」，最后一句是**对读者习惯的断言，我们零数据支撑**，读起来是教训不是测量。改法：把 "You only ever ask it" 换成 "It only ever gets asked after the move."——同样的意思，把手指从读者身上移开。

---

## 6. 诚实边界 —— 🔴 **不通过，这是退回的主因**

**(a) 口径日：基本通过。** 旗舰两次写 "At Thursday's close"、V3 结尾 "(Thursday's close.)"，`date(2026,8,27).strftime('%A')` = Thursday ✅，没有一处说成「今天」。V1/V2 无日期无 ticker，免疫。
🟡 两个小口：① 旗舰 "You've had that chart open **since Thursday**" 若周一发，中间隔了一整个 08-28 交易日，这句读起来像没发生过周五；② V4 "Same day" 未指明哪天。

**(b) 50 日线止损 —— 这里翻车了。**

> 🔴 旗舰第二段：*"Put the stop at that average — **my convention**, use your own and every number here moves"*

「my convention」＝**宣称把止损放 50 日线是 Andy 自己的惯例**。他公开记录里不是：`PUBLISHED_X:115` 写的是 *"The stop sits **0.73 ATR** from entry — close because the structure is tight."* CRM 那个 50 日线止损是 **29.03%，是他那笔的 6.7 倍宽**。更糟的是它和他同一段里的原话直接打架——*"a sloppy chart with **nowhere to put a stop** gets a tiny position automatically"*：按他自己的话，一个要放 29% 止损的图，就是「nowhere to put a stop」。

稿子把一个**我们自己引进的假设**，用第一人称写成了**他的既定方法承诺**。这条撞的是本轮铁律「不代写 Andy 的观点、立场、承诺」，也正是研究包 反面事实 §1 标红的那一条——它被披露了敏感性（"every number here moves"），但**归属搞反了**：应该说这是一个假设，结果说成了他的习惯。

> 🔴 **附带的更深一层（不是拦路，但框架必须调）**：把止损定在 50 日线之后，「延伸度」和「止损距离」变成**同一个量**——ext = 距50线 ÷ ATR%，而止损距离就是距50线。于是「越延伸→仓位越小」是一个**恒等式**，不是一次市场测量。CRM 与 VEEV 的 49.8/50.4「撞在一起」也不是发现：它们 ext 本来就几乎相等（9.68 vs 9.41）。
> V3 恰好把这层包装成了实证发现——*"Two charts with nothing to do with each other… different sector, different price, different volatility"* 列了四个**不相干**的差异，却没说唯一相干的那个变量**几乎相同**。（它下一句 "the answer stops depending on the stock" 部分救回来了，但顺序是先制造惊讶再解释。）
> **V4 是四条里唯一把这件事说明白的**（*"any position size quoted without its stop is decoration. Including mine" / "What survives the swap is the direction"*）——而分发站把它排到了**下周**，排在四条依赖该假设的稿子后面。这个顺序应该倒过来。

---

# 回退清单（改完可直接过闸，不必重开轮）

### 🔴 退回旗舰站 —— 一句话

**原句**：`Put the stop at that average — my convention, use your own and every number here moves —`
**问题**：把我们引入的假设写成 Andy 的既定止损规则，与 `PUBLISHED_X:115` 的 0.73 ATR 结构止损直接冲突。
**改法（二选一，都不需要改动其他任何一句）**：
- A（保守）：`Put the stop at that average — one convention, not the only one; use yours and every number here moves —`
- B（更强，把假设变成他的真规则）：`Put the stop where the chart lets you. On a bar this far from the base, the chart doesn't let you put it close — call it the 50-day and the rent is 29.03% of the price.` ← 这一版把 extension → size 接到他自己公开的因果上（结构不给你近止损 → 止损远 → 仓位小），恒等式问题也一并解决。

同时建议顺手处理：`This was never a rule about being careful.`（08-24 被亲手删掉的同形句），以及 prose 里那个单独的 `186%`（ext=2 全带 175.8–192.6，写「about 186%」或「180 to 190%」）。

### 🔴 退回分发站 —— V3 一句话

**原句**：`same stop convention, any name, any volatility, ten ATRs out. If you get a number outside 44 to 55, one of us did the arithmetic wrong`
**问题**：真实股票池 16.6% 的可交易票（全池 32.2%）落在带外；带的真实范围是 40.6–68.0。这是一个公开发出去、会被读者正确证伪的声明。
**改法（二选一）**：
- A：把邀请收进已测范围 —— `any name that moves between 2 and 8 percent on an average day, ten ATRs out. Outside 44 to 55 and one of us did the arithmetic wrong.`
- B：换成实测全池带 —— `any name in a liquid universe, ten ATRs out: 41 to 68. If you land outside that, one of us did the arithmetic wrong.`（复算命令：`ratio(a,10)` 扫 `tradeable=true` 的 2,561 只）

顺带 V1 的 `60 to 67` → **`60 to 68`**（真值 60.32–67.53）。

### 🟡 不拦路，但建议在同一轮改掉
- V2 结尾 `You only ever ask it after the move.` → `It only ever gets asked after the move.`（去教训感）
- V2 `Below that you're being paid to be early. Above it you're paying to be late.` —— 备一个非对仗版给 Andy 选，这句大概率被划。
- 发布顺序建议倒过来：**V4 或含改法 B 的旗舰先行**，让「止损约定决定一切」这句话先落地，后面三条才站得住。

### 若改完，Andy 发布前必须知道的 3 条
1. **数据陈旧两场**（08-27 收盘 + 08-28 全天缺）。周一发之前跑 `python3` 复算 ①，比对 CRM 那行；跌出 ≥7 就换票不换角度。
2. **50 日线止损是我们的假设，不是你的规则**——你公开的是 0.73 ATR 结构止损。定稿用哪个措辞由你拍，但正文不能出现「my convention」指 50 日线。
3. **「收藏/赞 >0.5」这个判据我们从没达到过**：全库 14 帖总收藏 **1**，历史最佳收藏赞比 **0.20**。分发站建议的两级判据（一级＝出现任何收藏，基础率 1/14）是对的，采纳它，否则每条都会被判失败。

**本轮我未写任何仓库文件、未 commit、未 push、未发任何消息。** 复算用的临时草稿在 `/private/tmp/claude-501/-Users-taolezhu-Documents-AI-Trading-System/9343d385-11b6-46a9-926d-90a89d572241/scratchpad/drafts.txt`。