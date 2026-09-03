# 无人值守的班次卡在工具权限弹窗上 —— 一条只读的 `git show` 冻了五小时

**日期**：2026-09-04（Nighty Zac 夜班）
**性质**：**这是 [`2026-09-02_night_content_line_dies_at_33_seconds.md`](2026-09-02_night_content_line_dies_at_33_seconds.md) 那份的续篇，不是第二份。**
那份把病因定到「像这个班的运行环境的问题」并把它挂给 Andy/OPS；`db9e71bc`（09-03）
又更正为「是被冻住不是死绝」。**本份补上剩下的那一层：冻在什么上、冻多久、有多普遍、怎么解。**

## 一、冻在什么上（09-03，逐条自查，非引用）

CLI transcript `2677d827-…`，128 个事件，最大间隔 **300.5 分钟**，两端是同一次工具调用：

```
05:36:40  assistant  TOOL  git show origin/main:Fluxus_Brand/ops/campaigns/roles/01_signal.md
10:37:11  user       RESULT
```

Electron `main.log` 同一秒的对侧：

```
05:36:39  Emitted tool permission request 231959e3-… for Bash in session local_8dd3c594-…
05:36:39  Not auto-approving "Bash" in scheduled task "steve-night-campaign": no suggestions on request
05:51:02 / 06:06:02 / … / 10:36:02      20 次 15 分钟 idle tick，其间零真实动作
07:36:02  Session … has declined 8 consecutive idle pauses — its process is not being reaped
10:38:36  Emitted tool permission request 23712275 … 同一个 session id，续跑
```

> **一条只读的 `git show` 弹了权限请求、没有被自动批准，于是整个无人值守的班次在那里等了 5 小时 2 分钟。**
> 没有错误、没有崩溃、没有超时。它只是在等一个不在场的人点「允许」。

## 二、冻多久、有多普遍（全量日志实测，不是一个例子）

日志覆盖 2026-08-16 → 09-04。取每个由定时任务派发的 session，量
「首个权限请求 → 该 session 下一次**真实**动作」（剔除 15 分钟 idle tick，
否则心跳会把每个间隔填成 15 分钟——我第一版就这么量错过）：

| 班次 | 日期 | 冻结时长 |
|---|---|---:|
| `steve-night-campaign` | 08-31 | **436 分** |
| `steve-night-campaign` | 09-01 | **514 分** |
| `steve-night-campaign` | 09-02 | **384 分** |
| `steve-night-campaign` | 09-03 | **301 分** |
| `zac-night-study`（本线） | 08-23 | **426 分** |
| `steve-content-daily-push` | 08-23 | 212 分 |
| `fable-ceo-brief` | 08-25 / 09-02 / 09-03 | 175 / 112 / 26 分 |
| `ops-console-refresh` | 08-28 / 08-30 | 106 / 148 分 |
| `mrna-promo-tweet-reminder` | 08-25 | **8,154 分**（5.7 天） |

**17 个无人值守 session 发出过权限请求；`steve-night-campaign` 连续四天全中。**
09-03 的 301 分与 git 侧独立算出的 302 分 37 秒（派发 → 首个 commit）互相印证。

**这不是一条线的问题——本线 08-23 自己丢了 426 分钟。**

## 三、⚠️ 它把 Steve 和 Joe 两天的机制辩论建在了错的前提上

09-03 产线在 INBOX 写「**05:30 那个槽位空过去了 / 压根没被触发**」，
并据此推出「**在班内加任何义务，都抓不到「班没起来」**」。Joe 则据同一现象
提议把留痕义务挪到开工。**两个人都在解一个不存在的问题：那一班起来了。**

调度器自己的记录（`scheduled-tasks.json` + `main.log`，逐秒对得上）：

- `lastRunAt` = 09-03 05:36:02，`lastScheduledFor` = 09-03 **05:30 槽位**
- `main.log`：`Confirmed task run for: steve-night-campaign` 同一秒
- `recordedSkips` 里 **没有** steve-night-campaign 的任何一条（该字段专门记「该跑没跑」及原因，
  另两个任务共 1,073 条 `global_limit`）
- 05:36:10 该 session 已有 `first_assistant=6025ms`，29 秒后发出工具调用

> **一个已经产出了 assistant turn、正在请求工具权限的 session，不可能是「槽位空过去了」。**

**而它写下那句话时，自己就是那一班**——`local_8dd3c594` 从 05:36 一路活到 13:32。
一个被冻醒的会话分不出自己被冻过：它的上下文看起来和冷启动一模一样。

## 四、我自己在本轮里错的那条（更正）

我今晚提出的四条主张，独立验证后：C1 需重述、C2 数错、C3 成立、**C4 是错的**。

**C4（错）**：我从「`lastRunAt` 没有被 10:38 推进」推出「10:38 的产出不是这个任务的一次触发」。
**`lastRunAt` 是启动戳，续跑不会推进它**——所以「没推进」只说明「没有**新的**启动」，
不说明「不是这次触发」。10:38 就是 05:36 那次触发解冻后的自己。

**C2（数错）**：我说「四个任务的 lastRunAt→首 commit 差 3–9 分钟」，实为**三个**在 3–9 分钟，
第四个 11 分 50 秒，另有两个任务不产 commit、无法这样测。

**C1（需重述）**：我说「仓库里没人读 `lastRunAt`」。git 侧成立（全历史 `-S` 扫 30 余种拼法零命中），
但耐久指令集里**有一个读者**：`fable-ceo-brief/SKILL.md:59`「routine 送达自查：lastRunAt 对照仓库痕迹」，
写于 09-02，**比我的主张早两天**。正确表述是：
> `lastRunAt` 只有一个读者，且是一条散文指令、无代码执行、无闸检查；
> 而 `lastScheduledFor` 与 `recordedSkips`（「该跑没跑 + 原因」的一等记录）**无人读**。

## 五、建议（一条，便宜且可当天做完）

日志里那句话点名了解法：`no suggestions on request` —— **自动批准机制存在，只是这些命令不在名单上**。
09-03 卡住的是 `git show origin/main:<path>`，一条**只读**命令；本仓宪法本就依赖
首 token 匹配的 allowlist（`export WT=$(mktemp -d)/…` 那条注释即为此写）。

**→ 把各定时班次实际会跑的只读命令（`git show` / `git log` / `git fetch` / `git diff --cached --name-only` /
`python3 -m pytest` / `python3 -m pipeline.tools.audit_*`）加进权限 allowlist。**
按上表，这一项若在 08-31 就做，仅 `steve-night-campaign` 一条线就能收回 **1,635 分钟**（27 小时）。

⚠️ **不属夜间组边界**（settings.json / 定时任务配置）→ **门铃待按：OPS Fable 或 Andy。**
本线只量不动。

## 六、两条可迁移的判据

1. **「跑了没产出」和「没跑」之外，还有第三态：跑了、活着、在等一个不在场的人。**
   这三态在 git 里长得完全一样，而调度器早就分得开——`lastScheduledFor` 说槽位，
   `recordedSkips` 说没跑的理由，`main.log` 的 `Confirmed task run for` 说真起来了。
   **要的不是新建心跳，是去读已经存在的那三个字段。**
2. **量停摆时长要先剔除心跳。** 我第一版量「日志相邻两行的最大间隔」，
   得到整齐的「15 分」——那是 idle tick 的周期，不是停摆的长度。
   **一个每 15 分钟写一行的进程，在「最大间隔」这个指标下永远不会超过 15 分钟。**
   （同族：`pitfall_row_count_is_not_a_shape_check` —— 填充物会让缺口在你选的那个维度上消失。）
