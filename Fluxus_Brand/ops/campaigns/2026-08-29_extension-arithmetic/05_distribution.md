# 分发站 · 四个独立变体（v2 · 08-28 收盘重写）

**本文所有数字均由本轮会话现场脚本产出**（`data/output/universe.json` timestamp `2026-08-29T03:18:17.230043+00:00`、`data/output/quality.json` date `2026-08-28` status `ok`、`data/content/posts.csv`）。散文里没有一个手打的数。未发布、未发消息、未碰 campaigns/ 之外的任何文件。

**口径日 = 2026-08-28 ET 收盘（星期五）。** 今天是 08-30（周日），08-28 就是**最新的一根收盘**——本轮不存在上一版那个「陈旧两场」的问题。周一 08-31 开盘后，V3/V4 的读数会变，发布前跑一次 §复算 ①。

---

## 🔴 上一版发生了什么（本节写给下一站，别删）

上一版 V3 的支柱是「两张不相干的图撞出同一个答案：49.80 / 50.45 —— 都是一半」。**在 08-28 的数据上这句是假的**：VEEV 周五回踩，ext 从 9.403 掉到 8.346，比值从 50.45% 变成 55.09%；CRM 几乎没动（9.682 → 9.728，49.80% → 49.71%）。

审查站早就把原理说破了：把止损定在 50 日线之后，「延伸度」和「止损距离」是同一个量，两只票的比值撞在一起不是发现，只是它们 ext 本来就几乎相等。**周五的数据把这件事直接证实了。**

所以 V3 的钩子换掉：不再是「独立复现」，改成**「昨天/今天对照 + 可证伪带」**——尺子跟着图动了一天，这才是它是尺子不是修辞的证据。同时把「any volatility」收进已界定的范围（ATR% 2–8 → 比值 44.44–54.55）。⚠️ **注意这条带是代数后果不是普查结果**（严格单调函数在闭区间上的值域＝两个端点），文案里只许说成算术；真正的实证部分是「**2,091 / 2,556 = 81.8% 的可交易票落在 ATR% 2–8 这个区间里**」——那才是关于股票池的经验事实。

---

## 变体 1 · 「那把尺子背面印着剂量」

**文体 G（机制型短文）· hook 类型：翻译钩 —— 立共识 → 一句推倒（Ariel #6 骨架）**
**⭐ 常青弹药：零 ticker、零日期、零盘面状态。任何一天任何一只票飞了都能原样重发。**

```
The extension scale draws its lines at 4, 7 and 10. Entry. Trim. Take profit.
Everyone reads it as a temperature.

It's a dosage chart, and nobody turned it over.

Hold your risk budget fixed, hold one stop convention — the 50-day, say — and
those same three lines read out as size instead of heat:

4 — call this one full position.
7 — the arithmetic is already handing you 60 to 68 percent of it.
10 — 44 to 55.

Those ranges are the entire contribution of volatility, across names that move
2 to 8 percent on an average day. Swap a quiet one for a wild one and the
number shifts a few points. The distance does the rest.

The trim line isn't where the stock turns dangerous. It's where the division
already had you at two thirds.
```

**本轮改了两处**：① `60 to 67` → **`60 to 68`**（真值 60.32–67.53，上一版手工向内取整）；② 加了 `across names that move 2 to 8 percent on an average day` —— 没有这句，V1 和上一版 V3 犯的是同一条罪（把一个只在 ATR% 2–8 上成立的带说成普适）。
> 第 3 轮微调：原写 `measured across`，`measured` 暗示这是实测结果，实为函数值域，已删该词（Gate 🟡-5）。**V1 是四条里 Gate 三轮零拦路的两条之一**（另一条是 V4）。
**为什么它能独立存在**：它不引用任何一天的盘面，也不需要读者见过旗舰稿。它对着一件读者**已经在用**的东西（4/7/10 那把尺）说「你只读了它的一半」。
**它挑的那一个东西**：一个证据点 —— 三条公开的分档线换算成仓位刻度后是 100% / 60–68% / 44–55%。
🟡 **备选收口（非镜像版，给 Andy 选）**：`By the time a chart reaches the trim line, the division has already cut you to two thirds. Nobody had to decide the stock got dangerous.` —— 原句 `isn't … It's …` 是负面清单上的「不是 A，是 B」镜像句；留原句是因为它读起来最狠，但备一个。
**判据**：一级 = **有没有出现收藏**（全库 14 帖总收藏 = 1，出现收藏本身就是稀有事件）；一级过了才看二级 收藏/赞 >0.5。bucket 记 `ARC`，views 对照 ARC 中位 180 / 全库最高 421。
**⚠️ 分档归属纪律**：4/7/10 是 **Jacobs / Jeff Sun 那套**（`pipeline/screeners/atr_enrichment.py` docstring「0-4 entry / 5-7 hold / >=7 scale-out」；4x 禁入 = `JeffSun_Wiki/wiki/entry-rules.md:30`；个股 10x 止盈 = `JeffSun_Wiki/wiki/atr-extension-signals.md:63`）。**不是我们代码的色带**（green≤4 / amber≤6 / red>6）。两套别混，也别在帖子里说是「我们的」分档。

---

## 变体 2 · 「先把它反过来跑一遍」

**文体 I（条件句预告）· hook 类型：反面先行钩 —— 第一句就替读者说出最狠的反驳（TSF #18 骨架）**
**⭐ 也不含 ticker，同样常青。**

```
Before you decide that sizing by stop distance is a rule for cowards, run it
the other way.

Same risk budget, one stop convention — the 50-day, say — and a chart sitting
two ATRs above it instead of ten. Against a full position at four ATRs — the
top of the entry zone — the arithmetic hands you 175 to 193 percent. The
spread is just how volatile the name is. That's the division talking, not your
margin clerk.

The halving point — where the same budget buys half of that four-ATR position
— sits between 8.7 and 11.8 ATRs, wherever your stock's volatility puts it.
Under that number the same risk buys more shares than a full position. Over
it, fewer.

Nobody ever feels the first half. Nobody runs the number when they're early.
They run it after they've already missed it, get a small answer back, and
conclude the rule is timid.

The rule isn't timid. It only ever gets asked after the move.
```

**本轮改了四处**（第 2 轮 Gate 的 🔴-3 与 🟡-2，加工头两处）：
1. 🔴 `same stop convention as before` → **`one stop convention — the 50-day, say —`**。`as before` 在这条帖子里**没有先行词**（V2 全篇从没提过任何 stop convention），它是在向旗舰稿借上下文——而这条稿子自称常青可独立发。三个词修好。
2. 🔴 首句 `Before you decide this is a rule for cowards` 的 `this` 同样悬空 → **`Before you decide that sizing by stop distance is a rule for cowards`**。
3. 🟡 `176 to 193` → **`175 to 193`**。真值 **175.7576–192.5926**，下界向内取整＝把带说窄了——与上一轮 `60 to 67` **同病**（散文里手工向内取整，角度稿自己禁的那条）。
4. **对仗格言换成默认非对仗版**：`Below that you're being paid to be early. Above it you're paying to be late.` 已被审查站**连续两轮点名**（paid/paying × early/late 双轴对称）。工头定：默认走非对仗版（现正文那句），依据是 Andy 划掉过同形状的收口句这条既有反馈——**这是措辞层的可逆选择，不是替他表态**。
   > **若 Andy 想要那句巧话，原句在此**：*"Below that you're being paid to be early. Above it you're paying to be late."*
（上一轮已改的结尾 `You only ever ask it` → `It only ever gets asked after the move.` 保留。）
**数字**：**175–193**（真值 175.7576–192.5926，本轮把下界从 176 放回 175）与 8.7–11.8（真值 8.696–11.765）是纯函数带宽，与盘面无关，不受数据刷新影响。
**为什么它能独立存在**：它回答的问题和旗舰稿相反 ——「这套算术会不会把我变成胆小鬼」。情绪极性是**进攻**不是**克制**。
**判据**：这条赌的是**赞和转发**（它是一句可铸的立场），收藏比预期低于变体 1。bucket 记 `ARC`。若它赞数高而收藏为零 → 证实 Voice Bible 收藏闸（立场只拿赞），这本身是可用的实验结论。
**⚠️** 193% 是**比值**（相对你自己的基座仓位），不是绝对仓位，也不是加杠杆建议 —— `not your margin clerk` 那句就是干这个用的，**不许删**。

---

## 变体 3 · 「周五它自己动了一格」（整条重写）

**文体 Q 微缩（旋钮研究 · 数据交付）· hook 类型：昨天/今天对照 + 可证伪带**
**⚠️ 依赖盘面，发布前必须重跑 §复算 ①。**

```
Two charts, Thursday's close. Both parked just under ten ATRs above their
50-day. Fix the risk budget, fix one stop convention — the 50-day — and ask
each one what it buys compared to what it would have bought back at 4 ATRs.

49.80 percent. 50.45 percent. Half, both of them.

Then Friday happened to one of them. Not a crash. One session. It came in to
8.35 ATRs, and the same division now hands it 55.1. The other barely moved:
9.73, and 49.7.

A saying about extended stocks wouldn't have moved. This did, the day the
chart did. It's a live reading, and it updates whether or not you like where
it lands.

The part that isn't an opinion: take a name that moves 2 to 8 percent on an
average day. Ten ATRs out, one stop convention, and the answer lands between
44 and 55 percent — the only thing moving it inside that range is how volatile
the name is. That isn't a survey I ran. It's a division you can do on the back
of a receipt, and inside that band it can't come out anywhere else.

How often does that band apply: four out of every five liquid tickers — 2,091
of the 2,556 I can trade — move between 2 and 8 percent on an average day. Run
yours. If your name is in the band and the answer lands outside, one of us did
the arithmetic wrong, and I'd want to know which.

($CRM and $VEEV, Thursday and Friday closes.)
```

**本轮改了什么**：
- **premise 换掉**。上一版靠「两只不相干的票撞出同一个数」当发现——那是恒等式的产物，且 08-28 数据直接把它证伪（VEEV 55.09%）。新版把这件事**反过来当卖点**：两只票分开了，因为尺子读的是图不是标签。
- **可证伪声明收进已测范围**。上一版 `any name, any volatility` 在真实池里 **11.2% 的可交易票落带外**（tradeable n=2,556，全带 40.60–67.86）。新版限定 ATR% 2–8，这条声明不再会被正确证伪。
- 🔴 **末段整段重写（第 2 轮 Gate 的头号拦路，工头执行）**。中间版写的是 *"Here's the part you can break … I ran all 2,091 of them that qualify and not one landed outside."* —— **这是同义反复，不是证据**：
  > `ratio(a) = f(4a)/f(10a) = 0.4·(1+10a)/(1+4a)`，`d/da = 0.4·6/(1+4a)² > 0`，在 a>0 上**严格单调**。一个严格单调函数在闭区间上的值域就是它的两个端点：`ratio(2%)=44.4444`、`ratio(8%)=54.5455`。**只要一只票的 ATR% 在 2–8 之间，它的比值必然在 44–55 之间**——与它是哪只票、什么行业、什么价格完全无关。
  >
  > 筛选条件（ATR% 2–8）与被"检验"的结论（44–55）**是同一件事的两种说法**。「我跑了 2,091 只」的信息量是 **0**，`the part you can break` 是一个**没有东西可以 break** 的证伪邀请。后果不是被证伪，是**被看穿**——而两分钟能看穿它的那个读者，正是我们最想要的读者。
  >
  > ⚠️ **这是本 campaign 内同一形状的第二次复发**：上一轮是 CRM/VEEV 的"巧合"（两票 ext 几乎相等），这一轮换成 2,091 只的"普查"。参见根 `CLAUDE.md` 三次律——**第三次就该升级成机制**（建议：给旗舰站加一条开工自检「我这句话有反例吗？没有→它是算术，不许写成实测」）。
  - **改法**：把算术说成算术（`That isn't a survey I ran. It's a division you can do on the back of a receipt, and it can't come out anywhere else.`），把**真的**实证结果单独拎出来当第二段——`四分之四中的四/五 = 2,091 / 2,556 = 81.81%`，**那个才是关于我们股票池的经验事实**，与函数值域无关。证伪邀请保留（`Run yours.`），但它现在邀请的是「你自己那只票的算术」，不是一个不可能有反例的命题。
- 去掉 `I didn't pick these two because they agreed`（那句现在没有对象了）。
- 移除镜像句：`The number isn't a saying… It tracks…` → `A saying … wouldn't have moved. This did.`

**我的判定：这条重写后仍然独立成立，不出局。** 理由：它是四条里唯一**带时间维度**的（其余三条都是静态换算），也是唯一**发出可被读者验证的公开声明**的。⚠️ 但它的可信度现在**全部**押在末两段的诚实分割上（哪句是算术、哪句是实测）——**这两段任何一句被改回"我扫了 N 只"，这条就必须毙**。
**它挑的那一个东西**：一个证据点 —— 同一把尺，隔一个交易日给出两个不同答案，其中一个动了 4.6 个百分点。
**判据**：这条是四条里**唯一能靠回复被验证**的 —— 判据不是收藏，是**有没有人贴出自己算的比值**。有一个人贴 = 工具被用了。bucket 记 `ARC`，note 栏标「带可证伪带」。
**⚠️ 三条纪律**：① 全篇零方向、零买卖、零持仓；② `I` 只出现在倒数第二段（开头不许是「我」这条守住了）；③ **`fix one stop convention — the 50-day` 是假设不是 Andy 的规则**，措辞不许滑成 `my convention`（上一轮旗舰站就是死在这里）。
**⚠️ 与 V1 的重叠**：44–55 这个带在 V1 里也出现过一次。若 V1 先发，V3 里那句可以改成「你已经见过的那条带」。

---

## 变体 4 · 「所有仓位数字都是装饰，除非它带着止损」

**文体 J（换变量）· hook 类型：自拆钩 —— 先拆自家产出的可信度，再指出什么活了下来**
**⚠️ 依赖盘面，发布前必须重跑 §复算 ⑤。**

```
Here's the part sizing threads never print: the number moves when you move the
stop, and they never tell you where they put it.

Friday's close, two charts, one risk budget. Move the stop from the 50-day to
the 21-day and the position the arithmetic hands back grows by 49.8 percent on
one of them and 92.5 on the other. Nothing about either company changed.
Nothing about the market changed. A line moved.

So any position size quoted without its stop is decoration. Including mine,
which is why the stop convention is written into every one of these.

Further from your stop, smaller position — every convention, every time.

Direction is the only part that survives, and it survives under anyone's stop
convention. Nobody had to agree to it.
```

**本轮改了三处**：① `43 percent / 71` → **`49.8 percent / 92.5`**（08-28 实测；上一版的 43/71 是 08-27 收盘的读数，已作废）；② `Same day` → **`Friday's close`**（审查站指出上一版没说是哪天）；③ **收口换成非对仗版当默认**（工头定）。
🟡 **收口取舍**：原句 `That part isn't a convention. / That part is division.` 是排比＋对仗双段收口，已被审查站**连续两轮点名**。依据既有反馈（Andy 划掉过我评分第一的对仗收口句，「要一读就懂的重话，不要要回味的巧话」），默认改走非对仗版——**这是措辞层的可逆选择，不是替他表态**。
> **若 Andy 想要那句巧话，原句在此**：*"…every convention, every time. That part isn't a convention. / That part is division."*
**为什么它能独立存在**：它的靶子不是延伸度，是**整个「晒仓位数字」的品类**。读者从没见过 CRM 也照样中枪 —— 他今晚刷到的每一条带百分比的帖子，都被这条重新标价了。
**它挑的那一个东西**：一个构建序列 —— 换掉一个变量（止损参照），看什么塌了、什么没塌。
**⭐ 它是本轮唯一把恒等式说破的一条**：把止损定在 50 日线之后，「延伸度」和「止损距离」就是同一个量，「越延伸→仓位越小」是除法不是市场测量。审查站定的排期结论：**这条（或含新止损因果的旗舰）必须先行**，见 §排期建议。
**判据**：这条最可能引来**反驳型回复**（有人会说「我的止损放结构低点」）—— 那正是它要的。判据 = 回复数 > 全库唯一那条 REPLY（2026-07-30，81 曝光）的量级，且回复里出现**具体的止损约定**。bucket 记 `ARC`。

---

## hook 类型互不相同（校验）

| 变体 | 文体 | hook 类型 | 第一拍干的事 | 依赖盘面？ |
|---|---|---|---|---|
| 1 | **G** 机制型短文 | **翻译钩** | 拿起读者已有的东西，说他只读了一半 | ❌ 常青 |
| 2 | **I** 条件句预告 | **反面先行钩** | 替读者先说出最狠的反驳 | ❌ 常青 |
| 3 | **Q** 旋钮研究 | **昨天/今天对照 + 可证伪带**（旧「独立复现钩」已作废） | 给两个数，再让其中一个当着读者的面动掉 | ✅ 08-28 |
| 4 | **J** 换变量 | **自拆钩** | 先拆自己的可信度 | ✅ 08-28 |

四条都不是旗舰稿的摘要：1 和 2 换了论证对象（分档尺 / 基座那一半），3 换了论证形式（时间序列 + 证伪带），4 换了靶子（整个品类）。
**AI 腔自查**：`moreover / furthermore / delve / crucial / it's worth noting / ultimately / not only` 零命中；`X was never Y` 零命中；剩余两处镜像句（V1 收口、V4 收口）与一处对仗格言（V2 中段）**均已附非对仗备选**，由 Andy 拍。

---

## 每个数字的出处 + 复算命令

**全部指向 `data/output/universe.json` timestamp `2026-08-29T03:18:17.230043+00:00`（= 2026-08-28 ET 收盘，星期五），`quality.json` date `2026-08-28` status `ok`。**

| 数字 | 用在 | 出处 / 命令 |
|---|---|---|
| **08-27 → 08-28 变了什么**（唯一一行跨日对照） | V3、本文 §上一版发生了什么 | 旧值取 `git show 03761dc8:data/output/universe.json`（timestamp `2026-08-28T05:36:00Z` = 08-27 收盘）。**CRM** ext 9.682→**9.728**、比值 49.80→**49.71**；**VEEV** ext 9.403→**8.346**、比值 50.45→**55.09**；**OKTA** ext 4.401→**3.267**、比值 92.50→**118.39**；**OOMA** ext 2.406→**2.081**（`tradeable=false`，四条正文均未使用它）。命令 ① + ① ′ |
| **9.73 / 8.35**（ext，周五）· **49.7 / 55.1**（比值，周五） | V3 | 命令 ①：CRM ext 9.728 / 比值 49.71；VEEV ext 8.346 / 比值 55.09。与文件存储列 `atr_from_sma50`（9.7275 / 8.346）一致——⚠️ **同一实现同一输入，不是独立验证**；独立复算见 [06_gate_review.md](06_gate_review.md) §1 |
| **49.80 / 50.45**（比值，周四） | V3 | 命令 ① ′（08-27 快照） |
| **60–68%**（ext=7）· **44–55%**（ext=10）· **175–193%**（ext=2） | V1, V2, V3 | 纯函数扫 ATR% 2→8：60.32–67.53 / 44.44–54.55 / 175.76–192.59。命令 ②。⚠️ **这三条带是 ATR% 区间的代数后果，不是普查结果**（`ratio(a)=0.4(1+10a)/(1+4a)` 严格单调，端点即带宽）——报它们时不许说成「我扫了 N 只都没例外」 |
| **8.7 – 11.8 ATR**（比值跌到 50% 的位置） | V2 | 二分求解 8.696–11.765。命令 ③ |
| **2,091 / 2,556 = 81.8%** | V3（正文里唯一的实证数） | `tradeable=true` n=**2,556**；其中 ATR% 落在 2–8 的 n=**2,091**（**81.81%**）。⚠️ **这条是实证**（我们股票池的经验分布），可以写进文案。<br>❌ 而「这 2,091 只的比值都在 44–55 内」**不是实证**，是 ATR% 2–8 这个筛选条件的代数后果，**不许写成普查**（见 V3 §本轮改了什么 🔴 项）。<br>**对照**：不加 ATR% 限制时整个可交易池的真实带是 **40.60–67.86**，**11.15%（285/2,556）落 44–55 带外** —— 这才是上一版 `any volatility` 塌掉的地方，**这个 11.15% 也是实证** |
| **+49.8% / +92.5%**（止损换 21EMA） | V4 | CRM 止损 29.34%→19.58%，仓位 0.852→1.277（+49.81%）；VEEV 24.97%→12.97%，1.001→1.928（+92.52%）。命令 ⑤ |
| **"Thursday" / "Friday"** | V3, V4 | `date(2026,8,27).strftime('%A')` = Thursday；`date(2026,8,28)` = Friday |
| **判据基线**：ARC 中位 180 / 全库最高 421 · 14 帖总收藏 **1** · 最佳收藏赞比 **0.20**（08-24 LONGFORM，1 收藏 / 5 赞）· REPLY 基线 81 | 判据栏 | 命令 ⑥ |

```bash
# ① 主读数（08-28 收盘；周一发布前的重跑口）
python3 - <<'PY'
import json
u=json.load(open('data/output/universe.json')); rows={r['ticker']:r for r in u['rows']}
R=0.25; stop=lambda d: d/(1+d)
print('universe timestamp:', u['timestamp'])
q=json.load(open('data/output/quality.json')); print('quality date:', q.get('date'), q.get('status'))
for t in ['CRM','VEEV','OKTA','OOMA']:
    r=rows[t]; a=r['atr']/r['close']; d=r['sma50_dist']
    print(t,'close',round(r['close'],2),'atr%',round(a*100,3),'ext',round(d/a,3),
          'stored',r.get('atr_from_sma50'),'stop%',round(stop(d)*100,2),
          'ratio%',round((R/stop(d))/(R/stop(4*a))*100,2),'tradeable',r.get('tradeable'))
PY

# ① ′ 08-27 收盘快照（V3 的「周四」那两个数）
python3 - <<'PY'
import json,subprocess
u=json.loads(subprocess.run(['git','show','03761dc8:data/output/universe.json'],
    capture_output=True,text=True).stdout)
rows={r['ticker']:r for r in u['rows']}; R=0.25; stop=lambda d: d/(1+d)
print('SNAPSHOT timestamp:', u['timestamp'])
for t in ['CRM','VEEV','OKTA','OOMA']:
    r=rows[t]; a=r['atr']/r['close']; d=r['sma50_dist']
    print(t,'ext',round(d/a,3),'ratio%',round((R/stop(d))/(R/stop(4*a))*100,2))
PY

# ② 比值带宽（V1 的 60-68 / 44-55，V2 的 176-193）
python3 -c "
def ratio(a,m,m0=4.0):
    a=a/100.0; f=lambda x:(x*a)/(1+x*a); return f(m0)/f(m)*100
for m in [2,7,10]:
    v=[ratio(a/10,m) for a in range(20,81)]
    print('ext=',m,round(min(v),2),round(max(v),2))"

# ③ 减半点 8.7-11.8（V2）
python3 -c "
def ratio(a,m,m0=4.0):
    a=a/100.0; f=lambda x:(x*a)/(1+x*a); return f(m0)/f(m)*100
def solve(a,t=50.0):
    lo,hi=4.0,200.0
    for _ in range(200):
        mid=(lo+hi)/2; lo,hi=(mid,hi) if ratio(a,mid)>t else (lo,mid)
    return (lo+hi)/2
h=[solve(a/10) for a in range(20,81)]; print(round(min(h),3),round(max(h),3))"

# ④ V3 的可证伪带：真实股票池 vs ATR% 2-8 子集
python3 - <<'PY'
import json
u=json.load(open('data/output/universe.json'))
def ratio(a,m,m0=4.0):
    f=lambda x:(x*a)/(1+x*a); return f(m0)/f(m)*100
tr=[r for r in u['rows'] if r.get('tradeable') and r.get('atr') and r.get('close')]
vals=[]; sub=[]
for r in tr:
    a=r['atr']/r['close']; v=ratio(a,10); vals.append(v)
    if 0.02<=a<=0.08: sub.append(v)
out=sum(v<44 or v>55 for v in vals)
print('tradeable n',len(tr),'band %.2f-%.2f'%(min(vals),max(vals)),
      'outside 44-55: %d (%.2f%%)'%(out,100*out/len(vals)))
print('ATR%% 2-8 subset n',len(sub),'(%.1f%%)'%(100*len(sub)/len(tr)),
      'band %.2f-%.2f'%(min(sub),max(sub)),
      'outside 44-55:',sum(v<44 or v>55 for v in sub))
PY

# ⑤ 止损参照换 21EMA → +49.8% / +92.5%（V4）
python3 - <<'PY'
import json
u=json.load(open('data/output/universe.json')); rows={r['ticker']:r for r in u['rows']}
R=0.25
for t in ['CRM','VEEV']:
    r=rows[t]; c=r['close']; d=r['sma50_dist']
    s50=d/(1+d); s21=(c-r['ema21'])/c
    print(t,'stop50%',round(s50*100,2),'stop21%',round(s21*100,2),
          'size50',round(R/s50,3),'size21',round(R/s21,3),
          'growth%',round((R/s21)/(R/s50)*100-100,2))
PY

# ⑥ 判据基线
python3 - <<'PY'
import csv, statistics as st
rows=list(csv.DictReader(open('data/content/posts.csv'))); iv=lambda r,k:int(r[k] or 0)
print('n posts',len(rows),'total bookmarks',sum(iv(r,'bookmarks') for r in rows))
print('posts with >=1 bm',[(r['date'],r['bucket'],iv(r,'bookmarks'),iv(r,'likes'))
      for r in rows if iv(r,'bookmarks')>0])
arc=[iv(r,'views') for r in rows if r['bucket']=='ARC']
print('ARC n',len(arc),'median',st.median(arc),'max',max(arc))
print('REPLY',[(iv(r,'views'),r['date']) for r in rows if r['bucket']=='REPLY'])
PY
```

（命令均在仓库根目录跑。）

---

## 排期建议（本轮倒过来了）

审查站的结论：**「止损约定决定一切」这句话不先落地，另外三条都站不住**——因为它们全部依赖同一个我们自己引入的 50 日线止损假设。

**建议顺序：V4 → V1（隔一天，常青，测纯机制帖的收藏率）→ V3（接盘面，带证伪邀请）→ V2。**

> 🔴 **第 3 轮更正：这里原本写的是「V4（**或含新止损因果的旗舰**）先行」——那个版本已经不存在了。** 第 3 轮按 Gate 的 🟡-1 把旗舰段 2 里那句无出处的图表法则（`a bar this far from its base doesn't let you put it close`；仓库自己的 `sp_stop` 给 CRM 21.84% / VEEV 14.64%，都比 50 日线止损近得多）删掉了，**旗舰因此不再解释「凭什么是 50 日线」**。所以现在**只有 V4 说破了「止损约定决定一切」这件事，它必须打头阵，旗舰替不了。**
> ⚠️ 另：**旗舰与 V1 的第一拍是同一个动作**（立人群共识 → 一句推倒），排期上别让这两条挨着发。

- 旧版建议的「旗舰 → V1 → V3 → V2 → V4（下周）」**作废**：它把唯一说破恒等式的那条排在四条依赖该假设的稿子后面。
- **一天只上一条，变量才分得开。** V4 和旗舰共用同一次参照替换（21EMA），**同周同题**，两者只能上一条，另一条改作自挂回复。
- V3 和旗舰共用 CRM/VEEV；若旗舰当周发，V3 顺延。

---

## ⚠️ 三条置顶给下一站（Studio Q / Andy）

1. **「收藏/赞 >0.5」这个阈值我们从没达到过 —— 判据改两级。** 现场复核 `data/content/posts.csv`（命令 ⑥）：全库 **14** 帖，**总收藏 = 1**（唯一有收藏的是 08-24 LONGFORM：1 收藏 / 5 赞），历史最佳收藏赞比 **0.20**。0.5 是从 swipe file 的对照组（Muninn 2.59 / wey_how 1.02）借来的，不是我们自己的记录。**一级 = 出现任何收藏（基础率 1/14）；一级过了才谈二级 收藏/赞 >0.5。** 否则每条都会被判失败。

2. **50 日线止损是我们的假设，不是 Andy 的规则。** 他公开记录里写的是 **0.73 ATR 结构止损**（`Fluxus_Substack/drafts/mrna_2026-08/PUBLISHED_X_2026-08-24_en.md:115`），而 CRM 那个 50 日线止损是 **29.34%**。四条变体正文一律用 `one stop convention` / `same stop convention` 措辞，**任何一稿出现 `my convention` 指 50 日线，直接退回**（上一轮旗舰站就是死在这一句）。

3. **数据本轮不陈旧，但周一会变。** 08-28 是最新收盘，08-29/08-30 是周末——V3/V4 现在报的就是当前读数。但 **08-31（周一）盘后 cron 一跑，V3 的 8.35/9.73 和 V4 的 49.8/92.5 全部作废**，发布前必跑命令 ① 和 ⑤。V1/V2 不受影响（纯函数）。**若 CRM 跌出 ≥7 档，V3 换票不换角度；VEEV 已经从 9.403 掉到 8.346，一天走掉一格 —— 这类读数的半衰期就是一个交易日。**

---

**负面清单缺件（如实登记，不脑补）**：`Fluxus_Brand/voice/verdicts.jsonl` 本轮**只有表头一行，零条判决**（`wc -l` = 1，内容是 `_header`）。PIPELINE §4 要求读它当负面清单，**本轮实际输入为空**。本文用的负面清单来自 `06_gate_review.md §4` 列名的六条 + Voice Bible §4.8 起草纪律。Andy 对本轮的否决/采纳，应成为 `verdicts.jsonl` 的第一条真判决。

**本会话未发布、未发任何消息、未 commit、未 push，未改 campaigns/ 之外的任何文件。**
