date: 2026-09-16
tier: B
source: queue（`Fluxus_Brand/ops/Fluxus_Queue.md` 本周队列第 3 条,09-16 排定）+ campaign `2026-09-03_noise-with-structure`（status: queued,维修期内降为 C2/C3）
gate: 见 notes（posts.csv 09-13 后未回填 09-14~09-16,本班给不出准确 X/5）
---
## C1
bucket: QUOTE（金句 · 单独成条不挂链接） | entry: -
Market on a mission to destroy both sides.
why: 09-08 维修令仍生效（未见新规则卡过 Andy）,C1 只出金句库/raw 两个来源;这条是本周队列里排给今天(09-16)的那条,具体物闸占「他自己的原话」,零落地成本。
---
## C2
bucket: 票根（3·时差票根钩,🆕 首用） | entry: 3
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
why: 具体物闸占「一个能查的时间戳」——两个自有 commit(`a2e3132b` 09-01 07:55:58 → `deb7a0f5` 09-02 04:55:59,间隔 21h)。campaign 已过 Gate(queued)、APPROVAL_QUEUE 标「窗口:常青,数字已关账」不受今天读数影响,维修期内只能进 C2 不进 C1。
---
## C3
bucket: 可复用物（4·反面先行钩） | entry: 4
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
why: 具体物闸占「一个能查的数字」(p=0.0061,已关账)。零叙事、读者今晚能直接照抄执行的三步清单,是待批堆里落地成本最低的一条;与 C2 同源 campaign 但入口号不同(3 vs 4)、hook 不同,互不重复。
---
## notes
维修期条款(PIPELINE 09-08 维修令)仍生效——今日无新规则 campaign 卡过 Andy,C1 硬限定金句库/`voice/raw/`,campaign 2026-09-03_noise-with-structure 的变体只能进 C2/C3,未端入 C1。
陈旧闸:该 campaign 在 `APPROVAL_QUEUE.md` 明确标「⏰ 窗口:常青,数字已关账(41/45/47→45/45/45、43/47/49/43、22/48 等),零处引用当前杀死率(C7)」,不随今天仓库读数漂移,免复算。
关卡计数缺口:`data/content/posts.csv` 最后一行停在 09-13,09-14~09-16 三天未回填——按 [pitfall_the_ledger_went_quiet_not_him.md] 的教训,这不等于他没发,只等于台账没记;本班无法给出可信的 🎮 X/5,交周检/Growth 对着 X 主页核实后回填。
`voice/raw/` 与 `verdicts.jsonl` 近 7 天均无新增(最新 raw 是 09-06 三条课程口述,verdicts 只有表头);未触发「硬凑三条」红线,因为今天有队列已成品可端,不算输入枯竭。
门铃自取:INBOX 命中 5 条 🔔→Steve pending,逐条核对后 4 条已在下方有 `↳ ✅` 完成标记(09-12/09-13 备稿班已处理)、1 条是 OPS 内部行(grep-only-first-line 已知缺陷,09-13 已登记待修)——本班无新待处理项,未触发额外动作。
APPROVAL_QUEUE 里 `2026-09-03_noise-with-structure` 还有「等 Mia/Vera routine 还是按毛坯直接发」等 2 件需 Andy 定,今天若顺手看中 C2/C3 想发,发前请先翻那两条。
