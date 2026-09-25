# 提案：共享主树上 `reset --hard` 与 `stash` 同罪

提出：DATA ALEX · 2026-09-25 · **未经 Andy 批准前不是规矩，任何会话不得引用**

## 起因（我自己干的）

2026-09-25 17:42 JST，我在 `~/Documents/fluxus-ops` 主树上跑 `git reset --hard` 对齐 origin/main，
把当时未提交的 `tools/daemon.py` · `tools/worker.py` · `tests/test_daemon.py` · `tests/test_worker.py`
一并清除。那是守护进程派出的 ops 工人正在做的 T-0925-74，工人会话的上下文随之消失，只能重做。
未提交内容不在对象库，reflog 恢复不了。事故档：私有仓 `audits/2026-09-25_alex_reset_hard_wiped_daemon_edits.md`（`0ec93a4`）。

## 现行宪法为什么没挡住

「Git 三铁律」第 2 条只写了 **永不使用 `git stash`**。而 `reset --hard`、`checkout -- <file>`、
`checkout <branch>`（带覆盖）对**别人未提交的改动**杀伤完全一样，甚至更彻底——stash 至少还能
`stash list` 找回来，`reset --hard` 一点痕迹不留。条文按**命令名**写，漏掉了同形状的其它命令。

## 提议的措辞（加在「Git 三铁律」第 2 条后）

> 2b. **共享主树上一切会丢弃未提交改动的命令与 `stash` 同罪**：`reset --hard` · `checkout -- <file>` ·
> `checkout/switch <branch>` · `clean -fd` · `restore` 无 `--staged`。判据不是命令名，是
> **「这条命令会不会让别人未提交的改动消失」**——会，就不在共享主树上跑。
> 要对齐 origin/main、要提交、要回退，一律在**临时树**里做（见「直推 main 的标准动作」）。
> 唯一例外：该改动确认是自己刚才造成的（如错误 reset 留下的回退痕迹），还原它是修复不是破坏。

## 为什么它不是「作者给自己发落地权」

按 09-08-31 那条利益冲突判据：这条规矩**只收紧、不豁免任何路径**，作者（我）是被约束方不是受益方，
与 `4ffda68a`（禁群发）同形状——为已发生的伤害而立。

## 配套（不属于本提案，已在别处进行）

OPS 开了 T-0925-79 修工具层：`taskboard` 的锁认 worktree、`finally` 不再把真异常吞成 KeyError、
`DirtyTree` 的报错改成指向「临时树 + `--repo`」这条正路。
他们的判断值得记进来：**当「主树脏」和「worktree 不可用」两条路同时堵死时，人就会去清主树——
这一下是设计缺陷的产物，不只是手滑。** 规矩堵动作，工具得给出路，两件都要做。

---

**2026-09-26 已采纳**（Andy 原话：「批」）。正文以 `CLAUDE.md` Git 三铁律第 2b 条为准；采纳时按提案里的两处建议改了措辞（例外写死成「逐个认领 git status 里的文件」、条文末尾直接给出临时树那条正路）。本文件留作过程记录。
