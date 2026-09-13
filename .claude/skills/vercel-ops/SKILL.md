---
name: vercel-ops
description: Fluxus Dashboard 在 Vercel 上的运维与判断手册：部署存储/容量、保留期与 30 天恢复期、删部署、Hobby 用量上限与暂停、vercel.json 与 Ignored Build Step、回滚、网站没更新。内含 2026-09 实测核过的计费口径和五道「下判断之前必过的闸」——专治从总量反推个数、按速度线性外推时间（09-12 把「要 280 天」说成事实）这类错。凡涉及 Vercel 的判断或操作都先读它。
when_to_use: Andy 转来 Vercel 邮件（storage 快满 / upgrade to pro / usage limit）；问容量多大、要删多少、多久能降下来、要不要升级 Pro；要删部署或改保留期；fluxus-dashboard.vercel.app 打不开、503 DEPLOYMENT_PAUSED、页面停在旧日期、部署次数异常、要回滚——即使他只说「网站」「部署」「存储」「上线」没提 Vercel。不触发：Vercel AI SDK 写代码、别的托管平台选型、GitHub Actions 定时任务、前端配色与数据文件拆分。
paths:
  - vercel.json
  - scripts/vercel_ignore_build.sh
  - pipeline/tools/audit_deploy_cost.py
---

# vercel-ops — 先数清楚，再说多久

> 2026-09-06 到 09-13 一周四轮换来的（125 GB 事故 → 改保留期 → 误判 280 天 → 否掉「删最旧 10 天」）。
> 每条事实带出处和核实日期。Vercel 会改文档和控制台，**超过一个月的事实先重核再用**。

## 一张图：容量是怎么来的

**Deployment Storage ≈ 每个仍被 Vercel 存着的部署 × 它的构建产物大小**。三个乘数分属三处：
- **部署次数**——每推一次 main 就是一次生产部署（除非 Ignored Build Step 跳过）
- **产物大小**——我们的产物 98% 是数据（`data/output` + `modelbooks`），应用代码只占约 2%
- **保存多久**——保留期 **加上删除后的 30 天恢复期**

每个乘数单独看都对，爆的是乘积，而乘积没有主人。所以回答任何容量问题，都要分别说清这三个数现在是多少、各自在往哪走。

## 必须知道的计费事实（核于 2026-09-13）

| 事实 | 出处 |
|---|---|
| 产物「contributes to Deployment Storage **while Vercel stores it**」 | docs/deployment-retention |
| 到保留期后，后台任务通常 **48 小时内**标记删除；被例外保护的，例外解除后重评**最长 30 天** | docs/deployment-retention |
| 删除后进**恢复期 30 天**（成功构建的部署），期满「all associated resources are **permanently removed**」；**误删和保留期删除一样**都进恢复期 | docs/deployment-retention |
| ⇒ **删部署不会马上腾出容量**，要等恢复期满（文档没有逐字写「恢复期内计入容量」，但上面两句 + 09-11～13 实测一致：保留期已删掉 14 天以前的全部部署，容量几乎不动） | 推论 + 实测 |
| 保留期例外（到期也不删）：项目最近 10 个部署；最近 20 个 READY 的生产部署；挂着生产别名的；活跃分支最新预览 | docs/deployment-retention |
| 计费按 GB-month：每天记当天最大存储量，整个周期加总 | docs/deployment-storage |
| Usage 页的数字**不随日期范围变**（「最近 7 天」和「最近 30 天」都显示同一个 126.05 GB，09-06 实测）——别把它当窗口累计 | 实测 |
| Hobby 超额：「you will have to wait until 30 days have passed before you can use the feature again」 | docs/plans/hobby |
| 被暂停时：**生产站停止服务、访客看到 `503 DEPLOYMENT_PAUSED`**，**不会自动恢复**，要去控制台或 API 逐个恢复。文档**没写**存储超额是否触发暂停 | kb/why-is-my-account-deployment-blocked |
| Hobby 每天最多 **100** 次部署（闸落地前 09-05 一天到过 79 次） | docs/plans/hobby |
| `ignoreCommand`：**退出码 1 → 构建，0 → 跳过** | docs/project-configuration/vercel-json |

## 本项目的现状

- 项目 `fluxus-dashboard`，Hobby；`projectId=prj_SKz7d6P3kRrycsT2i7KHpfmSMsam`，`teamId=team_0YuCrfwzMHjHuDPUFFlCtMuu`（也在仓库 `.vercel/project.json`）
- **保留期**（09-06 改）：Canceled 1 天 · Errored 1 周 · Pre-Production 1 周 · Production 2 周
  - ⚠️ 设置入口在 **Settings → Build and Deployment → Deployment Retention Policy**，不是文档说的 Security；**Recently Deleted** 在 Settings → Security
- **部署闸**：`vercel.json` 的 `ignoreCommand` → `scripts/vercel_ignore_build.sh`，只有 `frontend/`、`data/output/`、`vercel.json`、`package*.json`、脚本自己变了才构建（`89c59a1d`；14 天回放 781 次 commit 只该构建 56 次）
  - ⚠️ **比较基准是「上次成功部署」**（`VERCEL_GIT_PREVIOUS_SHA`，`7603736e`，09-13），不是 `HEAD^`：旧版只看一次推送的最后一个 commit，09-13 隐私清洗一次推 5 个 commit、最后一个只改测试，整批被判「没碰产物」跳过，清洗后的数据没上线。基准不在浅克隆里会先加深拉取，仍拿不到就偏向构建
  - 「网站没更新」先查这条：多 commit 推送里产物改动在中间那几个，旧闸会漏
- **成本审计**：`python -m pipeline.tools.audit_deploy_cost`，接在周六 `weekly-data-audit`。它盯的是**乘积**：闸在不在且覆盖产物的每个来源（D1）、预算（D2）、大而久不变的产物（D3）。它只读 git，不依赖 Vercel 凭证。

## 怎么取真实数字

**看用量**：控制台 Usage → Deployment Storage。用 JS 从页面表格取数字时，只取行文本，别回传含 URL/查询串的字符串（会被隐私过滤拦成 `[BLOCKED: Cookie/query string data]`）。

**数部署**（容量问题的第一步，永远先做）：Andy 的 Chrome 登录态下，在 vercel.com 同源调 `/api/v6/deployments?projectId=…&teamId=…&limit=100`，用 `pagination.next` 当下一页的 `until` 翻完。
- 翻页会超过 CDP 的 45 秒——**先把任务挂到 `window.__xxx` 上后台跑、立刻返回，再轮询**；直接 `await` 会超时丢结果
- 只回传聚合（按天 × 生产/预览 × 状态计数），不回传 uid 或 URL
- **同时回传「翻了几页、为什么停」**（`next` 为空 / 空页 / 撞上循环上限）。整数总数（比如 500）一定会被怀疑是分页截断，停因就是回答。09-13 那次：6 页、`next` 为空自然停、HTTP 200，所以 500 是真数
- 按天分组用的是 `toISOString()`，即 **UTC 日**；和交易日（ET）差一天时要说明
- 官方公开接口是 `GET api.vercel.com/v7/deployments`，要 Bearer token；机上 `~/Library/Application Support/com.vercel.cli/auth.json` 那枚 token **09-06 已过期**，别把流程建在它上面

**改设置**：一次一个点击；把几个下拉框的点击塞进同一个批量调用，会被权限分类器拦下。

## 下判断之前必过的五道闸

这五条每条都对应一次真实的错判。

1. **数，别推。** 任何「有多少个」「占多少」都来自真实清单，不来自「总量 ÷ 我假设的单价」；反过来「个数 × 假设的单价 = 多少 GB」也一样不行。Vercel 实际给单个部署记多少**从没实测过**（源侧产物 `audit_deploy_cost` 量过约 100 MB，但 Vercel 压缩、去重之后记多少不知道；事故档的 75 MB 是反推的），所以「稳态会停在几 GB」「删掉能腾几 GB」目前都答不了——说「不知道，缺哪个数」，别乘出一个。
   *09-12 我拿 126 GB ÷ 假设的 75 MB 说「积压约 1,600 个、要 280 天」——真实活跃部署只有 500 个，而且下降根本不看删得快慢。评测里没读本 skill 的对照组又两次走了同一条链：「54 次/天 × 30 天 ≈ 1,600 个 → 每个 77 MB → 稳态 26 GB」「126 GB ÷ 500 = 0.25 GB/个 → 稳态 33 GB」。这条链很顺手，所以才要写成闸。*
2. **先弄懂账怎么记，再说一个动作有没有用。** 问自己：这个动作让哪个数变？什么时候变？
   *09-13 Andy 提议「删最旧 10 天」——删了只是挪进 30 天恢复期，腾不出空间，还把回滚窗口从 14 天砍到 5 天。*
3. **预测要有机制，不能只有速度。** 「每天降 0.42 GB，所以 280 天」假设了线性。这里的机制是恢复期，形状是**某个日期的台阶式下降**，不是一条斜线。给时间就给「哪一批、哪天期满」。
4. **不可逆的动作先对齐范围。** 批量删部署前：用真实清单报准确个数和日期范围；排除当前生产部署、挂别名的、最近 20 个 READY 的；说清它会不会改善目标数、什么时候；**等 Andy 在对话里明确点头**。能让保留期自己做的，优先让它做。
5. **每个数都有出处。** 报给 Andy 的数字标来源（API 拉取 / 控制台 / 文档原话）和日期；推论要写明是推论。

## 当前时间线（09-13 判断，过期要重核）

- 活跃部署 500 个，全在 08-30～09-13（6 页翻完，非截断）；闸落地前（08-30～09-06）431 个，之后（09-08～13）69 个
- 预期**两个台阶**，不是斜线（都是推论：保留期到期 → ≤48h 标删 → 30 天恢复期满）：
  - **台阶①约 10-06～10-11**：09-06 改保留期后标删的那一大批（08 月中下旬的旧部署）。窗口两端的依据不同——10-06～08 是「改设置 + 48h + 30 天」；10-11 是 09-12 面板里**可见的** 8 行都显示「29 days left」。面板只露 8 行、排序没核过，所以两端都留着
  - **台阶②约 10-13～10-22**：仍活着的 431 个闸前部署，依次满 14 天后再过 30 天
- 台阶之后停在几 GB：**不知道**（见闸 1）。能动稳态的只有「少部署」和「缩小产物」，缩保留期只能小幅改善且赔回滚历史
- 待核的异常：`CANCELED` 保留期只有 1 天，清单里却还活着 35 个（例外条款最多保住 10 个）——要么清理滞后，要么新设置不追溯旧部署
- **要动手的唯一信号**：生产站返回 `503 DEPLOYMENT_PAUSED`。那时去控制台恢复，并考虑升一个月 Pro 顶过去
- **复查：每周一次**（Andy 09-13「Vercel 用量台阶改成每周一次检查」）——定时任务 `vercel-storage-weekly`，每周一 09:20 JST 读 Usage、数活跃部署、查生产站状态，追加到 [`data/research/vercel_storage/weekly.csv`](../../../data/research/vercel_storage/weekly.csv)。10-12 之后还没掉一大截，说明「恢复期内计入容量」这条推论错了，回头重核

## 付过学费的坑（按日期追加，别删旧的）

- **[09-06] 125.62 GB 是厂商发邮件告诉我们的，不是我们量出来的。** 14 天 781 次 main commit，只有 56 次碰前端产物——92% 的部署白跑。修法：Ignored Build Step + `audit_deploy_cost`。事故档 `data/reference/incidents/2026-09-06_vercel_storage_125gb.md`（⚠️ 那份档里「≈75 MB/次」是反推值，不是量出来的）。
- **[09-06] 用 Vercel CLI token 读数失败**——机上那枚 token（文件建于 3 月）调用返回 `invalidToken: true`；具体何时失效不知道。现在走浏览器登录态。
- **[09-06] 改保留期找错页面**——文档写 Security，实际在 Build and Deployment。
- **[09-12] 「要 280 天」**——见闸 1。
- **[09-13] 「删最旧 10 天」**——见闸 2。同一天把 Hobby 暂停的后果从「部署停了」更正为「生产站 503 下线且不自动恢复」。
- **[09-13] 部署闸只看最后一个 commit**——OPS 隐私清洗一次推 5 个 commit，最后一个只改测试，整批被跳过、清洗过的数据没上线；修为以上次成功部署为基准（`7603736e`，测试 `pipeline/tests/test_vercel_ignore_build.py`）。「有闸」是 bool，缺口住在它比的是哪两个点。
