# 技能操作系统 v2 — 按官方机制重写

*2026-09-04 · OPS Fable · Andy 批「点头，按官方的改 spec 和计划」*
*v1（路由表 + 两个 hook）已废；废的原因在 [`2026-09-04-skill-os-vs-official.md`](2026-09-04-skill-os-vs-official.md)。*

## 一、要解决的问题（不变）

零件在传送带没有：62 个第三方 skill 绝大多数零使用、3 个自建 agent 08-23 后零调用、hooks 三处全无、
本机定时任务曾因权限提示冻住 27 小时。Andy 要的是：skill 在对的时刻被用、用完按固定流程变好、planning 走同一条路。

## 二、v1 → v2 改了什么

| v1 | v2 | 为什么 |
|---|---|---|
| SKILL_ROUTER.md 路由表 + hook 甲每条消息注入 | **砍。** 触发走官方：`description`（pushy）+ `when_to_use` + `paths:`；触发率用 skill-creator 的描述优化器**量出来** | 路由表在替模型做官方让 description 做的事；官方原话「Claude has a tendency to undertrigger — make descriptions a little bit pushy」 |
| hook 乙解析 transcript | **留**，简化：读 Stop 输入自带的 `last_assistant_message` | 官方 Stop hook 直接给这个字段 |
| 「裁决记录」是唯一迭代 | 裁决记录**降级为反馈输入**；迭代主回路换成官方两套：technique skill 走 skill-creator 评估（带/不带 skill 对照 → benchmark → 人评 → 改），discipline skill 走 writing-skills 的文档 TDD（先跑没有 skill 的基线、记借口、再写） | 我们只有定性裁决，没有基线，永远不知道改好还是改坏 |
| 周检数「7 天内有裁决的行数」 | 换成能量的：有 evals.json 的 skill 数 · 最近一次 benchmark 的 delta · 描述优化器的触发率 · `/plugin`「Not used recently」条数 | 官方指标，不是我们发明的 |
| 没管权限 | **补根**：用户级 `~/.claude/settings.json` 加 allow 规则；本机每个定时任务在桌面端表单里设权限模式（Andy 手点） | 27 小时冻住的根在这层；项目级设 auto 不生效 |
| — | `.claude/commands/tearsheet.md` 迁 `skills/` | 官方说 commands/ 是遗留位置 |

## 三、架构：全部是官方零件

```
触发   description + when_to_use + paths:  ──(量)──►  skill-creator run_loop.py 触发率
用     skill 被调 → 干活 → 收工写 skill-used/skipped/none 行 ──(查)──► hook 乙 (Stop)
变好   technique: evals.json → 带/不带对照 → benchmark → eval-viewer → feedback → 改
       discipline: 基线（没有 skill 时的借口）→ 写 skill 堵借口 → 压力场景复测
留痕   每个 skill 末尾「裁决记录」= 上面 feedback 那一步的人话版
```

### 3.1 触发（替代路由表）
每个保留的 skill：
- `description`：第三人称、含**做什么 + 什么时候用**、把 Andy 的中文说法和项目黑话写进去（「出题」「盘一遍」「这里乱了」）。
- `when_to_use`：补触发条件（与 description 共 1,536 字符）。
- `paths:`：只在改匹配文件时才自动加载的 skill 用它（code-cartography 前端分册 → `frontend/src/components/**`）。
- **触发率是数**：20 条真实问句（8–10 该触发、8–10 不该触发且是近似题），`run_loop.py` 每句跑 3 次、60/40 训练测试、最多 5 轮，取测试集最优 description。**没跑过优化器的 skill 不算上线。**

### 3.2 迭代回路（替代「只有裁决账」）
- **technique skill**（code-cartography、tearsheet、抓取类）：`evals/evals.json` 2–3 条真实任务 → 同一 prompt 带 skill / 不带 skill 各起一个 subagent 同时跑 → assertions → `aggregate_benchmark.py` → `generate_review.py` 给 Andy 看 → `feedback.json` → 改 → `iteration-N+1/`。
- **discipline skill**（fable-voice、直推 main、永不群发这类「知道也会违反」的）：按 writing-skills 的 RED-GREEN-REFACTOR——先在**没有** skill 的 subagent 上跑 3+ 压力场景（时间 + 沉没成本 + 权威），逐字记它的借口；skill 只写堵这些借口的话；带 skill 复测；出现新借口再堵。
- **裁决记录**保留，作为 feedback 那一步的人话版；Andy 每裁一次追一行，下一轮迭代读它。
- 三次律接口不变：同一 skill 被划三次 → 必须改或退。

### 3.3 hook 乙（留，简化）
- Stop 事件；读 stdin JSON 的 `last_assistant_message`，grep `skill-(used|skipped|none):`；没有 → `decision: block`，reason 写补哪一行；`stop_hook_active=true` → 放行。官方有 8 次连续 block 上限兜底。
- `.claude/settings.json` 提交进仓库（官方原话「Commit a setting there to apply it in cloud sessions」）。
- 各任务书收工节加固定行；个人类任务写死 `skill-none`。

### 3.3b hook 丙（新增，Andy 09-04「改成 TaskCompleted hook」）
- **和 hook 乙不是一回事**：乙守「收工有没有留痕」（Stop），丙守「任务标完成前它点名的测试是不是绿的」（TaskCompleted）。两个都要。
- 官方契约（hooks 参考页原文）：事件在 `TaskUpdate` 标 completed 时触发；输入带 `task_id` `task_subject` `task_description`；**阻止＝exit 2，stderr 原文回给模型**（`continue:false` 对 TaskUpdate 触发的场合被忽略）。官方示例就是「跑测试，不过 exit 2」。
- 我们的版本：从 `task_subject + task_description` 里抓 `pipeline/tests/test_*.py` 路径，只跑点名的（全套收集就超两分钟，不能每次全跑）；没点名测试的任务（文档、归档）放行；红了 exit 2 并把 pytest 尾巴 15 行塞进 stderr。
- **它守的是「绿」，不是「先红后绿」。** 先写会红的测试这一步，hook 量不到——它只看完成那一刻。红-先靠三样：writing-plans 把「跑测试确认失败」写成独立步骤、SDD 的 reviewer 审 spec 符合性、每个 agent 预加载 `superpowers:test-driven-development`（官方：subagent 可 `skills:` 预加载）。这是诚实的边界，别把 hook 丙说成 TDD 闸。
- 同样写进 `.claude/settings.json`（入库），与 Stop 并列。

### 3.4 权限补根
- 用户级 `~/.claude/settings.json`：`permissions.allow` 加这个项目定时任务实际用的只读命令与 git 读命令（从 transcript 统计，不是拍）。
- 本机 10 个定时任务：**Andy 在桌面端逐个「Run now → always allow」**（官方唯一解法），或在编辑表单设权限模式。这一步只有他能做。
- 云端 routine 不需要（官方：没有权限提示）。

### 3.5 现存 79 件的四档处置（判据改）
| 档 | 判据 | 动作 |
|---|---|---|
| 用 | 有情境 + **描述优化器测试集触发率 ≥ 80%**（或 discipline skill 压力场景通过） | 进 verdicts.md「用」 |
| 修 | 有情境但触发率 < 80% | 重写 description/when_to_use，再跑优化器 |
| 退 | 零调用 + 对不上情境，或与另一件重复 | gstack 56 个整套搬到 `~/.claude/skills/_retired/`；自建 agent 搬 `.claude/agents/_retired/`；`enabledPlugins` 该关的关；verdicts.md 留一行 |
| 建 | 三次律 ≥3 且无现成品 | 先跑基线（没有它时 agent 怎么失败），再写，再评估 |

### 3.6 首批住户
| 事 | 处置 | 触发方式 | 迭代方式 |
|---|---|---|---|
| 代码重构整理 + 组件整理 | 建 `code-cartography`（同一 skill，前端分册用 `paths:`） | description + `paths: frontend/src/components/**` | technique：evals 对 WatchlistPage（1,195 行）带/不带对照 |
| handoff | 不建；HANDOFF.md + hook 乙 | — | — |
| planning | 用现成 superpowers（brainstorming → writing-plans → subagent-driven-development） | 已批；内置 Plan Mode 是零安装备选 | 第三方，裁决记 verdicts.md |
| 写中文给 Andy | fable-voice（唯一自建） | 重写 description 跑优化器 | discipline：压力场景 |

## 四、验证（怎么知道它在跑）
周检第一节四个数：**有 evals.json 的 skill 数 / 最近 benchmark 的 with−without delta / 描述优化器测试集触发率 / `/plugin` Not-used-recently 条数。** 上线第一周每天记，第一个数不涨就是死的。

## 五、风险
| 风险 | 处理 |
|---|---|
| `claude -p` OAuth 过期（09-04 实测），优化器与评估跑不了 | **Andy 交互终端 `claude login`**；这是阶段三的前置，只有他能解 |
| 描述优化器要真问句，写假的会过拟合 | 问句从 Andy 的真实消息与 Discord 语料里抄，含错别字 |
| hook 乙误拦定时会话 | `skill-none` 放行；先在哨兵 routine 试一天 |
| 搬走 gstack 后 Andy 某天要用 | 目录在 `_retired/`，搬回即恢复；gstack 自带 `gstack-upgrade` |
| 评估回路每轮起 4–6 个 subagent，费 token | 每个 skill 首轮 2–3 条 eval 即可，官方原话「Keep the prompt lean」 |

## 六、不做
不做路由表；不做中央调度；不改第三方 skill 的文件；不给 gstack 逐个评估（整套退）；不在本轮做 planning-with-files 的 session-catchup（HANDOFF 已够用，列为 v3 候选）。
