# 全系统深检蓝图（Andy 2026-08-28 立项；夜间流水线首件跑通后开工）

> 目的：确认整套联邦**不是壳**。方法 = Workflow fan-out 广度扫描（审计要全覆盖=宪法判据）+ ralph loop 修复循环（发现→修→阳性对照→下一个）。每维产出：证据表 + 修复清单 + 可淘汰清单。

## 十维（① - ⑥ Andy 亲定，⑦ - ⑩ OPS 补）

**① 不是壳**：每条宪法条/机制找一次真实触发记录（commit/晨报/事件）；没触发过的=纸面机制，设计阳性对照逼它触发一次或降级删除。
**② 每环节实跑**：9 定时任务 + 3 公箱 + 门铃/挂单/回执/verdicts/campaign 六条流水线，各按「具体场景」走一遍全程（谁写→谁读→谁核销），断点记录。
**③ 冲突/过期/淘汰**：任务书 vs 宪法接线审计（08-28 已抓到一次）；routines 两两查职责重叠；对话设计（推送格式）与现实用法 diff；14 孤儿任务书复查；建了没人用的资产清单（游戏面板/visuals 筛选台/……用量实测）。
**④ 数据归纳与 absolute truth**：六个存放地（GitHub/本地/Discord/Vercel/Obsidian/Notion）逐个盘：里面放着什么→KNOWLEDGE.md 是否登记→格式是否统一→agent 能否零人工找到并使用（用一个新上下文 agent 实测「按 KNOWLEDGE.md 找 X」的成功率）；Obsidian/Notion 若实际闲置→明写「不用」也算归纳。
**⑤ Skills 固化**：按三次律盘点已成功 ≥3 次的操作（直推 main 标准动作/fxtwitter 抓帖/临时树验收合并/看板刷新/契约核销……），逐个做成 `.claude/skills/` 或 SOP，登记 KNOWLEDGE.md。
**⑥ Token/成本效率**（Andy 点名）：每个定时任务的上下文重量（任务书长度/重复读取的文件）；日推+早报+晨报的内容重叠度；砍冗余读取。
**⑦ 单点与恢复力**（OPS 补）：App 开着才跑=本机单点；Comet 单浏览器；bundle 备份停在 08-22——演练「这台 Mac 今晚死了，新机器多久恢复联邦」，写成 RECOVERY.md。
**⑧ 安全面**（OPS 补）：key/token 存放盘点（GAS token/WHOP/Anthropic）、gitignore 覆盖率、PII 全仓再扫（上次只扫了两个名字）。
**⑨ 测试真实性**（OPS 补）：mutation 基线（Joe todo 在册）——抽 10 个守卫注入 bug 看红不红；「红得不是地方」原则全覆盖。
**⑩ 会话卫生**（OPS 补）：活着的长命交互会话逐个查开机日期 vs 宪法版本（Zac 案例的全面版）；过期会话列归档建议。

## 执行序
首件验收通过 → ①②③ 一轮 Workflow fan-out（每维 2-3 审计员+独立 verifier）→ 修复用 ralph loop 逐个清 → ④⑤⑥ 第二轮 → ⑦⑧⑨⑩ 第三轮。每轮产出落本目录，修复走各自白名单/留分支规矩。审计员全部在基于 origin/main 的临时树跑（宪法主树保护第 5 条）。

## Andy 输入（2026-08-28 问答定案）
- **④ 扩容为立项**：Obsidian = 交易资料 + 系统的 second brain（含散乱课程内容的归宿）；Notion = 常用数据库。方案参考 github.com/AgriciDaniel/claude-obsidian（文件级 skills：ingest/query/lint，PARA/Zettelkasten，带 provenance——与我们「结论带出处」同族）。**边界先划死：git 仓库 = 运营真理（体系/契约/数据），Obsidian = 领域知识（交易资料/课程），不许搅混。** 待 Andy：vault 路径；Notion 需在 claude.ai 连接器授权后才盘得动。
- **Discord 三项全做**：会员商业数据（Gary 已大半，验完整性）+ 频道内容结构索引（29 教育频道→KNOWLEDGE 资料层）+ **Andy 历史发言→voice/raw 矿**（接进流水线原料）。
- **淘汰授权**：可逆的直接停并报备清单；不可逆删除与改动 Andy 日常动线（早报/日推）的等周日批。
