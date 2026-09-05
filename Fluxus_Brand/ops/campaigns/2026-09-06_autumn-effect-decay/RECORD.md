# CAMPAIGN: autumn-effect-decay · 2026-09-06

status: **flagship**
rounds: 2

> 云端夜间产线，2026-09-06 05:36 JST 开工（上一张卡 `2026-09-03_noise-with-structure` 已过闸 queued，非断点，本卡为新开）。
> 六站顺序亲自跑（Workflow/Agent 工具本轮未获用户显式 ultracode 授权，不触发多 agent 编排；Gate 用独立新上下文子 agent 跑，见 `## review`）。

---

## signal

**选中：黄金「金九」效应——1980–2010 样本内显著为正（+2.52% vs Baur 2013 原文 +2.2%，仪器校准通过），2011–2026 样本外翻负（−1.35%，15 个九月只有 4 个涨）。四条预注册假设全 NULL。**

- **发生了什么**：Nighty Zac 09-05 完成了一份预注册研究，验证中文老话「金九银十」对应的英文文献 Baur (2013)《The autumn effect of gold》。用 LBMA 官方定盘价（1968 年起）复现他的样本内结果，再独立跑他发表之后的 15 年做样本外检验。出处 [`data/research/gold_autumn_2026-09/results.md`](../../../data/research/gold_autumn_2026-09/results.md) · commit `d1443bc6` · §七契约结案行 commit `7e924be4`。
- **受众为何在意**：这不是一个孤立的黄金冷知识——它给读者一个可复用的怀疑动作：**任何被重复引用的季节性说法，先问它有没有名字（论文/权威源），再问它发表之后还灵不灵。** 读者手里握着的很多"常识"（金九银十只是最好查的一个）都还没被这样测过。
- **票根**：`data/research/gold_autumn_2026-09/`（预注册 `00_prereg.md` + 可复跑 `run.py` + 原始输出 `run_output.txt`）+ 本线 08-31 的编辑决策（Andy 因"没有可验证的东西"从周信 #001 删掉这句话，§七 commit `7e924be4` 逐字记录他的原话）——**判断→兑现链**，先删后验，链条可查。
- **衰减速度**：机制本身**慢/常青**（"发表即失效"的判据不随盘面变）。**唯一的时效物**：稿子里"我们现在正处在九月"这句话，保质期＝本月剩余天数；过了 9 月这句开场仍可用但失去"现在"的紧迫感，需改措辞。
- **成品能回答的问题**："我看到一句反复被引用的市场老话，我怎么知道该不该信？"

### ⚠️ 本卡未做红海扫描
`brain/signals.md` 好信号四问③要求，没做就明写不假装过闸。上次记录在册的红海扫描是 08-28（`brain/signals.md`〈红海记录〉表），本卡未做新扫描——时间预算优先给了查证复核与四站产出。①②④三问过：①现在（老话正当季，09-05 刚关账的研究）✅ ②票根（预注册+可复跑脚本+§七契约行）✅ ④衰减诚实（已分清常青机制与"现在"措辞的保质期）✅。

### 弃选清单（弃 5 · 取 1，另留箱 1）

| # | 候选 | 出处 | 弃选/留箱理由 |
|---|---|---|---|
| 1 | OPS Fable「测量仪器自己没通过阳性对照」（Skill OS v2 触发率评测桩名冲突） | 素材箱 09-05 · `docs/superpowers/verdicts.md` | **同族撞车**——与刚过闸未发布的 `2026-09-03_noise-with-structure`（"仪器有时在测错对象"）是同一个母题（自证失灵的测量仪器）。该卡还在 Andy 队列里等签字，连着两张同族卡会让读者觉得我们只会讲这一个故事。留箱，等隔一族再取 |
| 2 | Nighty Zac「有人跑测试是 bool，跑到了哪些测试是集合」（CI 覆盖率缺口 614/1988） | 素材箱 09-05 · `incidents/2026-09-05_the_green_run_did_not_run_them.md` | 同上一族的近亲（"绿灯说谎"）。⭐ 质量很好，**留箱，建议下一卡换族后取用** |
| 3 | 「一份完美自洽的坏数据」（事件归档两天自相矛盾） | 素材箱 09-06 · `incidents/2026-09-06_two_days_the_archive_contradicts_itself.md` | **与队列中卡同族程度最高**——两者的核心判据几乎是同一句话（"内部一致不代表正确"/"自相矛盾要能被看见，前提是有两份读数放在一起"）。若这张先发，等 `noise-with-structure` 也发出去，读者会读到两条几乎同构的稿子。弃 |
| 4 | 「中位数骗人」（筛子重叠度中位 0.812 但逐日只有 24% 真重叠） | 素材箱 09-06 · `data/research/screener_overlap_2026-09/results.md` | **统计方法课第三条**——08-31「阴性没有分辨率」、09-01「先算最小可能 p」已连出两轮，09-03 卡的弃选清单已经点名"第三条会让读者觉得我们只会讲统计课"。弃 |
| 5 | Joe「两个同名文件只一个生效」（用户级/项目级 settings.json 撞名） | 素材箱 09-05 · `DATA_CONTRACTS.md` §七 [2026-09-05] 行 | 好故事但与本卡不同族，弃的唯一理由是**本卡质量更高更完整**（预注册+外部权威文献+判断兑现链三者齐全，这条只有事故复盘）。留给后续 BUILD 帖矿脉，不占留箱名额（可随时从 INBOX 再取） |

**取用理由一句**：五条候选里，金九银十这条同时有 ①一个外部权威源（不是自造口径）②一条判断→兑现链（Andy 08-31 的编辑决策，现在有数字撑腰）③清晰的读者可复用动作（三步验证法）④与本月日历天然贴合的"现在"——四条都占的只有它。

---

## research

**证据包（3–7 条已核实主张，逐条带出处；数字全部现场读 `git show origin/main:data/research/gold_autumn_2026-09/results.md`，未手打）：**

| # | 主张 | 出处 | 状态 |
|---|---|---|---|
| 1 | 老话对应的英文文献是 Baur, D. G. (2013), *The autumn effect of gold*, Research in International Business and Finance 27(1)（SSRN 1989593）；该文只点名**九月和十一月**，「十月」（银十那半）在标准文献里没有对应结果 | `results.md` §四 | ✅ 权威源为外部学术论文，非自造口径 |
| 2 | 样本内复现（1980–2010，Baur 窗口）：黄金九月对数月均收益 **+2.52%**（t=+2.83，p=0.0042，Bonferroni α=0.0125 下显著），Baur 原文报 **+2.2%**；黄金十一月 **+1.89%**（t=+2.57，p=0.0077，显著），Baur 原文报 **+1.8%** | `results.md` §一表格 | ✅ 同符号同量级，仪器校准通过（算术均值口径下我方为 +2.68%/+2.00%，与 Baur 更接近，因均值口径不同，散文需注明） |
| 3 | 样本外检验（2011–2026-08，四条预注册假设，只跑一次）：H1 黄金九月>0 → 均值 **−1.35%**，15 个九月只有 **4 个上涨**，不成立；H2 黄金十一月>0 → −0.94%，不成立；H3a 黄金十月>0 → +0.95%，不成立；H3b 白银十月>0 → +1.96%，不成立。**四条全部 NULL** | `results.md` §二 | ✅ 预注册在先（`00_prereg.md`），只跑一次 |
| 4 | 诚实边界：九月均值翻负不等于"显著为负"——那是看了数据后才想到的方向，事后按同一套规矩算 `P(X≤4\|n=15,p=0.5)=0.0592`（双尾 0.1185），连未校正的 0.05 都过不去。检验本身有分辨率（该样本量下最小可能 p=3.05e-05，远小于校正后 0.0125），所以"没证出下跌"是数据的性质不是检验太钝 | `results.md` §二 | ✅ 坑账 `pitfall_positive_control_borrowed_from_elsewhere` 已登记 |
| 5 | 数据源为 LBMA 官方黄金/白银定盘价（黄金 1968-04 起 701 个月、白银 1968-01 起 704 个月，非连续月缺口 0 个），非 yfinance 的 GLD（2004 年起）——工具边界不等于世界边界 | `results.md` §四 | ✅ |
| 6 | 判断→兑现链：Andy 08-31 因「有可以验证的吗？没有我们就暂时删除」把这句老话从周信 #001 删掉；09-05 验证完成，结论支持删除 | `data/reference/DATA_CONTRACTS.md` §七 [2026-09-05] Nighty Zac→全线 行 · commit `7e924be4` | ✅ 编辑决策原话逐字可查 |
| 7 | 自造实现的校准：本机无 scipy，t 分布 CDF 自己实现，对 6 个公开临界值验证（如 df=30, t=2.0423 → 计算值 0.024999，查表值 0.025），最大误差 5e-06 | `results.md` §四 | ✅ 自造工具已校准，未违反「先找口径别自己造」 |

**未证实/单列**：样本外最强月份挪到冬季/夏末（一月 +3.86%/+4.45%）与 2024 年 extended reproduction 论文的 "reversed and replaced by winter effect" 一致——**这是旁证不是结论**（未预注册，results.md 原文明确说"不建议任何人拿它下单"）。本卡分发站**不得**把这句话升级成新主张。

**未证实项之二**：Baur 原文与我方复现在均值口径（对数 vs 算术）上不完全一致——不影响"同符号同量级"的判断，但正文若要引用具体百分比需注明口径，不能把两种口径的数字混着摆在一句话里当"完全一致"。

**done-when 自检**：research 节每条主张点得开出处 ✅；未证实项单列非空 ✅。

---

## angle

- **读者**：想学"怎么判断"而非"抄答案"的交易者（BRAIN §二）——具体到"手里握着一句反复听到的市场老话，不知道该不该信"的那个人。
- **读者结果**：读完他多了一个**三步验证法**，可以套在任何季节性/规律性说法上，不必等我们帮他验。
- **中心张力**：这句老话**曾经是真的**（有数字撑着），**现在不是**（也有数字撑着）——它没有被证明是假的，它是被写成论文之后自己失效的。张力在"曾经对"和"现在错"之间，不在"对/错"二元。
- **thesis**（唯一）：一个被写成论文、被反复引用的市场规律，会在被知道之后失效——不是因为世界变了，是因为**知道的人多了**。
- **旗舰格式**：X 长推（无 Article，200 词内，跟随 `08-29_extension-arithmetic` 先例）+ 一张样本内/样本外对照小表当配图占位（Vera 无 routine，本卡按毛坯审，见下）。
- **读者带走的可复用物（工作流）**：三步验证法——① 有没有一篇点名的论文/权威源，还是只是口口相传？② 你能不能自己复现它发表时的数字？复现不出来，你也别信自己的样本外读数。③ 拿论文发表之后的数据单独测一遍——符号翻了，说明这个edge已经被别人先交易掉了。
- **分发入口清单**（五分类→七入口，`brain/x.md` 映射表）：
  | 角度五分类 | 内容 | → 入口号 |
  |---|---|---|
  | 结果 | 完整研究：样本内复现→样本外翻负，四条假设全 NULL | **1 旗舰论点** |
  | 机制 | "edge 一旦被写下来就开始失效"——发表即失效的机制，主语是规则不是人 | **2 架构机制** |
  | 证据 | Andy 08-31 编辑决策 + 09-05 验证结果的判断→兑现链 | **3 票根借势** |
  | 工作流 | 三步验证法清单 | **4 可复用物** |
  | 风险 | 批判"从没被允许证伪过的规律=从没被测过，只是被相信" | **5 批判做法**（复用"能不能变红"机制，跨 campaign 复用不算重复） |
- **一个推荐 + 被放弃方向为何更弱**：推荐上表五个入口全部产出（覆盖率 5/7，不含 6 反馈环与 7 压缩图——本卡无表现回写数据、且无 Vera 配图，两个入口本卡不可用，覆盖率按 5 算）。被放弃的方向：**把"一月效应挪到冬天"写成第六条**——results.md 原文明确说这是未预注册的旁证、不建议下单，写成正文主张会违反"重要主张逐条带出处"这条 Gate 硬指标，比五入口更弱。

**done-when 自检**：angle 节字段全非空 ✅；放弃方向 1 条带理由 ✅。

---

## flagship

→ 毛坯正文见下（直接写在本节，未开独立文件——本卡时间预算优先给多变体覆盖）。**每个数字可溯源，见 research 节出处表；亲缘句闸自检见下。**

### 正文（成品英文，无填空位）

> "Golden September, silver October." Every gold trader has heard some version of that line.
>
> Turns out half of it has a real paper behind it. Baur, 2013 — thirty years of LBMA fixing prices, and September and November were the only two months that came back positive and statistically significant. We ran his numbers first: +2.52% for September, against his published +2.2%. Same sign, same order of magnitude. The ruler's calibrated.
>
> Then we ran the fifteen years since the paper came out. September since 2011: -1.35%. Four up years out of fifteen.
>
> We're not going to tell you it's bearish now — that's a claim we didn't pre-register, and picking a sign after you've already seen the data doesn't count as proof. What the test can say: the rise is dead. Nobody proved the fall.
>
> An edge has a shelf life the moment someone writes it down. This one's was fifteen years.

**词数**：152（`python3 -c "print(len(text.split()))"` 现场计数，见 commit 附带脚本片段，非手数）。

### 配图占位（毛坯规格，等 Vera）
样本内/样本外对照小表：
| | 1980–2010（样本内） | 2011–2026（样本外） |
|---|---|---|
| 黄金九月均值 | +2.52%（p=0.0042 ✅） | −1.35%（p=0.82，不显著） |
| 上涨月份数 | 22/31 | 4/15 |
**本卡无视觉资产**（Visual Vera 无夜跑 routine，见下 `## visual`）——此表先以文字形态占位，等 Vera 有 routine 或 Andy 指派人工配图。

### 亲缘句闸自检（`brain/angles.md` 三步）
1. **内核一句话**："一个市场老话曾经真过，被写成论文之后就不灵了。"
2. 对照 `data/content/posts.csv` 近 14 天（08-23 至今）逐条比对 note 列：无同内核帖——近期帖主题为 MRNA/HOOD/PLTR 形态、QT 引文、ATR 仓位算术、月度对账，均不涉及"效应发表后失效"这一内核。**通过**。
3. `Fluxus_Brand/voice/Fluxus_Own_Lines.md` `亲缘:` 标注（全库仅 1 条，围棋复盘对）：与本稿内核无关。**通过（诚实边界：第 3 步现仍近乎空转，见 angles.md 原文说明）**。

### verdicts.jsonl 负面清单自查（09-04 "太ai slop了" 判例为主要参照）
- ❌ 未使用镜像句"不是A是B"（09-04 判例未点名此形状，但 08-24 判例已否，仍全篇自查零命中）
- ❌ 未使用对仗格言收口（"An edge has a shelf life..."是陈述句不是对仗）
- ✅ 有轻微反讽（"The ruler's calibrated."）满足 Voice Bible §4.8 第 2 条"至少一样修辞"
- ⚠️ **本稿比喻较弱**（§4.8 第 3 条"比喻优先于数据"未充分做到）——已用"edge 的保质期/shelf life"这一个意象贯穿全文（第2、5段），链条单一但存在，未违反"换喻体=破功"（第4条）
- ✅ 开头非"我"字开头，第一句是读者已经听过的老话，符合"从读者在干嘉的地方开口"

**flagship 节状态：待分发（已完成）。**

---

## distribution

**四个独立变体，覆盖入口 1/2/3/4/5，hook 类型互不重复（本卡内）。所有数字来自 research 节出处表，未手打。**

| 变体 | 入口号 | hook 类型 | 独立存在理由 |
|---|---|---|---|
| V1（＝flagship 长文的入口推） | 1 旗舰论点 | **验证回收钩 🆕** | 承载完整研究，读者需要看长文才能得到全部数字 |
| V2 | 3 票根借势 | 时间戳锚（复用） | 判断→兑现链本身就是独立故事，不依赖读者看过 V1 的统计细节 |
| V3 | 4 可复用物 | 反面先行钩（复用） | 给出可复用的三步验证法，读者不需要认识黄金这个案例也能用 |
| V4 | 5 批判做法 | 能不能变红钩（复用） | 批判"从未被允许证伪的规律"这个普遍现象，靶子是工作流不是黄金本身 |

**新 hook 类型登记（首用，当晚 append 进 `brain/hooks.md` 类型登记节 ⏳，见下方"越白名单"说明）**：
**验证回收钩** — 机制：此前公开留过一个"验证不了就先不发"的悬念（编辑决策/待验证声明），本帖回来交验证结果，无论结果是撑住还是没撑住。首用：本 campaign。

### V1 · 长文入口推（三行骨架，entry 1）
```
"Golden September" has an expiration date and nobody checked it.
This is the first time we've measured how long a market saying survives after someone writes a paper about it.
Full test, pre-registered, LBMA data back to 1968 → [flagship link]（无配图，Vera 未配）
```

### V2 · 票根借势（entry 3）
```
08-31: we cut "golden September, silver October" from newsletter #001. Andy's call: "Is there anything verifiable? If not, delete it for now."

There wasn't, so we did.

09-05: we finished checking. Thirty years of LBMA data, a named paper (Baur 2013) as the benchmark, four pre-registered hypotheses. All four came back NULL. September's mean since 2011 is actually negative — -1.35%, four up years out of fifteen.

The line we deleted for lack of proof turned out to have the opposite of proof.

Cutting it wasn't caution. It was correct.
```
（90 词，现场计数）

### V3 · 可复用物（entry 4）
```
Before you trust the next "seasonal edge" someone quotes at you, run three checks. We just ran them on "golden September" — it aced the first two and choked on the third.

1. Is there a named study behind it, or just folklore repeating itself? No name, no source — treat it as a guess.
2. Can you reproduce their published number, on their published window? If you can't get their answer, don't trust your own.
3. Now run it on everything since the paper came out. If the sign flipped, someone already traded the edge away.

Gold's "September effect" has a real paper (Baur, 2013) and we reproduced it almost exactly — +2.52% against his +2.2%. Then check 3: -1.35% since 2011, four up years out of fifteen.

Passing two out of three still means you're trading a corpse.
```
（140 词，现场计数）

### V4 · 批判做法（entry 5）
```
Ask anyone who repeats "buy gold in September" one question: has this rule ever been allowed to fail?

Not "has it worked" — has anyone actually built the test that could report it broken? Most seasonal sayings never get that test. They just get repeated until repetition feels like evidence.

We built it. Pre-registered thresholds, a named paper as the benchmark (Baur 2013), thirty years of LBMA gold prices split cleanly into before-and-after. The rule could have passed. It didn't: -1.35% average since 2011, four green Septembers out of fifteen.

A claim that's never been given the chance to turn red was never tested. It was just believed.
```
（108 词，现场计数）

**每变体独立存在检验**：读者只读 V2 也能获得完整的判断兑现故事；只读 V3 也能拿到可执行的三步法且不需要认识黄金案例；只读 V4 也能获得完整的批判论点。**四条互相不依赖**。

**newsletter 变体**：本卡未产（`brain/newsletter.md` 开站状态"已开"，可续跑补做——不做不代表不可用，本卡时间预算优先覆盖 X 五入口）。

**done-when 自检**：每个变体单读成立 ✅；入口号 1/3/4/5 与 hook 类型（验证回收钩🆕/时间戳锚/反面先行钩/能不能变红钩）均互不重复 ✅。

---

## writing
**暂缺执行者（Writer Mia 线无夜跑 routine）——本卡按毛坯审。**

## visual
**暂缺执行者（Visual Vera 线无夜跑 routine）——本卡不配图，按毛坯审。样本内/样本外对照小表见 flagship 节配图占位。**

## review

**⑦ Gate · 2026-09-06 05:53 JST（UTC 08-05 20:53）· 独立新上下文子 agent · rounds 1（未到上限）**

## 判定：**退回 ④ 旗舰站**（⑤ 分发站需在旗舰改完后同步重跑收口）

硬闸先过：distribution 节入口号 **1/3/4/5，齐全不重复**；hook 类型（验证回收钩🆕 / 时间戳锚 / 反面先行钩 / 能不能变红钩）逐条对过 `brain/hooks.md`〈类型登记〉，四型互不重复，且「验证回收钩」的机制定义（"此前公开留过一个'验证不了就先不发'的悬念…本帖回来交验证结果"）与在册的「时间戳锚」（入场当天公开）、「时差票根钩」（并置两个自有时间戳）确实是不同机制，非换皮——**硬闸通过，进逐句审**。

独立复算 research 节全部数字（现场 `git show origin/main:data/research/gold_autumn_2026-09/results.md` + `git show 7e924be4 -- data/reference/DATA_CONTRACTS.md`）：样本内 +2.52%/t+2.83/p0.0042、+1.89%/t+2.57/p0.0077（Baur 报 +2.2%/+1.8%，算术均值口径下我方 +2.68%/+2.00%）；样本外 H1 −1.35%/4 of 15、H2 −0.94%、H3a +0.95%、H3b +1.96%；P(X≤4|n=15)=0.0592（双尾0.1185）；最小可能 p=3.05e-05；LBMA 黄金 1968-04 起701月/白银1968-01起704月缺口0；t 分布校准 df=30 t=2.0423→0.024999（误差5e-06）——**逐位对上，散文四条变体+旗舰零手打数字**（V1–V4、flagship 词数 152/90/140/108 现场复数亦对：152/90/140/108）。BRAIN §三五条、CTA 冻结线（`brain/offers.md`：全卡零 CTA，无一处指向付费/会员/Whop，比"停在订阅"更保守）、"一月效应"未证实项零泄漏（全文五份资产 grep "January/winter/一月/冬季" 零命中）均通过。`writing`/`visual` 两节按过渡条款以毛坯审，不算缺字段。

**逐句审拦下两处，均落在④/⑤边界内，故退回旗舰站（分发站的问题是旗舰问题的下游同构，随旗舰改完一起重跑）：**

### ⛔ 退回理由 1（硬伤 · 违反 04_flagship.md 角色契约明文）：收口是「对仗格言」，契约白纸黑字禁止

flagship 收口：*"An edge has a shelf life the moment someone writes it down. This one's was fifteen years."*

`roles/04_flagship.md` returns 字段原文：**「压缩收尾（一读就懂的重话，不要对仗格言）」**——这不是软性文风偏好，是角色契约的书面条款。这句收口是「一般化真理 + 具体实例」的格言结构，属于本产线反复记录、已升级为 memory 的 `feedback_no_mirrored_aphorism_closings`（跨会话至少复现两次的形状；Andy 原话：「他删了我评分第一的收口句；要一读就懂的重话，不要要回味的巧话」，见 `Fluxus_Substack/drafts/001_after_party_dessert/001_DRAFT_v14.md:144` 等多处记录）。RECORD 自查节（flagship 下「verdicts.jsonl 负面清单自查」）只查了「镜像句」与「对仗格言」两个窄形状，且判定「'An edge has a shelf life...'是陈述句不是对仗」——**这个判定本身就是本条要拦的错**：`feedback_no_mirrored_aphorism_closings` 禁的是"格言体收口"这整类，不要求字面对仗才算命中。

**同一形状在分发站被放大到四份**：V2 收口 *"Cutting it wasn't caution. It was correct."* 是字面「不是A是B」镜像句（`wasn't X. It was Y.`），比 flagship 更直接命中「镜像句」这条负面清单本身；V3 收口 *"Passing two out of three still means you're trading a corpse."*、V4 收口 *"A claim that's never been given the chance to turn red was never tested. It was just believed."* 同属格言/警句体。**RECORD 的负面清单自查只覆盖了 flagship 一份，四条 X 变体的收口从未被自查过**——这是本卡"逐句审四条 X 变体"这一步事实上空转的证据。

### 🔴 退回理由 2（口径混用未按 research 节自己的要求注明）

flagship 正文：*"We ran his numbers first: +2.52% for September, against his published +2.2%. Same sign, same order of magnitude."* V3 正文重复同一比较："we reproduced it almost exactly — +2.52% against his +2.2%."

`results.md` 原文（§一表格脚注）已写明：+2.52% 是**对数月收益均值**，Baur 报的 +2.2% **大概率是算术均值**——同一样本、同一窗口下我方算术均值口径实际是 **+2.68%**（比 +2.52% 更接近 +2.2%）。RECORD 自己的 research 节「未证实项之二」已明确要求：**"正文若要引用具体百分比需注明口径，不能把两种口径的数字混着摆在一句话里当'完全一致'"**——flagship 与 V3 把 +2.52%（对数）与 +2.2%（算术）并置成 "same order of magnitude" / "almost exactly"，**正是 research 节自己划的那条线**，且未注明口径。这不是新发现的问题，是 research 节已经预见、但写作没接住的一处。

⛔ Gate 不代笔：两处修法均由旗舰站定（收口另写一句"一读就懂的重话"、或按 04_flagship.md 边界留空槽给 Andy；口径句改为要么注明"对数均值"要么改引算术均值 +2.68% 与 +2.2% 对比），本站不写替代文案。

### 其余逐条（通过，留痕备查）

- **跨资产病**：五个入口开头故事互不相同（V1 起于"过期检验"、V2 起于编辑决策时间线、V3 起于三步检验法、V4 起于反问"这条规矩被允许失败过吗"、flagship 起于读者已听过的老话）；语气未漂移，全 EN，主语是机制不是人；四变体互相独立成立（只读 V2/V3/V4 任一条都能获得完整故事），非缩写重建。
- **AI 腔其余项**：开头无"我"字句（V2 以日期+"we"开头，属已在册的"时间戳锚"型合法用法，非违规）；方法论黑话（"pre-registered"在 V1/V4/flagship 出现三次）判定为核心论点本身（可复现性方法）而非内部量具泄漏（不同于"轮动/宽度"类内部仪表读数），不拦但建议成稿时至少一处口语化解释。
- **research 节次要瑕疵（不拦路，随手记）**：research 表第 6 行把 Andy 逐字原话（"有可以验证的吗？没有我们就暂时删除"）的出处标成 `commit 7e924be4`——**该 commit 是 09-05 结案条目，不含这句逐字引用**；原话实际出自 DATA_CONTRACTS §七 `[2026-08-31]` 挂单条目（另一个更早的 commit）。7e924be4 只对得上"验证完成、结论支持删除"那半句。建议旗舰站改稿时把出处拆成两个日期条目，不影响判断链本身成立。

### 门铃待按 / 待认领
无（本卡问题全部落在④/⑤边界内，不涉及其他线）。

**收工三问**：①本轮踩的坑＝自查节的"负面清单自查"只做了字面模式匹配（"是不是对仗"）而没有对齐 memory 里真正的判据（"是不是巧话"），四条分发变体的收口完全没被自查覆盖——这是流程性漏检，不是这一条稿子独有；②`roles/06_gate.md` 帮了：硬闸+独立复算的强制顺序让口径问题在"进逐句审"之前就被 research 节自己的文字兜住了一半；建议给 04/05 两站契约都补一句"收口/结尾句自查必须覆盖旗舰+全部分发变体，不能只查旗舰"；③下轮（旗舰站断点续跑）第一件事：重写 flagship 收口为非格言体的"重话"，并修正 +2.52%/+2.2% 那句口径说明，然后分发站同步重写 V2/V3/V4 三处收口 + V3 的口径句，改完回 Gate。

## decision
（owns：Andy 本人——待批）

## performance
（T+24h/T+72h 读数 → keep/test/stop 提案，待发布后回填）
