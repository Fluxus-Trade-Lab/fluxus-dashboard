# 05 · 分发变体 —— noise-with-structure（2026-09-04）

> ⑤ 分发站产出。**每个变体从 [`03_angle.md`](03_angle.md) 的 brief 重建，不从 [`04_flagship.md`](04_flagship.md) 缩写**（本站铁律）。
> 毛坯当素材库用：正文里出现的每个数字都能在 04 §二 的出处表上找到编号，⛔ **零处引用 C7（当前杀死率）**。
> 语言：对外一律 EN（`brain/x.md`）。**本站无任何发布权**——过 Gate → `APPROVAL_QUEUE.md` → Andy 签字。

**产出（09-04 第 2 轮修订，见文末〈本轮修订记录〉）**：X 变体 **6 个已写全文**（入口 1/2/3/4/5/6）+ **入口 7 本轮撤下**（Gate 09-04 裁决：独立性不成立，三行表保留为 V1 配图规格，不再作独立帖）+ **newsletter 变体 1 个**（`brain/newsletter.md` 顶部「开站状态：已开」→ 照产）。
**入口号 1–6 各占一条，hook 类型 6 个互不重复**，其中 **2 个是首次使用**（已在 `brain/hooks.md`〈类型登记〉append ⏳ 行）。入口 7 本卡不出。

---

## 变体总表

| # | 入口号 | hook 类型 | 一句话独立存在理由（检验：看过其它帖的读者仍得到新东西） |
|---|---|---|---|
| V1 | **1 · 旗舰论点** | 反高潮/诚实卖关子（✅ 在册） | 唯一一条给出**前后两组结果对**（41/45/47 → 45/45/45）并挂长文的；轴是什么、清单是什么全部留在长文里，读完短帖仍缺答案 |
| V2 | **2 · 架构机制** | **翻译钩**（⏳ 在册） | 唯一一条讲清**判据本身**：缓存新鲜度由「取整到秒的时钟 + 一个长度」决定；这条对任何复用型工具成立，不依赖本卡任何一个跑分 |
| V3 | **3 · 票根** | **时差票根钩**（🆕 首用） | 唯一一条给可核验票根：两个自有 commit 相隔 **21 小时**；它交付的是「这事真发生过 + 代价是多少小时」，机制帖与清单帖都给不了 |
| V4 | **4 · 可复用物** | **反面先行钩**（⏳ 在册） | 唯一一条读者今晚能抄到自己台账上的**动作清单**，且三步各自带「做了等于没做」的反例；零叙事、不复述故事 |
| V5 | **5 · 批判做法** | **自拆钩**（⏳ 在册） | 唯一一条回答「**我明明检查过**」这个反驳：把我们自己那三次「全绿」的稳定性自检拆开；结果帖和清单帖都不处理这个反驳 |
| V6 | **6 · 反馈环** | **能不能变红钩**（🆕 首用） | 唯一一条把这台仪器当**台账对象**报过去式数字（四晚零测试 → 同一 commit 补 7 条 / 其中 3 条按名各扛一个失效场景），并给出一条与本卡 thesis 不同的判据：绿不是证据，专职把关才是 |
| ~~V7~~ | ~~7 · 压缩图~~ | ~~对照钩~~ | **本轮撤下**（Gate 09-04 裁决：与 V5 三行表重叠、独立性不成立）——三行表保留，改列为 V1 的配图规格，见文末 V7 节 |
| NL | （Substack） | — | X 全看过的人打开仍有新东西：22/48 的精度限定、p 值为什么不算证明、「损伤其实很小」这半、以及为什么我们自己造仪器（X 装不下的上下文） |

⚠️ **本卡六入口发帖**（入口 7 本轮不出，角度站原判七入口全可用，但 Gate 09-04 裁决 V7 独立性不成立，见文末）。日推按 `brain/x.md`「一个入口一条」排期，**不是一天一条**。

---

## V1 · 入口 1（旗舰论点）· hook：反高潮/诚实卖关子 · 三行骨架入口推

> 骨架规范 `brain/hooks.md`：行1 结果/代价句（**不给答案**）· 行2 第一次看到的量化 · 行3 入口（挂 Article + 一张图）。
> ⚠️ 08-25 的单行入口推（103 曝光）已进 STOP；**本条是三行骨架的第一次真正上测**（hooks.md：变量此前没被测过，在 performance.md TEST 清单）。

```
Three runs of the same check gave 41, 45, 47. The gap is small enough that the
reasonable thing is to average it and move on — which happens to be the one move
that guarantees you never find out what you were looking at.

A separate, earlier measurement of the same tool had already turned up six
verdicts that changed sides between two of its runs. Nobody asked how big that
swing was either. One question got asked instead: the six that flipped — do
they look like each other? Six out of six, identical along an axis that is
nowhere in the score. Same protocol as the 41/45/47 run, after the fix: 45, 45,
45, identical position by position.

What that axis was, and the three-step swap it leaves you with:
↓ [X Article]
```
（配图 = 三行对照表，规格见文末「V1 配图规格」节；长文发布后 **Pin 到 profile**，`brain/x.md` 载体规则。）

**独立存在理由**：它是唯一交付**结果对**的变体——「41/45/47 → 45/45/45 逐位相同」这组前后对照只在这里出现一次。轴（字节数）、机制（缓存判据）、清单（三步）全部**扣着不给**，所以读过 V2–V6 任何一条的人来读它，拿到的是「原来前后差这么多」而不是重复；反过来只读它的人，答案仍在长文里。
**⛔ 自查**：无「6%」（本条不出现跨度数字）· 无 C7 · 未断言「多跑几次看不见它」· 主语是 check / question，不是人。
**⚠️ 09-04 第 2 轮修订（退回理由 1 的修法）**：原文把「41/45/47」（C5，三次独立调用，10 个翻转）与「六个全中」（C4，映射自 Joe 四次跑分里翻转的那 6 个，属另一组测量）拼成了一句，读者只能读成同一组跑分里的 6 个翻转——而那三次实际是 10 个。现改为明写「a separate, earlier measurement」+「between two of its runs」，把两组测量的边界立起来；「after the fix」只回接 41/45/47 那组（C5 本身就是这组的前后对），不再暗示六个翻转也来自这三次。

---

## V2 · 入口 2（架构机制）· hook：翻译钩

> 翻译钩机制（hooks.md）：**把术语读数翻译成人话代价**。这里翻译的是 "cache invalidation"。
> ⛔ 角度站硬约束：「两个字段都不在任何 diff 里」**只能当机制段，不许升成中心主张**（那是下一张卡的 thesis）。本条的中心是**判据本身**，最后一段已把 diff 那句降级为一句附注。

```
Before Python reuses a compiled copy of a source file, it has to decide whether
the cached copy is stale. By default it decides by comparing two things: the
source file's last-modified time, truncated to whole seconds, and the source
file's size in bytes. That is the entire test. It has been the default since the
hash-based alternative arrived in 3.7, and it is still the default today.

Translated out of the jargon: whether you get fresh output is not decided by what
is in your file. It is decided by a rounded clock and a length.

Now point that at a tool whose job is to edit one line at a time — 20 into 21,
== into !=. Neither edit moves the byte count by one. Run fast enough and the
second version can be handed the compiled bytes of the first one, while the
report prints the second one's name.

Two fields, and neither of them is source code — which is also why reading the
diff more carefully was never the fix. But the rule is the part worth keeping:
freshness gets decided by a rounded timestamp and a length, and any edit that
leaves both untouched is invisible to it.

docs.python.org/3/reference/import.html#cached-bytecode-invalidation
```

**独立存在理由**：全卡唯一一条把**判据拆开讲完**的帖。它不含任何跑分，所以读过 V1（结果）或 V5（为什么自检看不见）的人在这里第一次拿到「为什么会这样」；反过来单读它的人拿到一条**可迁移的工程规则**（任何按 mtime+size 判新鲜度的缓存都吃这一口），完全不需要知道我们跑了几次。
**⛔ 自查**：C6 版本范围与「默认仍是时间戳」已带 · 用 "can be handed"（可能性）不用 "was"——**未断言 U3「同一秒内写完」** · 未提 `-B` 对既有 `.pyc` 的作用（禁令 5）· 「不在 diff 里」出现在末段附注位，非中心主张。

---

## V3 · 入口 3（票根）· hook：时差票根钩（🆕 首用）

> 新 hook 机制：**把两个自有时间戳并置，让「间隔」本身承重**——不是「入场当天公开」（那是在册的时间戳锚），是事后用跨度当主张。
> 已在 `brain/hooks.md`〈类型登记〉append ⏳ 行。

```
Sept 1, 07:55 — a commit that says: run our own test-checker four times against
the same code on the same machine and it returns 43, 47, 49, 43. Six percentage
points. Six of the forty-nine verdicts change sides between two of the runs.
Written down at the time as: a thing you measure with is worth about what a guess
is worth, until you have measured it.

Sept 2, 04:55 — the next commit. Cause located, intervention run, dispersion
gone, fix in main, and seven tests on a tool that had been running four nights
with none of its own.

Twenty-one hours between those two timestamps. The gap is the claim here: the
expensive part was not the fix. It was somebody asking a different question
instead of running it a fifth time.
```

**独立存在理由**：唯一一条提供**可核验票根**的变体——两个带时间戳的 commit（`a2e3132b` 09-01 07:55:58 → `deb7a0f5` 09-02 04:55:59，间隔 21h00m01s）。它交付的不是机制也不是清单，是「这事在我们自己的仓库里真发生过，从发现到关账花了 21 小时」。看过全部其它帖的人在这里第一次拿到**时间成本**这个量。
**⛔ 自查**：43/47/49/43 是 **C1**（那台仪器在 `a2e3132b` 的历史跑分），**不是 C7 当前杀死率** · 跨度写 "six percentage points"，⛔ 零处「6%」 · 主语是 commit / question，两位当事人以「somebody」出现，未点名 · 「四晚零测试 + 补 7 条」出处 02_research L115–118。

---

## V4 · 入口 4（可复用物 · 文字形态）· hook：反面先行钩

> 反面先行钩（hooks.md ⏳）：**先给会失败的做法，再给规则**。判据帖体裁（「我要看到什么才改口」）。
> 与 V7 的分界＝**形态**：能读出来的是 4，只能看的是 7（`brain/x.md` 入口 4/7 分界）。

```
Three ways to check whether a wobble in your own numbers is noise. All three feel
like work. None of them can find a thing that is actually sitting there.

— You report the spread. Or the standard deviation of the runs, which is the
  spread wearing a hat. A scalar cannot have a shape.
— You go looking inside the reading's own dimensions: recompute the variance,
  run one more significance test on the same numbers.
— You finish on a p-value.

The swap, three steps:

1. Report the list, not the spread. Write down the items that changed sides
   between two runs — which trades, which folds, which verdicts.
2. Ask whether that list resembles itself, along a dimension that is not in the
   reading. Order. Timing. Size. What was left over from the item before.
3. If it resembles itself, go turn the shared thing off and measure again.
   Dispersion collapsing to zero is the confirmation. A probability is not.

Step 3 is the one that gets skipped. Ours came with p = 0.0061, and it proved
nothing — the proof was turning the cache off.
```

**独立存在理由**：唯一一条读者**今晚能对自己台账执行**的东西，且三步各自带反例（反例列是 V1/V5 里没有的）。它零叙事——不提我们的仪器、不给跑分，所以看过全部故事帖的人在这里拿到的是**可携带物**，而看过它的人仍然不知道故事是什么。
**⛔ 自查**：p=0.0061 后**紧跟**「真正的证明是把缓存关掉」（C4 强制限定，已执行）· 无 C7 · 无交易类比数字（禁令 3）。

---

## V5 · 入口 5（批判常见做法）· hook：自拆钩

> 自拆钩（hooks.md ⏳）：**公开拆自己上一说法的漏洞**。靶子＝「跑几次取平均」**这个工作流**，⛔ 不是任何人、不是对手盘。
> ⚠️ 角度站硬要求：**必带三行表**，否则读者会把结论读成「多测几次」——那正好是反的。

```
We had checked this tool for stability. Repeatedly. Every check came back clean.

  same edit, 12 runs in isolation      →  12 / 12 identical
  --repeat 3, inside one invocation    →  zero flips across 49 edits
  three separate invocations           →  10 verdicts flipped

Read it from the bottom. The flips were there the whole time. Repeating inside a
single run is not a check, because a single run is exactly the scope where the
stale state is already sitting there, identically, for every repetition.

The dimension you repeated is the dimension the contamination does not vary in.

Twelve clean runs was never a clean bill of health. It was a photograph of the
same contaminated state, twelve times, filed as evidence.
```

**独立存在理由**：唯一一条处理那个必然出现的反驳——「我明明做过稳定性检查」。它的交付物是**一条判定规则**（重复的那一维不能是污染不变的那一维），而不是结果或清单。看过 V1（结果）与 V4（清单）的人在这里第一次知道**为什么自己现有的自检天生看不见这类问题**。
**⛔ 自查**：⛔ 未写「多跑几次看不见它」——三行表最后一行明写「三次独立调用 → 10 个翻转」，即**独立调用看得见**（禁令 2，X3 推翻项）· 主语是 checks / repetition，全条零人名 · 无 C7。

---

## V6 · 入口 6（反馈环 · build in public）· hook：能不能变红钩（🆕 首用）

> 新 hook 机制：**用一个「全绿」读数当钩，反问它有没有能力报红**——没被注射验证过的绿是装饰。
> 已在 `brain/hooks.md`〈类型登记〉append ⏳ 行。build in public 纪律：**只报过去式、落在数字或 NULL、不预告**（BRAIN §一）。

```
Past tense, our own ledger. The tool we use to grade our tests had been running
four nights with zero tests of its own. The commit that fixed its self-noise
added seven.

Three of those seven exist for one job each, and none of the three is "pass
quietly": take away the flag that suppresses the bytecode cache, and one of
them has to report the leftover file — not stay silent about it. Hand another
a genuinely flaky test, and it has to come back UNSTABLE, not a kill. Hand the
third something that hangs, and it has to report no verdict, not a kill.

A green suite tells you nothing about whether it can go red. Three of ours are
built with exactly one way to pass: report the specific failure they were
named to catch. That is the number we would put in front of anybody.
```

**独立存在理由**：唯一一条把这台仪器当**台账对象**报表现数据（四晚零测试 / 7 条 / 3 条按名各扛一个失效场景），也是唯一一条给出**与本卡 thesis 不同的判据**：绿不是证据，专职把关才是。看过 V1–V5 的读者在这里第一次看到「事后我们改了什么工作方式」。
**⛔ 自查**：只报过去式、无预告 · 无 C7 · 未提「测试测的是模块不是接线」（那是弃选 #6，留给下一张卡）——**本条只讲阳性对照，不讲接线**。
**⚠️ 09-04 第 2 轮修订（退回理由 2 的修法：降级口径，未补实跑）**：原文「have been made to go red on purpose」/「have been made to」断言三条测试**被执行过**且确实报红——查证站只核过 commit 存在、`+210` 行 stat 相符、三条测试的**名字与其声称职责**对得上，没有跑过它们、没有留痕「注入后真的变红」。改稿去掉「made to go red」这个执行态动词，只说三条测试**各自被设计为只有一种通过方式**（报出它们被命名要抓的那个失效场景）——这是查证站实际核到的那一层，不越一次执行。

---

## V1 配图规格（原 V7，09-04 Gate 裁决撤下独立帖，改列为 V1 的配图）

> **裁决摘录**（RECORD.md `## review`）：「V7 作为独立帖撤下，入口 7 本卡不出；V5 正文的三行表原样保留、⛔ 不许改两列」——V7 唯一的独立性来源（第三列「could you see it?」）逐格对照后是 result 列的同义复述，不构成重建；`brain/hooks.md` 的**对照钩**定义是「两个标的同读数不同待遇的并置」，V7 的「三种测法 × 同一处污染」不落在该定义里。表本身**仍是好素材**，保留作 V1（入口 1）的配图。

**图内容（三行 × 三列，供 Visual Vera 按 `roles/07_visual.md` 配 V1 用）**

| what was repeated | result | could you see it? |
|---|---|---|
| the same edit, 12 runs in isolation | 12 / 12 identical | **no** |
| `--repeat 3`, inside one invocation (49 edits) | zero flips | **no** |
| three separate invocations of the tool | 10 verdicts flipped | **yes** |

图脚一行（图内排版，不放正文）：`The dimension you repeated is the dimension the contamination does not vary in.`

⛔ **不单独配文发布**——这张表只作为 V1 长文帖的随文配图，不构成入口 7 的独立帖，避免「同一条帖发两遍」。

---

## NL · newsletter 变体（Substack「How Much」）

> **开站状态核对**：`git show origin/main:Fluxus_Brand/brain/newsletter.md` 顶行 = **「开站状态：已开（2026-08-27 首篇上线）」** → 按 `roles/05` 条件**照产**。
> 判据（newsletter.md）：① 当周 X 内容能自然链过去 ✅（V1 长文即本期骨架）② 三个月后打开还成立 ✅（C1–C6 全部 **【常青】**，零 C7）。
> 开头不许是「我」✅ · 比喻优先于数据且连成一条链 ✅ · 内部术语不上台面（`.pyc` / mutation testing 全部译成人话）✅ · 收口要一读就懂的重话，不要对仗格言 ✅。
> **状态**：分发变体 v1（骨架 + 已写死的段落），**成稿交 Writer Mia**；本站不定标题终版。

**它比 X 多出来的东西（这就是它存在的理由）**：
1. **22/48 的精度限定**——X 上这个数只能带一句限定，长文里可以讲清为什么「这不是 Python 的常数，是这一个模块在这一个 commit 上的数」，以及为什么把它当常数引用就是下一个 bug。
2. **p 值为什么不是证明**——0.0061 与「关掉缓存后离散度归零」的区别，X 上只能塞一句，长文里是一整节，且它是本卡最可迁移的一课。
3. **「损伤其实很小」这半**——475 个变异体里错的判定一共 5 个，六个模块五个逐位相同。这半在 X 上会被读成认怂，在长文里它是**信用**。
4. **个人上下文**：为什么我们自己造检查测试的工具，而不是信一个绿色的测试套件。X 装不下。

**段落骨架（Mia 成稿用）**
- **开头**（⛔ 不许以「我」开头，已写死）：`Every instrument you own has a number it gives you, and a number nobody has ever asked it for: how much it agrees with itself.`
- **段 1 · 那件事**：同一份代码、同一台机器、四次跑分 43/47/49/43，**六个百分点**。任何人都会叫它噪声。
- **段 2 · 那个别的问题**：翻转的那六个彼此像不像 → 六个全部与前一个变异体字节差为 0。**比喻链起点**：一台天平，秤盘上还留着上一个东西。
- **段 3 · 判据**：取整到秒的时钟 + 一个长度（CPython 官方口径，3.7 起 hash-based 可选、**默认仍是时间戳**）。⚠️ 22/48 的限定在这一段写足。
- **段 4 · 证明不是概率**：p=0.0061 → 关掉缓存 → 45/45/45 逐位相同。**离散度归零＝确认。**
- **段 5 · 诚实的那一半**：475 里错 5 个，五个模块逐位相同。机制真、损伤小，两件事都说。
- **段 6 · 交易者那一段**（⛔ 零数字、⛔ 不许写「我们发现」）：走低的那一折、连着三笔亏、滑点更差的那一周——**形状相同，仅此而已**；形状交给你的是问题不是结论。
- **段 7 · 《翻转清单》三步**（同 V4，长文版每步多一句为什么）。
- **收口**（重话，非对仗格言）：`No amount of reweighing gets the last thing off the tray.`
- **CTA**（`brain/offers.md` 冻结线）：温读者**只给订阅** `fluxuscapital.substack.com/welcome`；⛔ 会员/付费零字。

---

## 出处节（复算命令与保质期）

**⛔ 本页七个 X 变体 + newsletter 骨架，零处引用 C7（任何闸的当前杀死率）**——研究站实测保质期＝**几小时**（09-02 一夜之间三个闸的杀死率都动了，02_research §C7）。旗舰站已零引用，本站同。

| 变体 | 用到的数字 | 编号 | 保质期 | 复算命令 |
|---|---|---|---|---|
| V1 | 41/45/47 → 45/45/45 逐位相同 | **C5** | **常青**（历史读数，已关账；修复在 main） | `git show origin/main:data/research/audit_mutation_2026-09-02.md` §五（commit `10991810`）+ `night_reports/2026-09-02.md`（`deb7a0f5`） |
| V1 | 6/6 沿一个不在读数里的轴一致 | **C4** | 常青 | 02_research §六 **R3**（R1 的六元组映射回 R2 的变异体序号） |
| V2 | 失效判据 =（mtime 取整到整秒, 文件字节数）；3.7 起 hash-based 可选、默认仍是时间戳 | **C6** | **需复查的唯一一条**：若 CPython 哪天把默认翻成 hash-based 即失效 → 重读[语言参考 §5.4.6](https://docs.python.org/3/reference/import.html#cached-bytecode-invalidation) 与 [PEP 552](https://peps.python.org/pep-0552/) | 02_research §六 **R4**（本机读 `_bootstrap_external.py` 的 `source_mtime = int(...)`） |
| V3 | 43/47/49/43（**六个百分点**）· 49 个判定里 6 个翻转 | **C1 / C2** | 常青（`a2e3132b` 的历史跑分，非当前读数） | 02_research §六 **R1**（两份归档 JSON 的 `survivors` 对称差） |
| V3 | 两 commit 时间戳与 21 小时间隔 · 四晚零测试 → 补 7 条（3 条注射式阳性对照） | C5 / 02_research L115–118 | 常青（commit 时间戳不变） | `git -C <repo> show -s --format=%ci a2e3132b deb7a0f5` |
| V4 | p = 0.0061 | **C4** | 常青（**必须紧跟「真正的证明是把缓存关掉」**——已执行） | 02_research §六 **R3** |
| V5 | 12/12 一致 · `--repeat 3` 零翻转 · 三次独立调用 10 个翻转 | **M1** | 常青 | 同 C5 源（`audit_mutation_2026-09-02.md` §五） |
| V1 配图 | 同 M1（原 V7 表，改列为 V1 配图规格） | **M1** | 常青 | 同上 |
| V6 | 7 条测试 / 3 条各按名扛一个失效场景（名称见 02_research L117；⚠️ 09-04 降级：未断言已执行验证） | 02_research §C5 | 常青（已在 main） | `git -C <repo> show --stat deb7a0f5` |
| NL | 22/48 零字节差（**特指 `audit_universe_shape` @ `02e387d1`**）· 475 里错 5 个 | **C3 / X5** | 常青，但 **22/48 的限定不可去**（去掉即变成一个关于 Python 的假常数） | 02_research §六 **R2**（用工具自己的 `sites()`/`build_mutant()` 重生成 49 个变异体量相邻字节差） |

---

## 本站的 ⛔ 禁令终检（`03_angle.md` §七 六条 + 两条推翻项，逐条按**全部 6 个 X 变体 + NL 骨架**扫，09-04 第 2 轮复扫）

| # | 禁令 | 判 | 证据 |
|---|---|---|---|
| 1 | ⛔「读数大面积是错的」 | ✅ 未犯 | 全页零处；NL 段 5 反向写出「475 里错 5 个」 |
| 2 | ⛔「多跑几次看不见它」 | ✅ 未犯 | V5 三行表最后一行明写**三次独立调用 → 10 个翻转**（看得见）；限定词 "inside a single run" 在 V5 正文 |
| 3 | ⛔ 三个交易类比带数字 / 写成「我们发现」 | ✅ 未犯 | 仅 NL 段 6 以类比语气出现，**零数字**，且明写「形状相同，仅此而已」；X 六条全无类比 |
| 4 | ⛔ U5 红海断言 · U6 全仓唯一 · U3 同一秒内写完 | ✅ 三条全未出现 | V2 用 "can be handed"（可能性）；全页零处「没人写过这个角度」 |
| 5 | ⛔「`-B` 能救已有脏 `.pyc`」 | ✅ 未犯 | V6 只写「拿掉抑制缓存的 flag → 测试必须报出残留文件」，未主张 `-B` 能清理既有 `.pyc` |
| 6 | M3 锋利句必带「这台机器、这个 commit」限定 | ✅ 规避 | **本站六个变体全部未引 M3（真值 22/49）**——它留在长文尾部（04 正文已带限定） |
| 7 | ⛔ 断言未经执行验证的结果（**09-04 新增自查，对应退回理由 2**） | ✅ 已修 | V6 不再写「have been made to go red」这类执行态断言，只写测试的设计职责（名字对应的失效场景） |
| X1 | 单位：⛔ 永不写「6%」 | ✅ | **变体正文零命中**（`grep '6%'` 仅命中本页三处自查/禁令的元文本，不是可发布文案）；V3/NL 写 "six percentage points" / **六个百分点** |
| X5 | ⛔ 过头（「所有杀死率不可信」） | ✅ | 未出现；NL 段 5 正面承认损伤小 |
| X8 | ⛔ 数据组混淆（**09-04 新增自查，对应退回理由 1**） | ✅ 已修 | V1 已把「41/45/47（C5）」与「六个全中（C4，映射自 Joe 四次跑分）」用「a separate, earlier measurement」「between two of its runs」分清边界 |
| — | ⛔ 入口 2 的「两个字段都不在任何 diff 里」不许升成中心主张 | ✅ | V2 中心＝判据本身，该句降级为末段附注一句，且立刻转回规则 |
| — | ⛔ 主语是机制不是人 | ✅ | 六条零人名；V3 用 "somebody"，V5/V6 用 "we"（作为犯了那个工作流错误的**我们自己**，非指认他人） |
| — | CTA 冻结线 | ✅ | 冷读者（V2/V3/V5/V6）**零 CTA**；温读者（V1 长文、NL）**只给订阅**；⛔ 会员/付费零字 |

---

## 交接 ⑥ Gate（`roles/06_gate.md`）

1. **入口号 1–6 各一条、hook 类型六个互不重复**（总表已列，入口 7 本卡不出）；08-29 首件的教训是**文体不同 ≠ 入口不同**，本页按入口定义逐条判过。
2. **两个新 hook 类型**（时差票根钩 / 能不能变红钩）已按 `roles/05` append 进 `brain/hooks.md`〈类型登记〉，各一行 ⏳，**只碰了那一节**。
3. **09-04 第 2 轮：仅修了 Gate 09-04 第 1 轮退回的两处**（V1 数据组混淆、V6 未验证执行断言），并按拍板①执行了 V7 撤下。V2–V5 与 NL 骨架**逐字未动**。
4. 排期口径：**一个入口一条**，不是一天一条（`brain/x.md`）。长文（V1 挂的 Article）发布后 **Pin 到 profile**。

---

## 本轮修订记录（09-04 第 2 轮，分发站断点续跑）

对照 RECORD.md `## review`（Gate 09-04 第 1 轮判定「退回 ⑤ 分发站」）逐条执行：
1. **退回理由 1（V1 数据组混淆）→ 已修**：改用「a separate, earlier measurement」「between two of its runs」把 C5（41/45/47，10 翻转）与 C4/C2（六个全中，来自 Joe 四次跑分里翻转的那 6 个）的边界立起来，不再暗示同一组。
2. **退回理由 2（V6 越证据）→ 已降级口径**（未补实跑，未走「查证站补一次实跑」的另一分支——本轮无查证站执行权，选降级）：去掉「have been made to go red」等执行态断言，改为陈述三条测试的**设计职责**（按名字扛一个失效场景），这是查证站实际核到的那一层。
3. **拍板①（V7 vs V5 三行表）→ 已执行**：V7 撤下独立帖身份，改列为「V1 配图规格」；V5 正文三行表**原样保留，未改列**（遵 Gate 明令「⛔ 不许改两列」）。
4. **拍板②（V6 是否啃下一张卡的料）→ Gate 已裁「不算，保留」**，本轮未动 V6 的核心论点，只修了退回理由 2 的执行态断言。
5. V2 / V3 / V4 / V5 / NL 骨架：**逐字未动**（Gate 09-04 已判通过，PIPELINE〈断点续跑〉「已过闸的站不重做」）。
