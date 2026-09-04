# 旗舰站毛坯 v1 · 「41, 45, 47 → 45, 45, 45」

**载体**：X Article（长版），文体 G · 机制型短文。发布时必带三行骨架入口推（入口 1），否则不发（`brain/x.md` STOP 清单）。
**thesis（唯一）**：一个波动是不是噪声，由「翻转的那些样本彼此像不像」决定，不由它有多大决定。
**主语约束**：全文主语是机制（失效判据 / 缓存 / 这台仪器）。两位当事人只以「第一个问的人 / 第二个问了别的问题的人」出现，中文毛坯与英文正文都不点名。
**状态**：毛坯（未成稿）。Writer Mia 成稿、Visual Vera 配图之后才进 Gate。

> ⚠️ **本页正文里没有一个手打的数字。** 每个数字都从 [`02_research.md`](02_research.md) 的编号条目复制，出处表见 §二。
> ⛔ 已逐条自查 [`03_angle.md`](03_angle.md) §七 的六条禁令，自查结果见 §三。

---

## 一、正文（英文，无填空位）

> ### Three runs of the same check gave 41, 45, 47. Then one question turned it into 45, 45, 45.
>
> You have a number you don't fully trust, so you run the thing again. The second number is a little different. The gap is small, so you do the reasonable thing — you call it noise, you average it, you get on with your day.
>
> That reflex is the whole subject here. Not because averaging is lazy. Because it is the one move that guarantees you never find out what you were looking at.
>
> #### The instrument
>
> The case it came out of is small and boring, which is the point. We keep a tool whose only job is to check whether our tests actually hold the code down. It edits one line of the source at a time — `20` becomes `21`, `==` becomes `!=` — reruns the tests against the edited version, and counts how many of those edits the tests catch. A machine for grading the graders.
>
> Somebody finally asked it to grade itself. Same commit, same machine, same module, four runs: **43%, 47%, 49%, 43%** — a spread of six percentage points, with **six of the forty-nine verdicts changing sides** between two of the runs.
>
> Six points on a self-check. What would you have done with that? Run it a few more times and take the middle. The gap is small, the tool is ours, and there is real work waiting. This is where the story ends for most instruments, and most instruments are still out there.
>
> #### The other question
>
> The second person to look at it didn't ask how big the wobble was. He asked:
>
> **the ones that flipped — do they look like each other?**
>
> They did. Along an axis that was nowhere in the reading. Every one of the six flipped verdicts belonged to an edited file that was **exactly the same size in bytes as the file tested immediately before it. Six out of six, zero difference.**
>
> Here is why that matters. Before Python reuses a compiled version of a source file, it checks whether the cached copy is stale, and by default it checks by comparing two fields: the source file's last-modified timestamp — **truncated to whole seconds** — and the source file's **size in bytes**. That is the entire staleness test, it has been the default since the alternative was introduced in 3.7, and it is still the default today.
>
> Now look again at what this tool does for a living. It turns `20` into `21`. It turns `==` into `!=`. Neither of those changes the size of the file by a single byte. Of the 48 consecutive pairs of edits in that module at that commit, **22 pairs had identical byte counts** — that number belongs to that module at that commit, it is not a constant of Python. But it is enough of a floor that on a fast machine the second edit can be handed the compiled bytes of the first one, still sitting on the tray, while the report prints the second one's name.
>
> If flips landed at random, six-for-six on the zero-difference pairs comes out at **p = 0.0061**. That is a nice number and it proves nothing; it is a coincidence being unlikely, not a cause being found. The proof was turning the cache off.
>
> #### What the intervention said
>
> Same protocol, bytecode cache disabled: **45%, 45%, 45%, with the surviving set identical position by position** — where the same protocol had given **41 / 45 / 47 with ten flipped verdicts** the run before. Across every module, two independent baseline rounds over 475 edits matched position by position. The fix is a flag and an environment variable inside one subprocess call, and it is in main.
>
> And here is the part that would sell better if it weren't true: **the readings were not mostly wrong.** After the fix, five of the six modules scored identically to before. The verdicts that had actually been wrong numbered **five, out of 475** — all in one module. The mechanism was real, the dispersion was real, and the damage was small.
>
> Which is the uncomfortable half. A bug that had cost us almost nothing so far was also a bug that nothing in our process was ever going to surface, because the two fields it turns on — a timestamp and a byte count — are not source code. They appear in no diff. There is no review that catches this by reading more carefully.
>
> #### Why "run it again" was never going to work
>
> This tool had been checked for stability. Repeatedly. Every check came back clean:
>
> | what was repeated | result |
> |---|---|
> | the same edit, 12 runs in isolation | 12 / 12 identical |
> | `--repeat 3`, inside one invocation, 49 edits | zero flips |
> | three separate invocations of the tool | 10 flipped verdicts |
>
> Read that table from the bottom. The flips are there the whole time; they only become visible when the tool is invoked again from scratch. Repeating inside a single run isn't a check, because a single run is precisely the scope in which the stale cache is already sitting there, identically, for every repetition. **The dimension you repeated is the dimension the contamination doesn't vary in.** Do that and you don't get a clean bill of health. You get a photograph of the same contaminated state, twelve times, and you file it as evidence.
>
> #### The flip list
>
> So the takeaway is a swap. Stop asking how wide the spread is. Ask for the list.
>
> **1. Don't report the spread. Report the list.** Write down the items that changed sides between two runs — which trades, which folds, which verdicts. A spread is one scalar, and a scalar cannot have a shape. The list can.
> *Doesn't count if:* you report the standard deviation of the runs. That's the spread wearing a hat.
>
> **2. Ask whether that list resembles itself — along a dimension that isn't in the reading.** Order. Timing. Size. What was left over from the item before. In this case the axis was file size in bytes, which is not something a test score knows about.
> *Doesn't count if:* you look for the pattern inside the reading's own dimensions — recomputing the variance, running one more significance test on the same numbers.
>
> **3. If it resembles itself, go find the intervention.** Turn the shared thing off and measure again. **Dispersion collapsing to zero is the confirmation. A probability is not.**
> *Doesn't count if:* you finish on a p-value. The p-value here was 0.0061 and it was still just a reason to go do the experiment.
>
> If you keep a ledger, you already have candidates. The walk-forward fold that came back below the others. The three losses in a row. The week the slippage felt worse than the week before. None of that is evidence of anything in this piece — it is the same shape, and shape is all it is. But the shape hands you the question. Not how far apart the folds were. Which trades changed side between them, and whether those trades have something in common that the fold score never knew about — the hour, the order they were filled in, the size, what was still open from the trade before.
>
> For the record: on this machine, at this commit, the true score was 22 out of 49. None of the four original runs landed on it.
>
> No amount of reweighing gets the last thing off the tray.

---

## 二、每个数字的出处（逐条，全部复制自 `02_research.md` 编号条目）

| 正文里的数字 / 主张 | 证据编号 | 权威源 | 强制限定（已执行） |
|---|---|---|---|
| 43% / 47% / 49% / 43%，**六个百分点**的跨度 | **C1** | `data/research/audit_mutation_2026-09-01.md` §六（commit `a2e3132b`）；其中 2 次由查证站从归档 JSON 逐格核过（`_single.json` 21/49、`_all.json` 23/49） | ⛔ 全文零处出现「6%」；正文写 "six percentage points" |
| 49 个判定里 6 个翻转 | **C2** | 同上 §六六行表；查证站从两份 JSON 的 `survivors` 对称差**独立重算**（L56 / L64 / L83 / L96 / L155 / L158），并核过描述符去重 28/28、26/26 | 正文只用「6 个」总数，不逐行列（那是入口 4/7 的料） |
| 48 对相邻里 22 对字节数相同 | **C3** | `night_reports/2026-09-02.md` §②甲（`deb7a0f5`）+ `audit_mutation_sweep.py` L127–140；查证站用工具自己的 `sites()`/`build_mutant()` 在 `02e387d1` 上**重算**：`mutants 49 / pairs 48 / zero-delta 22` | ✅ 正文原句带限定：*"that number belongs to that module at that commit, it is not a constant of Python"* |
| 6 个翻转的字节差 6/6 全为 0；超几何 **p = 0.0061** | **C4** | 查证站独立复现（把 C2 的 6 个映射回 C3 的序列量差值）；二项近似 0.0093 | ✅ 引 p 的下一句即 *"The proof was turning the cache off."*；并已写明「关联不是因果」 |
| 41 / 45 / 47（10 个翻转）→ **45 / 45 / 45 逐位相同**；475 个变异体两轮逐位相同；修复在 main | **C5** | `audit_mutation_2026-09-02.md` §五（`10991810`）+ 夜报（`deb7a0f5`）；查证站核到修正后 baseline JSON `audit_universe_shape` = 22/49 = 0.449，且 `-B` + `PYTHONDONTWRITEBYTECODE=1` 确在 main 的 `audit_mutation_sweep.py` L168–171 | 本卡唯一许用的「结果」数字组 |
| 475 个变异体里错的判定共 **5 个**，六模块五个逐位相同 | **X5（推翻 signal 节的那条）** | `audit_mutation_2026-09-02.md` §四 | ✅ 正文正面写出来（"the readings were not mostly wrong"），不是省略 |
| CPython 失效判据 =（mtime 取整到整秒，文件字节数）；3.7 起 hash-based 可选，**时间戳仍是默认** | **C6** | 三处互证：[语言参考 §5.4.6](https://docs.python.org/3/reference/import.html#cached-bytecode-invalidation) · [PEP 552](https://peps.python.org/pep-0552/) · CPython `Lib/importlib/_bootstrap_external.py` 的 `source_mtime = int(st['mtime'])` | ✅ 正文写 "since the alternative was introduced in 3.7, and it is still the default today"（版本范围 + 默认口径） |
| 隔离 12 次 12/12 一致 · 同一次调用 `--repeat 3` 零翻转 · 三次独立调用 10 个翻转 | **M1**（02_research §五） | 同 C5 源 | ✅ 以三行表出现（angle brief 硬要求），并配一句读表方向 |
| 真值 22/49，四次原始跑分无一命中 | **M3** | 查证站双向核（修正后 baseline JSON 22/49 vs 21/23/24/21） | ✅ 必带限定已带：*"on this machine, at this commit"*；主语是跑分不是人 |

**⛔ 一个都没引的**：任何当前杀死率（**C7**，保质期几小时——09-02 一夜之间三个闸的杀死率都动了）。

---

## 三、⛔ 六条禁令逐条自查（`03_angle.md` §七）

| # | 禁令 | 自查 | 证据 |
|---|---|---|---|
| 1 | ⛔「读数大面积是错的」/「所有杀死率都不可信」 | ✅ 未犯，且**反向写了** | 正文原句 *"the readings were not mostly wrong… numbered five, out of 475"* |
| 2 | ⛔「多跑几次看不见它」（须限定为**同一次调用里**） | ✅ 未犯 | 正文原句 *"Repeating inside a single run isn't a check"*；三行表最后一行明写「三次独立调用 → 10 个翻转」，即独立调用**看得见** |
| 3 | ⛔ 三个交易类比带数字 / 写成「我们发现」 | ✅ 未犯 | 类比段零数字，且原句自证 *"None of that is evidence of anything in this piece — it is the same shape, and shape is all it is."* |
| 4 | ⛔「没人写过这个角度」·⛔「同形状全仓只此一处」·⛔「同一秒内写完」 | ✅ 三条全未出现 | 时间戳那半只写机制（文档口径），**未断言两个文件写在同一秒**；正文用 "can be handed"（可能性）不用 "was"（U3 只证了字节数那一半） |
| 5 | ⛔「`-B` 能救磁盘上已有的脏 `.pyc`」 | ✅ 未犯 | 正文只写「关掉缓存后离散度归零」，不谈 `-B` 对既有 `.pyc` 的作用 |
| 6 | M3 锋利句必带「这台机器、这个 commit」限定 | ✅ 已带 | *"on this machine, at this commit"* |

**另外两条来自 signal 节的推翻，也已执行**：X1 单位（全文 "six percentage points"，零处 "6%"）· X5 过头（正文正面承认损伤小）。

**红海扫描未做**（U5）：全文零处出现「没人这么写过 / 这个角度没人碰」这类断言。

---

## 四、亲缘句闸自检（`brain/angles.md`〈亲缘句闸〉三步）

**第 1 步 · 本稿内核**（读者会复述的那一句）：
> **你重复的那一维，正是污染不变的那一维——所以要看的不是跨度，是翻转的那些彼此像不像。**

**第 2 步 · 对 `data/content/posts.csv` 近 14 天逐行比 note 列**（现场读 `git show origin/main:data/content/posts.csv`，覆盖 2026-08-19 → 09-03 共 11 行）：

| 日期 | 帖 | 内核 | 亲缘？ |
|---|---|---|---|
| 08-19 ×2 | $MRNA 入场锚帖 + 加仓追帖 | 入场当天公开时间戳 | ✗ |
| 08-24 | MRNA HOWTO 长文 | 一笔交易的完整流程 | ✗ |
| 08-25 | MRNA 长文入口推 | 分发 | ✗ |
| 08-25 | $HOOD $PLTR 同型 launchpad | 形态迁移 | ✗ |
| 08-27 | Everyone gets their turn | 轮动 | ✗ |
| 08-28 | 宴会比喻 QT | 落后板块上桌＝健康宽度 | ✗ |
| 08-28 | Hamptons / algo monkeys | 段子＋pre-market memo | ✗ |
| 09-01 | ES hourly swing failure + 图 | 价格与结构在做什么 | ✗ |
| 09-01 | QT @GnT_Trades（Covel 止损） | 快速止损 | ✗ |
| 09-03 | $MU 基本面 vs $IBIT $HOOD 动量 | instant feedback | ✗ |
| 09-03 | 跟帖 $GEV $BE | AI trade 没完 | ✗ |

→ **零亲缘。** 近 14 天没有任何一条的内核涉及「自检的盲维 / 方差有结构」。

**第 3 步 · `voice/Fluxus_Own_Lines.md` 的 `亲缘:` 标注**：全库仅 1 条（#129 围棋复盘 ↔ 其对偶），与本稿无关。
⚠️ 按 angles.md 自己写的诚实边界：**第 3 步现在几乎是空转，本闸的承重全在第 2 步**——不把一条标注说成一个体系。

**判定：过闸。** 与角度站独立跑出的结论一致（本站未抄 brief 的结论，重新读了 posts.csv）。

**顺带的正向关系（不是亲缘，是可用的回声）**：Own_Lines #101 是 Andy 自己的句子 ——
「买卖点是主观的，结构是客观的，成交量是真实的」/ *"Entries are opinion. Structure is fact. Volume is truth."*
本稿的内核（方差有结构就不是噪声）与它同源但**不同内核**，成稿站若要接一句 callback，这是唯一在册的合法接口；毛坯不接，交 Mia 判。

---

## 五、交接 ⑤ 分发站

- **入口 1** 的三行骨架请从正文标题那一组数字起（41/45/47 → 45/45/45），长文发布后 Pin。
- **入口 4**（《翻转清单》）与 **入口 7**（三行表压缩图）在本毛坯里分别是「The flip list」节与那张三行表，两者**必须各自独立成立**，不是同一条帖发两遍。
- **入口 2** 的机制段素材在正文「The other question」节尾（两个字段都不在任何 diff 里），⛔ 但别把它写成本条的中心——那是下一张卡的 thesis（角度站放弃方向 B）。
- ⛔ 变体一律不引任何当前杀死率（C7）。

## 六、字数

正文（`## 一、正文` 引用块内英文，含那张三行表）**实测 1272 词**
（`sed -n '/^## 一、正文/,/^## 二、/p' 04_flagship.md | grep '^> ' | sed 's/^> //' | wc -w`，未手打）。

X Article 长版量级合适；若成稿站要压，**可砍的只有类比段**（ledger 那一段）——它是全文唯一零票根的部分（U4），
砍掉不伤证据链，但会丢掉「交易者为什么该在意」的唯一落点，**别先砍三行表和《翻转清单》**，那两样是可复用物本体。
