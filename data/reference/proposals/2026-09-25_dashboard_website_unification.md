# 官网与 Dashboard 合一：最小化 / 过渡 / 最终三份实现

**任务**：T-0925-73（ops）。触发条件：课程上线开卖（09-25，已触发）。
**背景裁决**（不重复调研，直接引用）：
- 产品三个实体：Discord=社群 · Dashboard=工具 · 课程/内容=education（Andy 2026-09-25，见 `agents/claire/memory/rulings.md` 同日条）。
- 过渡期约束：未完成/未审核板块不对会员开放，标 Beta（Andy 原话同上）。
- 课程门禁已验证的技术路线：Whop + Cloudflare Pages，Whop 的 access check（OAuth + `/me/has_access/:id`，Company / Access Pass / Experience 三级）已经跑通一次（T-0922-80，`fluxus-masterclass-lab.pages.dev`）。
- Dashboard 现状：纯静态 SPA（React，Vercel 托管），**没有任何账号/会员系统**；`data/output` 与整个仓库是 public，今天所有人（含未付费者）能看到全部内容；`/pricing`（`frontend/src/components/public/PricingPage.jsx`）标着 $79–99/月，CTA 外链到 `whop.com/fluxus-trade-lab/`，不做任何门禁校验。
- Squarespace 官网现状（Andy 原话）：「门面半瘫痪状态，里面是没有实际内容，只有上warp购买课程和进入discord会员的接口」。

## 三份实现

### 最小化 —— 今天能上线的版本

- **谁在哪注册**：不新建账号系统。复用 Whop 现有身份——课程买家和 Discord 会员在 Whop 那边已经有购买记录，dashboard 加一个「会员登录」按钮走 Whop OAuth，回跳后调 `/me/has_access/:id` 查这个人持有哪张 access pass（课程 / Discord 会员）。这条路径 T-0922-80 已经验证过一次，不是新技术。
- **钱在哪收**：不变，仍在 Whop（课程 $1,499 一次性、Discord 会员 $79/99 月费）。Dashboard 本身这一步不新增收费，也不新增门禁——登录只是把人标成「已验证会员」，用于展示欢迎状态和后续埋点，还不拿它挡任何页面。
- **门在哪判**：不判。当前 dashboard 内容对所有人公开这件事本来就是既成事实（仓库 public + Vercel 原样输出），最小化阶段不改这一点，只是把「已验证会员」这个状态接出来，为下一阶段的门禁做地基。
- **Beta 怎么标**：未完工/未审核的板块（如 Portfolio Review 里还没定稿的功能、Education 里还没搬完的 ModelBook 段落）加一个锁图标 + "Beta — opening soon" 文案，对所有人（含已验证会员）一律不开放，不分人群。
- **工程量**：一次 OAuth 回调页 + 一个校验 hook + 若干 Beta 占位组件，claire 一天内能出预览稿。**不用先解决 Vercel Hobby 的商用问题**，因为这一步还没实际让 dashboard 变成付费产品的执行面——但下一步（过渡）一启动就必须解决，见下方。

### 过渡 —— 官网与 dashboard 并存、门禁开始生效

- **谁在哪注册**：仍是 Whop 身份为准，但登录态从「一次性校验」升级成真正的 session（token 刷新，不再是单纯 localStorage flag）；同时接入 Discord OAuth，让「社群身份」和「工具身份」认成同一个人——这是后面板块④（每日复盘 PDF 从 Discord 搬上 dashboard）的前提。
- **钱在哪收**：三条线仍分开收（课程 / Discord 会员 / dashboard 会员），但统一走 Whop 后台，不再各自对账。
- **门在哪判**：dashboard 开始真正按身份分内容——已完工的板块对验证过的会员开放，未完工的继续 Beta 锁；未登录/未付费的人看到的是现在这版免费预览（Market State 等公开内容）。为了让 webhook（退订、转移会员）能实时同步而不是每次裸调 Whop API，这一步建议加一层轻量后端（Vercel serverless function 或 Cloudflare Worker）代理 Whop webhook。
- **Beta 怎么标**：逐板块转正，节奏跟着四块内容（市场观察 / Portfolio / Education / 复盘 PDF）各自的完工进度走，不是一次性开闸。
- **Squarespace 怎么处理**：保留，但降级成纯跳转牌——首页两个入口（买课程 / 进 Discord）换成一个「进入 Dashboard」，dashboard 内部再分流到课程和 Discord。不重做 Squarespace 的内容，因为它本来就没有内容可重做。
- **Vercel Hobby**：这一步必须先解决（见下方单独一节），因为这是 dashboard 第一次真的开始按付费身份执行门禁。

### 最终产品 —— 付费合一、使用合一

- **谁在哪注册**：Dashboard 是唯一入口，一次登录，内部再关联 Discord 身份、课程进度、会员状态——用户不用感知「这是在用 Whop」。
- **钱在哪收**：结账嵌进 dashboard 里（如果 Whop 支持 embedded checkout 就直接复用；不支持则要另立项自建支付网关，工作量显著更大，值不值得做取决于到时候的用户规模）。定价可能仍分级（社群/工具/教育），但用户体验上是一次付费旅程，不再外跳。
- **门在哪判**：dashboard 自己维护一份权限矩阵（谁能看哪些板块），Whop/Discord 降级为身份与支付的下游连接，不再是门禁本体。
- **Beta 怎么标**：不需要了——四块内容全部转正，课程也整体搬进 dashboard 的 Education 板块。
- **Squarespace 怎么处理**：关站，域名 301 重定向到 dashboard（如果这个域名有 SEO 历史权重就留跳转，没有就直接下线）。

## Squarespace 去留（结论）

**不是现在要决定「关不关」，是现在不用碰它。** 最小化和过渡两个阶段都只需要把它降级成跳转牌，真正关站是最终产品阶段的事，而且不可逆（涉及域名/SEO），到时候单独走 Andy 拍板，不在本单结论。

## `/pricing` 的 Vercel Hobby 口子怎么处理

**建议：升级 Vercel Pro（$20/月）。** 理由：
1. 这不是 `/pricing` 一个页面的问题——它标价、外链 Whop 结账，是「advertising the sale of a product」，Vercel 条款原文覆盖的正是这种行为，挪页面位置或撤下 CTA 治标不治本。
2. 一旦「最小化实现」上线，dashboard 本身就要开始服务付费会员，商用信号只会更强，不会更弱——现在不解决，过渡阶段一样要解决，不如一次做完。
3. 流量对 100 人量级远够（Pro 含 1TB/月），不是因为用量需要升级，是因为条款需要升级。

**这是一笔钱，按宪法「花钱先问」——推荐动作已经写清楚，是否升级需要 Andy 一个字。**

## 需要 Andy 拍板的两点

1. **Vercel Pro 升级（$20/月）**——推荐做，理由见上。
2. 以上三层实现的划分本身——是否同意从「最小化」（今天可上线，无门禁、只加登录态+Beta 标签）开始，按过渡→最终的顺序推进，而不是一步到位。

## Owner 与下一步

- 三层规划本身在此结单（ops）。
- **最小化实现的落地**（Whop OAuth 登录按钮 + 校验 hook + Beta 占位组件）转给 claire，走前端预览稿流程（frontend-preview-loop skill）。Landing page 改造解冻，claire 可以按「最小化」这版继续。
- Vercel Pro 升级等 Andy 一个字后由 ops 执行（升级操作本身可逆、非破坏性，批准后不需要再开单）。
