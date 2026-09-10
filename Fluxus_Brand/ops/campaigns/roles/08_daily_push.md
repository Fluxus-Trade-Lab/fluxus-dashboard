# 日推

**owns**：每日 09:25 备稿 `data/content/today_draft.md`（C1/C2/C3 三段），供老板早报内联。

> ⚠️ 本文件是 reads 镜像，不是任务书。权威任务书在 `~/.claude/scheduled-tasks/steve-content-daily-push/SKILL.md`（repo 外，
> 由 update_scheduled_task 管理）。**改任务书第 1 步的读取清单时必须同步本段**——立此镜像正是为了让
> `audit_reads_declarations` 闸能查到「谁读：日推」的另一头（2026-09-11，Steve 转交件遗留：「查不了 1」销账）。

**reads**：
- `Fluxus_Brand/ops/campaigns/`（最新 campaign 卡的 `RECORD.md` status）
- `data/content/today_draft.md`（昨日份，覆盖前读回）⚠️ 读 `git show origin/main:` 权威版（机器整份覆盖直推；主树是更长的**旧**稿，别被行数骗）
- `data/content/posts.csv`（昨日读数）⚠️ 读 `git show origin/main:` 权威版
- `Fluxus_Brand/voice/verdicts.jsonl`（近 7 天判决）⚠️ 读 `git show origin/main:` 权威版（机器 append 直推；09-11 实测主树 1 行 / main 9 行——读主树＝判决账拿到 11%）
- `Fluxus_Brand/brain/x.md`（七入口菜单）⚠️ 读 `git show origin/main:` 权威版
- `Fluxus_Brand/voice/raw/`（Andy 口述）⚠️ 读主树工作区（五件套同族例外）
- `Fluxus_Receipts/receipts.md`（待兑现项）⚠️ 读主树工作区（五件套）
- `Fluxus_Brand/ops/campaigns/PIPELINE.md` 顶部维修令（判断维修期条款是否生效）
- `NOW.md`（优先级）⚠️ 读 `git show origin/main:` 权威版（`now:` 班次写；09-11 移出主树例外）
- `Fluxus_Brand/ops/Fluxus_Week_Plan.md` 与 `Fluxus_Brand/ops/Fluxus_Queue.md`（**用 ops/ 下这两份完整路径**——根目录同名文件是 08-02 死档）⚠️ 基准暂按宪法五件套例外读主树，**收窄提案已交 Andy**（09-11 实测两份的写者均为 Steve 周检机器、main 更新）

**writes**：`data/content/today_draft.md`（整份覆盖）· `data/content/posts.csv` 回填 · 均走直推 main 标准动作。
