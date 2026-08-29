# 旗舰站毛坯 · 「同样的止损，延伸到 9.68 个 ATR 之后买到多少」

**载体：X 长推 + 一张读数表图（不用 Article）。长度 ~150 词。**
**口径日：2026-08-27 ET 收盘。⚠️ 08-28 全天数据仓库里没有 —— 周一发之前必须重跑（脚本见 §出处表末行），CRM 若跌出 red 档，换票不换角度。**

---

## 一、正文（成品英文，无填空位）

> You've had that chart open since Thursday, and you already know what everyone is going to tell you. It's extended. Great. Now type that into the order box.
>
> Your stop isn't a line on a chart. It's rent. The further it sits from your entry, the more you pay for the same square footage. At Thursday's close $CRM sat 9.68 ATRs above its 50-day. Put the stop at that average — my convention, use your own and every number here moves — and the rent is 29.03% of the price.
>
> Same 0.25% of risk. It buys 49.8% of the position it would have bought at the base. $VEEV, different chart, different volatility, 50.4%. Half, both times.
>
> It runs the other way, and that half matters more: two ATRs off the 50-day, the same rule buys 186% of normal. This was never a rule about being careful.
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

---

## 二、每个数字的出处

| 数字 | 出现在 | 出处 | 复算命令 |
|---|---|---|---|
| **9.68** | 正文段2 | `data/output/universe.json` → CRM `atr_from_sma50` = 9.6822；独立复算 `sma50_dist / (atr/close)` = 9.68，逐位一致 | 见 ①（下） |
| **29.03%** | 正文段2 | 同上，`sma50_dist / (1 + sma50_dist)` = 0.2903 | ① |
| **0.25%** | 正文段3 | `Fluxus_Substack/drafts/mrna_2026-08/PUBLISHED_X_2026-08-24_en.md:18`(副标 "0.25% for 23R") + `:115`("0.25% ÷ 4.34% ≈ 5%")。**Andy 已公开的 1R 规则值**，非 MRNA 那笔的 0.217%(`:104`) | `grep -n "23R" …` |
| **49.8%** | 正文段3 | 脚本：CRM 现仓位 0.861% ÷ ext=4.00 时 1.729% | ② |
| **50.4%** | 正文段3 | 同上，VEEV 0.917% ÷ 1.817% | ② |
| **186%** | 正文段4 | 读数表 ATR%=4 列 / 2 ATRs 行。**选 ATR%=4 列是因为 CRM 实测 ATR% = 4.225%** | ③ |
| **表格全部 20 格** | 配图 | 纯函数生成，散文里一个都没手打 | ③ |
| **"Thursday"** | 正文段1、段2 | `date(2026,8,27).strftime('%A')` = Thursday | `python3 -c "from datetime import date;print(date(2026,8,27).strftime('%A'))"` |
| **"$CRM / $VEEV"** | 全篇 | cashtag，非美元金额。`grep -nE '\$[0-9]\|million\|万美元'` 全文 = 空 | 已实测 CLEAN |

```bash
# ① 主读数（我实跑过，输出与信号站给的表逐位一致）
python3 -c "
import json
u=json.load(open('data/output/universe.json'))
rows={r['ticker']:r for r in u['rows']}
R=0.25
print('universe timestamp:', u['timestamp'])
for t in ['CRM','VEEV','OKTA','OOMA']:
    r=rows[t]; atrp=r['atr']/r['close']
    stop=r['sma50_dist']/(1+r['sma50_dist'])
    print(t, round(atrp*100,3), round(r['sma50_dist']/atrp,2), r['atr_from_sma50'],
          round(stop*100,2), round(R/stop,2))"

# ② 反事实比值（49.8 / 50.4）
python3 - <<'PY'
import json
u=json.load(open('data/output/universe.json')); rows={r['ticker']:r for r in u['rows']}
R=0.25; stop=lambda d: d/(1+d)
for t in ['CRM','VEEV']:
    r=rows[t]; a=r['atr']/r['close']; d=r['sma50_dist']
    print(t, round(R/stop(d),3), round(R/stop(4.00*a),3), round(R/stop(d)/(R/stop(4.00*a))*100,1))
PY

# ③ 读数表（配图数据源）
python3 -c "
def ratio(a,m,m0=4.0):
    a=a/100.0; f=lambda x:(x*a)/(1+x*a); return f(m0)/f(m)*100
print('ext | '+' | '.join(f'ATR%={a}' for a in [3,4,5,6]))
for m in [2,4,6,8,10]: print(m,' | '.join(f'{ratio(a,m):.0f}%' for a in [3,4,5,6]))"

# ④ 周一发之前必跑：cron 跑完后重算 9.68，跌出 red(>=7) 就换票
#    跑 ① 即可，比对 CRM 那行的第 2/3 列。
```

**实跑校验结果（本会话真跑，不是抄）**：`universe.json` timestamp = `2026-08-28T03:25:47.716461+00:00`（= 08-27 23:25 EDT）；CRM `change_pct` = 0.2258、`high_52w_dist` = −0.0586、`days_since_52wh` = 166 —— 所以**全篇没有一个字写「新高」或「龙头突破」**。OOMA `tradeable` = false，已整只划掉。天真算法 `4.00/9.6822` = **41.3%**，正文里不存在。

---

## 三、我做的三个可逆选择（措辞层面，Andy 二选一）

### 选择 1 · 比喻链：**rent / square footage**（默认）vs 无比喻直白版

我选了 **rent（租金）→ 你付的是同一块面积的租金 → 租金 29.03%**，理由：Voice Bible §4.8 第 3 条「比喻优先于数据」，而 08-28 那条宴会链是上一条的梗，重复会掉价，所以换了一条属于「算术」的新链。租金这个喻体的门槛为零（不需要懂任何东西），而且和你已有的 "the Market God is the landlord" 同源，不用点破。

> **备选（去掉比喻）：** *"Your stop isn't a line on a chart. It's a cost. The further it sits from your entry, the more each share costs you in risk. At Thursday's close $CRM sat 9.68 ATRs above its 50-day…"*

⚠️ 一旦选了 rent，**中途不许换喻体**（§4.8 第 4 条）。所以这两个版本只能整段替换，不能混。

### 选择 2 · 收口：**第三人称重话**（默认）vs 第一人称「我做了除法」

默认：*"You can still buy it. You just can't buy as much of it. Conviction doesn't change the division."*
理由：主语留在读者身上，没有「我做到了而你没有」的味道（1B 变体 C 自己标注的那个风险）。而且它一读就懂，不是要回味的巧话 —— 我没写对仗式收口。

> **备选（回到你 08-24 的原声）：** *"You can still buy it. You just can't buy as much of it. I didn't decide to be smaller — I did the division."*
> 这一版更贴你 `PUBLISHED_X:115` 的 "I didn't decide on 5%, I arrived at it."，代价是最后一拍从读者手里拿回到你手里。

### 选择 3 · 结尾要不要加一条指向周日 Ledger 的路标

默认：**不加**。理由有二：一是你自己的规矩「不预告，只报过去式」；二是这条帖子的最后一拍是「你买不了那么多」，后面接任何招呼都会泄气。

> **要加的话，只加这一行，且不剧透：** *"Sunday I publish what August's ideas actually did."*
> 加了的好处是给 #001 拉一次预期；坏处是把一条纯工具帖变成半条预告帖。

---

## 四、交稿前自查（§4.8 逐条，我已过）

- ✅ 第一句主语是**读者**（"You've had that chart open"）
- ✅ 有反转/嘲讽：*"It's extended. Great. Now type that into the order box."*
- ✅ 有可复述的画面：**stop = rent，你付的是同一块面积的租金**
- ✅ 比喻同一条链（rent → pay → square footage → rent is 29.03%），无换喻
- ✅ 「延伸」只以**人群的话**出现一次（"everyone is going to tell you. It's extended."）随即被驳倒；「轮动」「宽度」「收藏比」零出现
- ✅ 主题句一句（软件板块**一个字没提** —— 那是 @firesidealpha 68,980 曝光那条的红海赛道，我不去）
- ✅ 表格上半部 >100% 那一半写进正文了（"It runs the other way, and that half matters more"），所以它不是空头论调
- ✅ 止损参照已当场声明（"my convention, use your own and every number here moves"）—— §四那个诚实前提没被省略
- ✅ `grep -nE '\$[0-9]|million|万美元'` = 空；无美元金额、无账户规模、无绝对仓位列
- ✅ 无 41%；无已平仓结果 / R 战绩 / 胜率 / 持仓块（#001 边界）
- ⚠️ **唯一未过的一条：数据是 08-27 收盘。周一发之前跑 ④，比对 CRM 那行。**