# @Clement_Ang17 历史帖库 —— 四人帖库项目的收尾

*采集 2026-08-10,按 `data/research/README_x_account_scrape.md`,**用修好的 handle 作用域抓取器**(前三个账号的数据未做此清洗)。3 个宽窗,18 条。*
*机器可读:`data/research/clement_top100.json` · 索引:`data/research/clement_index.csv`*

---

## 一、四人全期中位数

| | 粉丝 | 赞/曝光 | 收藏/曝光 | **收藏/赞** |
|---|---|---|---|---|
| @ZaStocks | 87K | **0.92%** | 0.13% | 0.15 |
| @ohiain | 44.5K | 0.57% | 0.19% | 0.33 |
| **@Clement_Ang17** | 小号 | 0.57% | **0.23%** | **0.36** ⬅️ **最高** |
| @thesetupfactory | 5,075 | 0.34% | 0.00% | 0.11 |

**Clement 的中位收藏比是四人最高的。** 而且他有 **4 条 >1.2**(Za 只有 1 条 >0.9,TSF 只有 1 条)。

---

## 二、⭐ 他 1.59 那条:把自己的交易记录喂给 AI,然后公开结果

**2025-12-06 · 99,870 views · 418 ♥ · 665 收藏(1.59)**

> *"**06 Dec 2025: Analyze Your Winners.**
> December should absolutely be the time to analyze your biggest winners, here's mine **(from Grok)**:
> *Technical Characteristics of Your Top 50 Biggest Long Winners (From Provided File)*
> *I analyzed all 50 winning trades in the attached file (all longs, including both common stocks and leveraged ETFs like TSLL, TQQQ, SOXL—your biggest wins heavily feature these for amplified momentum). This gives a comprehensive view (**~$2.8M total profit across the 50**). The patterns are even stronger with the full set…"*

**骨架:**
1. **日期 + 标题当开头**(`06 Dec 2025: Analyze Your Winners`)—— 他的每日复盘固定格式
2. **一句为什么是现在**(12 月该复盘了)
3. **把自己的真实交易文件喂给 AI**,标明 `(from Grok)`
4. **公开 AI 找出的模式** + **真实金额($2.8M)**

> ### 🔑 **这是「展示过程」的极致形态,而且它正好是用户要的那四件事**
> *「我怎么计算风险、我怎么提前用小止损入场、我的 Scanner 怎么发现、我一整套思维的训练和框架」*
>
> **而用户比 Clement 更有资格做这件事:**
> Clement 用 Grok 临时跑了一次 50 笔交易;**用户有完整 trade log + `performance_review.py` 引擎 + 一份已经做完的行为诊断**(BABA 五次 −$54k / 仓位做成目标两倍 / 回撤时反而降风险)。
> **Clement 665 收藏拿到的东西,我们手上是常备产能。**

---

## 三、⚠️ 但他最高的那条(1.81)内容不是他的

**2026-01-30 · 600 收藏 · 正文只有三个字:`This is gold!`** —— 转发别人的内容。

> **收藏给的是被转的东西,不是他。**
> 这和 ParadisLabs 策展帖的战略警告同源(见 Swipe File 文体 H):**策展和转发能拿到收藏,但那个收藏不属于你。**
> **排收藏比的时候必须先看正文是不是自己的** —— 这条要写进方法。

---

## 四、他的最高赞帖,收藏比是全库最低

**2026-07-07 · 436 ♥(他的最高赞)· 16 收藏 · 比值 0.04**

**和 Za 完全同一个规律:赞最高的那条,收藏最低。**
四个账号全部复现这一点 —— **赞和收藏不是同一个东西,而且常常反向。**

---

## 五、每日复盘格式(用户点名的原因)

他的复盘用固定头:**`DD Mon YYYY: [标题]`**
- `06 Dec 2025: Analyze Your Winners`(665 收藏)
- `06 Aug 2026: Stally Wally`(被引用在「洗个澡,再敷个面膜」那条里)

**这个头做了两件事:** ①给帖子一个**档案编号**,让它可被回溯引用(他自己就常 QT 旧复盘)②把「今天的复盘」变成一个**连载**,而不是一次性内容。

⚠️ **但数据上:他的日常复盘并不特别高。** 18 条里 4 条 >1.2 的收藏比,**没有一条是普通的日复盘** —— 高的都是「年度分析」「转发的 gold」这类特殊件。
→ **日复盘的价值在连载和档案,不在单条数据。** 别指望它爆。

---

## 六、四人帖库项目 —— 一句话收口

| 账号 | 中位收藏/赞 | 最高那条是什么 |
|---|---|---|
| Za 87K | 0.15 | 年度前瞻长文 + 自评 B+ + 认错(0.94) |
| ohiain 44.5K | 0.33 | A–Z 体系文章(编号目录)(2.17) |
| **Clement 小号** | **0.36** | ~~转发别人的~~ → **真正属于他的是「把 50 笔交易喂给 AI」(1.59)** |
| TSF 5,075 | 0.11 | 周度分析的 14 行议程(纯目录)(2.13) |

> **四个账号、四种风格、粉丝差 17 倍 —— 收藏比最高的那条,全部是「目录 / 长文 / 把自己的记录摊开」。**
> **没有一条是盘面观点、图表点位、或情绪金句。**

---

## 七、诚实边界

- **只有这个账号用了修好的抓取器**;前三个未清洗,污染率实测约 17%
- 18 条样本,是四人里最薄的
- 3 个宽窗(不是季度),所以**看不出季度轨迹** —— 只能看全期
- 正文只补了 2 条
