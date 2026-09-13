# Vercel 部署存储周检台账

写入方：定时任务 `vercel-storage-weekly`（DATA ALEX，每周一 09:20 JST；Andy 2026-09-13「Vercel 用量台阶改成每周一次检查」）。
每周追加一行，不改旧行。口径、判断闸、预期台阶见 [`.claude/skills/vercel-ops/SKILL.md`](../../../.claude/skills/vercel-ops/SKILL.md)。

- `storage_gb`：控制台 Usage 的 Deployment Storage 读数；取不到留空，notes 写原因，**不拿上周的数顶替**
- `active_deployments` / `pages` / `stop_reason`：`/api/v6/deployments` 翻页结果；停因不是 `next null` / `empty page` 时总数可能被截断
- `oldest_utc_day` / `newest_utc_day`：按 UTC 日分组（`toISOString()`），不是交易日
- 拉响条件只有三条（写在任务书里）：生产站 503/DEPLOYMENT_PAUSED；10-12 之后仍 ≥120 GB（自设线）；10-26 之后连续两周 <10 GB（可停周检）
