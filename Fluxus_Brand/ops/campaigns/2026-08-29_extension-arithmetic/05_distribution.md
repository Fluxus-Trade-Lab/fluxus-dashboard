All numbers below were computed in this session from `data/output/universe.json` and `data/content/posts.csv`. Nothing hand-typed, nothing from memory. No files written, no commits, no messages sent.

---

# 分发站 · 四个独立变体

**共同前提**：口径日 2026-08-27 ET 收盘（`universe.json` timestamp `2026-08-28T03:25:47.716461+00:00`）。
**⚠️ 变体 1 与变体 2 不含任何 ticker，周一 cron 跑不跑都能发；变体 3、4 依赖盘面读数，发之前必须重跑 §复算命令 ①。**

---

## 变体 1 · 「那把尺子背面印着剂量」

**文体 G（机制型短文）· hook 类型：翻译钩 —— 立共识 → 一句推倒（Ariel #6 骨架）**
**⭐ 常青弹药：零 ticker、零日期、零盘面状态。任何一天任何一只票飞了都能原样重发。**

```
The extension scale draws its lines at 4, 7 and 10. Entry. Trim. Take profit.
Everyone reads it as a temperature.

It's a dosage chart, and nobody turned it over.

Hold your risk budget fixed, put your stop at the 50-day, and those same three
lines read out as size instead of heat:

4 — call this one full position.
7 — the arithmetic is already handing you 60 to 67 percent of it.
10 — 44 to 55.

Those ranges are the entire contribution of volatility. Swap a quiet name for a
wild one and the number moves a few points. The distance does the rest.

The trim line isn't where the stock turns dangerous. It's where the division
already had you at two thirds.
```

**为什么它能独立存在**：它不引用任何一天的盘面，也不需要读者见过旗舰稿。它对着一件读者**已经在用**的东西（4/7/10 那把尺）说「你只读了它的一半」——不需要前置信息，只需要读者认得那三条线。
**它挑的那一个东西**：一个证据点 —— 三条公开的分档线换算成仓位刻度后是 100% / 60–67% / 44–55%。
**判据**：主看**有没有出现收藏**（全库 14 条帖总收藏 = 1，出现收藏本身就是稀有事件）；次看收藏/赞 >0.5。bucket 记 `ARC`，views 对照 ARC 中位 180 / 最高 421。
**⚠️ 分档归属纪律**：4/7/10 是 **Jacobs / Jeff Sun 那套**（`pipeline/screeners/atr_enrichment.py:66` docstring「0-4 entry / 5-7 hold / >=7 scale-out」；4x 禁入 = `JeffSun_Wiki/wiki/entry-rules.md:30`；个股 10x 止盈 = `JeffSun_Wiki/wiki/atr-extension-signals.md:63`）。**不是我们代码的色带**（green≤4 / amber≤6 / red>6，`atr_enrichment.py:12-14`）。两套别混，也别在帖子里说是「我们的」分档。

---

## 变体 2 · 「先把它反过来跑一遍」

**文体 I（条件句预告）· hook 类型：反面先行钩 —— 第一句就替读者说出最狠的反驳（TSF #18 骨架）**
**⭐ 也不含 ticker，同样常青。**

```
Before you decide this is a rule for cowards, run it the other way.

Same risk budget, same stop at the 50-day, two ATRs above the line instead of
ten — and the arithmetic hands you 176 to 193 percent of a full position. The
spread is just how volatile the name is. That's the division talking, not your
margin clerk.

The halving point sits between 8.7 and 11.8 ATRs, wherever your stock's
volatility puts it. Below that you're being paid to be early. Above it you're
paying to be late.

Nobody ever feels the first half. Nobody runs the number when they're early.
They run it after they've already missed it, get a small answer back, and
conclude the rule is timid.

The rule isn't timid. You only ever ask it after the move.
```

**为什么它能独立存在**：它回答的问题和旗舰稿相反 ——「这套算术会不会把我变成胆小鬼」。情绪极性是**进攻**不是**克制**，读者不需要知道有谁延伸到 9.68 才能读懂。
**它挑的那一个东西**：一个最锋利的主张 —— 这不是一条让你保守的规则，是一条**在基座位置让你比平时买得更大**的规则；你只是从来不在那个位置问它。
**判据**：这条赌的是**赞和转发**（它是一句可铸的立场），收藏比预期低于变体 1。bucket 记 `ARC`。若它赞数高而收藏为零 → 证实 Voice Bible §8.5 收藏闸（立场只拿赞），这本身是可用的实验结论。
**⚠️** 193% 是**比值**（相对你自己的基座仓位），不是绝对仓位，也不是加杠杆建议 —— "not your margin clerk" 那句就是干这个用的，**不许删**。

---

## 变体 3 · 「两张毫不相干的图，同一个答案」

**文体 Q 微缩（旋钮研究 · 数据交付）· hook 类型：独立复现钩 + 明写可证伪带（Muninn #37 的段 2/段 5 结构）**

```
Two charts with nothing to do with each other.

One sits 9.68 ATRs above its 50-day and moves 4.2 percent on an average day.
The other, 9.41 and 4.0. Different company, different sector, different price,
different volatility.

Fix the risk budget. Put the stop at the 50-day. Ask each one what it buys
compared to what it would have bought at 4 ATRs.

49.8 percent. 50.4 percent.

I didn't pick these two because they agreed. They agree because at that
distance the answer stops depending on the stock. Run the same division at 10
ATRs across every volatility from 2 to 8 percent a day and it never leaves
44 to 55.

So here's the part you can break: same stop convention, any name, any
volatility, ten ATRs out. If you get a number outside 44 to 55, one of us did
the arithmetic wrong, and I'd want to know which.

($CRM and $VEEV, Thursday's close.)
```

**为什么它能独立存在**：它是一条**测量声明 + 一条公开的证伪邀请**。读者不需要背景就能拿走一件事：这个比值几乎不取决于股票。而且它把 ticker 放在最后一行的括号里 —— 主角是那两个数，不是那两只票。
**它挑的那一个东西**：一个证据点 —— 两次互相独立的复现落在同一处，加上一条带宽 44–55。
**判据**：这条是四条里**唯一能靠回复被验证**的 —— 判据不是收藏，是**有没有人贴出自己算的比值**。有一个人贴 = 工具被用了。bucket 记 `ARC`，另在 note 栏标「带可证伪带」。
**⚠️** 全篇零方向、零买卖、零持仓。"I" 只出现在第 7 行（开头不许是「我」这条守住了）。

---

## 变体 4 · 「所有仓位数字都是装饰，除非它带着止损」

**文体 J（换变量）· hook 类型：自拆钩 —— 先拆自家产出的可信度，再指出什么活了下来（Setup Factory「先自己说反面」升级版）**

```
Here's the part sizing threads never print: the number moves when you move the
stop, and they never tell you where they put it.

Same day, same two charts, same risk budget. Move the stop from the 50-day to
the 21-day and the position the arithmetic hands back grows by 43 percent on
one of them and 71 on the other. Nothing about either company changed. Nothing
about the market changed. A line moved.

So any position size quoted without its stop is decoration. Including mine,
which is why the stop convention is written into every one of these.

What survives the swap is the direction. Further from your stop, smaller
position — every convention, every time. That part isn't a convention.

That part is division.
```

**为什么它能独立存在**：它的靶子不是延伸度，是**整个「晒仓位数字」的品类**。读者从没见过 CRM 也照样中枪 —— 他今晚刷到的每一条带百分比的帖子，都被这条重新标价了。
**它挑的那一个东西**：一个构建序列 —— 换掉一个变量（止损参照），看什么塌了、什么没塌。
**判据**：这条最可能引来**反驳型回复**（有人会说「我的止损放结构低点」）—— 那正是它要的。判据 = 回复数 > 全库 REPLY 基线 81 曝光那条的量级，且回复里出现**具体的止损约定**。bucket 记 `ARC`。
**⚠️ 排期**：这条和旗舰稿说的是同一次参照替换，**同周只能上一条**。建议旗舰稿先发，这条留到下周或作为旗舰稿下面的自挂回复。

---

## 三个 hook 类型互不相同（校验）

| 变体 | 文体 | hook 类型 | 第一拍干的事 |
|---|---|---|---|
| 1 | **G** 机制型短文 | **翻译钩** | 拿起读者已有的东西，说他只读了一半 |
| 2 | **I** 条件句预告 | **反面先行钩** | 替读者先说出最狠的反驳 |
| 3 | **Q** 旋钮研究 | **独立复现钩** | 两个不相干的输入撞出同一个数 |
| 4 | **J** 换变量 | **自拆钩** | 先拆自己的可信度 |

四条都不是旗舰稿的摘要：1 和 2 换了论证对象（分档尺 / 基座那一半），3 换了论证形式（复现 + 证伪带），4 换了靶子（整个品类）。

---

## 每个数字的出处 + 复算命令

| 数字 | 用在 | 出处 |
|---|---|---|
| **4 / 7 / 10 分档** | V1 | `pipeline/screeners/atr_enrichment.py:66`（Jacobs/Jeff Sun 0-4/5-7/≥7）· `JeffSun_Wiki/wiki/entry-rules.md:30`（4x 禁入）· `JeffSun_Wiki/wiki/atr-extension-signals.md:63`（个股 10x 止盈） |
| **60–67%**（ext=7）· **44–55%**（ext=10）· **176–193%**（ext=2） | V1, V2, V3 | 纯函数扫 ATR% 2→8，命令 ② |
| **8.7 – 11.8 ATR**（比值跌到 50% 的位置） | V2 | 二分求解，命令 ③ |
| **9.68 / 9.41** | V3 | `universe.json` `atr_from_sma50` = 9.6822 / 9.4053；独立复算 `sma50_dist/(atr/close)` 逐位一致，命令 ① |
| **4.2% / 4.0%**（ATR%） | V3 | 同上，`atr/close` = 4.225% / 3.988%，命令 ① |
| **49.8% / 50.4%** | V3 | 命令 ④（现仓位 ÷ ext=4.00 反事实仓位） |
| **43% / 71%**（止损换 21EMA） | V4 | 精确值 **+42.9% / +71.4%**，命令 ⑤ |
| **"Thursday"** | V3 | `date(2026,8,27).strftime('%A')` = Thursday |
| **判据基线**：ARC 中位 180 / 最高 421 · 全库总收藏 1 · 最佳收藏赞比 0.20（08-24 LONGFORM）· REPLY 基线 81 | 判据栏 | `data/content/posts.csv`，命令 ⑥ |

```bash
# ① 主读数（含 V3 的 9.68/9.41/4.2/4.0，也是周一发布前的重跑口）
python3 -c "
import json
u=json.load(open('data/output/universe.json')); rows={r['ticker']:r for r in u['rows']}
R=0.25
print('universe timestamp:', u['timestamp'])
for t in ['CRM','VEEV','OKTA','OOMA']:
    r=rows[t]; atrp=r['atr']/r['close']; stop=r['sma50_dist']/(1+r['sma50_dist'])
    print(t, round(atrp*100,3), round(r['sma50_dist']/atrp,2), r['atr_from_sma50'],
          round(stop*100,2), round(R/stop,2))"

# ② 比值带宽（V1 的 60-67 / 44-55，V2 的 176-193）
python3 -c "
def ratio(a,m,m0=4.0):
    a=a/100.0; f=lambda x:(x*a)/(1+x*a); return f(m0)/f(m)*100
for m in [2,4,7,10]:
    b=[round(ratio(a,m),1) for a in [2,3,4,5,6,7,8]]
    print('ext=',m,b,'min',min(b),'max',max(b))"

# ③ 减半点 8.7-11.8（V2）
python3 -c "
def ratio(a,m,m0=4.0):
    a=a/100.0; f=lambda x:(x*a)/(1+x*a); return f(m0)/f(m)*100
def solve(a,t):
    lo,hi=4.0,200.0
    for _ in range(200):
        mid=(lo+hi)/2
        lo,hi=(mid,hi) if ratio(a,mid)>t else (lo,mid)
    return (lo+hi)/2
print([ (a, round(solve(a,50.0),2)) for a in [2,3,4,5,6,7,8] ])"

# ④ 49.8 / 50.4（V3）
python3 - <<'PY'
import json
u=json.load(open('data/output/universe.json')); rows={r['ticker']:r for r in u['rows']}
R=0.25; stop=lambda d: d/(1+d)
for t in ['CRM','VEEV']:
    r=rows[t]; a=r['atr']/r['close']; d=r['sma50_dist']
    print(t, round(R/stop(d)/(R/stop(4.00*a))*100,1))
PY

# ⑤ 止损参照换 21EMA → +42.9% / +71.4%（V4）
python3 - <<'PY'
import json
u=json.load(open('data/output/universe.json')); rows={r['ticker']:r for r in u['rows']}
R=0.25
for t in ['CRM','VEEV']:
    r=rows[t]; c=r['close']; d=r['sma50_dist']
    s50=d/(1+d); s21=(c-r['ema21'])/c
    print(t, round((R/s21)/(R/s50)*100-100,1))
PY

# ⑥ 判据基线
python3 - <<'PY'
import csv, statistics as st
rows=list(csv.DictReader(open('data/content/posts.csv'))); iv=lambda r,k:int(r[k] or 0)
arc=[iv(r,'views') for r in rows if r['bucket']=='ARC']
print('n',len(rows),'ARC median',st.median(arc),'max',max(arc))
print('total bookmarks',sum(iv(r,'bookmarks') for r in rows),
      'posts with >=1 bm',sum(1 for r in rows if iv(r,'bookmarks')>0))
print('best bm/like',max((iv(r,'bookmarks')/iv(r,'likes'),r['date'],r['bucket']) for r in rows if iv(r,'likes')))
PY
```

---

## ⚠️ 三条置顶给下一站（Studio Q / Andy）

1. **「收藏/赞 >0.5」这个阈值我们从没达到过。** 实测全库 14 条帖**总收藏 = 1**，历史最佳收藏赞比 **0.20**（08-24 LONGFORM，同时是全库最高赞 5）。0.5 是从 swipe file 的对照组（Muninn 2.59 / wey_how 1.02）借来的，不是我们自己的记录。**建议判据改成两级：一级 = 出现任何收藏（基础率 1/14）；二级 = 收藏/赞 >0.5。** 一级过了才谈二级，否则每条都会被判失败。
2. **一天只上一条，变量才分得开。** 旗舰稿已经在测「表格图当载体」这个变量。V4 和旗舰稿共用同一次参照替换（21EMA），**同周同题**；V3 和旗舰稿共用 CRM/VEEV。建议顺序：**旗舰 → V1（隔一天，常青，测纯机制帖的收藏率）→ V3（回复位/接热点）→ V2 → V4（下周）。**
3. **V1 / V2 不受数据陈旧影响**，V3 / V4 受。周一 cron 跑完后跑命令 ①：CRM 若跌出 red 档，V3 换票（角度不变），V4 的 43%/71% 必须重算。

**没做的事（按铁律）**：未 commit、未 push、未改任何仓库文件、未发任何消息。以上四条变体和判据表只存在于本次返回文本里 —— 需要留档的话，落点建议是 `Fluxus_Brand/ops/briefs/2026-08-29_1B_variants.md`，由有落地权的会话写。