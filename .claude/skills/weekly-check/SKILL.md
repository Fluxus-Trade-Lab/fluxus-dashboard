---
name: weekly-check
description: 仓库周检——每周体检员，扫发布计分/本机心跳/远端分支堆积/契约盘点/门铃滞留/技能操作系统四个数/发布闸误伤，产出一份中文报告落 data/research/repo_health/。凡任务 type=weekly_check、或班次 ops-weekly-check 触发、或有人说「跑一次周检 / 仓库这周怎么样 / 周检报告在哪 / 契约盘点一下 / 技能触发率怎么样」都用本 skill，别重新发明六节判据。
owner: ops
---

# weekly-check — 仓库周检

你是 Fluxus Dashboard 仓库的每周体检员（原云端「仓库周检」routine 适配本地守护进程，2026-09-19 迁入；在 `~/Documents/AI-Trading-System` 的临时 worktree 里跑）。先读仓库根的 CLAUDE.md、TEAM.md 和 NOW.md，然后做下列各节并产出一份中文报告。

## 要做什么

零、发布计分（报告第一节）：读 data/content/posts.csv，统计过去 7 天对外发帖数、最长连续断更天数；对照 NOW.md 本周主线写一句判断。posts.csv 无本周数据就写出最后一行的日期——缺数据本身是最响的警报。

零点五、本机心跳（你是唯一能报「整台 Mac 静默」的哨兵）：本地定时任务都要往仓库留痕，查三处最后更新日期：① data/research/night_reports/ 最新晚报（含 origin/auto/night-* 分支）= 夜间研究班心跳 ② 任务板 `agents/*/runs/` 里各线最近一次 run 记录 = 各定时班心跳 ③ posts.csv 最后行 = Steve 回填心跳。任一超过 3 天无痕 → 写进摘要第二行「⚠️ 本机任务痕迹缺失：<谁> 自 <日期> 无产出，可能守护进程未跑或任务卡批准」。

一、远端分支堆积体检：`git fetch origin && git branch -r` 列出所有远端分支；对每条算 (a) 是否已合入 origin/main（merge-base --is-ancestor）(b) 最后 commit 距今天数。分类：已合并可删 / 超 14 天未动且未合并（列名字+主题）/ 活跃。标出 wip(archive) 与 archive/* 数量。只报告不删。

二、契约盘点：读 data/reference/DATA_CONTRACTS.md §七/§八，对每条未勾行用全仓 grep 按成分核实，分类：已落实（证据文件+行号）/ 未落实仍有效 / 事实已过期。行内注明「在别的仓库」的按注释处理。**另查：上周报告里存在的未勾行这周还在吗？消失了又没 ✅ 痕迹的，按「删行事故」报。**

二点五、门铃滞留（存量清尾，见 CLAUDE.md「通信＝任务板」，不再往 INBOX 追提醒行）：`python3 -m pipeline.tools.doorbells --older-than-hours 168` 列出超过 7 天没人取的门铃（光 grep pending 会把已办的也数进去，办没办看行下的 `↳ ✅`）；写进报告。列出的每条按收件线开一个任务板单：`python3 ~/Documents/fluxus-ops/tools/taskboard.py new --owner <线> --type followup --title "门铃滞留：<一句话>" --body-file <文件>`，正文里的 `## 验收` 记下这条门铃在 INBOX.md 的行号（或行内日期+收件线定位）与开出的 task id，方便回查——不再直接改动或追行 INBOX.md。

三、技能操作系统四个数：跑 `PYTHONPATH=. python3 -m pipeline.tools.skill_health`，把它打印的三个数抄进报告——自建 skill 数、有评估集的 skill 数、最近一次 benchmark 的 delta。
**delta 怎么读看 `docs/superpowers/verdicts.md`**：code-cartography 那个 1.0 量的是「照没照单子做」，不是「答案更好」——别当质量指标引用。
第四个数你自己数：过去 7 天各任务书的收工回复里 `skill-used:` 与 `skill-skipped:` 的行数比（从 INBOX 与各线 commit 里能看到的那些）。
**触发率**：读各 `.claude/skills/*/evals/trigger_results.md`，留出 recall 低于 80% 的逐个点名。vercel-ops 09-13 实测留出 recall 17–25%、precision 100%——量具有局限（空白目录、临时 command、不测 `paths:` 触发）：**下一步先换量具（在本仓库目录里跑、用真实会话回放）再改描述，换量具之前不改描述**。报告里写：换了没有、recall 多少。
**闸：有评估集的 skill 数 < 自建 skill 总数 → 🔴。** 红线格式：`- [MM-DD] 🔴 **技能体系欠账**：自建 N 个，只有 M 个有评估集 · 缺的是 <名字>` append 进 `data/research/night_reports/INBOX.md` 并 push。这是「不改报告之外的文件」的例外之一，只允许 append，永不改别人的行。

四、发布闸误伤扫描（同形坑三次律：walled 08-28 / no-baseline 09-04 / shortlist_feedback 09-11）：
`grep -n 'ledger\.error(' pipeline/screeners/run_all.py`（及 pipeline/ 下其他调用 ledger.error 的文件，全仓 grep）逐条核对：**判据＝「这是产出模块自身的失败，还是外部依赖（GAS/Sheets/vendor API）打嗝？」** 前者该 error（真缺陷该拦发布）；后者必须是 `ledger.note(..., WARN 词)`（打嗝不拦发布）。基线（2026-09-12 首扫，OPS 判定合理）：run_all.py 共 6 处——breadth/asset_signals/market_light/shortlist 四处模块自身 try/except（留）+ no_downgrade blocked / universe_quality severe 两处闸保护（留）。**报告只列相对基线新增或变更的调用点**，新增里凡外部依赖打嗝记成 error 的 → 🔴 append INBOX 点名（格式同技能欠账行），并注明参考修法 commit 8fb4ec76。

报告写入 data/research/repo_health/YYYY-MM-DD.md（当天日期；摘要 ≤6 行——第一行发布计分、第二行心跳；再各节明细，全文 ≤110 行）。commit `health: 每周仓库体检 YYYY-MM-DD` ——按 `_worker_protocol.md` 第 5–6 步：在自己的临时树提交、推分支、算 gate，gate=none 才自合，reviewer 就等复核。除上面点名的 INBOX 例外，不改报告之外的文件，不动 §七 原文。

## 红线

不发任何消息；不删分支、不改契约原文、不改门铃原行（只 append）；只在临时工作树里改文件，主树不动。

## 验收

- [ ] `data/research/repo_health/YYYY-MM-DD.md` 已产出，摘要 ≤6 行、全文 ≤110 行，六节齐全
- [ ] 契约盘点做了「消失未打勾」核查；技能欠账闸与发布闸误伤扫描按基线只报增量
- [ ] 触及的 INBOX append（技能欠账红行/发布闸误伤红行）均只追加不改原行；门铃滞留改开的任务板单已逐条核实 `taskboard.py list --owner <线>` 能看到；commit 已核实在 origin/main

## 出处

正文原文迁自 `schedule.json` 班次 `ops-weekly-check` 的 `body` 字段（该班次已 done 3 次，做法只活在 schedule body 里，T-0919-29 / T-0921-16 / T-0928-12 因此各重写了一遍；T-0928-32 迁完后 schedule body 改成指向本 skill 的一句话，不再重复正文）。
