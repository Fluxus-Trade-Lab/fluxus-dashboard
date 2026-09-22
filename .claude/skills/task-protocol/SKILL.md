---
name: task-protocol
description: 任何会话开工、Andy 派活、Andy 说以后这样做、Andy 回 y/n/加/不做 时用。凡是这一轮里出现「我该干什么」「这件事归谁」「以后都这样办」「这个先别做」「批了」「加进去」，或者你要把一件活交给别的线、要给 Andy 留一个待拍板的问题——先读本 skill，按任务板的命令落盘，别只在对话框里答应。
owner: ops
---

# task-protocol — 交互会话的任务板规矩

任务板是 `~/Documents/fluxus-ops`（私有仓）里的 `tools/taskboard.py`。子命令只有这些：
`new` · `list` · `claim` · `done` · `needs-andy` · `block` · `close` · `review` · `gate` · `handoff` · `reap` · `andy`。

## 一、开工

```bash
python3 ~/Documents/fluxus-ops/tools/taskboard.py list --owner <自己> --status open
```

先看名下有什么，再问自己要不要开新活。领一件：

```bash
python3 ~/Documents/fluxus-ops/tools/taskboard.py claim <id> --by chat
```

`--by chat` 表示这件活由交互会话自己做，不是守护进程派给工人的。

### ⚠️ 自己做或派子 agent 去做之前，**先 claim，再动手**（Andy 2026-09-22：「把这个 claim 规矩写进协议」）

凡是交互会话决定接手任务板上的一件活——**自己做，或用 Agent 工具派一个子 agent 去做**——第一步都是：

```bash
python3 ~/Documents/fluxus-ops/tools/taskboard.py claim <id> --by chat
```

**然后**才开写、才派子 agent。顺序不能反。

为什么：守护进程每 60 秒拉一次板，看到 `open` 的单就派工人。交互会话不 claim，守护进程就不知道已经有人在做，同一件活会被**两个写者**并行做完。09-21 连出两次：T-0921-32（主树提交钩子）和 T-0921-34（按类型复核）都被 OPS 派的子 agent 和守护进程的工人各做了一遍，第二次还在重启时被重新领走，只能靠关单止损。

- `--by chat` 的领单**不会被 reap 收回**（Ruling 58），所以长时间的交互工作放心 claim，不用担心三小时后被转给工人。
- 派子 agent 时，把任务号写进它的提示词，并让它**不要**再 claim / done——收尾由派它的交互会话来做（`done` 或 `close`），免得两边都去改同一张单的状态。
- 做完一定要 `done` 或 `close`；claim 了不收尾，这张单会一直挂着 `claimed`，没人再碰它。

## 二、Andy 说「以后这样做」

这是规矩，不是一次性的活。**逐字**写进自己的 `~/Documents/fluxus-ops/agents/<name>/ROLE.md`（或 `agents/<name>/memory/`），附他的原话与日期，每条末尾用括号注明出处，然后 push fluxus-ops。

- 只活在对话框里的裁决等于没定——下一个会话读不到它。
- 写的是他说的那句，不是你的转述。转述可以加在后面，原话不许改。

**对公共 skill 的纠正**（他改的是某个 skill 的做法，不是你这条线的习惯）→ 不要自己去改别人的 skill，开一件任务给那个 skill 的 owner：

```bash
python3 ~/Documents/fluxus-ops/tools/taskboard.py new --owner <skill owner> --type skill_fix --title "<一句话>"
```

任务正文里附他的原话。

## 三、Andy 回一个字

- 他批了、让你继续：把原话记进那件任务 —— `taskboard.py andy <id> --quote "<原话>"`，然后由执行者跑 `taskboard.py done <id> --result <sha> --tests-passed`。
- 他说不做、作废：`taskboard.py close <id> --by andy --note "<原话>"`。
- 你需要他拍板才能往下走：`taskboard.py needs-andy <id> --question "<一句话>"`——问题写成一句话＋一个字的选项（y/n、A/B），别出问卷。
- 你做不了：`taskboard.py block <id> --reason "<一句话>"`。
- 该给别的线：`taskboard.py handoff --from <id> --owner <名> --type <type> --title "<一句话>" --body-file <文件>`。

## 四、他派新活

```bash
python3 ~/Documents/fluxus-ops/tools/taskboard.py new --owner <该线> --type <type> --title "<一句话>"
```

**当场落盘**，并在回复里一句话确认「已转给〔线名〕」。永不叫 Andy 去别的会话说——让他换窗口＝事故。

## 五、收工自查

```bash
git -C ~/Documents/fluxus-ops diff --stat HEAD~5
```

看本轮的裁决有没有真落进 ROLE.md / memory / 任务文件。看不到就是没落盘，补完再收工。

## 附：审核与合并相关

`gate <id> --worktree <路径>` 算这件改动该走哪道闸（none / reviewer / andy）；`review <id> --verdict PASS|FAIL --evidence-file <文件>` 写审核结论（判词按 `branch-review` skill 出）；`reap --max-hours <N>` 回收挂死的认领。交互会话派聊天复核员时，每轮判词用 `taskboard.py review <id> --verdict <PASS|FAIL> --record-only --evidence-file <文件>` 登记（T-0922-34：只写 `review_log` + 一条 commit，不改 status/attempts/claimed_at，metrics 否决率照样计入）。

- 任务板命令在工作树有未提交改动或未推送提交时会拒绝执行（DirtyTree）；先提交推送或丢弃再用。
