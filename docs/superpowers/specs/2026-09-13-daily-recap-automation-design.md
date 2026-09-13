# 每日市场复盘自动化 — 设计

- 日期：2026-09-13 · 线：OPS Fable
- 状态：**Andy 批准**（原话「Spec同意」）
- 上游规格（产品形态最高权威）：Andy 的 `Daily_Recap_Workflow_Spec.md`（本机 `~/Downloads/`）
- 数据规则：`.claude/skills/daily-recap/SKILL.md`

## 1. 目标

Andy 现在每天手工走八步：找 YouTube 当天视频链接 → 提取字幕 → 字幕转 MD → 连同规格发给 Claude → 在 dashboard 截 3 张图 → 让工具编排、校对数据、给 1–2 个教育选题 → 他挑一个 → 出中英两份 PDF。
自动化后**只保留一处人工关卡：教育选题 A/B 由 Andy 挑**。其余七步机器做。视觉版式归 Visual 线。

## 2. 立项三件套

| 项 | 内容 |
|---|---|
| 发布物 | 每个交易日 `Market_Recap_YYYY-MM-DD_EN.pdf` + `_ZH.pdf`，给 Discord 会员 |
| 截止日 | **09-15（周二）首次生产跑**，复盘 09-14 场。之前先交**过去一周样张**：09-08 至 09-11 四份日复盘 + 一份周复盘（Andy 原话「先做过去这一周的每天复盘和每周复盘，作为调试的样本」） |
| 到期规则 | 09-15 没做通 → 降级为「材料包自动备好，Andy 说一句『出』才生成」，先用上再补 |

## 3. Andy 09-13 的裁决（选项原文）

| 问题 | 他选的 |
|---|---|
| 教育选题怎么接 | 「早上递 A/B，挑完出成品」——其余部分先做完，他回一个字母再写教育段与配图；不回就等，机器不替他选 |
| Big Picture 的叙事来源 | 「照原 spec，字幕叙事为主」——他的 Discord / Founders Note 做加强 |
| 送达时间 | 「10:30 JST 前」 |
| 首跑日 | 「09-15 周二」 |
| 持仓口径 | 「管线只做R 和%, 不写股数和美元」 |
| 口吻 | 「正文里不出现Andy 说这样的字眼，也不用第一人称」——判断改写成中性陈述，引号原句不署名；成品闸加「Andy」= 0 |
| Founders Note 缺失 | 「Founders note如果连接不上，可以空着，有时候我没有写，写的时候可以加上」——整节不出现，页面不提示 |

## 4. 架构：本机一条龙，材料包为界

选本机不选云端：yt-dlp 从机房 IP 抓 YouTube 未验证；A/B 选题要在会话里回复，云端别扭；首跑只剩两天。
取材与生成之间以**材料包**为界——生成端将来要迁云时只搬后半段。

| 阶段 | 时间（JST） | 做什么 | 失败时 |
|---|---|---|---|
| 取字幕 | 09:00 起 | 在 Revere 频道挑当天日更（排除 Your Money Podcast 与 Weekend Review），yt-dlp 抓英文自动字幕，VTT 去重成 `transcript.md`。实测上传时间 06:09–08:44 | 每 15 分钟重试到 10:00；仍无则出无字幕版并在交付说明写明 |
| 取数 | 同上 | 读当天 `data/output` / 历史日期读 `data/history` 归档；等数据班落地（最晚 10:00） | 10:00 未落地：对应格占位并写明 |
| 取原话 | 同上 | Discord 三频道当日消息（`data/output/threads/<date>/messages.json`）；Founders Note 走 GAS（取 T 与 T 后第一条） | 没写或连不上：整节不出现、页面不提示，只记进交付说明；永不代笔 |
| 持仓 | 同上 | 从 GAS 直接取，只算 R 与 % | GAS 不通：Portfolio 节占位 |
| 画面 | 同上 | 市场状况、板块龙头两块：生产日用 Chrome 无头截亮主题（先核页面日期 = 目标交易日）；历史日期用归档数据渲染 | 截图日期不对就改用渲染 |
| 生成 | 取材完成后 | 按 Andy 规格写结构化内容（EN + ZH；ZH 过 fable-voice 与 biaoda 两本账），给 A/B 选题，停在会话里等 Andy | — |
| 选题关卡 | 约 10:00 | Andy 在该定时任务的会话里回 A 或 B（手机可回） | 不回就等 |
| 渲染 | 选题后 ≤15 分钟 | 写教育段 + 配图 → HTML → PDF → 三道闸 | 任一闸不过不交付，INBOX 记一行 |

要赶 10:30，Andy 需在 10:15 前回选题。

## 5. 组件

- `pipeline/content/recap/fetch_transcript.py`：日期 → 当天日更 → 字幕 → transcript.md
- `pipeline/content/recap/build_pack.py`：日期 → `pack.json`（数据摘录、原话、Founders Note、持仓 R/%、字幕路径）
- `pipeline/content/recap/render.py`：结构化内容 → 双语 HTML → PDF；`pdftotext` 抽文本跑四道闸：规格 §4 禁用专属名词 = 0 · 「领导力」= 0 · 美元金额与股数 = 0 · 「Andy」= 0；另查末页正文不少于约 3 行
- `pipeline/tests/test_recap_*.py`：VTT 去重、日更挑选、三道闸（每道闸先用注入样本证明能报红）
- PDF 环境：`~/.venvs/fluxus-recap`（weasyprint + matplotlib），不放 /tmp
- 定时任务 `recap-daily`（本机，周二至周六 09:00 JST）：**样张过 Andy 之后再建**
- 版式：首跑用 9/4 已批版式；Visual 线模板合进 main 后替换，接口是结构化内容文件

## 6. 数据与隐私

仓库是公开的，所以以下**一律不进 git**，只存本机 `~/Documents/Trading/01_Market_Reports_Daily/YYYY-MM/`：字幕、材料包、PDF、任何持仓数据。
PDF 与所有产物不出现股数与美元金额；Portfolio Update 只用 R 与 %。

## 7. 与现有规则的关系

- 产品形态（节次、禁词、无 Actions、教育一段、配图规范）以 Andy 规格为准。
- skill 的数据规则继续适用：四问、均线规则、三条法 A/B（无标准不当标准读数；算不出就不用）。
- skill 三条法 C（判断句只取 Andy 原话）**对 Big Picture 让位**给「字幕叙事为主」；教学选题的命名权仍归 Andy。
- skill 09-06「Portfolio 以他最后交付物/截图为权威」**被取代**：改为 GAS 直取、只算 R 与 %。

## 8. 测试与验收

- 单元测试：见第 5 节，全部带阳性对照。
- 样张验收：Andy 审过去一周四份日复盘 + 一份周复盘，裁决进 skill 裁决记录。
- 首跑验收：09-15 10:30 前两份 PDF 在本机目录、三道闸全绿、交付说明写明缺什么。
