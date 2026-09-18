---
name: failure-triage
description: 数据班没落地时的分诊：健康检查 → 查有没有 run 在飞 → 用 failure_class 判 A_infra/B_vendor/C_gate/D_code，照它说的做。凡任务 type=failure_triage 或 type=morning_check、或 dashboard 停在前一天、或 daily-data-update 这班红了、或 Andy 说「数据怎么还没到 / 昨天的数据不见了 / cron 又挂了」都用本 skill；C_gate 判出来之后接 data-recovery。
owner: alex
---

# failure-triage — 先分诊，再动手

职责只有一条（Andy 2026-09-04 亲定）：发现问题立即修复，直到修复成功为止，top priority，不设重试上限，不请示。

## ⏰ 死线：JST 08:30（Andy 2026-09-17 定，宪法「Dashboard 数据是早班的地基」）

Andy 原话：「Dashboard出现错误，一定要马上紧急修补，每天的很多事情都等着它上面的数据才能开始工作」「这些数据一定要准备好了这个时间点的优先级很重要的」。

- 最近完成交易日的数据必须在 **JST 08:30 前**落 main 并上线。09:00 每日复盘读 `data/history` 归档，数据没到就做不出。
- **JST 07:00 起**：正班还没落地且没有 run 在飞 → 已经是迟到状态，立刻分诊，INBOX 挂「⏰ 死线风险」行。
- **JST 07:30 之后仍未落地＝紧急修复**。backstop 排在 10:30 JST，已过死线，**不许等它**。
- **JST 08:00 起**是最后一道：到这里还没好，除了修，必须在 INBOX 写清「dashboard 停在哪天 · 卡在哪一步 · 谁来接」，并把接力挂到任务板上（见「转手」）。

## ⛔ 先读这一段（2026-09-04 事故换来的）

那晚哨兵重跑了五次。账本显示：**其中两班的数据本来是好的**（23:29 tradeable 2553、02:31 tradeable 2554，quality 都是 ok），它们只是被下游的闸挡住了。五次全量重拉把 runner 的机房 IP 从 429 打到 401 Invalid Crumb，可交易数归零，dashboard 停更两天——**而那两天的数据我们已经抓到过两次**。

> **闸拒了好数据时，重抓是错的动作。数据在手上，去修闸。**

在 CI 日志里这两种失败长得一模一样（都是红的 exit code 1），所以**不许靠肉眼分类**，用工具。

## 重跑窗口（依据是代码不是规矩：`pipeline/screeners/run_all.py`）

管线自己拒跑 **ET 04:00–16:15（交易日）**：那段时间拉到的是盘前/盘中实时价，不是收盘价。所以：

- **可发时段 = ET 16:15 起到次日 04:00 前**（周末全天可发）；换算 UTC 约 20:15Z–07:59Z。
- 其余时段不 dispatch，只做诊断＋告警，写明「下一个合法时段的班接力」。
- 发前 `TZ=America/New_York date` 自查；周六/日不受限。

## 一、健康检查（先做，健康就收工）

```bash
git log origin/main --grep='chore: market data' -1
```

拿最近落地 session；用 ET 算最近已完成交易日（周末/假日差一天算正常）。已追平 → 回「数据健康（session X）」收工。

主排程 cron 是 20:20Z（常迟 1.5–2.5 小时），backstop 01:30Z（常迟 4–5 小时）；正班还没到点时前一交易日在就算健康——**但 JST 07:00 起不再适用这条宽限**，见死线节。

## 二、不健康 → 查有无 run 在飞

```bash
gh run list --workflow=daily-data-update.yml --limit 3
```

有 `in_progress` → 轮询到 `completed`（每 90 秒，上限 40 分钟）再判。

## 三、分诊（必须用工具，不许肉眼判）

```bash
python3 -m pipeline.tools.failure_class --run-id <失败的 run id>
```

它读 `data/history/run_ledger.jsonl` 里那一班的读数，输出四类之一和唯一正确的下一步。**照它说的做。**

- **A_infra**（账本里没这班记录）→ 直接重跑。**说「丢了」之前先跑 `python3 -m pipeline.tools.audit_schedule_windows`**：窗口过了 600 分钟还没有 run 才算丢；没到 600 分钟只写「迟到中」。
- **B_vendor**（quality severe / 可交易崩塌）→ 上游真的没给回价格。**别立刻重跑**：全量重拉正是把 429 变成 401 的动作。隔班接力可以（换 runner 即换 IP），每班最多一发。
- **C_gate**（抓取正常，闸挡的）→ **绝对不要 dispatch。** 转 `data-recovery` skill（从 artifact 恢复，不重抓）。
- **D_code**（traceback）→ 不重跑。改代码、加一条能红的测试、合 main，再让下一班跑；死线前修不完就转手（见下）。

工具跑不起来 → 当 A_infra 处理，并在 INBOX 里写明「分诊器不可用」。

## 四、重跑（仅 A/B 类、且在可发时段内）

```bash
gh workflow run daily-data-update.yml
```

轮询到 completed（上限 40 分钟）。成功且 market data commit 落 main → INBOX append「✅ 已修复（run <id> · 第 N 班接力）」并 push。失败 → 本班到此，下班接力。

## 五、告警去重

写 INBOX 前 grep 今日「🔴 数据哨兵」行，已有不重写；仅类别/局面变化时追新行。格式：

```
- [MM-DD] 🔴 **数据哨兵**：<分诊类别> · run <id> · 已重试至第 N 班 · dashboard 停在 <日期> · <下一步>
```

append-only，push 被拒推分支 `sentry/alert-<日期>`。**类别一律抄分诊器给的那个键**（A_infra/B_vendor/C_gate/D_code）。

## 六、转手（本地工人版，不再挂门铃）

自己这班修不完、或要交给别的线：

```bash
python3 ~/Documents/fluxus-ops/tools/taskboard.py handoff --from <task_id> --owner <名> --type <type> --title "<一句话>" --body-file <文件>
```

要 Andy 拍板才能继续的：`taskboard.py needs-andy <task_id> --question "<一句话>"`。做不了的：`taskboard.py block <task_id> --reason "<一句话>"`。

## 收工

最终回复 ≤4 行中文：健康/不健康 · 分诊类别 · 动作与结果 · dashboard 停在哪天（JST 07:00/08:00 班加一句「死线状态：安全/风险/已破」）。要紧信息必须在 INBOX 行里。
