# 我们的架构 vs 官方 harness — 对账表

*2026-09-04 · OPS Fable · Andy 原话：「完整地阅读官方文件以及官方使用 harness 的方式，然后看看我们的架构是不是 100% 契合，我们是不是用各种各样的东西拼凑起来……先学习再规划。」*

**读了什么**：六路 claude-code-guide agent 分读官方文档（skills / subagents / hooks / settings / memory / scheduled tasks / routines / plan mode / workflows / worktrees / plugins / permissions），每条结论带 URL；本机四份官方件我逐行读完：`skill-creator/SKILL.md`（485 行）、superpowers `writing-skills/SKILL.md`（679 行）、Anthropic `anthropic-best-practices.md`（关键章节）、`testing-skills-with-subagents.md`（384 行）、`CLAUDE_MD_TESTING.md`。所有「我们的现状」数字都当场实测，不转抄。

## 一句话结论

**底层容器全是官方的，不是拼凑。拼凑的是我们在容器之上又造了一层，而官方的「越用越好」回路装在本机从来没跑过。**

具体到我昨天设计的技能操作系统：**hook 乙（收工留痕）是正统的，hook 甲＋路由表不是**——它在替模型做官方让 description 自动匹配的活。

## 对账表

判定词：**契合** = 官方就是这么设计的 · **拼凑** = 官方有正道我们另造了一个 · **官方没覆盖** = 我们在填官方的空白 · **没用上** = 官方有现成的我们装了没跑

| # | 我们的东西 | 官方机制 | 判定 | 证据 |
|---|---|---|---|---|
| 1 | memory/ 目录 + MEMORY.md 索引 + 四种 type | 官方 auto memory 原样：`~/.claude/projects/<p>/memory/`，索引前 200 行/25KB 加载，type ∈ user/feedback/project/reference | **契合** | 索引实测 170 行，离上限 30 行；官方无自动去重/过期，靠人 |
| 2 | 项目 CLAUDE.md | 官方目标 ≤200 行；超了用 `.claude/rules/` 按路径加载 | **契合** | **实测 193 行**（我此前口头说 250 是错的） |
| 3 | 直推 main 标准动作（临时树基于 origin/main） | worktrees 文档：隔离 checkout、基于 origin/main | **契合** | — |
| 4 | Workflow fan-out（13 agent 消费图）· Explore agent 盘点 | workflows 文档：5–30 agent 用 Workflow；Explore 是内置 agent | **契合** | — |
| 5 | 本机 13 定时 + 云端 4 routine 混搭 | 官方原话：cloud for reliability without your machine, Desktop when you need local files | **契合** | 官方明确支持混搭 |
| 6 | INBOX.md append-only + push main 当跨 routine 信箱 | 云端 routine 不在会话消息网络里，git 是官方通道 | **契合**（云端）| 本机定时任务不能 push 的部分靠共享目录，这一半是我们自己的 |
| 7 | `.claude/settings.json` 提交进仓库让云端吃到 hook | 官方原话「Commit a setting there to apply it in cloud sessions」 | **契合** | 三层里只有项目级对云端生效 |
| 8 | hook 乙：Stop 时查 `skill-used/skipped/none` 留痕 | Stop hook 输入直接带 `last_assistant_message` 与 `stop_hook_active`；`decision:block` 有 8 次连续上限；command 型是最正统 | **契合**，且能简化 | 不用解析 transcript；planning-with-files 插件的 `check-complete.sh` 就是同款 Stop hook |
| 9 | **SKILL_ROUTER.md + hook 甲每条消息注入路由表** | 官方触发机制＝模型按 `description`（+ `when_to_use`）自动匹配；`paths:` 让 skill 只在改匹配文件时自动加载；skill-creator 有**描述优化器**（`run_loop.py`：20 条该触发/不该触发的真实问句，60/40 训练测试，每句跑 3 次，迭代 5 轮，按测试集选最优 description） | **拼凑** | 我们在手工做编译器的活；官方原话「Claude has a tendency to undertrigger skills — make the descriptions a little bit pushy」 |
| 10 | 3 个 `.claude/agents/`（08-23 后零调用） | subagent 靠 description 自动委派或 `@agent-名` 显式；可 `skills:` 预加载；`isolation: worktree`、`background: true` | **拼凑** | 从没调过 description；没人 @ |
| 11 | 62 个用户级 skill（56 个是 gstack 一套） | 官方有预算机制：`skillListingBudgetFraction`、`skillOverrides: name-only`、`/doctor` 看占用、`/plugin` Installed 页有「Not used recently」（≥2 周 ≥10 会话未用） | **没用上** | gstack 是整套装的，该在插件层关，不是逐目录搬 |
| 12 | 迭代学习＝手工：踩坑→memory→第 3 次→机制；fable-voice 末尾手追裁决 | 官方是**工业级回路**：skill-creator 评估（同一 prompt 带 skill / 不带 skill 各起一个 subagent → assertions → benchmark.json 均值±标准差 → eval-viewer 给人看 → feedback.json → 改 → 下一轮；盲评 A/B）；superpowers writing-skills 是「文档的 TDD」：**先跑没有 skill 的基线、逐字记下 agent 的借口，再写 skill 堵那些借口** | **没用上** | 我们只有定性裁决，没有基线对照；官方原话「If you didn't watch an agent fail without the skill, you don't know if the skill teaches the right thing」 |
| 13 | 规划：superpowers brainstorming → spec → writing-plans → plan | 内置 Plan Mode（Shift+Tab / `--permission-mode plan`，Ctrl+G 改计划）是零安装正道；superpowers 是官方 marketplace 分发的**社区**插件（obra），加了 TDD 与逐任务审查 | **契合但要知道来路** | 两条都合法；superpowers 更严，Plan Mode 更轻 |
| 14 | 权限：用户级/项目级都没设 defaultMode，allow 规则 0 条；本机定时任务冻住 27 小时 | 桌面定时任务的权限模式**在每个任务的编辑表单里单独设**（任务书文件没这个字段）；官方解法「Run now → 逐个 always allow」；用户级 `~/.claude/settings.json` 的 allow 规则定时任务也吃；**项目级 settings 设 auto/dontAsk/bypass 不生效** | **拼凑**（我们用迁云端绕过了，没修根） | Andy「设了 auto 看到 manual」的解释在这里 |
| 15 | `.claude/commands/tearsheet.md` | commands/ 是遗留位置，官方原话「Use `skills/` for new plugins」 | **拼凑** | 迁到 `.claude/skills/tearsheet/SKILL.md`，调用名不变 |
| 16 | Ralph loop 5 小时自迭代 | 官方定位：会话内 Stop hook 循环；`/loop` 7 天过期、要会话开着；无人值守的正道是 routine | **契合但有边界** | 用来做单会话冲刺可以，别当持久机制 |
| 17 | HANDOFF.md + 任务书收工节 + 晨报回执节 | 官方**没有** handoff 文档概念；会话独立，只有 `--continue/--resume`；社区 planning-with-files（已装、**禁用中**）有 `session-catchup.py` + task_plan/findings/progress 三件套 | **官方没覆盖** | 我们在填空白；planning-with-files 是同题另一解 |
| 18 | 三次律（同形第 3 次升机制）· 收工三问 · 永不群发 | 官方没有 memory→CLAUDE.md 的晋升路径；没有收工范式；cross-session-messaging 文档只管交互会话 | **官方没覆盖** | 逻辑通，保留 |

## 三条最重的发现

### 1. 触发不靠路由表，靠 description——而且这件事能量出来
官方对「skill 为什么没被用」的回答不是「加一张表」，是：description 写得不够「pushy」。skill-creator 附带的描述优化器把它变成一个可测的数：给 20 条 Andy 真实说法（含错别字、中文、项目黑话），标记该触发/不该触发，脚本用 `claude -p` 每句跑三遍算触发率，再让模型改 description，迭代五轮，按**留出测试集**选最好的那版。**我们昨天设计的路由表，官方早就做成了自动化，而且装在这台机器上。**

配套两个我没用过的 frontmatter 字段：`when_to_use`（与 description 共享 1,536 字符）、`paths:`（只在改匹配文件时自动加载——「改 frontend/src/components/ 前」这条路由，官方一个字段就解决）。

### 2. 「越用越好」官方有整套，我们的裁决账只是它的第五步
skill-creator 的回路：**同一个 prompt，带 skill 和不带 skill 各起一个 subagent 同时跑** → 断言 → benchmark（均值±标准差、delta）→ eval-viewer 给人看 → 人写 feedback.json → 改 skill → 下一轮 → 还能盲评 A/B。
superpowers 的 writing-skills 更狠：**先跑没有 skill 的基线，逐字记下 agent 找的借口**（「我已经手测过了」「事后补测试效果一样」），skill 只写堵这些借口的话；它甚至附了一份测 CLAUDE.md 四种写法哪种能让 agent 真去查 skill 的战役方案。
我们的「裁决记录」= 上面那个 feedback.json 那一步，**没有基线对照**——所以永远不知道 skill 改好了还是改坏了。fable-voice 首裁「都批」是定性的，官方要的是「带它 vs 不带它，通过率差多少」。

### 3. 27 小时冻住的根在权限层，不在任务书
桌面定时任务的权限模式**不在 SKILL.md 里**（文件只有 name/description），在桌面端每个任务的编辑表单里；用户级 settings 的 allow 规则定时任务也会吃——而我们两处**全是空的**（allow 0 条、defaultMode 未设）。官方原话还说项目级 settings 设 `auto` 不生效。所以「我明明设了 auto」很可能设在了不生效的层。我们把三个班次迁到云端是对的（云端**根本没有权限提示**），但留在本机的 10 个还是裸的。

## 官方装了、我们没跑过的清单

| 东西 | 在哪 | 干什么 |
|---|---|---|
| skill-creator 描述优化器 `scripts/run_loop.py` | `~/.claude/plugins/cache/anthropic-agent-skills/document-skills/*/skills/skill-creator/` | 量触发率、自动改 description |
| skill-creator 评估回路 + `eval-viewer/generate_review.py` | 同上 | 带/不带 skill 对照，出 benchmark |
| superpowers `writing-skills` + `testing-skills-with-subagents.md` | `~/.claude/plugins/cache/claude-plugins-official/superpowers/6.2.0/skills/` | 文档的 TDD；压力场景测 discipline skill |
| `paths:` / `when_to_use` / `context: fork` / `disable-model-invocation` frontmatter | skills 文档 | 精准触发，不用路由表 |
| `/doctor`、`skillOverrides`、`skillListingBudgetFraction` | settings | skill 预算可视化与降噪 |
| `/plugin` Installed 页「Not used recently」 | 交互终端 | 官方自带的「没人用」审计 |
| planning-with-files（已装、禁用） | `~/.claude/plugins/cache/planning-with-files/` | task_plan/findings/progress + Stop hook 查完成 + session-catchup 交接恢复 |
| Plan Mode + Ctrl+G | 内置 | 零安装的规划路径 |

## 这对昨天那份 spec 意味着什么（只列方向，规划下一步再定）

- **砍**：SKILL_ROUTER.md、hook 甲。
- **留**：hook 乙（改用 `last_assistant_message`，更简单）、`.claude/settings.json` 入库、裁决记录（作为 feedback 那一步）。
- **换成官方的**：每个保留的 skill 改写 description（pushy、含 Andy 的中文说法）+ `when_to_use` + 该用 `paths:` 的用 `paths:`；跑一次描述优化器拿到触发率；新 skill 先跑基线（不带 skill 让 agent 失败一次）再写；gstack 在插件层关。
- **补根**：本机 10 个定时任务逐个设权限模式 + 用户级 allow 规则；`.claude/commands/tearsheet.md` 迁 skills/。
- **周检的那个数**换成官方能量的：有评估集的 skill 数 · 最近一次 benchmark 的 delta · 「Not used recently」清单长度。

## 我自己这轮的两条坑（收工三问①）
1. **转抄过期数**：CLAUDE.md「约 250 行」说了三次，实测 193——违反「数字只有一个家」，且差点让一条判定（超规）成立。
2. **本会话开头就加载了 superpowers 的 using-superpowers（写着「有 1% 可能适用就必须调用」），我干了一整天没调用**，直到 Andy 点破。这不是记忆问题，是 skill 的 description 没让我「必须」——正是官方描述优化器要治的病，我是活样本。
