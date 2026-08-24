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

**43 行 − 2 个非客户账号（Andy 本人 + 一个 `@whop.com` 员工号）= 真实人头 41**（身份合并若确认则 40）。

| 分层 | 人数 |
|---|---|
| Lifetime 终身会员 | 7（4 人有 Whop 账号 · 3 人 PayPal-only） |
| Whop 付费过（非终身） | 25（含 3 canceling、1 expired） |
| 纯课程买家（PayPal-only） | 1 |
| 零消费免费用户 | 8（含 1 canceling） |

status：active 36 · canceling 4 · expired 1｜billing：subscription 13 · one-time 20 · free 8｜delivery：discord 37 · **无 Discord 4**。

### ⚠️ 三处口径漂移（08-24 baseline 的数字需停止引用）

1. **「会员 30 人」过时** —— 那是 Whop 店面口径，未含 PayPal-only 4 人、未剔除 2 个非客户账号。真实 **41**。
2. **MRR $1,139 站不住** —— 该值按「10×$99 + 1×$149」推算，与 baseline 自己记录的三轨定价（$240/3mo · $900/年 · $99/月）矛盾。按 plan ID + 续费日期重算：**活跃订阅 9 个，MRR ≈ $774/月**（推算值）。
3. **历史总收入 ≈$23,647 不可直接引用** —— Whop 平台累计 $27,288.70 与 PayPal 直收 $24,961.20 **有重叠**（4 位 Lifetime 同时是 Whop 用户），不能相加。

### 开口（未测量的一律留空不估）

- **plan_id → 价格/计费周期 映射缺失**：Whop 导出只给 Plan ID 不给价格，累计消费反解不出单价（同 plan 下不同用户累计额无公因数）。→ 需 Andy 在后台看一眼各 plan 定价，`members.csv` 的 `price_usd`/`billing` 才能补全，MRR 才从推算变实测。
- **4 位付费会员未落地 Discord**（3 位 Lifetime 各 $3,399 + 1 位 Masterclass $584.10）：钱收了人没进群，是**交付缺口**。

### 本周落库

- `members.csv` **首次填充**：41 行全匿名（`G001–G041`，无姓名/邮箱/单人消费），逐 token 自检通过。
- `metrics.csv` 追加 08-25 离周期修正行。
- `weekly/2026-08-24-baseline.md` **PII 脱敏**（见该文顶部注记）。
