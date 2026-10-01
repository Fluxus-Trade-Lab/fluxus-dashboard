---
name: daily-page
description: 老板每日页——给 Andy 出一份纯业务语言的页面（固定 Artifact URL，republish 到同一个链接），数据来自 ~/Documents/fluxus-ops/state/dailypage.json。凡任务 type=daily_page、或有人说「出每日页 / 老板早报 / 今天的牌面 / 更新那个每日链接 / 我今天要拍板什么」都用本 skill；看板形态（skill kanban-page，Andy 10-01 定为默认标准），fable-voice 七病自查、送达自核、降级不顶替缺一不可。
owner: ops
---

# daily-page — 看板：四行变状态条＋四列，「等你拍板」是第一列

⛔ 产出不是对话文字，是**一个固定链接的页面**：用 Artifact 工具、**带 `url` 参数 republish**（先 `action:"read"` 那个 url，再 publish 同一个 url；conflict 用 `force:true`——此页是每日重生快照）。**不带 url 的 publish 会新建一个链接，Andy 收藏的那个就停了。**

Artifact 工具不可用时：把完整 HTML 写入仓库 `data/research/daily_page/YYYY-MM-DD.html` 并直推 main（白名单内），汇报写明《Artifact 不可用，页已落仓库待代发》——**诚实降级，不静默**。

✒️ 页面所有中文写完先过 `.claude/skills/fable-voice/SKILL.md` 的**七病自查**（Andy 首裁全批的现行规矩）；比喻从两个场取：货运场管交付，检修场管质量。引用业务数字走 `KNOWLEDGE.md` 数字权威表，**现场读权威源**。

## 数据源：`~/Documents/fluxus-ops/state/dailypage.json`

v2 起，本页的数据**只从这一个文件来**（由任务板工具生成）。

⛔ **v2 取消了两项扫描**：原来的「八个产地扫描」与「门铃滞留扫描」不再做——待办现在在任务板上，`dailypage.json` 就是扫描结果。

## 页面就这么多（Andy 2026-09-18：「如果是agent之间在做的事情，我不想看到」）

**四行**，一行一句，读完不用点任何东西：

| 行 | 读 `dailypage.json` 的 | 印什么 |
|---|---|---|
| 1 | `heartbeat` | 守护进程心跳 · **额度＝账号真实读数**「5 小时 `plan_5h_pct`% · 本周 `plan_week_pct`%」（`tier_source` 为 `ledger` 或读数缺失时写「额度读数缺，按自记账估算 `ledger_week_pct`%」，不把估算当真实） · 最慢领取（一件任务从 open 到 claimed 等了多久） |
| 2 | `dashboard` | dashboard 数据日期 · **是否在 JST 08:30 前落地**（是/否） |
| 3 | `projects` | **每个进行中的项目一行**——每行的 `metric` 里有 `stale` 就照印「⚠️ 数据停在 `<日期>`」，有 `unavailable` 就照印那句原因（如「未开卖（09-25 起）」「列 X 还没建」），不许省略成只印项目名/只印数值（T-0922-104：`metric_source` 现场取数，读不到/过旧都是要点给 Andy 看的信号，不是噪音） |
| 4 | `agents` | 各 agent **昨日** done / blocked 计数 |

**加一节「等你拍板」**：列 `needs_andy` 状态的任务，**最多 5 件**。排序：**先按优先级 P0 → P2，同级按最老的在前**。每件一行，四样齐：

```
<id> · <一句话> · <一个字的选项：y/n 或 A/B> · 挂了 N 天
```

⛔ **挂满 3 天的 needs_andy，上页前必须现场核过**（Andy 2026-09-27 点头；起因 09-27 同一天每日页两次把他早批过的事当新题端上去——`T-0925-04` 门禁钥匙他已回「确认付费的人可以使用」、`T-0923-101` 他已回「ok 同意」——根因是本节此前只读任务板 `status` 字段，而他在 Whop/Discord 后台、对话框、页面批注里做的事，任务板收不到回执）：

- **判据**：`dailypage.json` 该条 `needs_andy` 自带的 `days` 字段（`(now - created_at).days`，即经过时长向下取整）**≥2**——严格等价于「已挂满 48 小时」，口语上叫「挂满 3 天」是约数。⚠️ 这不按自然日算：建单当天上午发生的事，第 3 个自然日就会踩中；但傍晚/深夜建的单，`.days` 到第 3 个自然日还不够 48 小时，通常要等到第 4 个自然日的早班才会被拦下（反例：09-25 18:00 建单，09-27 10:24 出页时 `.days` 仍是 1）——要严格按自然日卡，得让 `dailypage.json` 另出一个日历日字段，那是另一件事，这里先按 `.days>=2` 执行。
- **核的动作**（按单的类型选一条，都要留下能查的判据，不是感觉）：
  - 代码/分支类：`git cherry` 或 patch 比对 / `git show origin/main:<path>` 打出来看
  - 线上类：抓线上产物，且**探针只取会被渲染出去的字符串**（vite/esbuild minify 会剥注释，比注释串永远 0 命中），或直接比 `public/` 下静态文件的哈希
  - 外部后台类（Whop/Discord）：用只读 key 查；查不了就写「无法现场核」，别猜
- **留痕**：核完在该任务上追一行 `checked: <YYYY-MM-DD HH:MM> <判据>`（写进任务正文或用 `taskboard.py andy`/评论落盘，能被下一班读到即可）。查到已经在别处被 Andy 处理过（后台操作/对话/批注/§七），直接 `done`/`close` 收掉，**这条不再上页**——上页的只剩「核过、确认他确实还没答」的那些。核不动的写 `checked: 无法现场核 <原因>`，**页面上照印这句**，让 Andy 知道这条是未经验证地挂着。
- 挂满 3 天但既没有 `checked:` 也没有「无法现场核」留痕的单，**这一期不许上页**——先去核，核完（或标注核不动）下一期再印。
- **只读 status 字段就上页 = 违规。**

格式（挂满 3 天时多打印一段）：
```
<id> · <一句话> · <一个字的选项：y/n 或 A/B> · 挂了 N 天 · checked: <YYYY-MM-DD HH:MM> <判据>
```
或
```
<id> · <一句话> · <一个字的选项：y/n 或 A/B> · 挂了 N 天 · checked: 无法现场核 <原因>
```
挂未满 3 天的单不需要 `checked:` 段，照原格式印。

⛔ 没有别的节。**agent 之间的来往不上这一页**——工人跑了什么、哪条分支在等审核、门铃滞留多少，他不想看到。

**唯一例外：滞留分支超时**（Andy 2026-09-21 问卷选「只开单，超 48h 上页」）：真滞留分支平时只由守护进程给归属线开跟进单，**不上这一页**；只有 `stale_branches.escalated.count` > 0（跟进单开出超过 48 小时仍没 done/closed）时，在第 1 行末尾加一句「⚠️ 滞留分支 N 条，跟进单超 48 小时没人处理」。为 0 或字段缺失时什么都不加，不写「无」。

读不到 `dailypage.json`，或某一节缺：**写明「读不到」，不拿昨天的顶替**。「等你拍板」为空是合法的，照实写一句「今天没有要你拍板的」。

## 页面结构＝看板（Andy 2026-10-01：「完美，这个以后是默认标准了」）

**先读 `.claude/skills/kanban-page/SKILL.md`。** 模板就是 `.claude/skills/kanban-page/template.html`——它本身就是 Fluxus 每日的看板版。
每天的动作只有一个：**替换模板里 `<script type="application/json" id="data">` 那一块**，其余一个字不动，然后带 url republish。

上面「四行 + 等你拍板」的内容不变，只是换了摆法：

| 原来 | 看板里 | JSON 字段 |
|---|---|---|
| 一句话结论 | h1 | `headline` |
| 行 1 心跳 / 行 2 dashboard | 顶部状态 chip（+「今天的系统」列各一张卡，卡背放读数） | `status[]` · `today[]` |
| 行 3 项目 | 「项目」列，一个项目一张卡（截止标签、进度条、指标） | `projects[]` |
| 行 4 agent 昨日 | 「各线昨天」列，一张卡内每条线一根横条 | `agents[]` · `agents_date` |
| 等你拍板（≤5） | 第一列，每件一张卡：优先级/挂几天标签 · 一句话 · 要他回的那句 · 卡背放现场核依据 | `decide[]` |
| 数字出处 | 底部折叠 | `sources[]` |

- 发布：`Artifact action:"read"` 固定 url → `publish url:<同上>`。**不要传 `capabilities`**（省略＝沿用已存的 `comments composer_only`，「回话」按钮靠它）。
- 「回话」：Andy 在卡片上留的评论就是回执——开工先 `ArtifactComments read` 这个 url，评论与任务板冲突时评论赢，照办后在汇报里写「Andy <时刻> 评论：『原话』」。

## ⛔ Gate（三件，缺一件不算完）

1. **送达自核**：publish 之后用 `Artifact action:"list"` 核「Fluxus 每日」的 updated 是今天；不是就写「未送达」。JSON 块必须 `json.loads` 得过（发布前跑一次）。
2. **数字出处**：页脚折叠块列权威源路径。
3. **降级诚实**：源读不到写明不顶替；四行里有三行读不到就只出「等你拍板」并标「本期降级」。

量上限 ≤35 分钟。无人值守时不发消息；除白名单文件外不改仓库。最终回复一行：「每日页已更新 · <链接>」。
