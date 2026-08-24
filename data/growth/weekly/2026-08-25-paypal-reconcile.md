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

- ~~plan_id → 价格映射缺失~~ **已解，见下节。**
- **3 位付费会员未落地 Discord**（`G025`/`G026` Lifetime 各 $3,399 + `G017` Masterclass $584.10，合计 $7,382.10）：钱收了人没进群，是**交付缺口**。（原为 4 位，其中一位随 G027→G008 合并后确认已在群内。）

### 本周落库

- `members.csv` **填充 40 行**全匿名（`G001–G041` 去 `G027`，无姓名/邮箱/单人消费），逐 token 自检通过。
- `metrics.csv` 追加 08-25 离周期修正行。
- `weekly/2026-08-24-baseline.md` **PII 脱敏**（见该文顶部注记）。

### 待决（08-25 仍开口）

- **`G025` 与 canceling 的 `G007` 是否同人/家人**：两者仅同姓，PayPal 侧 `G025` 是 Lifetime $3,399、Whop 侧 `G007` 累计 $3,983 且 canceling 中。**该问题未答**——若为同一家庭，`G007` 的 canceling 是「家里已有终身席位」而非流失，挽留动作完全不同。Andy 08-25 的「同意」仅覆盖 `G027`≈`G008`，不含本条。

---

## 定价实读 + MRR 重算（2026-08-25，Whop 后台只读盘点）

**方法**：用 Andy 已有的浏览器登录态**只读**查阅（与 08-24 OPS 同法），未输入任何凭证、未点任何同意/条款/收款控件。Products 与 Premium 产品编辑页逐档抄录。

### 各档定价（后台实读，权威）

| 产品 | plan_id | 定价 | 在档人数 | 试用 |
|---|---|---|---|---|
| Premium Membership | `plan_a3AfskxLVcRT2` | **$240 / 3 个月** | 6（主力） | 7 天 |
| Premium Membership | `plan_SUgEa6eV2hGHW` | **$900 / 年** | 3 | — |
| Premium Membership | `plan_ySnCQI7dAC94t` | **$99 / 月** | 2 | 7 天 |
| Premium++ Members Access | `plan_pAMoMvrGL6NJu` | **$149 / 月** | 1 | — |
| Free Access | — | 免费 | 1 | — |
| Swing Trade Masterclass | `plan_8RfO9OFDQdVUV` | 一次性，**实付两档 $584.10 / $649.00** | 15 | — |

「三轨并存、季付最受欢迎」经后台核实成立，且 6/3/2 的人数分布与 08-24 导出的 plan_id 反推**完全吻合**。

### ⚠️ 新发现：第五个产品「Substack for PT Swing Traders」不在 Products 列表里

后台 Products 列表（筛选 = Visible and Hidden）只有 4 个产品，但会员数据里有 **7 人挂在 `prod_0WddY2iwoTitp`**，产品名在 Memberships 视图中显示为 **Substack for PT Swing Traders**。直接访问该产品页会被重定向——**已归档但会员资格仍在生效**，其中 **6 个带活跃续费日期**（2026-10 至 2027-01）。

价格反解（导出只给 plan_id，后台已无该产品页）：
- `plan_7TpyDYwfvaXzY` = **$1,149 / 年** —— 单挂锚点一名实付 $1,149；三名组合用户 $1,798−1,149=$649、$1,733.10−1,149=$584.10、$1,798−1,149=$649，**全部落在 Masterclass 的两个已知实付档上，4/4 算术吻合**。
- `plan_6y1CaoSkK6lNC`（2 人）**未解出**：单挂锚点 $900，但组合用户余额为 $931.50，与任何已知 Masterclass 档都对不上。按铁口径**留空标未测量**，不估。

### MRR 重算

| 组成 | 口径 | 金额/月 |
|---|---|---|
| Premium $240/3mo × 6 | 后台实读 | $480.00 |
| Premium $900/年 × 3 | 后台实读 | $225.00 |
| Premium $99/月 × 2 | 后台实读 | $198.00 |
| Premium++ $149/月 × 1 | 后台实读 | $149.00 |
| **小计（可见产品，已测量）** | | **$1,052.00** |
| 归档产品 $1,149/年 × 4 | 算术反解，4/4 吻合 | +$383.00 |
| 归档产品 `plan_6y1C` × 2 | **未测量** | — |
| **合计（下限）** | | **≥ $1,435.00** |

- **08-24 记录的 MRR $1,139 是错的**，两个方向都错：按「10×$99」高估了 Premium 的人均（实际三轨混合，11 人合计仅 $903/月），同时**完全漏掉了归档产品那 6 笔活跃订阅**。
- `metrics.csv` 的 `mrr_usd` 列按铁口径只记**已测量的 $1,052**；反解与未测量部分记在本文与 notes，不混进读数列。
- ⚠️ **即将到期的减项**：$99/月 那档有一人「23 小时内取消」（后台状态），落地后 MRR −$99。

### 附带发现（后台 Memberships 视图）

- **取消原因后台有记录**：观察到 "Too Expensive" ×3、"Technical Issues" ×2、"Other" ×1 —— 这是流失分析的现成数据源，08-24 baseline 未提及。
- 存在**同一人多条 membership**（试用结束/重新订阅/跨产品），所以「membership 数」≠「人数」。本台账一人一行的口径不受影响，但引用后台任何「active users」数字时要注意它数的是 membership。

## 本次落库补充

- `members.csv` **15 行补上 `price_usd` / `billing`**；仍留空的是：`plan_6y1C`（2 人，未测量）、同时挂多个订阅 plan 的行（已在 notes 标注）、以及 Masterclass 一次性两档价（同 plan 两个实付值，不写单一值）。

---

## Andy 裁决记录（2026-08-25）

### 📌 归档产品维持不可见

`prod_0WddY2iwoTitp`「Substack for PT Swing Traders」**维持不可见（Andy 08-25）**——与 Masterclass 同性质，是节奏选择不是遗漏。**此条从「缺陷」改记为「决定」**，后续任何报告不得再把它列为待修问题。

⚠️ **但有一个技术风险与该决定无关，需在 2026-10-17 前验证**：

本产品的状态比 Masterclass 更深一层——Masterclass 在后台列表中显示为 `Hidden`（可见性筛选能筛到）；本产品**连筛选 Visible+Hidden 都列不出，产品页直接重定向**，属于已归档/已删除，不只是隐藏。**「对买家不可见」是商业选择；「归档是否会静默阻断存量订阅续费」是技术问题，两者不是一回事。**

存量敞口：**7 人挂靠，其中 6 人有活跃续费日期**，跨度 2026-10-17 至 2027-01-29，对应已确认 MRR 贡献 ≈ $383/月（`plan_7Tpy` $1,149/年 × 4）+ 2 人未测量（`plan_6y1C`）。

| 续费日 | 距 08-25 | 说明 |
|---|---|---|
| 2026-10-17 | 53 天 | **第一个观察点** —— 若这笔正常扣款，归档不阻断续费得证 |
| 2026-10-29 | 65 天 | 第二笔 |
| 2027-01-04 / 01-26 / 01-26 / 01-29 | 132–157 天 | 其余四笔集中在 1 月 |

**行动**：2026-10-17 那笔是免费的自然实验，不需要现在改任何设置。增长官在 10-17 后的首个周一记账时核对该笔是否入账；若未入账，则归档静默阻断续费成立，届时 1 月那四笔（约 $4,600/年规模）面临同样风险，需在 2027-01-04 前处置。**在验证出结果之前，不把它当问题，也不把它当没事。**

### ⏸ G025 与 G007 的关系：Andy 调查中

两者仅同姓（PayPal 侧 `G025` 是 Lifetime $3,399，Whop 侧 `G007` 累计 $3,983 且 canceling 中）。**Andy 08-25：仍在调查。** 在结论出来前：
- `G025` 的 Discord 触达**保持阻塞**（见 `private/outreach_no_discord_2026-08-25.md`），避免对已在群内的家庭成员重复邀请、或在对方正要取消时踩点；
- `G007` 的 canceling **不计入流失判断**——若两者同属一个家庭且已有终身席位，该 canceling 是结构性调整而非流失，性质完全不同；
- 另两位无 Discord 的付费会员（`G026` Lifetime $3,399、`G017` Masterclass $584.10）**不受此阻塞**，可随时触达。

---

## ⚠️ 遗留产品与在设计产品重名（2026-08-25 发现，需 Andy 处置）

**Andy 08-25 原话：「Substack for PT Swing Traders 目前没有这个产品，在设计中。」**
**后台数据与此冲突**：`prod_0WddY2iwoTitp` 存在、7 人挂靠、**6 人有活跃续费**，已定价部分年化 **$4,596**（`plan_7Tpy` $1,149/年 × 4），另 2 人档位未测出。

### 证据：它是遗留产品，不是待上线产品

| 判据 | 归档产品 `prod_0WddY2iwoTitp` | 对照 · Premium `prod_JP6vlypnDQTNk` |
|---|---|---|
| 挂靠者入会区间 | **2025-11-14 → 2026-01-20** | 2025-11-21 → **2026-08-20** |
| 2026-01-20 之后是否进新人 | **否** | 是（持续到本月） |
| 后台 Products 列表 | 不存在（产品页重定向） | 在列表中，Visible |

另有旁证：后台 Discord 频道列表存在 **「F2 Substack Access to Discord」**，与该产品名对应；08-24 baseline 记录的七个档位里也有「F2 Substack Access（隐藏）」。

**结论：老 cohort 的遗留产品仍在自动续费，而 Andy 正在设计一个同名新产品。两者是两个东西。**

### 由此产生的三个问题（增长官不代决）

1. **交付问号 —— 最要紧的一个。** 这 6 人每年付约 $1,149，**他们现在收到的是什么？**若新 Substack 尚未开张、旧产品又已归档，则存在「持续收款、交付内容不明」的敞口。这不是数据问题，需要 Andy 确认他们实际拿到什么。
2. **新产品上线时这 6 人怎么办？** 他们已持有一份自动续费的旧权益。迁移 / 保留 / 折价升级 —— 这是新产品设计的输入条件，越晚决定成本越高。
3. **续费是否会被归档静默阻断？** 见本文前节。第一个观察点 **2026-10-17**（G024）。若阻断成立，这 6 个老客户会在无人察觉的情况下失去权益。

### 关联：canceling 的 G007 也在这个产品上

`G007`（累计 $3,983，全部会员中最高，canceling 中，身份关系 Andy 调查中）**是这 7 人之一，且是唯一没有续费日期的**。他的 canceling 与该产品的归档状态是否有关，未查证。

### 附：Masterclass 的处置思路（Andy 08-25 提出，执行不在增长线）

Andy：「可以变成可见，然后改成不可购买。或者数量满了等等。」即以「已售罄 / 满员」形态陈列而非隐藏，保留社会证明与期待感，同时不接单。**Whop 店面设置属 Marketing Steve / Andy，增长官只记录不执行。**若执行，增长台账需同步：Masterclass 由 `Hidden` 改为 `Visible + 不可购买`。

---

## 🚨 更正：`prod_0WddY2iwoTitp` 不是 Substack 产品，是 Premium++ 旧档（2026-08-25，Andy 质疑后复查）

**本文前两节把 `prod_0WddY2iwoTitp` 认成「Substack for PT Swing Traders」，是错的。**Andy 08-25 质疑「这 6 个人确定不是挂靠在 Premium 档位上？」后，逐人复查后台 Memberships 页，8 个样本 8/8 全部推翻原结论。

### 正确的产品对照（后台 Memberships 页产品名 × 导出 Product IDs，逐人核对）

| Product ID | 后台产品名 | 状态 | 挂靠 |
|---|---|---|---|
| `prod_dTRZGYQvAc0pe` | Swing Trade Masterclass | Hidden（列表可筛） | 15 |
| `prod_JP6vlypnDQTNk` | Premium Membership | Visible + Discover | 10 |
| `prod_lqtg4j5LTtBVh` | **Premium++ Members Access（新档）** | Visible，$149/月 | **1** |
| `prod_0WddY2iwoTitp` | **Premium++ Members Access（旧档）** | **已归档，列表里没有** | **7** |
| （另有） | Substack for PT Swing Traders | 死档，仅 2 条 membership 且均 Ended | 0 活跃 |

**关键：两个产品同名「Premium++ Members Access」——新档在列表里，旧档已归档。**后台 Products 页显示 Premium++「Active users 1」指的只是新档；旧档的 7 人不在那个计数里。

**Andy 说「Substack for PT Swing Traders 目前没有这个产品，在设计中」是对的**——那个产品确实是死的（仅一位已流失会员的两条 Ended membership）。与它同时出现在 Memberships 视图里的只是巧合，我把「列表里没见过的产品名」直接安到了「导出里没对上的 Product ID」上，**没有做逐人核对就当成了发现**。

### 错在哪（方法论）

两个「异常项」同时出现，就假定它们互相解释。实际验证只需一步：拿任一挂靠者，比对「导出的 Product IDs」与「后台 Memberships 页显示的产品名」——G004 的导出是 `prod_dTRZGYQvAc0pe,prod_0WddY2iwoTitp`，后台显示 Masterclass + Premium++，一步即证。
**这一步我当时没做，因为结论「看起来能自洽」。自洽不是证据。**

### 数字影响

- **MRR 不变**：$1,149/年 × 4 = $383/月 的算术成立，错的只是它挂在哪个产品名下。总计仍为**已测量 $1,052 + 反解 $383 = 下限 $1,435**。
- **前节「遗留产品与在设计产品重名」整节作废**——不存在「6 人为一个在设计中的产品付费」这回事。他们付的是 Premium++ 旧档，权益即 Premium++，交付路径清楚。**该节提出的三个「待决」中，第①条（交付问号）与第②条（新产品迁移）随之取消。**
- **仍然成立的一条**：归档产品是否静默阻断续费，观察点 `2026-10-17`（G024）。旧档 Premium++ 已归档而 6 人仍在续费，这个风险与产品叫什么名字无关。

### G007 状态更正（Andy 08-25 确认）

**G007 是永久会员，仍在。** 后台显示的「Cancels in 5 months」是他 Premium++ 旧档订阅的取消，**不是会员流失**。此前把他列为「累计 $3,983 的大客流失、挽留优先」是错的口径，`08-24 baseline` 与本文前节的相关表述一并作废。
