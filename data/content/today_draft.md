date: 2026-09-05
tier: A
source: 2026-09-03_noise-with-structure
gate: 🎮 4/5 · streak 1 周
---
## C1
bucket: ARC | entry: 2
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
why: 09-03 卡三轮过闸，这是包里第一条今天就能整条粘出去的——不挂长文、不等配图、零跑分数字。入口 1（V1）虽然排在前面，但它整条的作用是给长文当入口推，长文没成稿、配图（原 V7 三行表）没人画，它今天在物理上发不出去。C6 那条唯一需要复查的口径我刚在本机 3.14.3 上重跑过：`source_mtime = int(...)` 仍在，默认写的仍是 timestamp pyc，没翻。
---
## C2
bucket: ARC | entry: 3
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
why: 同一包的入口 3，也不需要图和长文。它交的是票根——两个自有 commit 的时间戳，谁都能去仓库里核。跟 C1 不撞：C1 讲机制，这条讲代价。
---
## C3
bucket: LINE | entry: -
普通人不是不敏感，是什么都想要——只想要刺激的那一半，不认账的那一半。
why: 队列今天（09-05 六）排的就是它，你自己的原话（Own_Lines #127）。本周还差 1 件过关，这条 10 秒发完就 5/5；而且 09-01 之后中文圈一条没拿到。
---
## notes
- 陈旧闸：本卡全部数字关账，零处引用当前杀死率。唯一需要复查的 C6（CPython 缓存判据）今早本机 3.14.3 复跑通过，未过期。
- 09-03 包仍在 `APPROVAL_QUEUE.md` 待你签字，两件事没定：① 等 Mia/Vera 成稿还是按毛坯发 ② V1 长文的配图谁画。C1/C2 是这包里不受这两件事影响的两条。
- ⚠️ 同一包的前一张卡（08-29 extension-arithmetic）昨天被你一句「太ai slop了，也不行」判死，整包零发布。本包和它一样是**毛坯**，没过 Mia 的笔。C1/C2 你看着不对就直接否，判例我记进 verdicts。
- 昨天备的三条一条没发，队列 #29（micromanage）已逾期，本班未把它顺延成新排期。
