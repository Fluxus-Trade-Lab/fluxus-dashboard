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

`gate <id> --worktree <路径>` 算这件改动该走哪道闸（none / reviewer / andy）；`review <id> --verdict PASS|FAIL --evidence-file <文件>` 写审核结论（判词按 `branch-review` skill 出）；`reap --max-hours <N>` 回收挂死的认领。
