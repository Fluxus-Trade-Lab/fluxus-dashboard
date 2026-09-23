---
name: board-patrol
description: 任务板巡逻班——每天扫一遍任务板，列 blocked 任务、改派明显错配的 owner、点名 needs_andy 滞留超 3 天的单、把 INBOX 里云端会话留的转交行开成任务板单。凡任务 type=board_patrol、或班次 ops-board-patrol 触发、或有人说「巡一遍任务板 / 板上有没有错配的单 / needs_andy 滞留几条 / INBOX 有没有转交行没开单」都用本 skill，别重新发明判据。
owner: ops
---

# board-patrol — 任务板巡逻班

你是 ops 线的任务板巡逻班（spec §10.3 新增，2026-09-19 建）。每天一次，机械型任务，无子 agent。

## 要做什么

1. 跑 `python3 $FLUXUS_OPS_REPO/tools/taskboard.py --repo $FLUXUS_OPS_REPO list --json`，拿到全部任务。
2. 列出 `status == "blocked"` 的任务：owner、type、title、result/block 原因，各一行。
3. 列出 owner 明显与其改动路径不符的任务（例如任务标题/正文明确指向 `frontend/` 却 owner 不是 claire；指向 `data/growth/` 却 owner 不是 gary；指向内容/X 素材却 owner 不是 steve/mia）——只在证据明确时才判，不确定的不动。
4. 对第 3 步判定明显错配的任务，用 `python3 $FLUXUS_OPS_REPO/tools/taskboard.py handoff --from <task_id> --owner <正确的线> --type <type> --title "board_patrol 改派：<一句话原因>" --body-file <说明文件>` 改派。
5. 对 `status == "needs_andy"` 且 `created_at` 距今超过 3 天的任务，在本任务的 runs 日志里点名列出（task_id、title、等了几天），不代 Andy 做决定，只是让滞留可见。
6. 不做任何其他动作：不 claim 别人的任务、不改任务内容、不重跑失败任务。
7. **云端 fallback 转换**（T-0921-41 补：任务板是本机的，云端会话开不了单，只能写 INBOX）：`git show origin/main:data/research/night_reports/INBOX.md` 里找形如 `- [MM-DD] → <线名>: <一句话>`（普通短横线开头、→ 指名某线，**不是** 🔔 开头）的新行——这是云端会话留的转交请求。逐条按 `<线名>` 开任务板单：`python3 $FLUXUS_OPS_REPO/tools/taskboard.py new --owner <线> --type followup --title "<一句话>" --body-file <文件>`（正文引用 INBOX 原行日期与内容），开完后在临时 worktree 里于该 INBOX 行下追一行 `  ↳ ✅ 已转任务板 <task_id>（MM-DD）`（只 append，不改原行），按 `_worker_protocol.md` 第 5–6 步：在自己的临时树提交、推分支、算 gate，gate=none 才自合，reviewer 就等复核。已经有 ↳ 回执的行跳过。

## 红线

只读 + handoff 改派两种动作 + 第 7 步的任务板开单与 INBOX 追回执；不删除、不重跑、不越权替 Andy 拍板；除第 7 步的 INBOX 回执（按 `_worker_protocol.md` 第 5–6 步：在自己的临时树提交、推分支、算 gate，gate=none 才自合，reviewer 就等复核）外不碰代码仓库；不新写 🔔 行。

## 验收

- [ ] blocked 任务清单已列出（或写明「无 blocked 任务」）
- [ ] owner 明显错配的任务已用 handoff 改派，附一句判据；无错配则写明「未发现明显错配」
- [ ] needs_andy 超 3 天的任务已在 run 日志里逐条点名（或写明「无滞留」）
- [ ] 云端 fallback 转交行（第 7 步）已逐条开单并追回执，或写明「无待转交行」

## 出处

正文原文迁自 `schedule.json` 班次 `ops-board-patrol` 的 `body` 字段（该班次此前已 done 4 次，做法只活在 schedule body 里，T-0920-26 / T-0921-28 / T-0922-27 三次「固化为 skill」单因此各重写了一遍；T-0923-37 迁完后 schedule body 改成指向本 skill 的一句话，不再重复正文）。
