# CAMPAIGN: <slug> · <日期>
status: signal|research|angle|flagship|distribution|writing|visual|review|queued|approved|published|measured|killed
rounds: <本卡累计跑过几轮；≥3 轮未过闸时第 4 轮 Gate 只能放行或 killed>
> **状态机（08-31 定，此前 approved 谁写没定义，两种相反的失败都可能发生）**：
> 退回＝status 写回对应站名＋一句退回原因。**Gate 过闸 → 写 `queued`**（含义＝在 Andy 队列里等，**不再占用当晚槽位**）→ 同时往 `APPROVAL_QUEUE.md` 追一行。
> **只有 Andy 本人在 decision 节签字后才写 `approved`**——Gate 永远不写 approved（那是绕过人批边界）。
> 断点续跑判据＝status ∉ {queued, approved, published, measured, killed}。毙件标 killed 留原地当案例。
## signal
（发生了什么 · 受众为何在意 · 出处 · 衰减 · 弃选理由列表）
## research
（3-7 条已核实主张，每条带 URL/权威源路径；未证实项单列）
## angle
（读者 / 结果 / 张力 / thesis / 旗舰格式 / 可复用物 / 分发入口）
## flagship
（毛坯正文或路径；每个数字带出处）
## distribution
（X 变体 ×N，各标：**七入口号（1–7，brain/x.md 菜单，互不重复）** · hook 类型（brain/hooks.md）· 独立存在理由；长文必配三行骨架入口推）

| 变体 | 入口号 | hook 类型 | 独立存在理由 |
|---|---|---|---|

## writing
（Writer Mia：成稿路径 · 与毛坯相比改了什么 · 七道闸自查结果）
## visual
（Visual Vera：每个变体的视觉资产路径，或明确「不配图＋理由」）
## review
（审查站判定：过/退/毙 + 逐条理由）
## decision
（**owns：Andy 本人**——六站无人可写本节。他发了哪个 / 否了什么+一字理由；日推收录进 verdicts.jsonl 后在此追「↳ 已录 verdicts（日期）」）
## performance
（T+24h/T+72h 读数 → keep/test/stop 提案）
