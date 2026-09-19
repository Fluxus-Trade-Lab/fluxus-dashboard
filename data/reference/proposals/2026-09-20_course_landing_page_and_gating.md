# 课程落地页 + 会员门禁：三方案对比（待 Andy 拍板）

**状态**：待裁。任务 T-0920-02（claire）。09-25 课程发售前需要定。
**背景**：Module 1 交互课件（`~/Documents/SwingMasterclass/_web/dist/`）已由 Q 线交付，静态站、无后端。Andy 09-19 定课程走 Whop 卖，$1,499，按环节 unlock。当前 dashboard（frontend/）是纯静态 SPA，部署在 Vercel，**没有任何账号/会员系统**——`PricingPage.jsx` 只是外链到 Whop 结账页，不做门禁。

## 三个方案

| | **A. 自建（Vercel + Whop OAuth）** | **B. Squarespace Member Areas** | **C. Whop 原生 Course/Experience（推荐）** |
|---|---|---|---|
| 月费 | Vercel Pro **$20/月起**（Hobby 禁商用，dashboard 若还在 Hobby 必须先升级）| Core $18/月或 Pro $35/月，另加 1–4% 交易费 | **$0 新增**——Whop 本来就在收这笔 $1,499，抽成模式不变 |
| 100 人注册会不会宕/超限 | 不会：Pro 含 1TB 流量/月，100 人量级远够 | 不会宕机（Squarespace 自家扛），但多一个「Whop 收钱、Squarespace 发货」的对账缝隙——两边状态对不上，人交了钱看不到课 | 不会：门禁本来就在 Whop 自己的基础设施上，收钱发货同一家，零对账 |
| 门禁工程量 | **最大**：现在完全没有账号系统，要新建 session/校验状态，还要接 Whop OAuth 判断是否购买 | **中**：Squarespace 自己的会员墙，但课件是外部交互 HTML，能不能干净塞进 Squarespace 页面（iframe 还是重写）没验证过 | **最小**：Whop 已有 experience 级别的 access check（OAuth + membership 校验现成 API），我们只需把静态 HTML 塞进 Whop app view |
| 品牌一致性 | 最好，和 dashboard 同一个壳 | 独立站点，视觉要重做 | 在 Whop 的壳里，视觉受 Whop app view 框架限制 |
| 未验证的风险 | 无 | 复杂交互（拖拽收盘价、裸读计时）能否在 Squarespace 自定义代码块里跑，没测过 | Whop app view 对纯静态复杂 JS/CSS 的自由度没做过 spike，需要 30 分钟验证 |

## 我的推荐：C，理由三条
1. **零新增月费**——A、B 都要为一个 09-25 就要上线的东西现在开始按月付费；C 复用已经在付的钱。
2. **不产生第二套需要对账的系统**——B 的「Whop 收钱 / Squarespace 发货」两边状态不同步，是 09-25 上线当天最可能出的那种事故（人付了钱看不到课，或者退款了还留着门禁）。
3. **门禁工程量最小**——A 要从零建认证状态（现在的 dashboard 是纯静态站，这是最大的新增架构面）；C 直接用 Whop 现成的 access check，不用我们自己存谁买了什么。

**代价**：C 没做过 spike，不确定 Whop app view 能不能干净托管现有的交互 HTML/JS（拖拽、计时、盲测这些）。如果验证下来装不进去，退回 A。

## 未做但需要 Andy 一句话的判断
门禁验证在哪一侧（读会员进度、算 unlock 到第几课）也要定：Whop 侧存不存进度、还是我们侧的 dashboard 存——这个只有拍了 A/B/C 之后才能往下定，本次不展开。

—— claire，T-0920-02
