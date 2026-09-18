---
name: daily-page
description: 老板每日页——给 Andy 出一份纯业务语言的页面（固定 Artifact URL，republish 到同一个链接），数据来自 ~/Documents/fluxus-ops/state/dailypage.json。凡任务 type=daily_page、或有人说「出每日页 / 老板早报 / 今天的牌面 / 更新那个每日链接 / 我今天要拍板什么」都用本 skill；分档硬上限、fable-voice 七病自查、送达自核三件缺一不可。
owner: ops
---

# daily-page — 一页，他不点任何东西就看得完

⛔ 产出不是对话文字，是**一个固定链接的页面**：用 Artifact 工具、**带 `url` 参数 republish**（先 `action:"read"` 那个 url，再 publish 同一个 url；conflict 用 `force:true`——此页是每日重生快照）。**不带 url 的 publish 会新建一个链接，Andy 收藏的那个就停了。**

Artifact 工具不可用时：把完整 HTML 写入仓库 `data/research/daily_page/YYYY-MM-DD.html` 并直推 main（白名单内），汇报写明《Artifact 不可用，页已落仓库待代发》——**诚实降级，不静默**。

✒️ 页面所有中文写完先过 `.claude/skills/fable-voice/SKILL.md` 的**七病自查**（Andy 首裁全批的现行规矩）；比喻从两个场取：货运场管交付，检修场管质量。引用业务数字走 `KNOWLEDGE.md` 数字权威表，**现场读权威源**。

## 数据源：`~/Documents/fluxus-ops/state/dailypage.json`

v2 起，本页的数据**只从这一个文件来**（由任务板工具生成）。它有这几节：

| 节 | 印什么 |
|---|---|
| `heartbeat` | 守护进程心跳 · 额度 · 最慢领取（一件任务从 open 到 claimed 等了多久） |
| `dashboard` | dashboard 数据日期（最近落地的交易日） |
| `projects` | 项目，**一行一个** |
| `agents` | 各 agent 的 done / blocked 计数 |
| `needs_andy` | 「等你拍板」——needs_andy 状态的任务，**每件一句话 ＋ 一个字的选项**（y/n、A/B），**≤5 件** |

⛔ **v2 取消了两项扫描**：原来的「八个产地扫描」与「门铃滞留扫描」不再做——待办现在在任务板上，`dailypage.json` 就是扫描结果。

读不到 `dailypage.json`，或某一节缺：**写明「读不到」，不拿昨天的顶替**。

## 分档（Andy 亲点，硬上限）

- 🔴 **今天**：有日期且今天到 / 不做作废 / 卡住别人。**上限 3。**
- 🟡 **这周**：他说过要做且单件 ≤15 分钟。**上限 5**；大件拆出「一句话授权」进黄、本体进白。
- ⚪ **不急**：无硬日期，**必须放默认折叠的 `<details>`**。

**超限宁降不挤。红档为空是合法的，照实写。**

⏰ **到期闸**：条目写了窗口/保质期的，用 `pipeline.marketcal` 的 ET 交易日核；过期标「⛔窗口已过」，**不当待办**，写明还能救什么。
🔁 **反向核销**：近 7 天 commit 里有完成证据的，印成「可销账：<条目> ← <commit>」。

## 页面结构（HTML 深色，沿用现版骨架——先 `Artifact action:"read"` 看一眼线上现状再重建）

1. 顶部状态行：heartbeat · 额度 · 最慢领取 · dashboard 数据日期
2. **等你拍板**（🔴 档，每件一句话 + 一个字的选项，≤5）
3. 🟡 这周
4. ⚪ 不急（默认折叠）
5. 项目：一行一个
6. 各 agent：done / blocked 计数
7. 怎么回话（页面划词批注即可）

**结论与判据必须在页面上就完整**，链接只承载明细。`.md` 是机器读的耐久处，不是给 Andy 的交付形态。

## ⛔ Gate（三件，缺一件不算完）

1. **送达自核**：publish 之后用 `Artifact action:"list"` 核「Fluxus 每日」的 updated 是今天；不是就写「未送达」。
2. **数字出处**：页脚折叠块列权威源路径。
3. **降级诚实**：源读不到写明不顶替；三个以上读不到只出前两节并标「本期降级」。

量上限 ≤35 分钟。无人值守时不发消息；除白名单文件外不改仓库。最终回复一行：「每日页已更新 · <链接>」。
