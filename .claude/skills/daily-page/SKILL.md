---
name: daily-page
description: 老板每日页——给 Andy 出一份纯业务语言的页面（固定 Artifact URL，republish 到同一个链接），数据来自 ~/Documents/fluxus-ops/state/dailypage.json。凡任务 type=daily_page、或有人说「出每日页 / 老板早报 / 今天的牌面 / 更新那个每日链接 / 我今天要拍板什么」都用本 skill；四行 + 等你拍板一节，fable-voice 七病自查、送达自核、降级不顶替缺一不可。
owner: ops
---

# daily-page — 四行，加一节「等你拍板」

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

⛔ 没有别的节。**agent 之间的来往不上这一页**——工人跑了什么、哪条分支在等审核、门铃滞留多少，他不想看到。

**唯一例外：滞留分支超时**（Andy 2026-09-21 问卷选「只开单，超 48h 上页」）：真滞留分支平时只由守护进程给归属线开跟进单，**不上这一页**；只有 `stale_branches.escalated.count` > 0（跟进单开出超过 48 小时仍没 done/closed）时，在第 1 行末尾加一句「⚠️ 滞留分支 N 条，跟进单超 48 小时没人处理」。为 0 或字段缺失时什么都不加，不写「无」。

读不到 `dailypage.json`，或某一节缺：**写明「读不到」，不拿昨天的顶替**。「等你拍板」为空是合法的，照实写一句「今天没有要你拍板的」。

## 页面结构（HTML 深色，沿用现版骨架——先 `Artifact action:"read"` 看一眼线上现状再重建）

1. 顶部四行
2. 等你拍板（≤5）
3. 怎么回话（页面划词批注即可）

**结论与判据必须在页面上就完整**，链接只承载明细。`.md` 是机器读的耐久处，不是给 Andy 的交付形态。

## ⛔ Gate（三件，缺一件不算完）

1. **送达自核**：publish 之后用 `Artifact action:"list"` 核「Fluxus 每日」的 updated 是今天；不是就写「未送达」。
2. **数字出处**：页脚折叠块列权威源路径。
3. **降级诚实**：源读不到写明不顶替；四行里有三行读不到就只出「等你拍板」并标「本期降级」。

量上限 ≤35 分钟。无人值守时不发消息；除白名单文件外不改仓库。最终回复一行：「每日页已更新 · <链接>」。
