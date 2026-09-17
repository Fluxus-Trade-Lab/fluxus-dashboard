# 谁在等 Dashboard 的数据（2026-09-17 盘点）

> Andy 09-17：「查看哪些工作需要调用这些数据，如果出错，是否有backup方案。」
> 规则本体在根 `CLAUDE.md`「Dashboard 数据是早班的地基」。本页是依赖清单，机制变化时更新。

**时间一律 JST。死线 08:30。**

| 工作 | 时间 | 读什么 | 数据没到 / 出错时现在会怎样 | 备用方案 | 状态 |
|---|---|---|---|---|---|
| 数据夜间班 `daily-data-update` | 05:20 正班 · 10:30 backstop | 生产 `data/output` + `data/history` | GitHub cron 常迟 102–153 分（正班）、269–295 分（backstop）；闸红时只把 `data/output` 存成 artifact | 哨兵分诊后走 artifact / 隔班接力 | ⚠️ backstop 已过死线；artifact 不含 `data/history` |
| 数据哨兵（云，`trig_01QCuAfFpqtYivKM5bbHwEws`） | 每 2 小时整点 + 07:00、08:00 专守死线 | run 列表、账本、`data/output` | 能分诊；**云端下载不了 artifact**（出口策略 403），09-17 因此违规 dispatch 撞上供应商冷却 | 取不到 artifact → 门铃交本机会话 | ⚠️ 任务书待改 |
| Plumber Joe 晨检 | 07:20 | cron、归档、各页 | 正班常在它之后才落地；09-17 的失败在 08:23，晨检早已结束 | 哨兵 08:00 班接力 | ⚠️ 时间对不上 |
| 每日复盘 `recap-daily` | 09:00（周二至六） | **`data/history` 归档**（按交易日取）＋ `data/output` 少量 | 数据未到每 15 分钟重试到 10:15；只修好 `data/output` 仍做不出；修好后**不会自动重跑** | 修复完成后由修复者手动 `run_scheduled_task recap-daily` | ❌ 缺自动重跑 |
| 每日页（云） | 10:07 | 仓库各台账 | 不依赖市场数据 | — | ✅ |
| 盘前摘要 `premarket-digest`（发 Discord 会员） | 21:00 / 22:00 | `data/output/universe.json` | **不核对数据日期**，旧数据照样挑票推给会员 | 应加日期闸：非最近完成交易日 → 不推候选、改发「数据延迟」 | ❌ 对外风险最大 |
| Andy 盘前看 dashboard | 晚间 | `data/output`（Vercel 原样发布） | 部分页面（breadth 等）有过期提示，没有全站提示 | — | ⚠️ 部分 |
| 周复盘 `recap-weekly` | 周日 10:00 | 归档 | 同每日复盘 | 同上 | ❌ |
| Steve 周结算 | 周日 20:00 | `groups_archive` | 有日期闸：归档不是最近交易日就跳过技术段 | ✅ | ✅ |
| Nighty Zac 夜班 | 04:30 | 归档（研究） | 不赶时间 | — | ✅ |

## 待补的机制（09-17 派出）

1. **盘前摘要加日期闸** → DATA ALEX。
2. **闸红时连 `data/history` 一起存 artifact**（09-17 缺这个，ALEX 只能按输出逐字节核对重建 17 个归档）→ DATA ALEX。
3. **哨兵任务书**：取不到 artifact 立即挂门铃给本机会话；07:30 未落地即紧急修复；修复后提醒重跑复盘 → OPS（本线的云端班）。
4. **正班不靠 GitHub cron**：05:20 由哨兵主动 dispatch，cron 保留作兜底 → 待 DATA ALEX / Plumber Joe 评估防重复闸后再定（Andy 未批，只是提议）。
5. **修复后自动重跑复盘** → 规则已写；自动化待定。

## 09-17 实例（为什么有这页）

09-16 正班 08:23 JST 失败（C_gate：OPS 删 `sentiment.json` 漏查 schema_snapshot 基线）→ 09:05 复盘发现数据没到 → 09:35 哨兵分诊，云端取不到 artifact，违规 dispatch 被供应商拒 → 10:04 OPS 本机取 artifact 恢复 `data/output`（`27883a92`），10:05 线上显示 09-16 → DATA ALEX 按输出重建 17 个归档（`739e6c4b`，0 违规）→ 复盘重跑。
