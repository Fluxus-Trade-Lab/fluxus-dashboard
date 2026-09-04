# 技能操作系统 v1 — 设计

> ⚠️ **已被 v2 取代**（2026-09-04 读完官方文档后重写）：路由表 + hook 甲被砍，触发改走官方 description 机制。看同目录 `*-skill-os-v2*`。本文件留作对照。


*2026-09-04 · OPS Fable · Andy 已批架构（原话「我当然选择硬规矩」「写成 spec 提交，然后出实施计划」）*

## 一、要解决的问题（有读数）

09-04 能力盘点的结论：**零件在，传送带没有。**

| 东西 | 数量 | 使用痕迹 |
|---|---|---|
| 用户级第三方 skill 目录 | 62 | 绝大多数零使用（`health` `retro` `review` `context-save/restore` `document-generate` 等全零） |
| 自建 agent（`.claude/agents/`） | 3 | `repo-janitor` `contract-clerk` 08-23 后零调用 |
| 自建 skill（`.claude/skills/`） | 1（`fable-voice`） | 09-02 建，有首裁记录——**唯一在迭代的** |
| superpowers 体系 | 14 个 skill | **用过**：5 份 spec + 8 份 plan（05-24 → 08-08），之后停 |
| impeccable | 1 | 用了两天（08-18）停 |
| hooks | 0 | 三处 settings 全无 |

根因不是缺 skill，是三件事没有：
1. **路由**：没有一张表说「什么情境该用哪个」，模型只能靠自觉。
2. **回流**：用完没有固定动作把裁决写回菜谱，所以菜谱不会变好（fable-voice 是唯一例外，因为它手工在做）。
3. **验证**：没有任何东西检查「skill 是否真被调用了」——闸对、测试对、没人调用，这个形状已经栽过三次。

Andy 的目标（原话）：「变成一个运用，然后可以把这个菜谱调整得越来越好」「说到 plan 时应该自动调取」「用固定的流程把它写死，然后包括迭代的学习也好 planning 也好」。

## 二、目标 / 非目标

**目标**
- 每个会话（本机交互 / 本机定时 / 云端 routine）在每条消息进来时都能看到路由表。
- 收工必须留下「本轮用了什么 skill、要不要改它」的记录，否则不许收工。
- 每个 skill 有主人、有裁决账本；三十天无裁决自动标「退」。
- 现存 62+14+3 全部过一遍四档处置（用/修/退/建），不留「摆着」这一档。
- 三个首批住户挂上去：代码重构整理、组件整理、handoff；planning 走 superpowers 现成路径。

**非目标（v1 不做）**
- 不做中央调度 agent。
- 不做 PreToolUse 拦截（v2，等路由表被用满一个月）。
- 不给每个第三方 skill 写用法说明——要么进表要么退。
- 不改 superpowers 本身；只把它接进路由表。

## 三、架构：三个零件

```
消息进来 ──► hook 甲：注入路由表精简版 ──► 会话按表调 skill ──► 干活
                                                              │
收工 ◄── hook 乙：查「本轮 skill 记录」行，没有则打回 ◄──────────┘
                     │
                     └──► 裁决追进该 skill 的「裁决记录」节 ──► 下次更好
```

### 3.1 路由表 `SKILL_ROUTER.md`（仓库根目录）

一行一个 skill，列固定：

| 列 | 含义 | 例 |
|---|---|---|
| 情境 | 触发关键词/场景，写给模型看的 | `设计 / 方案 / plan / 要不要做` |
| skill | 精确名 | `superpowers:brainstorming` |
| 主人 | TEAM.md 线名 | OPS |
| 状态 | 用 / 修 / 退 / 建 | 用 |
| 上次裁决 | 日期 | 2026-09-04 |
| 备注 | 一句话 | 今天第一次真用；产出本 spec |

**规则**：
- 状态为「用」的行才会被 hook 甲注入；「修」「建」注入时带 ⚠️；「退」不注入。
- 「上次裁决」超过 30 天 → hook 甲注入时自动标 `⏳ 30 天无裁决`，连续两周后主人必须改状态。
- 表的维护权归 OPS；每行内容的裁决权归主人线；**改状态必须带一句理由**。

### 3.2 hook 甲（UserPromptSubmit）

- 位置：`.claude/settings.json`，**提交进仓库**——项目级设置对本机交互会话、本机定时会话、云端 routine（拉代码即得）三者同时生效。
- 行为：读 `SKILL_ROUTER.md`，取状态≠退的行，压成 ≤ 40 行的精简表，经 `hookSpecificOutput.additionalContext` 注入。
- 精简表末尾固定一句：**「本轮若用了任一 skill，收工前必须写一行 `skill-used: <名> · <裁决/无>`；若明知该用而没用，写 `skill-skipped: <名> · <原因>`。」**
- 失败模式：路由表不存在或解析失败 → 注入一行警告，不阻断。**hook 甲永不阻断。**

### 3.3 hook 乙（Stop）

- 行为：扫本会话最后一条 assistant 消息，grep `skill-used:` 或 `skill-skipped:`。有 → 放行。无 → `decision: block`，reason 写「收工前补一行 skill-used / skill-skipped」。
- **误拦出口**：
  - 消息含 `skill-none: 本轮无适用 skill` 也放行（诚实说没用比硬凑强）。
  - 定时/云端会话的最终汇报本来就有固定格式，把这一行加进各任务书的「收工」节即可。
- 不看 skill 用得对不对——那是裁决的事，不是 hook 的事。hook 只保证**留痕**。

### 3.4 迭代回路

- 每个 skill 的 SKILL.md 末尾固定一节 `## 裁决记录`，格式照 fable-voice：`### [日期] <批/划/改> · <一句话>`。
- 谁用谁追：会话在写 `skill-used:` 那一行时，若 Andy 或主人给了裁决，**同一轮**追进该 skill 的裁决记录并 push。
- 第三方 skill（superpowers / gstack）不改它们的文件；它们的裁决记录写在 `SKILL_ROUTER.md` 备注列 + 一份 `docs/superpowers/verdicts.md`。
- 三次律接口：同一 skill 被「划掉」三次 → 主人必须改它或退它，不许第四次。

## 四、现存 skill 审计（实施计划第一阶段）

Andy 追加的四问，逐个 skill 回答，结果落进 `SKILL_ROUTER.md`：

1. **有没有调用的必要**——对得上我们哪个情境？对不上就退。
2. **它怎么工作**——读 SKILL.md，一句话写清它做什么、产出什么。
3. **有没有重复/冲突**——同一情境有两个 skill（例：gstack `review` vs `code-review` vs superpowers `requesting-code-review`；gstack `context-save` vs 我们的 HANDOFF.md + 收工三问）→ 留一个，其余退。
4. **是不是已经成体系**——superpowers 是（brainstorm→plan→execute→TDD→debug→review→finish 全链）；gstack 是另一套（ship/review/qa/design-review 偏发布流程）。**两套不能都当主线**：v1 定 superpowers 为开发主线，gstack 只挑单件进表。

处置四档的判据：

| 档 | 判据 | 动作 |
|---|---|---|
| 用 | 有情境 + 有主人 + 30 天内有裁决或本轮实测能跑 | 进表 |
| 修 | 有用但 description 触发不了我们的说法（中文情境、项目术语） | 主人改 description，进表标 ⚠️ |
| 退 | 零调用 + 找不到情境，或与另一 skill 重复 | `enabledPlugins` 关掉或目录移到 `_retired/`；表里留一行「退 · 原因」；**不删文件** |
| 建 | 三次律 ≥3 且无现成品 | `skill-creator` 建；建成进表，第一个裁决人是 Andy |

## 五、三个首批住户

| 事 | 处置 | 情境 | 主人 | 验收 |
|---|---|---|---|---|
| 代码重构整理 | **建** `code-cartography`（13 次无现成品）。方法就是 09-04 这一轮跑过的：盘消费者 → 量 → 拆分建议 → 带正面对照落地 | 周检；任一文件 > 800 行 | OPS | 周检产出一份带 file:line 的拆分建议，且至少一条落地 |
| 组件整理 | 同一 skill 的前端分册（不另建） | 改 `frontend/src/components/` 前 | UI Claire | 组件 > 300 行从 24 个开始只降不升 |
| handoff | **不建**。已有 `HANDOFF.md` + 收工三问；hook 乙就是它的执行 | 收工 | 各线 | `HANDOFF.md` 「最后核对」日期 ≤ 3 天 |
| planning | **用现成** superpowers:brainstorming → writing-plans | 设计 / 方案 / plan | OPS | 每份 spec 带 plan，且 plan 有执行痕迹 |

## 六、验证（怎么知道它在跑，而不是又一个装饰）

- **周检第一节新增一个数**：`SKILL_ROUTER.md` 里「上次裁决」在 7 天内的行数。上线后第一周每天数一次。**这个数不涨 = 系统死了**，无论 hook 装得多好。
- hook 甲/乙各配一条能红的测试：伪造一条无 `skill-used:` 的收工消息，hook 乙必须 block；伪造路由表缺失，hook 甲必须注入警告且不阻断。
- 上线第一天做一次注入 bug 验证：把 hook 乙的 grep 改成永远匹配，测试必须红。

## 七、风险

| 风险 | 处理 |
|---|---|
| hook 乙误拦定时会话，造成任务卡死 | 各任务书收工节加固定行；hook 乙对 `skill-none:` 放行；上线前先在一个 routine 试跑一天 |
| 路由表变成又一份没人维护的文件 | 30 天无裁决自动标退 + 周检数字；维护责任写死给 OPS |
| 云端 routine 拉的是 main，hook 改动未合 main 就没生效 | hook 文件走直推 main 标准动作，合并后核 `git log origin/main` |
| 第三方 skill 升级改了 description，路由表失配 | 路由表以 skill 精确名为键，不依赖 description |

## 八、一句话

**skill 是菜谱，hook 是厨房的门禁，路由表是今天的菜单，裁决记录是客人的评语。四样齐了菜才会越做越好。**
