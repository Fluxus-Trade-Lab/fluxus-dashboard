# 2026-09-15/16 · 周用量上限把整个联邦静音了约 30 小时，而静音本身没人报

**写者**：Plumber Joe（09-16 21:30 JST，晨检重跑班）· **状态**：已自愈（12:00Z 重置），机制缺口待 OPS 认领

## 发生了什么

- 云哨兵 `trig_01QCuAfFpqtYivKM5bbHwEws` 每小时照常开火（`list_runs` 每小时一条），但每班 13 秒就结束。
  run log 原文：`rate_limit: rejected (seven_day) resets_at=1789560000` → `You've hit your weekly limit · resets 12pm (UTC)`（1789560000 = 2026-09-16 12:00Z）。
- 最后一条有产出的哨兵 commit：`62245b8c` 2026-09-15 05:17Z。此后 main 上**零 Claude commit**，直到 12:00Z 重置。
- 同一时段受影响（同一账号的周额度）：本机 Joe 晨检（09-16 07:26 JST 班）、Zac 夜间自学（09-16 04:31 JST 班，main 上无 09-16 晨报/分支）、Discord→X 云生成端（09-15 22:40Z 班，main 无 09-15 草稿）、Fable 老板每日页（09-16 01:07Z 班挂起到 12:16Z 才开始干活）、每日复盘/内容日推等本机班。
- **没受影响的**：GitHub Actions 数据管线本身。09-15 场 run `35033478086` 22:57Z 起、23:17Z 落地 `88295474`，audit_archives 0 违规。数据是好的，只是没人看。

## 为什么值得一个档

1. **所有报警者和被报警对象共用一个额度**。哨兵、Joe、Zac 全部跑在同一个周额度上——额度耗尽时，能报「额度耗尽」的人正好全体失声。这是 `pitfall_my_gate_had_no_resolution` 的同形：闸和它要量的东西被同一个原因压住。
2. **失败方向指向绿色**：run 的 `result` 是 `success is_error=true`，调度器列表里每班都「有一条」，`list_task_runs` 里本机班是 `succeeded`。只看「开火没」全绿。
3. 如果 09-15 场数据管线红了，这 30 小时里没有任何会话会去修——哨兵的「不设重试上限，立即修复」在额度面前是空话。

## 判据（给下一个看到「一片安静」的人）

安静 ≠ 健康。哨兵在健康时**每班都 commit**（09-14 全天逐小时有 `sentinel(...)` commit）；main 上 `--grep='^sentinel'` 断档 >2 小时，先 `RemoteTrigger get_run_log` 看最近一班，找 `rate_limit`。

## 待认领（OPS Fable：用量/调度归 OPS）

- ① 一个**不耗 Claude 额度**的心跳：例如 GitHub Actions 里一个小 job，检查 main 上最近 `sentinel(` commit 距今 >3 小时就开 issue / 失败（Actions 失败会发 Andy 邮件）。这是唯一一个在额度耗尽时还能出声的通道。
- ② 额度预算：是哪些班把周额度烧完的？（哨兵每小时一班 × 24 × 7 是固定大头之一；健康时「无新动作」也跑完整流程。）是否把哨兵健康班改成先跑一条便宜的 shell 判断再决定是否起模型——这是 Andy 级决定（涉及花钱/套餐）。
