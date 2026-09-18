---
name: data-recovery
description: 数据班被闸拦下（C_gate）后，从 GitHub artifact 恢复 data/output 与 data/history，不重抓。凡任务 type=data_recovery、或哨兵/failure-triage 分诊结果为 C_gate、或 Andy 说「dashboard 停在前一天/数据没落地/数据抓到了但没上去」都用本 skill。
owner: alex
---

# data-recovery — 数据在手上，去修闸

前提：`failure-triage` 已经用 `python3 -m pipeline.tools.failure_class --run-id <id>` 判出 **C_gate**（抓取正常，是下游的闸挡的）。

> **闸拒了好数据时，重抓是错的动作。**（2026-09-04 事故：五次全量重拉把 runner IP 从 429 打到 401 Invalid Crumb，可交易数归零，dashboard 停更两天——而那两天的数据我们已经抓到过两次。）

⛔ **这条路径全程不 dispatch、不碰 Yahoo 一次。**

## 一、取 artifact

```bash
gh run download <run_id> -n data-output-<run_id> -D /tmp/recovered
```

本机跑有出口权限，下载正常。（云端班曾因出口策略 403 取不到，那是云端限制，本机不适用。）

下载仍然失败时：**不许退化成 dispatch**——2026-09-17 那一班就是这样违规重抓，撞上供应商冷却，白烧一班。改走「转手」：

```bash
python3 ~/Documents/fluxus-ops/tools/taskboard.py needs-andy <task_id> --question "C_gate · run <id> · artifact data-output-<id> 取不到，是否授权换路径恢复（死线 JST 08:30）"
```

或 `taskboard.py handoff --from <task_id> --owner <名> --type data_recovery --title "<一句话>" --body-file <文件>` 交给能取到的那条线。

## 二、三方比对后放回

拿到数据后，按三方比对决定每个文件放不放回：

1. 这次 run 的 base commit 上那份
2. artifact 里那份
3. 当前 `origin/main` 上那份

放回 `data/output/`（同日的归档放回 `data/history/`），然后：

```bash
python3 -m pipeline.tools.audit_archives
```

**修掉它报的那一条**（只修那一条，别顺手改别的），重审到 **0 violations**。

## 三、提交

按宪法「直推 main 标准动作」提交：临时工作树基于 `origin/main`、只 `git add` 指名文件、提交前 `git diff --cached --name-only` 数一遍、push 后 `git log origin/main -1 --oneline` 看到自己的 commit 才算送到。

⛔ 永不在共享主树 `~/Documents/AI-Trading-System` 上 commit；永不 `git add -A`。

## 四、修好 ≠ 修完（宪法三件事，缺一件就写明缺哪件、交给谁）

1. **归档补齐**：`data/history/` 同日归档补齐，`audit_archives` **0 违规**。
2. **被错过的复盘**：当天 JST 09:00 的复盘如果已经错过，先 `list_task_runs recap-daily` 看原班是否还在跑（09-17 教训：以为放弃了就手动重跑，造出两个写者）；确实没跑就重跑，或用 `taskboard.py handoff --owner ops --type daily_recap` 转给 ops。
3. **核线上**：
   ```bash
   curl -s https://fluxus-dashboard.vercel.app/data/output/watchlist.json | head -c 400
   ```
   看日期。取不到就写「线上未核」，**不写「已恢复」**。

## 五、告警与留痕

INBOX 行写完整：`dashboard 停在哪天 · 卡在哪一步 · 已恢复到哪个 session`。同日同类别不重写，仅局面变化时追新行。

## 收工

≤4 行：分诊类别 C_gate · artifact 取到没 · audit_archives 违规数 · dashboard 现在停在哪天 + 线上核没核。
