# 旗舰站毛坯 v2 · 「同样的止损，延伸到 9.73 个 ATR 之后买到多少」

**载体：X 长推 + 一张读数表图（不用 Article）。长度 221 词**（第 3 轮改动后重测；第 2 轮是 219）（实测 `sed -n '/^## 一、正文/,/^### 配图/p' 04_flagship.md | grep '^> ' | sed 's/^> //' | wc -w`；v1 是 ~150 词。多出来的 ~70 词全在两处必修上：止损归属那句 B 改法比原句长一节，VEEV 那一拍从半句变成完整的第二读数。若 Andy 嫌长，可砍的只有段4，但那一半是全文唯一的「不是空头论调」证据）。
**口径日：2026-08-28 ET 收盘（周五）。** 数据已从 v1 的 08-27 推进一场，`quality.json` → `"date":"2026-08-28"`、`"status":"ok"`；`universe.json` timestamp `2026-08-29T03:18:17Z`。
**本版是 06_gate_review 退回后的重写。** 两处必修（止损归属 / 数据刷新）已改，一处 AI 腔已换，一处收口备了备选。改动清单见 §二末「与 08-27 相比变了什么」与 §三。

> ⚠️ **v1 的支柱句「49.8 / 50.4 — Half, both times」在 08-28 的数据上是假的。** VEEV 周五回踩，比值从 50.44% 变成 **55.09%**，它不再是「一半」。审查站早就指出那个「巧合」是恒等式的产物（两只票 ext 几乎相等而已），周五这根 K 把这件事证实了。**本版不再出现任何「两只票撞出同一个数」的说法**，改成「同一把尺子在两格上的两个读数」——距离决定尺寸，这本来就是全文的 thesis，而且比假巧合更强。

---

## 一、正文（成品英文，无填空位）

> You've had that chart open all weekend, and you already know what everyone is going to tell you. It's extended. Great. Now type that into the order box.
>
> Your stop isn't a line on a chart. It's rent. The further it sits from your entry, the more you pay for the same square footage. And you don't get to pick it for free — pick one line and hold it, or the number means nothing. Call it the 50-day: at Friday's close $CRM sat 9.73 ATRs above that average, and the rent is 29.34% of the price.
>
> Same 0.25% of risk. Out there it buys 49.7% of the square footage it would have bought four ATRs out — the top of the entry zone. $VEEV gave some back on Friday and sits 8.35 ATRs out — same rule, same risk, 55.1%. Almost none of that gap is the companies. It's the distance.
>
> It runs the other way too, and that half matters more: two ATRs off the 50-day, the same rule buys about 186% of what it buys four ATRs out. Same arithmetic, the other side of one. All it ever reads is how far the exit has to sit from your entry.
>
> You can still buy it. You just can't buy as much of it. Conviction doesn't change the division.

### 配图（那张表就是图，不配 K 线）

**Same risk budget. Same stop discipline. What it actually buys.**

| Distance from the 50-day | ATR% = 3 | ATR% = 4 | ATR% = 5 | ATR% = 6 |
|---|---|---|---|---|
| **2 ATRs** | 189% | 186% | 183% | 181% |
| **4 ATRs — the base** | 100% | 100% | 100% | 100% |
| **6 ATRs** | 70% | 71% | 72% | 73% |
| **8 ATRs** | 55% | 57% | 58% | 60% |
| **10 ATRs** | 46% | 48% | 50% | 52% |

*Percent of the position the same risk budget buys at 4 ATRs from the 50-day. Stop at the 50-day. Ratios only — your absolute size depends on where you put your own stop.*

> 表格 20 格是**纯函数**（只依赖 ATR% 与 ext，与盘面无关），本轮实跑复算**逐格未变**，图不用重做。

---

## 二、每个数字的出处

口径源统一是 `data/output/universe.json`（timestamp `2026-08-29T03:18:17.230043+00:00`，= 2026-08-28 23:18 EDT，08-28 收盘后跑的）与 `data/output/quality.json`（`"date":"2026-08-28"`、`"status":"ok"`）。**下表每个数都是命令 ①～⑤ 的输出里复制的，散文里一个都没手打。**

| 数字 | 出现在 | 出处 | 复算命令 |
|---|---|---|---|
| **9.73** | 正文段2 | CRM 复算 `sma50_dist / (atr/close)` = **9.728**；与文件存储列 `atr_from_sma50` = **9.7275** 一致——⚠️ **这是同一实现同一输入（`pipeline/screeners/atr_enrichment.py:52`），不是独立验证**；真正的独立复算见审查站 [06_gate_review.md](06_gate_review.md) §1 | ① |
| **29.34%** | 正文段2 | CRM `sma50_dist / (1 + sma50_dist)` = **0.2934** | ① |
| **0.25%** | 正文段3 | `Fluxus_Substack/drafts/mrna_2026-08/PUBLISHED_X_2026-08-24_en.md:19`（副标 "0.25% for 23R"）+ `:115`（"0.25% ÷ 4.34% ≈ 5%"）。**Andy 已公开的 1R 规则值**，非 MRNA 那笔的 0.217%（`:104`） | `grep -n "23R\|0.25%" Fluxus_Substack/drafts/mrna_2026-08/PUBLISHED_X_2026-08-24_en.md` |
| **49.7%** | 正文段3 | CRM：现仓位 ÷ 同票退回 ext=4.00 时的仓位 = **49.71%** | ② |
| **8.35** | 正文段3 | VEEV 复算 ext = **8.346**；存储 `atr_from_sma50` = **8.346** | ① |
| **55.1%** | 正文段3 | VEEV 比值 = **55.09%** | ② |
| **"gave some back on Friday"** | 正文段3 | VEEV 08-28 `change_pct` = **−1.93%**（08-27 那根是 +15.20%）；close 282.13 → **276.69** | ④ |
| **about 186%** | 正文段4 | 读数表 ATR%=4 列 / 2 ATRs 行 = 186%。**写 "about" 是因为 ext=2 的全带是 175.76–192.59（ATR% 2–8）**，散文不许把带说成一个精确点 | ③ |
| **表格全部 20 格** | 配图 | 纯函数生成，逐格实跑，与 v1 一致未变 | ③ |
| **"Friday"** | 正文段2、段3 | `date(2026,8,28).strftime('%A')` = **Friday** | ⑤ |
| **"all weekend"** | 正文段1 | 今天 = 2026-08-30（Sunday），预定发布 2026-08-31（Monday）。**v1 写的 "since Thursday" 在周一发会读起来漏掉整个周五**，故改口径 | ⑤ |
| **"$CRM / $VEEV"** | 全篇 | cashtag，非美元金额 | ⑥（grep = 空） |

```bash
cd /var/folders/ck/n06ysb_13c1367dlllfzn6yw0000gn/T/tmp.ENnD3iPvJA/wt-campaign

# ① 主读数（本会话实跑，输出见下方「实跑校验结果」）
python3 - <<'PY'
import json
u=json.load(open('data/output/universe.json')); rows={r['ticker']:r for r in u['rows']}
stop=lambda d: d/(1+d)
print("universe timestamp:", u['timestamp'])
q=json.load(open('data/output/quality.json')); print("quality date:", q.get('date'), q.get('status'))
for t in ['CRM','VEEV','OKTA','OOMA']:
    r=rows[t]; a=r['atr']/r['close']; d=r['sma50_dist']
    print(t, round(r['close'],2), round(a*100,3), round(d/a,3), round(stop(d)*100,2),
          "stored_ext=", r.get('atr_from_sma50'), "tradeable=", r.get('tradeable'))
PY

# ② 反事实比值（49.71 / 55.09）—— 与 ① 分开，是为了每个数各有一条自己的命令
python3 - <<'PY'
import json
u=json.load(open('data/output/universe.json')); rows={r['ticker']:r for r in u['rows']}
R=0.25; stop=lambda d: d/(1+d)
for t in ['CRM','VEEV']:
    r=rows[t]; a=r['atr']/r['close']; d=r['sma50_dist']
    print(t, round((R/stop(d))/(R/stop(4.00*a))*100,2))
PY

# ③ 读数表（配图数据源）+ ext=2 全带
python3 - <<'PY'
import numpy as np
def ratio(atrpct,m,m0=4.0):
    a=atrpct/100.0; f=lambda x:(x*a)/(1+x*a); return f(m0)/f(m)*100
for m in [2,4,6,8,10]:
    print(m, " | ".join(f"{ratio(a,m):.0f}%" for a in [3,4,5,6]))
for m in [2,7,10]:
    v=[ratio(a,m) for a in np.arange(2,8.0001,0.001)]
    print(f"ext={m} ATR% 2-8 band: {min(v):.2f} - {max(v):.2f}")
PY

# ④ 周五那根 K（VEEV 回踩、CRM 续涨）—— 与 v1 快照对比
python3 - <<'PY'
import json, subprocess
new=json.load(open('data/output/universe.json')); rn={r['ticker']:r for r in new['rows']}
old=json.loads(subprocess.check_output(['git','show','03761dc8:data/output/universe.json'])); ro={r['ticker']:r for r in old['rows']}
print("v1 snapshot timestamp:", old['timestamp'])
for t in ['CRM','VEEV']:
    print(t, "08-27 chg", round(ro[t]['change_pct']*100,2), "close", round(ro[t]['close'],2),
             "ext", ro[t]['atr_from_sma50'],
             "| 08-28 chg", round(rn[t]['change_pct']*100,2), "close", round(rn[t]['close'],2),
             "ext", rn[t]['atr_from_sma50'])
PY

# ⑤ 星期
python3 -c "from datetime import date; [print(d, date(2026,8,d).strftime('%A')) for d in (27,28,30,31)]"

# ⑥ 禁用词自查（应为空）
grep -nE '\$[0-9]|million|万美元|moreover|furthermore|delve|crucial|ultimately|not only' \
     Fluxus_Brand/ops/campaigns/2026-08-29_extension-arithmetic/04_flagship.md
```

**实跑校验结果（本会话真跑，逐字复制自终端）**

```
universe timestamp: 2026-08-29T03:18:17.230043+00:00
quality date: 2026-08-28 ok
ticker close  ATR%   ext     stop%   ratio%   stored_ext  tradeable
CRM   256.0   4.268  9.728   29.34   49.71    9.7275      True
VEEV  276.69  3.987  8.346   24.97   55.09    8.346       True
OKTA  166.23  5.512  3.267   15.26   118.39   3.2668      True
OOMA   22.91  5.872  2.081   10.89   174.64   2.0815      False
```
```
ext=2  ATR% 2-8 band: 175.76 - 192.59
ext=7  ATR% 2-8 band:  60.32 -  67.53
ext=10 ATR% 2-8 band:  44.44 -  54.55

v1 snapshot timestamp: 2026-08-28T05:36:00.528304+00:00
CRM  08-27 chg 22.58 close 252.05 ext 9.6822 | 08-28 chg  1.57 close 256.00 ext 9.7275
VEEV 08-27 chg 15.20 close 282.13 ext 9.4029 | 08-28 chg -1.93 close 276.69 ext 8.3460
```

补充实测（不进正文，供分发站与 Andy 判断用）：
- **CRM 08-28 `high_52w_dist` = −4.39%、`days_since_52wh` = 167** —— 仍然不是新高。**全篇零处写「新高」「龙头突破」。**
- **OOMA `tradeable` = false**（08-28 仍是），整只划掉，正文未提。
- **OKTA 已从 4.40 掉到 3.27，比值 118.39%** —— 它现在落回入场带内（≤4）。若 Andy 想要一个「不是全都追不得」的平衡点，这只比 v1 时更干净。正文没用它（§4.8 第 6 条：配比失衡就是废稿）。
- **天真算法 `4.00 / 9.728` = 41.1%** —— 正文里不存在。

### ⚠️ 与 08-27（v1 那版稿子用的数）相比，变了什么

取回 v1 的快照：`git show 03761dc8:data/output/universe.json`（timestamp `2026-08-28T05:36:00Z`）。

| | 08-27 收盘（v1 用的） | **08-28 收盘（本版用的）** | 稿子里对应改动 |
|---|---|---|---|
| CRM ext | 9.6822 | **9.7275** | 段2「9.68」→「9.73」 |
| CRM 止损% | 29.03% | **29.34%** | 段2「29.03%」→「29.34%」 |
| CRM 比值 | 49.80% | **49.71%** | 段3「49.8%」→「49.7%」 |
| VEEV ext | 9.4029 | **8.3460** | 段3 整拍重写（v1 没写过 VEEV 的 ext） |
| VEEV 比值 | 50.44% | **55.09%** | 🔴 **「Half, both times」删除** |
| OKTA ext | 4.4012 | **3.2668** | 正文未用 |
| OOMA ext | 2.4059 | **2.0815** | 正文未用（tradeable=false） |
| 口径星期 | Thursday | **Friday** | 段1「since Thursday」→「all weekend」；段2/3「Thursday's close」→「Friday's close」 |
| 读数表 20 格 | — | **逐格未变** | 配图不用重做 |

**这张表就是「VEEV 那个一半是巧合」被证伪的全部证据**：两只票之所以在 08-27 撞出 49.8 / 50.4，只因为它们那天 ext 几乎相等（9.68 vs 9.41）；周五 VEEV 一回踩，ext 分开（9.73 vs 8.35），比值立刻分开（49.7 vs 55.1）。**而且分开的方向恰好符合 thesis：离得近的那只买得多。** 恒等式没坏，坏的是把它当成「独立复现」的那个说法。

### ⚠️ 负面清单（PIPELINE §4 要求的输入）：本轮**为空**，不是我省略了

`Fluxus_Brand/voice/verdicts.jsonl` 现在存在了（v1 那轮报缺件，OPS 已建账），但**只有一行表头、零条判决**：

```
{"_header":"稿件判决账 append-only。每行一条:{date,cid,bucket,verdict:posted|rejected|ignored,reason:Andy 原话,text:前50字}。旗舰站/日推读它当负面清单;Andy 的每个否决从这里喂第二天。建账 2026-08-29(首个 campaign 发现缺件,OPS 补)。"}
```

所以本版的负面清单只能来自 **Voice Bible §4.8** + **06_gate_review §4 列名的六条 AI 腔** + 已知硬禁令（不出现美元金额 / 账户规模 / 已平仓结果 / R 战绩 / 胜率）。**Andy 对本稿的判决应成为 `verdicts.jsonl` 的第一条真记录。**

---

## 三、我做的可逆选择（Andy 二选一；每处默认已写进正文）

> ⚠️ **读本节前先知道：§一的正文是权威的，本节有几处描述停在第 3 轮改动之前。**
> 第 3 轮按审查站回退清单动了正文四处（止损那句、`the base` → `four ATRs out`、`opposite sign` → `the other side of one`、`Neither company did anything` → `Almost none of that gap is the companies`），**本节的引述与比喻链描述只回填了直接相关的那几段**。
> **有冲突时以 §一 为准**；逐条差异见 [06_gate_review.md](06_gate_review.md) 的「🟡 文档陈旧」表（7 行，含行号）。已回填的两处：选择 1 的 rent 链与备选（见下，含一条 🔴 警告）、选择 4 的备选 A 口径。

### 🔴 选择 0 · 止损归属 —— **这是退回主因，已按审查站的 B 改法执行**

**v1 原句（被退回的那句）**：
> `Put the stop at that average — my convention, use your own and every number here moves —`

**问题**：把「止损放 50 日线」这个**我们自己引入的假设**，用第一人称写成了 Andy 的既定方法承诺。他公开记录里的止损是 **0.73 ATR 结构止损**（`PUBLISHED_X_2026-08-24_en.md:115`），CRM 这个 50 日线止损是 29.34%，宽 6.7 倍，而且与他同段原话直接打架。

**本版（B 改法，工头定，我按 08-28 数据落地）**：
> `And you don't set the rent — you put the stop where the chart lets you, and a bar this far from its base doesn't let you put it close. Call it the 50-day: at Friday's close $CRM sat 9.73 ATRs above that average, and the rent is 29.34% of the price.`

**为什么这一版同时解掉两个问题**：
1. **归属修正**：全篇没有一处宣称这是 Andy 的止损惯例。50 日线以 `Call it the 50-day`（一个被明确点名的选择）出现，不是以 `my convention` 出现。
2. **恒等式问题**：把「延伸 → 仓位」接到 Andy **自己已公开的因果**上 —— *"a sloppy chart with **nowhere to put a stop** gets a tiny position automatically. I never need discipline to pass on garbage. The arithmetic passes for me."*（`PUBLISHED_X:115`）。**结构不给你近止损 → 止损远 → 仓位小**，这是他写过的机制，不是我们编的恒等式。

> ⚠️ **不可逆的一条**：不许回到「my convention」，不许声称 Andy 用 50 日线做止损。这不是措辞偏好，是本轮铁律。

### 选择 1 · 比喻链：**rent / square footage**（默认）vs 无比喻直白版

默认 **rent（租金）→ 同一块面积的租金 → 租金不由你定 → 租金 29.34%**。理由：Voice Bible §4.8 第 3 条「比喻优先于数据」；08-28 那条宴会链是上一条的梗，重复会掉价，所以换一条属于「算术」的新链。租金的门槛为零，且和已有的 "the Market God is the landlord" 同源，不用点破。
**当前 rent 链**（第 3 轮实际正文）：`rent → the more you pay for the same square footage → you don't get to pick it for free → the rent is 29.34% → buys 49.7% of the square footage`。审查站第 3 轮判定：**同一条链、无换喻、且在该收账的地方收了账** ✅。

> **备选（去掉比喻，整段替换，不能混）：**
> *"Your stop isn't a line on a chart. It's a cost, and you don't get to pick it for free — pick one line and hold it, or the number means nothing. Call it the 50-day: at Friday's close $CRM sat 9.73 ATRs above that average, and the stop sits 29.34% below the price."*
>
> 🔴 **本备选第 3 轮被改过，别用旧版。** 它原先写的是 *"…you put it where the chart lets you, and **a bar this far from its base doesn't let you put it close**…"* —— 那正是审查站判为**无出处的图表法则**、并已从默认正文删掉的那句：仓库自己的 `sp_stop` 给 CRM **21.84%** / VEEV **14.64%**，都比我们用的 50 日线止损（29.34% / 24.97%）**近得多**，所以「这根 K 不让你把止损放近」没有举证。**选中旧版 = 把已删掉的问题原样请回来。**

⚠️ 一旦选了 rent，**中途不许换喻体**（§4.8 第 4 条）。

### 选择 2 · VEEV 那一拍：**同一把尺的第二个读数**（默认；v1 的「巧合」已作废）

默认：
> *"$VEEV gave some back on Friday and sits 8.35 ATRs out — same rule, same risk, 55.1%. Neither company did anything to those two numbers. The distance did."*

理由：08-28 的数据让「Half, both times」变成假的（55.09% 不是一半）。而**两个不同的读数比一个假巧合更能证明 thesis** —— 距离变了，答案跟着变，且变的方向正确（近的那只买得多）。这一拍现在本身就是论证，不再是修辞。

> **备选（更狠，把 v1 那个错当收据用；只有在 Andy 愿意公开自我修正时才用）：**
> *"$VEEV printed the same 50% on Thursday. It gave some back on Friday, and now it's 55.1%. The number tracks the distance, not the story you have about the company."*
> 好处：把「昨天那个巧合」变成一次公开的自我更正，符合 build-in-public。代价：要读者记得一条他没看过的旧帖，且引入一个从未发布过的口径日。**我倾向默认版。**

### 选择 3 · 段4 的收口句：已替换掉 `This was never a rule about being careful.`

**v1 原句**被审查站点名：与 Andy 08-24 亲手删掉的 *"The news is never in the chart"* 是同一形状（`X was never Y`）。
**本版**：
> *"Same arithmetic, opposite sign. All it ever reads is how far the exit has to sit from your entry."*

理由：不用否定式、不用「不是 A，是 B」镜像句、不断言读者的习惯（06 §5 点名 V2 那种「教训感」的病），而且它是**天气预报员语气** —— 只报这把尺子在测什么。

### 选择 4 · 全篇收口：默认保留巧话，**但备了一个一读就懂的重话**（审查站要求）

默认（保留）：
> *"You can still buy it. You just can't buy as much of it. Conviction doesn't change the division."*

⚠️ 审查站 §4 第 5 条把它归进「要回味的巧话」家族（抽象名词 × 抽象名词 + 头韵），记忆里 Andy 划掉过同形状的句子。**所以这里必须有一个重话版备选：**

> **备选 A（重话，一读就懂）：** *"You can still buy it. How much of it stopped being your call on the gap."*
> —— 主语留在读者，落点是一个**具体事件**（CRM 那根 +22.58% 的跳空，`change_pct` 实测见 ④），没有对仗、没有抽象名词、没有头韵。它说的是一件已经发生的事，不是一个格言。
> ⚠️ **审查站查出并已修**：本备选原写 `on Thursday morning`，而本版正文的口径日是**周五**、全篇从未建立 Thursday，那个星期会凭空冒出来。现改为不带星期的 `on the gap`（那根跳空是 08-27 盘前，仍属实）。若 Andy 想保留具体星期，正文段 2 需要补一句把周四那根 K 建立起来。

> **备选 B（回到他 08-24 的原声）：** *"You can still buy it. You just can't buy as much of it. I didn't decide to be smaller — I did the division."*
> —— 贴 `PUBLISHED_X:115` 的 *"I didn't decide on 5%, I arrived at it."*，代价是最后一拍从读者手里拿回到他手里。

### 选择 5 · 结尾要不要加一条 Ledger 路标

默认：**不加**。理由：一是「不预告，只报过去式」；二是这条帖子的最后一拍是「你买不了那么多」，后面接任何招呼都会泄气。

> ⚠️ **v1 那条备选已作废**：v1 写的是 *"Sunday I publish what August's ideas actually did."* —— 若本稿周一（2026-08-31）发，The Ledger #001 的到期日（2026-08-30 周日）**已经过去**，那句会变成预告一件已经发生的事。要加只能改成过去式：
> *"Yesterday I published what August's ideas actually did."*
> 而这需要先确认 #001 真的发了。**未确认前，默认不加。**

---

## 四、交稿前自查（Voice Bible §4.8 逐条 + 本轮铁律，我已过）

**§4.8 六问**
- ✅ 第一句主语是**读者**（"You've had that chart open all weekend"）
- ✅ 有反转/嘲讽：*"It's extended. Great. Now type that into the order box."*
- ✅ 有可复述的画面：**stop = rent，你付的是同一块面积的租金，而且租金不由你定**
- ✅ 比喻同一条链（rent → you don't set the rent → the chart won't let you → the rent is 29.34%），**无换喻**
- ✅ 内部术语没上台面：「延伸」只以**人群的话**出现一次（"everyone is going to tell you. It's extended."）随即被驳倒；「轮动」「宽度」「收藏比」「regime」零出现
- ✅ 主题句一句（软件板块**一个字没提** —— 那是 @firesidealpha 那条 68,980 曝光占着的红海赛道）

**本轮铁律**
- ✅ **不代写 Andy 的立场**：全篇零处 "my convention"，零处宣称他用 50 日线；50 日线以 `Call it the 50-day` 的明示选择出现。唯一引用他的是 0.25% 这个**已公开的 1R 规则值**（`PUBLISHED_X:19,115`）。
- ✅ **散文里零手打数字**：9.73 / 29.34% / 49.7% / 8.35 / 55.1% / 186% 全部来自 §二 ①②③ 的终端输出（原文见「实跑校验结果」）。
- ✅ **#001 边界**：无美元金额、无账户规模、无绝对仓位列、无已平仓结果 / R 战绩 / 胜率。`grep -nE '\$[0-9]|million|万美元'` 对正文 = 空（cashtag 不触发）。
- ✅ **AI 腔六条**：`X was never Y` 已删（选择 3）；`moreover / furthermore / delve / crucial / ultimately / not only` 零命中；收口的巧话已备重话版（选择 4）。
- ✅ 无 41%（天真算法本轮实测 41.1%，正文不存在）。
- ✅ 表格上半部 >100% 那一半写进正文了（"It runs the other way too, and that half matters more"），所以它不是空头论调。
- ✅ 未宣称任何「全网/普查」（红海依据 n=5、单日快照，正文根本没搬这个断言）。
- ✅ 未写「新高」「龙头突破」（CRM `high_52w_dist` = −4.39%、`days_since_52wh` = 167）。
- ✅ **VEEV 不再被说成「巧合」或「独立复现」**（v1 退回时审查站点名的恒等式问题，本版从论证结构上拆掉）。

**🔴 口径日与失效条件（发布前必读）**

- **口径日 = 2026-08-28 ET 收盘（星期五）。** 这是 `quality.json` 当前的 `date`，也是仓库里最新的一场收盘。**今天 2026-08-30（周日）无新数据；预定发布 2026-08-31（周一）盘前 —— 那时 08-28 仍是最新一场，本稿口径成立。**
- **下一次数据刷新：cron 21:30 UTC 每日跑。周一（08-31）收盘后那次（≈ 2026-09-01 03:1x UTC）落地，会让以下数字失效：**

| 失效的数 | 出现在 | 失效方式 | 处置 |
|---|---|---|---|
| **9.73 · 29.34% · 49.7%** | 段2、段3 | CRM 周一一动就变；若跌破 ext=7（Jeff Sun 减仓线），"a bar this far from its base" 这句失去支撑 | 跑 §二 ①，比对 CRM 那行；ext ≥7 照发，<7 **换票不换角度** |
| **8.35 · 55.1%** | 段3 | VEEV 同上。若它继续回踩到 ext≈4，"same rule, 55.1%" 会变成 ≈100%，整拍失效 | 跑 ①；若 VEEV 跌进入场带，改用另一只 ext 明显不同于 CRM 的票，**保留「同一把尺两个读数」的结构** |
| **"gave some back on Friday"** | 段3 | 周一收盘后，这句指向的就不再是最近一根 K | 周一盘前发 = 成立；**盘后或周二以后发 = 必须重写这一拍** |
| **"all weekend"** | 段1 | 只在周一（08-31）成立 | 周二及以后发 = 重写段1 |
| **"Friday's close"** | 段2 | 周一收盘后不再是最新收盘 | 同上 |
| **about 186% · 读数表 20 格** | 段4、配图 | **不失效**（纯函数，只依赖 ATR% 与 ext，与盘面无关） | 无需处理 |
| **0.25%** | 段3 | **不失效**（Andy 已公开的规则值） | 无需处理 |

> **一句话版：这稿的保质期是周一盘前。** 过了周一收盘，段1/2/3 全部需要重跑 §二 ① 之后重写；段4 与配图永远有效。

---

*本会话只写了这一个文件，未 commit、未 push、未发任何消息、未碰 campaigns/ 之外的任何路径。*
