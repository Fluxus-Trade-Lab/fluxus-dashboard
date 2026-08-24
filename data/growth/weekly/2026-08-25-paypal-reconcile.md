# PayPal 对账（2026-08-25，Andy 提供导出）

**结论：Lifetime 会员 = 7 人，每人恰好一笔 $3,399，合计 $23,793 毛收入。「有人分期两次」不成立**——唯一的双笔是同日重复付款、当天已全额退款（PayPal 备注 duplicated payment）；另一笔是 Pending→Completed 的同一交易。

- 另有 Masterclass 经 PayPal（Whop 代扣）2 笔 × $584.10 = $1,168.20（2025-11/12）。
- 与 Whop 名单 email 对照：7 个 lifetime 里 **4 人对上**（含 Discord 名），**3 人 PayPal-only**；其中 1 人经同 handle 双邮箱推定对上（待 Andy 点头合并），1 人与 Whop 某 canceling 会员仅同姓（**待 Andy 确认是否同人**），其余 2 人在 Whop 无迹。
- 总名单（含姓名/邮箱/Discord/档位/active-expired 分类/付款记录）：`data/growth/private/members_master_2026-08-25.csv`（43 行，PII 不入公共仓库）。
- 分类汇总：Lifetime 7（active）· Whop 档位 active 30 · canceling 4 · expired 1 · Masterclass 纯课程买家 1。
- 原始件：`data/growth/private/paypal_export_2026-08-25.csv`。

负责线：Growth Gary（增长官，08-25 定名）。

---

## 独立复核 + 存量确认（Growth Gary，08-25 接手当日）

**对账复核结论：上文全部成立 ✅**，方法记录如下（复核者一开始得出了相反结论，值得留档）。

按行汇总 PayPal 导出会得到 $48,754 且「3 人各有两笔 Completed」——**这是假象**。该导出含 `General Hold` / `General Hold Release` / `Pending→Completed` 生命周期行，同一交易会以不同状态重复出现。**按 `Transaction ID` 去重后**：唯一客户付款 10 笔 · Lifetime 7 × $3,399 = **$23,793** · Masterclass 2 × $584.10 · 有效收入 **$24,961.20**。两处「分期」假象定位到具体 txn：`5GK750…` 当日 `Payment Refund` 全额退回（终态 Reversed）；`53N762…` 是同一 txn 的 Pending→Completed 两行。交叉验证：去重合计与 `members_master` 的 `paypal_paid_usd` 列求和独立吻合。
名单完整性：Whop 导出 39 行 ↔ master `source=whop` 39 行，按 email 双向零差集。

### 现有会员确认（新增口径）

**43 行 − 2 个非客户账号（Andy 本人 + 一个 `@whop.com` 员工号）− 1 个已确认的重复身份 = 真实人头 40。**

> **身份合并（Andy 08-25 确认）**：`G027`（PayPal-only, Lifetime $3,399）与 `G008`（Whop 侧，已在 Discord）为同一人——同 handle、双邮箱（protonmail 走 Whop / gmail 走 PayPal）。已并入 `G008` 主行；`G027` 从 `members.csv` 移除，审计留痕保留在 `private/` 的 master 表。**其余 member_id 一律不重编**（main 上已有文档引用）。

| 分层 | 人数 |
|---|---|
| Lifetime 终身会员 | 7（**5** 人有 Whop 账号 · **2** 人 PayPal-only） |
| Whop 付费过（非终身） | 24（含 3 canceling、1 expired） |
| 纯课程买家（PayPal-only） | 1 |
| 零消费免费用户 | 8（含 1 canceling） |

status：active 35 · canceling 4 · expired 1｜billing：subscription 13 · one-time 19 · free 8｜delivery：discord 37 · **无 Discord 3**。

### ⚠️ 三处口径漂移（08-24 baseline 的数字需停止引用）

1. **「会员 30 人」过时** —— 那是 Whop 店面口径，未含 PayPal-only 会员、未剔除 2 个非客户账号、未去重复身份。真实 **40**。
2. **MRR $1,139 站不住** —— 该值按「10×$99 + 1×$149」推算，与 baseline 自己记录的三轨定价（$240/3mo · $900/年 · $99/月）矛盾。按 plan ID + 续费日期重算：**活跃订阅 9 个，MRR ≈ $774/月**（推算值）。
3. **历史总收入 ≈$23,647 不可直接引用** —— Whop 平台累计 $27,288.70 与 PayPal 直收 $24,961.20 **有重叠**（4 位 Lifetime 同时是 Whop 用户），不能相加。

### 开口（未测量的一律留空不估）

- **plan_id → 价格/计费周期 映射缺失**：Whop 导出只给 Plan ID 不给价格，累计消费反解不出单价（同 plan 下不同用户累计额无公因数）。→ 需 Andy 在后台看一眼各 plan 定价，`members.csv` 的 `price_usd`/`billing` 才能补全，MRR 才从推算变实测。
- **3 位付费会员未落地 Discord**（`G025`/`G026` Lifetime 各 $3,399 + `G017` Masterclass $584.10，合计 $7,382.10）：钱收了人没进群，是**交付缺口**。（原为 4 位，其中一位随 G027→G008 合并后确认已在群内。）

### 本周落库

- `members.csv` **填充 40 行**全匿名（`G001–G041` 去 `G027`，无姓名/邮箱/单人消费），逐 token 自检通过。
- `metrics.csv` 追加 08-25 离周期修正行。
- `weekly/2026-08-24-baseline.md` **PII 脱敏**（见该文顶部注记）。

### 待决（08-25 仍开口）

- **`G025` 与 canceling 的 `G007` 是否同人/家人**：两者仅同姓，PayPal 侧 `G025` 是 Lifetime $3,399、Whop 侧 `G007` 累计 $3,983 且 canceling 中。**该问题未答**——若为同一家庭，`G007` 的 canceling 是「家里已有终身席位」而非流失，挽留动作完全不同。Andy 08-25 的「同意」仅覆盖 `G027`≈`G008`，不含本条。
