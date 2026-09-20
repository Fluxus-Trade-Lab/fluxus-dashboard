# 会员抵扣码发放 · 名单口径 + 流程（T-0921-04）

Andy 2026-09-20/21 定：不给公开折扣，只给现有付费会员「会员费抵扣」，抵扣额＝各档月费；affiliate 保持 0（原话「AFFILIATE也是0，不分享收入」）。库存维持 0 in stock，等他确认内容齐、开始宣传再放开（原话见 `whop_launch_checklist_2026-09-25.md` 第 2 条）。

## 三个码（OPS 09-21 00:45–00:49 JST 已在 Whop 后台建好，均 Active，无过期日）

| 码 | 抵扣 | 限制 | 发给谁（档位·月费·人数） |
|---|---|---|---|
| `MEMBER-CREDIT-99` | $99 off | 只对 Masterclass $1,499 方案 · 每人一次 | Premium Membership，$99/月，11 人 |
| `MEMBER-CREDIT-119` | $119 off | 同上 | Premium++ Members Access，$119/月，7 人 |
| `MEMBER-CREDIT-149` | $149 off | 同上 | Premium++ Members Access，$149/月，1 人 |

购买入口：`https://whop.com/checkout/plan_8RfO9OFDQdVUV`（课件 paywall 页已指向它）。

## 排除名单

已买过 Masterclass 的 **15 人**（`whop_launch_checklist_2026-09-25.md` 里的「15 人徽章」同一批）不用再发码——他们不用买第二次。

## ⚠️ 名单产出卡在这里（本条待接）

按上表把「邮箱 → 该发哪个码」做成表，需要在 Whop 后台按这三档现场导出客户名单，再按邮箱/Discord ID 核对排除那 15 人——这是本仓库既有 SOP（见 `README.md`「名单导出 SOP」）里写明必须**人在场操作后台**的一步，本次任务是无浏览器/API 权限的后台工人（`config.json` 未挂 WebFetch），做不了这步，已 `block` 转交。

**真正接手时请注意两条硬规矩（README.md PII 政策，已写死）**：
1. 邮箱/姓名/单人消费明细**永不进这个仓库的已跟踪目录**（本仓库 public，见 `project_repo_is_public` 记忆）——「邮箱→码」这张真实名单只能落 `data/growth/private/`（已 gitignore），文件名建议 `member_credit_roster_2026-09-21.csv`。
2. 本仓库里公开可跟踪的部分到此为止：三档人数、码、限制、排除口径——都已经是聚合数，已经在上表。**不要把上表之外的任何个人字段提交进 `data/growth/`**。

## 用量监控（发码后按天看）

Whop 后台每个码有 `uses` 列。执行者从发码当天起，每天看一眼三个码的 `uses`：
- 正常：每人最多用一次，累计不超过 19（11+7+1）。
- 异常（同一码短时间内被大量使用、或 uses 超过对应档位人数）→ 立刻报 OPS。
- 7 天后把汇总（每码累计 uses，不带个人身份）写进 `data/growth/metrics.csv` 或本文件续行，不落个人明细。

## 发布日清单已同步更正

`whop_launch_checklist_2026-09-25.md` 第 1、2 条已按现状改：可见性闸已过期（档位现在是 Visible），**真正也是唯一的闸是 Stock=0**，且这一步只有 Andy 本人点。
