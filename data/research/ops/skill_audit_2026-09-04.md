清单来源：pipeline/tools/skill_inventory.py（commit f861a8ad），共 38 项；加插件层 11 个键

# Skill 审计 · 2026-09-04 · 四档处置

**一句话结论**：38 项里真正要动手的是 9 件「退」（全部有替代件或零调用）和 12 件「修」（全是描述缺我们的黑话或与宪法条冲突、要在任务书里钉死用法）；4 件「用」加 13 份定时任务书原样保留，「建」为 0 件——这轮不新造任何 skill。插件层 11 个键留 2 个、退 9 个（其中 1 个本来就是 false）。

**Action Plan**
1. 归档 9 件「退」（第 3 节清单，本地 mv 与 git mv，均可逆）+ 把 8 个插件键设 false——须 Andy 点头再动，理由：停插件是改配置。
2. 12 件「修」分两类：本仓库自有的（fable-voice、shuorenhua、video-subtitles）直接改 description；superpowers 的 9 件第三方不改，触发词与宪法覆盖句写进各线任务书。
3. 抽查（第 4 节）无一改判，判据可信；下轮周检按同一 JSON 再跑一遍看漂移。

判据（照 brief）：情境对不对得上 14 项清单 · description 有没有「做什么 + 什么时候用 + 我们的说法」（0–2 分） · 有没有真实调用痕迹 · 有没有另一件做同一件事且更好。

## 用（4 件）

| name | source | 它怎么工作 | 情境 | 冲突组 | 判定 | 理由 | 主人 | 归档动作 |
|---|---|---|---|---|---|---|---|---|
| contract-clerk | project-agent | 只读子 agent：逐行盘 DATA_CONTRACTS.md §七/§八，按成分 grep 全仓核实每行是否已落实，输出 ✅已落实/⏳未落实/🗑过期/❓无人认领 四类 ≤20 行中文报告，不改契约文件。 | 周检 | — | 用 | 第三人称、写了做什么（盘契约行核实落实/过期/无人接）和什么时候用（「盘一遍契约」），黑话（§七、契约、盘一遍）都在；周检盘契约行正是它的场。 | OPS | — |
| growth-officer | project-agent | 增长官子 agent：把 Andy 递来的 Whop/Discord 导出或口述数字录进 data/growth/ 台账，每周一追加 metrics.csv 一行并写 ≤10 行周报，每个数字必须带来源日期、量不到标「未测量」。 | 周检 | — | 用 | 第三人称、含做什么（会员/漏斗/转化率台账）和什么时候用（「叫增长官」、Andy 给导出或口述数字时），黑话（台账、摸清存量、Whop）齐；周一记账＋周报落在周检情境，TEAM.md 明确归 Growth Gary。 | Growth Gary | — |
| repo-janitor | project-agent | 每周 git 体检子 agent：fetch --prune 后逐项报未 push commit、脏 worktree、可删/重复分支；快进的未 push 直接 push、脏树封存 wip commit，删除类动作只列清单等 Andy 点头，≤15 行中文报告。 | 周检 | — | 用 | 第三人称、含做什么（查未 push/脏 worktree/可删分支出体检报告）和什么时候用（「跑一次大扫除」），黑话（大扫除、脏 worktree、等 Andy 点头）齐；TEAM.md 把「大扫除」和 .claude/agents/ 都划给 OPS Fable，周检情境对得上。 | OPS | — |
| podcast-to-md | user-skill | 跑 transcribe.py（本机已打补丁走 mlx-whisper）把小宇宙/YouTube/mp3 链接转成 00-raw-transcript + meta.json，再由 Claude 在对话里写出带说话人的逐字稿、总结+金句、三个口播稿角度和最终口播稿。 | 内容产线 | — | 用 | 在用：~/.cache/podcast-to-md-work 有 42 集缓存、最近一次 09-02 13:16，~/Desktop/中文表达训练/tools/run_batch.py 拿它做批量转录喂语料库，09-02 刚为本机打了 mlx-whisper 补丁；description 第三人称、有 what+when、含「文字稿/逐字稿/口播稿/金句」中文触发词。注意：它服务的是中文表达训练那条内容产线，不是 Fluxus_Brand 的；video-subtitles 只在「转录」一步与它部分重叠，输出物不同不算重复。 | OPS | — |

## 修（12 件）

| name | source | 它怎么工作 | 情境 | 冲突组 | 判定 | 理由 | 主人 | 归档动作 |
|---|---|---|---|---|---|---|---|---|
| fable-voice | project-skill | OPS Fable 写给 Andy 的中文前读的文风病例账：七个翻译腔病例的前后对照、语域表、60 秒自查、Andy 裁决记录与两个固定比喻场，随每次裁决追加。 | 写中文给 Andy | shuorenhua | 修 | 情境明确（写汇报/页面文案/回复/晨报前），黑话齐全（翻译体、汇报、晨报、Andy 原话），但 description 混了第一人称「我自己写过的句子」和祈使句「读这本」，不是第三人称——把那两处改成第三人称即可；与 shuorenhua 只是部分重叠（它是通用去 AI 味检查器，这本是 Fable 专属病例账＋Andy 裁决），不构成退役理由。 | OPS | — |
| shuorenhua | user-skill | 按 场景(chat/status/docs/public-writing)→protected spans→Tier→档位→scope 的固定顺序清理中英文文本里的 AI 套路（开场套话、空总结、二元骨架、黑话、翻译腔、名词化），产出单一推荐改写版，或用户要求时只出 1-5 条标注清单。 | 写中文给 Andy | — | 修 | 有情境（Andy 09-02 原话「你的中文是翻译体」、feedback_chinese_ai_flavor 定「中文 AI 腔是外发内容的大问题」，且 .claude/skills/fable-voice/SKILL.md:33、:73 已把它当上游规则书引用，两者是分工不是重复：fable-voice 记 Andy 裁决的病例，本件管手术流程）；描述第三人称、有做什么+适用需求，但触发词只有「去 AI 味/说人话」这类通用说法，没写进 Andy 的黑话「翻译体」「AI 腔」「ai slop」「机器印的」，两条只中一条。 | OPS | — |
| video-subtitles | user-skill | 调本机脚本 ~/.local/bin/video-subtitles（mlx-whisper large-v3-turbo 转写 + argos 离线 en→zh），把 .mov/.mp4 录像变成 EN .srt + ZH .zh.srt，落到 ~/Desktop/Video Recordings/video-subtitles/。 | 内容产线 | podcast-to-md | 修 | 有情境且有真调用：transcripts 里 2 次 Skill 调用 + 5 次直接跑脚本，输出目录 08-21 新增 4 个 .srt，docs/plans/2026-08-20-selection-lab-design.md:45 把它写成「转写（video-subtitles 管线）」的正式环节；描述第三人称、有做什么+触发关键词，但关键词全是英文（subtitles/SRT/transcribe），没写进我们的说法「转写」「字幕」「口述」「录像」「Selection Lab」，两条只中一条。与 podcast-to-md 只在「转写」一步重叠（那件吃 URL 走 Groq，本件吃本地文件走 MLX），不是同一件事。 | OPS | — |
| brainstorming | plugin-skill | 动工前逐问澄清意图、提 2-3 个方案、分节呈现设计并逐节要用户批准，产出 docs/superpowers/specs/ 下的设计文档，终态转 writing-plans。 | 设计/方案/plan | — | 修 | 对上「设计/方案/plan」，描述有做什么+何时用但零中文触发词；且它「每个项目都要逐节批准」与 CLAUDE.md 决策分级（可逆小事不问、直接出预览稿）正面冲突，任务书里必须写明我们只在新工程/不可逆事项上启用。 | OPS | 第三方不改；把我们的触发词写进 SKILL_ROUTER 已废→改写进各线任务书的『该用 skill』一句 |
| dispatching-parallel-agents | plugin-skill | 把 3+ 个互不相关的失败/任务按问题域拆开，同一条回复里并发派出多个自包含 prompt 的子 agent，回收后跑全套测试整合。 | 查 bug | — | 修 | 对上「查 bug」里多文件独立失败的形状，且与 CLAUDE.md「何时用多 agent」条（>10 同构项/全覆盖审计）同向；描述只写何时用、无做什么、无中文触发词。 | OPS | 第三方不改；把我们的触发词写进 SKILL_ROUTER 已废→改写进各线任务书的『该用 skill』一句 |
| finishing-a-development-branch | plugin-skill | 实现完成后先跑全套测试，再按 repo/worktree 状态给出「本地合并 / 推分支开 PR / 保留分支」三选一菜单，按选择执行并清理 .worktrees/。 | 收工 | — | 修 | 对上「收工」；但它的「本地 checkout base 分支再 merge」选项与主树保护六条、safe-merge 白名单、直推 main 标准动作相冲突，任务书必须钉死我们只走「推分支」或「白名单内自合」两条路；描述无做什么、无中文触发词。 | OPS | 第三方不改；把我们的触发词写进 SKILL_ROUTER 已废→改写进各线任务书的『该用 skill』一句 |
| subagent-driven-development | plugin-skill | 逐任务派新实现子 agent + 任务级审阅（spec 合规+质量）+ 最多 5 轮修复循环 + 全分支终审，进度写 .superpowers/sdd/ 台账以抗 compaction，收尾转 finishing-a-development-branch。 | 写代码前 | — | 修 | 对上「写代码前」（拿到计划准备动手时的执行驱动器），台账抗 compaction 与 CLAUDE.md「不落耐久处=没发生」同向；但描述只写何时用、无做什么、无中文触发词，且其工作区在 .superpowers/ 需与我们的临时树规矩对齐。 | OPS | 第三方不改；把我们的触发词写进 SKILL_ROUTER 已废→改写进各线任务书的『该用 skill』一句 |
| systematic-debugging | plugin-skill | 任何 bug 先走四阶段（根因调查→模式对比→单假设最小验证→带失败测试的单一修复），3 次修不好就停下质疑架构，禁止无根因的症状修补。 | 查 bug | — | 修 | 直接对上「查 bug」，四阶段与我们 failure_class 先分类、别重抓的教训同向；描述只写何时用、无做什么，缺「查 bug / 复发 / 事故 / 33 秒」这类中文触发词。 | OPS | 第三方不改；把我们的触发词写进 SKILL_ROUTER 已废→改写进各线任务书的『该用 skill』一句 |
| test-driven-development | plugin-skill | 红-绿-重构铁律：任何生产代码前先写一个会失败的最小测试并亲眼看它失败，再写最少代码转绿，先写了代码就删掉重来。 | 写代码前 | — | 修 | 对上「写代码前」，与记忆里「测试对、没人调用」「红得不是地方」等教训互补（它管红绿，不管接线）；描述只写何时用、无做什么、无中文触发词。 | OPS | 第三方不改；把我们的触发词写进 SKILL_ROUTER 已废→改写进各线任务书的『该用 skill』一句 |
| using-git-worktrees | plugin-skill | 开工前先检测是否已在隔离 worktree，否则优先用平台原生工具（如 EnterWorktree），兜底 git worktree add 到 .worktrees/ 并开新分支，装依赖、跑基线测试后报 ready。 | 写代码前 | — | 修 | 对上「写代码前」；但其兜底默认（.worktrees/ + -b 具名分支 + 自动 pip install）与主树保护第 2 条（scratchpad 只基于 origin/main detached HEAD）、直推 main 标准动作（mktemp 临时树）冲突，任务书必须覆盖目录与分支策略；描述有做什么+何时用但无中文触发词。 | OPS | 第三方不改；把我们的触发词写进 SKILL_ROUTER 已废→改写进各线任务书的『该用 skill』一句 |
| verification-before-completion | plugin-skill | 任何「完成/修好/通过」的说法之前必须在本条消息里重新跑出证据命令并读完输出，禁止 should/probably、禁止信子 agent 的自报成功。 | 收工 | — | 修 | 精确对上「收工」，与 CLAUDE.md「push 成功≠投递成功，必须核 origin/main」「完成=合进 main 且能点开」同一形状；描述有做什么+何时用，但缺「收工 / 已合进 main / 汇报」等中文触发词。 | OPS | 第三方不改；把我们的触发词写进 SKILL_ROUTER 已废→改写进各线任务书的『该用 skill』一句 |
| writing-plans | plugin-skill | 把已批准的 spec 写成零上下文工程师也能照做的实施计划：文件结构、按任务拆的 2-5 分钟步骤（含测试代码与提交），自审无占位符后存 docs/superpowers/plans/ 并交给 SDD 或 executing-plans 执行。 | 设计/方案/plan | — | 修 | 对上「设计/方案/plan」；但其计划头缺我们的立项三件套（发布物/截止日/到期规则）、默认存 docs/superpowers/ 而非 NOW.md/proposals，任务书须补；描述只写何时用、无做什么、无中文触发词。 | OPS | 第三方不改；把我们的触发词写进 SKILL_ROUTER 已废→改写进各线任务书的『该用 skill』一句 |

## 退（9 件）

| name | source | 它怎么工作 | 情境 | 冲突组 | 判定 | 理由 | 主人 | 归档动作 |
|---|---|---|---|---|---|---|---|---|
| tearsheet | project-command | 读 data/output/tickers/<SYM>.json 的 L1 数据 + WebSearch/WebFetch 抓新闻，合成 bull/bear、交易计划、催化剂等 ai_synthesis 字段写回 JSON 并单独 commit。 | 无 | daloopa:tearsheet、sp-global:tear-sheet | 退 | 最后一次真实调用是 2026-05-24（AAOI/NBIS 共 4 个 ai(tearsheet) commit），此后三个多月零调用；情境清单里没有「个股页 AI 段」这一项；description 是祈使句、无「什么时候用」、无中文说法。frontend/src/components/ticker/ 五个组件仍读 ai_synthesis（209/210 个 ticker JSON 已有该字段），退役命令不影响页面。skill-os-v2 plan Task 3/8 想把它迁成 skill 当首批住户——若 Andy 要留，按该 Task 重写 description 后再进阶段三实测。 | DATA ALEX | git mv .claude/commands/tearsheet.md 到 .claude/commands/_retired/tearsheet.md（主树与 skill-os-v2 worktree 各一份，两处同步） |
| lieflat-charts | user-skill | 按数据形状在 Lupi/Basics/Glance/Maps gallery 里锁定一个模板卡，沿用其 SVG/ECharts 骨架换数据，输出单文件 HTML 图表或 R01–R12 整页报告；默认 Mono 灰阶，可自动选 porcelain/palm/wire 色系。 | 做图表/artifact | dataviz、data:create-viz、data:data-visualization | 退 | 有情境，但同一情境已被 dataviz 覆盖且后者更好：dataviz 是 Artifact 工具强制前置加载的、色板可换成我们的 DESIGN token；lieflat 锁死 Mono/Inter、禁止混色系，与 DESIGN.v2 的 Plex + 蓝红配对冲突。DESIGN.v2.md:1028 明记它是 PolyForm Noncommercial、26 种几何「全部自己实现，只学公开样式规则」——已经把能学的学完。真实调用仅 2 个 transcript（08-15 试样 5 个 HTML），此后零调用；description 无「什么时候用」、无中文触发词。 | UI Claire | mv ~/.claude/skills/lieflat-charts 到 ~/.claude/skills/_retired/lieflat-charts |
| openmaic | user-skill | 分阶段引导用户选 Live Demo / 本地 / 二开模式，配置 OpenMAIC 的 provider key，启动服务并提交多 agent 互动课堂生成任务。 | 无 | — | 退 | 与本项目十四个情境无一对应（它是教学课堂生成器的安装向导）；Skill 工具零调用，transcript 里只有 09-01 安装当天一个会话提到 OpenMAIC；description 第三人称、有 what+when，但无我们的说法。 | OPS | mv ~/.claude/skills/openmaic 到 ~/.claude/skills/_retired/openmaic |
| youtube-clipper | user-skill | 六阶段流水线：查 yt-dlp/ffmpeg-full→下载 YouTube 视频+英文字幕→AI 切 2-5 分钟章节→用户选片→FFmpeg 剪辑、翻译成双语 SRT、烧录硬字幕、生成社媒文案→输出到 ./youtube-clips/<时间戳>/。 | 无 | podcast-to-md、video-subtitles | 退 | 零调用（transcripts 里 0 次 Skill 调用、0 次脚本执行、目录 02-01 装好后再没动过）且对不上任何情境——Fluxus 内容产线是 X/Substack 文字稿，没有「剪别人 YouTube 出短视频」这一环；下载+转写一步 podcast-to-md 已做且被用过，字幕翻译一步 video-subtitles 已做且被用过；另外它是第三方仓（op7418）、硬钉 model: claude-sonnet-4-5-20250514，描述第三人称有场景但无项目黑话。 | OPS | mv ~/.claude/skills/youtube-clipper ~/.claude/skills/_retired/ |
| executing-plans | plugin-skill | 在独立会话里加载一份已写好的实施计划，先批判性审阅再逐任务照步骤执行、遇阻即停，收尾转 finishing-a-development-branch。 | 写代码前 | subagent-driven-development | 退 | SKILL.md 自己写明「有子 agent 可用时改用 subagent-driven-development」，Claude Code 一直有子 agent，所以它是被同套件里更好的一件覆盖的兜底版；描述亦无做什么、无中文触发词。 | OPS | 第三方不改；任何任务书的『该用 skill』句都不指向本件，同情境统一指向 subagent-driven-development |
| receiving-code-review | plugin-skill | 收到审阅意见时先读完、复述、对照代码库核实再决定实现或有理有据地回推，禁止「你说得对」式表演性附和，多条意见先全部澄清再逐条实现并测试。 | 无 | — | 退 | 「处理别人给我的代码审阅意见」不在 14 项情境清单里；其核心精神（verify first、别顺着说）已由记忆 feedback_challenge_dont_agree 与 CLAUDE.md 覆盖，本仓库也不走 PR 审阅流。 | OPS | 第三方不改；任何任务书的『该用 skill』句都不指向本件 |
| requesting-code-review | plugin-skill | 任务完成/合并前取 BASE 与 HEAD SHA，用 code-reviewer.md 模板派一个 general-purpose 子 agent 审 diff，按 Critical/Important/Minor 分级处理返回意见。 | 发布前 | code-review、code-review:code-review | 退 | 与内置 code-review skill（原生 diff/PR/分支目标、--fix、ultra 多 agent 云审）做同一件事且后者更好；本件只是一个手填模板的子 agent 派发，描述亦无做什么、无中文触发词。 | OPS | 第三方不改；任务书『该用 skill』句在「发布前」情境统一指向内置 code-review，不指向本件 |
| using-superpowers | plugin-skill | 会话开头注入的元规则：只要有 1% 可能适用就必须先调 skill 再回应，流程 skill 优先于实现 skill，子 agent 忽略，用户指令（CLAUDE.md）高于 skill。 | 无 | — | 退 | 它是插件的路由器不是干活的件，14 项情境无一对应；「1% 就必须调」与 CLAUDE.md 决策分级/宁短勿长相悖，虽自述 CLAUDE.md 优先，仍不应被任何任务书引用为依据。 | OPS | 第三方不改；插件自动注入无法单独卸下，任何任务书的『该用 skill』句都不指向本件；要停用只能整体停 superpowers 插件（须 Andy 裁） |
| writing-skills | plugin-skill | 把 TDD 套到 skill 写作：先用子 agent 跑无 skill 的压力场景取基线，再写最小 SKILL.md 让 agent 合规，最后补理由化对照表堵漏洞；附 SDO 描述写法（只写何时用、不写做什么）。 | 周检 | anthropic-skills:skill-creator | 退 | 三次律「第 3 次成功=固化成 skill」归 OPS 周检，情境存在；但 anthropic-skills:skill-creator 是官方件、自带 eval 跑分与描述触发优化脚本，且本件坚持「描述不写做什么」正好与本次审计所依的官方打分条 (a) 相反——重复且另一件更好。 | OPS | 第三方不改；任务书『该用 skill』句在「周检/固化 skill」情境统一指向 anthropic-skills:skill-creator，不指向本件 |

## 建（0 件）

（无——本轮没有发现值得新造的 skill；三次律触发的固化走 anthropic-skills:skill-creator，见冲突组「周检」。）

## 用 · 定时任务书（13 份，有时钟就在跑，不做四档研究）

用 · 定时任务书，有时钟就在跑：`fable-ceo-brief`、`growth-weekly-ledger`、`joe-morning-check`、`ops-console-refresh`、`personal-cortisol-bath`、`personal-cortisol-breathing`、`personal-fitness-daily-push`、`personal-fitness-weekly-review`、`remind-3d-effects-direction`、`steve-content-daily-push`、`steve-content-weekly-batch`、`steve-night-campaign`、`zac-night-study`

## 插件层（~/.claude/settings.json → enabledPlugins，11 个键，只读）

| 键 | 当前值 | 判定 | 理由 | 动作 |
|---|---|---|---|---|
| `superpowers@claude-plugins-official` | true | 用 | 开发主线（控制器已裁）；能力盘点里有使用痕迹 | 保持 true |
| `document-skills@anthropic-agent-skills` | true | 用 | docx/xlsx/pptx/pdf 对上「审阅件出双版本」；能力盘点里有使用痕迹 | 保持 true |
| `planning-with-files@planning-with-files` | false | 退 | 已是 false；「设计/方案/plan」由 superpowers:writing-plans 接，不复开 | enabledPlugins 键保持 false |
| `ralph-loop@claude-plugins-official` | true | 退 | 只用过一次，对不上情境清单；同形状的内置 /loop skill 已在，重复且另一件是原生 | enabledPlugins 键设 false |
| `ui-ux-pro-max@ui-ux-pro-max-skill` | true | 退 | 零痕迹或用两天即停；UI 线的视觉决策走 DESIGN.v2 + artifact-design，不靠它 | enabledPlugins 键设 false |
| `frontend-design@claude-plugins-official` | true | 退 | 零痕迹或用两天即停；同上，前端设计的口径在 DESIGN.v2，不需要第二个审美源 | enabledPlugins 键设 false |
| `vercel@claude-plugins-official` | true | 退 | 零痕迹；部署走 main→Vercel 自动，且 deploy --prod 是须 Andy 先批的外部动作，不该有 skill 一键化 | enabledPlugins 键设 false |
| `claude-code-setup@claude-plugins-official` | true | 退 | 零痕迹；对不上任何情境（自动化推荐器） | enabledPlugins 键设 false |
| `claude-security@claude-plugins-official` | true | 退 | 零痕迹；本仓库是静态 JSON + 前端，安全扫描不在情境清单 | enabledPlugins 键设 false |
| `code-review@claude-plugins-official` | true | 退 | 零痕迹；只接 PR，本仓库不走 PR 审阅流；「发布前」情境由内置 code-review skill（非插件）接 | enabledPlugins 键设 false |
| `impeccable@impeccable` | true | 退 | 零痕迹或用两天即停；与 frontend-design/ui-ux-pro-max 同形状，三件一起退 | enabledPlugins 键设 false |

---

## 1. 冲突组（同 situation ≥ 2 件，共 7 组）

先说 brief 点名的四组：**含 gstack 的三组已随 gstack 整套退役而解散**——`~/.claude/skills/_retired/` 下现在躺着 gstack、review、qa、spec、ship、plan-* 等整套，它们不再出现在清单 JSON 里，所以不必再判「留谁」。四组里剩下真要判的只有一对：`code-review`（插件）vs `superpowers:requesting-code-review`。

| 情境 | 组员 | 留哪个 | 为什么 |
|---|---|---|---|
| 写中文给 Andy | fable-voice(修)、shuorenhua(修) | 两件都留（都是「修」） | 不是重复是分工：shuorenhua 管手术流程（场景→Tier→档位），fable-voice 管 Andy 裁决过的病例账；fable-voice 已把 shuorenhua 当上游规则书引用。修法：两件的 description 都补 Andy 的说法「翻译体 / AI 腔 / ai slop / 机器印的」。 |
| 周检 | contract-clerk(用)、growth-officer(用)、repo-janitor(用)、writing-skills(退) | contract-clerk、growth-officer、repo-janitor 留；writing-skills 退 | 三件子 agent 各盘一样东西（契约行 / 增长台账 / git 体检），没有交集；writing-skills 与 anthropic-skills:skill-creator 做同一件事，官方件自带 eval 与触发优化脚本，且本件的「描述不写做什么」与本次打分条相反——三次律固化 skill 时统一指向 skill-creator。 |
| 内容产线 | podcast-to-md(用)、video-subtitles(修) | 两件都留 | 输入物不同：podcast-to-md 吃 URL、产逐字稿/口播稿；video-subtitles 吃本地录像、产 EN/ZH .srt，且被 Selection Lab 设计文档写成正式环节。只在「转写」一步重叠。 |
| 设计/方案/plan | brainstorming(修)、writing-plans(修) | 两件都留（都是「修」） | 串联关系不是竞争：brainstorming 出 spec，writing-plans 出实施计划。修法写进任务书：只在新工程/不可逆事项启用 brainstorming（可逆小事直接出预览稿），writing-plans 的计划头补立项三件套、存 proposals 而非 docs/superpowers/。 |
| 查 bug | dispatching-parallel-agents(修)、systematic-debugging(修) | 两件都留（都是「修」） | systematic-debugging 管单个 bug 的四阶段；dispatching-parallel-agents 管多个独立失败的并发派单，与 CLAUDE.md「何时用多 agent」同向。任务书写触发词「查 bug / 复发 / 事故」与「>10 同构项」。 |
| 写代码前 | executing-plans(退)、subagent-driven-development(修)、test-driven-development(修)、using-git-worktrees(修) | subagent-driven-development、test-driven-development、using-git-worktrees 留；executing-plans 退 | executing-plans 自己写明「有子 agent 时改用 SDD」，Claude Code 一直有子 agent，它是被同套件覆盖的兜底版。留下三件各管一段：隔离树 → 红绿 → 逐任务派单；using-git-worktrees 的兜底目录与分支策略须被任务书覆盖成 mktemp + origin/main detached HEAD。 |
| 收工 | finishing-a-development-branch(修)、verification-before-completion(修) | 两件都留（都是「修」） | verification-before-completion 与「push 成功≠投递成功」同形状，直接对上；finishing-a-development-branch 的「本地 merge」选项与主树保护六条冲突，任务书钉死只走「推分支」或「白名单内自合」。 |
| 做图表/artifact（清单内单件，对手在清单外） | lieflat-charts(退) + dataviz、data:create-viz、data:data-visualization | 留 dataviz（内置），lieflat-charts 退 | dataviz 是 Artifact 工具强制前置加载的、色板可换成 DESIGN token；lieflat 锁 Mono/Inter、禁混色系，与 DESIGN.v2 的 Plex + 蓝红配对冲突，且 PolyForm Noncommercial 许可，能学的样式规则 DESIGN.v2 已学完。 |
| 发布前（清单内单件，对手在清单外） | requesting-code-review(退) + code-review、code-review:code-review | 都不留：留内置 code-review skill（harness 自带，非插件） | requesting-code-review 只是手填模板派子 agent；code-review 插件零痕迹且只接 PR，本仓库不走 PR 流。内置 code-review 原生支持 diff/分支/路径目标、--fix 与 ultra 多 agent 云审，是三者里最好的一件。 |

情境为「无」的 5 件（tearsheet、openmaic、youtube-clipper、receiving-code-review、using-superpowers）不进冲突组：对不上情境本身就是退役理由，tearsheet 的两个同名件（daloopa / sp-global）是外部数据源的公司一页纸，与我们个股页的 ai_synthesis 字段不是同一件事，不构成「留谁」的问题。

## 2. 体系判定

**superpowers = 开发主线（控制器已裁）。** 它在清单里共 14 件：

- **有情境、留用（9 件，全为「修」）**：brainstorming（设计/方案/plan）、dispatching-parallel-agents（查 bug）、finishing-a-development-branch（收工）、subagent-driven-development（写代码前）、systematic-debugging（查 bug）、test-driven-development（写代码前）、using-git-worktrees（写代码前）、verification-before-completion（收工）、writing-plans（设计/方案/plan）。共同缺口是 description 零中文触发词，且其中 brainstorming、dispatching-parallel-agents、finishing-a-development-branch、subagent-driven-development、using-git-worktrees、writing-plans 的默认动作与宪法条（决策分级、主树保护六条、safe-merge、立项三件套、临时树规矩）相冲——第三方文件不改，冲突覆盖句写进各线任务书的『该用 skill』一句。
- **无情境或被覆盖、退（5 件）**：executing-plans（被 subagent-driven-development 覆盖）、receiving-code-review（无情境）、requesting-code-review（被 code-review/code-review:code-review 覆盖）、using-superpowers（无情境）、writing-skills（被 anthropic-skills:skill-creator 覆盖）。第三方件不删，「退」的含义是任何任务书不指向它。
- **using-superpowers 是特例**：它是插件的路由器，随插件自动注入、无法单独卸下；它的「1% 就必须调」与 CLAUDE.md 决策分级相悖，但它自述 CLAUDE.md 优先，所以现状可忍——要真停只能整体停 superpowers 插件，那是 Andy 的裁决，本审计不建议。

**其余层次**：本仓库自有件（project-agent 3 件 + fable-voice）全部留用；用户级 skill 6 件里留 3 件（podcast-to-md、shuorenhua、video-subtitles），退 3 件；插件层只留 superpowers、document-skills。路由不再靠 SKILL_ROUTER（已废），靠三样：官方 description 触发 + 各线任务书的『该用 skill』句 + 本文件作为周检基线。

## 3. 归档清单（「退」9 件 + 插件 9 个键）

| 件 | 层 | 动作 | 一句原因 |
|---|---|---|---|
| tearsheet | project-command | git mv .claude/commands/tearsheet.md 到 .claude/commands/_retired/tearsheet.md（主树与 skill-os-v2 worktree 各一份，两处同步） | 三个多月零调用、情境清单无「个股页 AI 段」；页面读 ai_synthesis 不受影响 |
| lieflat-charts | user-skill | mv ~/.claude/skills/lieflat-charts 到 ~/.claude/skills/_retired/lieflat-charts | dataviz 覆盖且更好；锁色系与 DESIGN.v2 冲突、非商用许可 |
| openmaic | user-skill | mv ~/.claude/skills/openmaic 到 ~/.claude/skills/_retired/openmaic | 课堂生成器安装向导，与十四情境无一对应，零调用 |
| youtube-clipper | user-skill | mv ~/.claude/skills/youtube-clipper ~/.claude/skills/_retired/ | 零调用、无「剪 YouTube 短视频」情境，两步分别被 podcast-to-md / video-subtitles 做掉 |
| executing-plans | plugin-skill | 第三方不改；任何任务书的『该用 skill』句都不指向本件，同情境统一指向 subagent-driven-development | 自述有子 agent 时让位 SDD，是被同套件覆盖的兜底版 |
| receiving-code-review | plugin-skill | 第三方不改；任何任务书的『该用 skill』句都不指向本件 | 「处理审阅意见」不在情境清单，精神已在 CLAUDE.md 与记忆里 |
| requesting-code-review | plugin-skill | 第三方不改；任务书『该用 skill』句在「发布前」情境统一指向内置 code-review，不指向本件 | 内置 code-review 做同一件事且更好 |
| using-superpowers | plugin-skill | 第三方不改；插件自动注入无法单独卸下，任何任务书的『该用 skill』句都不指向本件；要停用只能整体停 superpowers 插件（须 Andy 裁） | 路由器不是干活件，无法单独卸下，只是不被任务书引用 |
| writing-skills | plugin-skill | 第三方不改；任务书『该用 skill』句在「周检/固化 skill」情境统一指向 anthropic-skills:skill-creator，不指向本件 | anthropic-skills:skill-creator 官方件更好，且描述写法与打分条相反 |
| `planning-with-files@planning-with-files` | enabledPlugins | enabledPlugins 键保持 false | 已是 false；「设计/方案/plan」由 superpowers:writing-plans 接，不复开 |
| `ralph-loop@claude-plugins-official` | enabledPlugins | enabledPlugins 键设 false | 只用过一次，对不上情境清单；同形状的内置 /loop skill 已在，重复且另一件是原生 |
| `ui-ux-pro-max@ui-ux-pro-max-skill` | enabledPlugins | enabledPlugins 键设 false | 零痕迹或用两天即停；UI 线的视觉决策走 DESIGN.v2 + artifact-design，不靠它 |
| `frontend-design@claude-plugins-official` | enabledPlugins | enabledPlugins 键设 false | 零痕迹或用两天即停；同上，前端设计的口径在 DESIGN.v2，不需要第二个审美源 |
| `vercel@claude-plugins-official` | enabledPlugins | enabledPlugins 键设 false | 零痕迹；部署走 main→Vercel 自动，且 deploy --prod 是须 Andy 先批的外部动作，不该有 skill 一键化 |
| `claude-code-setup@claude-plugins-official` | enabledPlugins | enabledPlugins 键设 false | 零痕迹；对不上任何情境（自动化推荐器） |
| `claude-security@claude-plugins-official` | enabledPlugins | enabledPlugins 键设 false | 零痕迹；本仓库是静态 JSON + 前端，安全扫描不在情境清单 |
| `code-review@claude-plugins-official` | enabledPlugins | enabledPlugins 键设 false | 零痕迹；只接 PR，本仓库不走 PR 审阅流；「发布前」情境由内置 code-review skill（非插件）接 |
| `impeccable@impeccable` | enabledPlugins | enabledPlugins 键设 false | 零痕迹或用两天即停；与 frontend-design/ui-ux-pro-max 同形状，三件一起退 |

执行顺序：本地 mv（用户级 skill）与 git mv（tearsheet，两树同步）都可逆、只影响我们自己的目录，OPS 可直接做；插件键设 false 是改 `~/.claude/settings.json` 配置，按「外部动作」条先问 Andy 一句再动。

## 4. 抽查（随机抽「退」3 件，重读原文件）

抽样：`random.seed(20260904)` 对「退」名单 `random.sample(_, 3)`，抽中 lieflat-charts、youtube-clipper、using-superpowers。

| 件 | 重读到什么 | 结论 |
|---|---|---|
| lieflat-charts | `~/.claude/skills/lieflat-charts/SKILL.md` 开头即写「以 Mono 为保底」「同一交付禁止混用色系」「必须从仓库模板生成，违反任意一条都必须返工」；description 只讲它是什么，没有一句「什么时候用」；仓内 `DESIGN.v2.md:1028` 原文「全部自己实现——lieflat 是 PolyForm Noncommercial，只学它公开的样式规则」。 | **站得住。** 硬约束与 DESIGN.v2 的蓝红配对正面冲突，能学的已学完，dataviz 是 Artifact 强制前置件。 |
| youtube-clipper | frontmatter 硬钉 `model: claude-sonnet-4-5-20250514`，正文第一行让人去 `npx skills add op7418/Youtube-clipper-skill` 装，是第三方仓原样；目录 mtime 停在 02-01；六阶段全是「下载别人的 YouTube→剪→烧字幕」。 | **站得住。** Fluxus 内容产线没有这一环，钉死的旧模型名也说明没人维护过。 |
| using-superpowers | 6.3.0 版原文：`If you think there is even a 1% chance a skill might apply... you ABSOLUTELY MUST invoke`；同时有 `<SUBAGENT-STOP>` 和末段「User instructions (CLAUDE.md...) take precedence over skills」。 | **站得住。** 它确实是路由器而非干活件；CLAUDE.md 优先的自述让现状可忍，但仍不该被任何任务书引用为依据，「退」的动作（不引用）没有改的必要。 |

抽查改判 0 件。

---

## 收工三问

1. **坑**：插件层不在清单脚本里（它只扫了 superpowers 的目录），判定靠能力盘点的痕迹而不是 JSON——下轮 `skill_inventory.py` 应把 enabledPlugins 也扫进去，否则这一层每次都是手判。
2. **规矩**：「散文里不许手打数字」这条帮了忙——正文所有计数由生成脚本从 JSON 数出，表格与结论天然对齐；建议周检的所有盘点报告都用同一做法。
3. **下轮第一件事**：Andy 点头后执行第 3 节归档；然后把 `修` 组的触发词写进各线任务书的『该用 skill』句（skill-os-v2 plan 的对应 Task）。
