# 一个工人去替别人的任务收尾，两棵树改同一批文件——而任务板上两张单都正常

**日期**：2026-10-02（ops；当事的两张单是 linda `T-1002-10` 与 ops `T-1002-15`）
**形状**：为第 1 次事故立的闸，判据建在那次事故**恰好不会变**的那个量上。
工人流程第 5.5 步问「我这张单的 `status` 变了吗」，而它要防的那件事（两个写者在改同一批文件）
从不经过任何一张单的 `status`。
**同族**：`pitfall_status_word_reported_as_fact`（状态字不是事实）·
`pitfall_chat_claim_not_verified_double_dispatch`（claim 了不等于只有一个写者）。
共有的那句话：**任务板记的是单，不是现实**。

---

## 一、时间线（JST，全部 2026-10-02；凡标「实测」的都附了命令）

| 时刻 | 事 |
|---|---|
| 04:30:40 | `T-1002-10`（linda，夜间研究班）建单；04:31:03 守护进程派工 |
| 06:23:01 | linda 开 `T-1002-15`（owner=ops）：把变异击杀率登记进 `KNOWLEDGE.md`，权威源指向 `data/research/audit_mutation_ledger.json`。**那个文件当时只活在 linda 自己的分支上，不在 main** |
| 06:24:16 | 守护进程派 `T-1002-15`；06:24:24 工人进程 `48055` 起（`claude -p … 你是 agents/ops，本次只做任务 T-1002-15`） |
| 06:24:22 | 它自己的协议工作树建好：`.git/worktrees/fx-worker-wt-6ykl9fv2`，HEAD `afb93f157`（当时的 origin/main）。这棵树此后**一个字没动** |
| 06:26:59 | **第二棵树**建出来：`.git/worktrees/wt-T-1002-10-finish`，checkout 在 `5b70609a3`——linda 的本地分支头，一个只存在于这台机器的 commit（远端 `agent/linda/T-1002-10` 停在 `8e588f899`）。实测：该树 `git reflog` 的 `HEAD@{4}` 是 `5b70609a3` 且 message 为空（＝`worktree add` 的那次 checkout），`HEAD@{3}` 是 `rebase (start): checkout origin/main` |
| 06:27:01–06:27:52 | rebase 撞上 `UU Fluxus_Brand/ops/material_inbox.md`（公箱同尾追加，CLAUDE.md 主树保护第 6 条点名的形状）；冲突被解掉，三个 commit 重放成 `fd3c05e9b` / `0a8b79e41` / `b9975e133`，**message 与 main 上的 `a097c1562` / `94502181e` / `36cddd539` 逐字相同** |
| 06:28:47 | linda 把 `T-1002-10` 打成 `done`，`result: 4712849d2`——她的产出**已经在 main 上** |
| 06:28:49 | 进程 `49467` 起，在那棵树里跑全量测试（`cd $WT10 && … pytest -q pipeline/tests tests`）。实测父链：`49467 → 48055`，而 `48055` 的 prompt 第一行是 `你是 agents/ops，本次只做任务 T-1002-15` |
| 06:29:41 | linda 收工时 `audit_unpushed` 判红（本轮唯一一处 U1），她开 `T-1002-18` 把它归因为「同一个 claim 下的第二个进程」 |
| 06:33 | 本档开工现场 `ps -p 48055`：`ELAPSED 08:26`，**活着**；`49467` 也活着。那棵树不是残留树，是**正在用的树** |

## 二、根因

**不是**「同一个 claim 下两个进程」（开单时的归因，已被实测推翻，见第七节）。

真正的那层：**一个工人要用的输入还没合进 main，而协议没给它一条合法的路。**
`T-1002-15` 要登记的权威源文件当时只在 linda 的分支上，于是这个 ops 工人自己去把
**别人的分支** checkout 进一棵新树、rebase、准备 push——它在替别人的任务收尾。

为什么闸看不见：

1. **第 5.5 步问的是「我这张单被别人收尾了吗」**，判据 `status != claimed`。本次两张单
   `status` 全程正确：`T-1002-15` 一直 `claimed`（它确实还在干），`T-1002-10` 到 06:28:47
   才变 `done`。两边都诚实作答，**问题是它问错了量**。
2. **「谁在改哪些文件」这个量，任务板从来没记过。** 工作树的归属只在磁盘上可见——
   `git worktree list` 看得到那一行，`.git/worktrees/<树名>` 的创建时间看得到先后。
   任务板没有这一维，所以任何建在任务板上的判据都盖不住它。
3. 树名里带的是**别人的**任务号。即使按开单时建议的判据（`git worktree list | grep <任务号>`）
   自查，这个工人 grep 自己的 `T-1002-15` 也是 0 行——**它从自己这一侧永远查不出来**；
   只有被越过的那条线（linda）grep `T-1002-10` 才看得见。所以光补「问磁盘」不够，
   还必须加一条**禁止**：不替别的任务号的分支收尾，树名只许带自己的任务号。

## 三、影响（量出来的）

**已确认受影响：0 字节内容损失。** main 的 `4712849d2` 在 06:28:47 前已落地，linda 的产出完整，
`T-1002-10` 的复核 PASS 仍成立。`audit_unpushed` 判红 1 处（U1：1 个只在本机的 commit），
那是本轮唯一一处违规。

**如果那棵树推上去了**（它基线 `afb93f157` 落后 main 1 个 commit，push 必被拒 →
按协议 `fetch + rebase` 一次 → 冲突仍在同一个公箱）。现场量 `git diff origin/main b9975e133`：
4 个文件、各 1 处。

| 文件 | 会发生什么 |
|---|---|
| `Fluxus_Brand/ops/material_inbox.md` | 这一处是 **-2 +1**：**删掉 main 上已有的两条素材行**（steve 10-02 那条 + linda 的终稿），换成 linda 的旧稿。diff 看起来只是「我改了一行」 |
| `data/research/audit_mutation_ledger.json` | `audit_tml.commit` 写回 rebase 前的 `e1d79e104`。这是**功能性字段**——`audit_mutation_sweep --show-ledger` 用它判新鲜度，指向一个不在 main 历史里的 sha，判词会从 `FRESH` 变 `UNKNOWN` |
| `audit_mutation_ledger_2026-10-02.md`、`night_reports/2026-10-02.md` | 文档引用回退到旧 sha |

**模式命中**：同一时刻机器上共 10 棵工作树（复核员实跑 `audit_unpushed`：
`0 violation(s), 9 warning(s) over 10 worktree(s)`）。只有这一棵的名字里带着**别人的**任务号。

## 四、修法

**已做**（fluxus-ops `fc21b7cd`）：

- `agents/_worker_protocol.md` 新增 **5.6 问磁盘**：`git worktree list | grep -F "{task_id}"`，
  排掉自己那棵后还剩行＝有第二棵树在做你这张单，先停下核对。两档判据：
  等价内容已在 main（`git cherry origin/main HEAD` 全是 `-`）→ `close … duplicate`；
  两边都没 push → **后建的那棵树让路**，先后用 `stat -f '%SB' .git/worktrees/<树名>` 定，
  同一秒则 HEAD sha 字典序小的留下。让路的一方不 push、**不删别人的树**。
- 新增 **5.7 永不替别的任务号的分支收尾**：要用的东西还没合进 main，三条路——
  等（`block` 写明等什么）· 转（`handoff` 给那条线）· 换做法。树名只许带自己的任务号。
- `tests/test_worker_protocol_text.py` 三条断言钉住正文（协议是纯 markdown，没有任何格式闸查它）。
  **它在修之前是红的**：对 `origin/main` 的协议三条全红；只把「后建的那棵树让路」一句换掉、
  其余都留着，恰 1 条红（`test_step_5_6_has_a_deterministic_yield_rule`）。两个方向都造过。

**欠条**：那棵树**没有删**。它属于活进程（`48055` / `49467` 正在里面跑测试），删它＝销毁别人
正在跑的活，也踩「永不在别人的 worktree 里工作」。清理挂在 `T-1002-21`（ops）：等 `T-1002-15`
收工后复查，若已空置则 `git worktree remove --force`；若那份内容真的推上了 main，同一张单
负责把被删的两条素材行追回去。

## 五、机制升级

- 「两个写者在改同一批文件、任务板看不出来」——这是**第 2 次**（第 1 次是 `T-0923-100`）。
  但**「闸的判据建在那次事故里不会变的量上」这个形状，是第 1 次**。三次律还差一次才升硬闸
  （代码层拒绝：建树时若树名含别人的任务号就拒），本次先给协议 + 文本断言。
- 可机器判的部分：5.6 是一条命令；5.7 的树名规则是一条 grep（树名里出现别人的任务号＝越线）。
  两条都不依赖「觉得自己在干嘛」。

## 六、教训

1. **这道闸问的那个量，在它要防的那次事故里变过吗？** `T-0923-100` 的特征恰恰是
   `claimed_at` / `first_claimed_at` / `status` 全程不变，而为它立的 5.5 问的就是 `status`。
2. **我手上这份活，涉及的文件归谁？** 任务板记任务号，不记文件。要用的东西还没在 main 上，
   那是「等 / 转 / 换做法」，不是「我顺手替他合了」。
3. **说「残留树」之前，先问它活着吗。** `ps -o lstart,etime -p <pid>` 加一条父链就看得出它是谁的。
   本次被判成残留的那棵树，当时正在跑 3265 条测试。
4. **别人树里的 commit message 与你逐字相同，不等于那是第二个你**——也可能是有人把你的分支
   拿去推。要分清这两件事，看的是那棵树的 `reflog` 第一跳（`worktree add` checkout 在谁的 sha 上）
   和跑在它里面的进程的父链，不是 commit message。

## 七、⚠️ 这份档推翻了开单时的归因 1 条

开单时写的是「**同一个 claim 下的第二个进程**在做同一张单」（`T-0923-100` 形状），
并据此建议把第 5.5 步改成按**自己的**任务号 grep 工作树。实测不成立：

```
$ ps -o pid,ppid,command -p 49467        # 跑在那棵树里的进程
49467 48055 /bin/zsh -c … WT10=…/wt-T-1002-10-finish; cd "$WT10"; … pytest …
$ ps -o pid,command -p 48055             # 它的父进程
48055 claude -p '… 你是 agents/ops，本次只做任务 T-1002-15 …'
```

那是 **`T-1002-15` 的工人**，不是 `T-1002-10` 的第二个工人。被推翻的那版仍然有价值——
它提出的「问磁盘」判据是对的，而且是本档 5.6 的来源；**但只有它不够**：
从越线那一方自查，grep 自己的任务号是 0 行（第二节第 3 条），所以才补了 5.7 那条禁止。
