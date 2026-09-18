# 专职编队 v2：本机常驻编排器 · 设计文档

- 日期：2026-09-18
- 作者：OPS Fable（与 Andy 七轮追问定稿）
- 状态：待 Andy 审阅
- 取代：`data/reference/proposals/` 中所有关于门铃、群发、挂单板、取铃的机制；`docs/superpowers/specs/2026-09-04-skill-os-design.md` 的路由与触发率部分
- 审计依据：《联邦一月审计》（三份只读审计合成，2026-09-18）

## 0. 一句话

每个专职 agent 从「要人打开的聊天会话」改成「仓库里的一个目录 + 本机守护进程按需起的一次性工人」；agent 之间只通过任务板交接；Andy 只做花钱、对外发布和一个字的裁决。

## 1. 需求（Andy 2026-09-18 原话与选择）

| 项 | Andy 的决定 |
|---|---|
| 归 Andy 的动作 | 「花钱绝对是我才可以做的。对外发布内容，比如X/SUBSTACK，也是我才能执行的。合工作流，其实我不想做。」 |
| 每日页 | 「如果是我需要做的事情，那我是要看的……如果是agent之间在做的事情，我不想看到。」 |
| 多 agent | 保留专职分工，每个有职位、记忆、常用 skill |
| 单独沟通 | 「希望可以有单独和某个 agent进行沟通和更改它的做法，改完它以后照新做法来。」 |
| 内容与交易 | 「内容和交易判断永远是我的，agent 只递材料。」 |
| 合并授权 | 倾向自动合，「审核员机制是重要的。但我不想看到这样会慢几小时。」 |
| OPS 角色 | C：agent 直接交接，OPS 每天巡一次任务板 |
| 运行环境 | Mac 与 Claude App 基本全天开着 |
| 额度 | 乙：设水位线，超过只跑数据线和每日页，其余减到每天两班；订阅为 Max 5x |
| 花名册 | B：按职能收编成 8 个 |
| 方案 | 丙，本机常驻编排器；「不喜欢分阶段式的方案」；「交接延迟最多1小时可以接受，但也需要验证」 |
| X 调研 | 暂时维持原样（登录 Chrome），不进守护进程 |
| 模型 | 每个 agent 的默认模型要单独考量，有效计划 token 用量 |

## 2. 审计结论（本设计要解的三个根）

1. **执行者不会自己醒。** 交互线靠 Andy 开窗口，定时线不许发消息，两者之间没有自动环节。门铃、代按、回执、滞留提示全是这一个缺口的补丁。实测：两条无人在场的线门铃回执 0/5，挂 5–7 天；53 条回执中 33 条靠开工一把扫关掉。
2. **规矩、裁决、方法各有各的家，没有一个是执行者开工时必读的。** 宪法 236 行、共享记忆 7,481 行、六个 skill 各自为政；7 个主力定时任务只有 1 个读记忆。Andy 的裁决 50 条在记忆、32 条在 skill、14 条在宪法。
3. **「完成」有七层定义，却没有一个状态字段。** 滞留量不出来（待合分支中位 62 小时，4 条自 8 月未销），待办会写错筐（Discord 角色回收 23 天）。

设计判据（Andy 2026-09-18 追问中定）：**约束交给代码，方法交给保证被读到的 skill，两边都不留给记性。**

## 3. 五个零件

| 零件 | 是什么 | 靠什么生效 |
|---|---|---|
| 任务板 | 一件活一个文件 | 工具改状态，git 拒绝并发 |
| agent 目录 | 职责书、记忆、日志、配置 | 工人启动时被塞进上下文 |
| 守护进程 | 盯任务板，起工人，记账 | 本机常驻程序，launchd 拉起 |
| 审核员 | 同一班里的只读核查 | 工人流程里的一道工序 |
| 额度水位线 | 超线减班 | 守护进程读账本 |

其余一切（每日页、项目层、周检）都从这五个零件的数据派生。

## 4. 存放位置：私有仓库

代码仓库 `fluxus-dashboard` 是公开的（2026-09-13 定案私有化放弃）。任务板会含会员名与金额，agent 记忆会含 Andy 原话。因此：

- 新建私有仓库 `fluxus-ops`，克隆到本机固定路径 `~/Documents/fluxus-ops/`，结构：
  ```
  tasks/            任务板
  agents/<name>/    8 个 agent 目录
  projects/         项目层
  schedule.yml      时刻表
  ledger/           token 账本（按周）
  heartbeat         守护进程心跳文件
  ```
- 代码仓库 `.claude/skills/` 继续放公共 skill（skill 正文不含敏感信息）。
- 代码仓库根目录只留一行指针指向私有仓库路径。

## 5. 任务板

### 5.1 任务文件

`tasks/T-<MMDD>-<NN>.md`，YAML 头 + Markdown 正文。

| 字段 | 值 | 谁写 |
|---|---|---|
| id | T-0918-03 | 工具 |
| title | 一句话 | 派活者 |
| owner | alex / claire / linda / q / mia / vera / steve / gary / ops | 派活者 |
| type | 任务类型（见 §8 附录） | 派活者 |
| project | projects/ 里的文件名，可空 | 派活者 |
| status | open → claimed → done / needs_andy / blocked / closed | 执行者，经工具 |
| priority | P0 数据死线 / P1 当天 / P2 本周 | 派活者 |
| gate | none / reviewer / andy | 工具按改动路径自动判，执行者不可改 |
| runtime | local（默认）/ app（要用 App 内浏览器的活） | 派活者 |
| created_by / created_at / claimed_at / closed_at | 时刻 | 工具 |
| attempts | 失败次数 | 工具 |
| result | 提交号或分支名 | 执行者 |
| andy | Andy 原话，逐字 | 转录者 |
| review | 审核员判词与证据 | 审核员 |

正文两节：「要做什么」「验收」。验收逐条列，审核员按条核。

### 5.2 状态机

- `open`：可领。
- `claimed`：执行者把 status 改为 claimed 并 push；push 被拒即领取失败，去领下一件。同一件同一时间只有一个执行者。
- `done`：工具检查通过后才允许写。检查项：result 指向的提交在 main 上；全套测试通过（`pipeline/tests` 与 `tests/` 两个根）；验收逐条打勾；gate=reviewer 的有 review 字段且判词为通过。
- `needs_andy`：gate=andy，或 reviewer 两次否决。进每日页「等你拍板」。
- `blocked`：attempts ≥ 2 或触到禁止项。进每日页。
- `closed`：Andy 说不做，或被合并进另一件。

超时回收：claimed 超过 3 小时无 push，任何工人上岗时改回 open，attempts +1。

### 5.3 完成的定义

只有 `status=done` 一种。今天七层定义各自变成：

| 旧定义 | 新形态 |
|---|---|
| 合进 main 且 Andy 能点开 | done 检查项①；needs_andy 自动上每日页 |
| 素材箱追一行 | done 之后工具自动开一件 P2 type=material 给 steve |
| 转交写完 ≠ 送到 | 交接＝新建任务文件，push 成功即送到 |
| .md 不是给 Andy 的交付形态 | 每日页与「等你拍板」栏是唯一交付面 |
| 收工三问 | 收工时工具比对本次对话里的裁决是否已写入 ROLE.md / skill（§6.3） |
| 分支每一行在 main 找得到 | done 检查项①用 `audit_stranded` 的行级判据 |
| 数据面三件事 | type=data_recovery 的验收模板固定含归档补齐、复盘重跑、线上核对 |

### 5.4 工具

`fluxus-ops/tools/taskboard.py`：`new / list / claim / done / handoff / reap / gate`。所有状态改动只经它；手改文件格式错则拒写。测试先行：并发 claim 只一个成功；格式错拒写；超时回收生效；gate 按路径判对；done 检查项缺一不放行。

### 5.5 三个旧信箱

- `night_reports/INBOX.md`：只留晨报与事故报告，不再派活。
- `DATA_CONTRACTS.md §七`：只留数据口径事实行。
- `material_inbox.md`：只由 done 任务自动追加。

## 6. agent 目录与身份

### 6.1 目录

```
agents/alex/
  ROLE.md        职责、文件边界、能直接合的路径、按 type 列出的必读 skill
  memory/        只属于此 agent：方法、坑、Andy 裁决；一行一条，只追加
  runs/          每次上岗日志，只追加
  config.yml     按 type 的模型、并发上限、允许/禁止工具、时刻表班次
```

八个 agent：alex（数据）、claire（前端）、linda（研究）、q（课程）、mia（写作）、vera（视觉）、steve（编辑部）、gary（增长）；加 ops（体系本身）。Joe 的晨检成为 alex 的时刻表任务；Zac 的夜班成为 linda 的时刻表任务；收藏夹整理归 steve。

### 6.2 身份

工人启动的第一句话固定为「你是 agents/<name>，读你的 ROLE.md」。聊天窗口标题即 agent 名，开工第一动作读同一份 ROLE.md。共享记忆目录里所有「本会话＝」条目删除；共享目录只留跨 agent 通用的方法。

### 6.3 Andy 的话如何生效

Andy 在任何窗口对某 agent 说的「以后这样做」，该会话在同一轮写进自己的 ROLE.md 或 memory，逐字附原话，合进私有仓库。收工时工具比对本轮对话中出现的裁决标记与 ROLE.md/memory 的 diff，没写则退回。关于公共 skill 的纠正：该会话新建任务给 skill 的 owner，附原话；不自己改。

### 6.4 ROLE.md 上限

120 行，工具超限拒合。每条带出处（事故编号或 Andy 原话日期）。

### 6.5 记忆三层

| 层 | 放哪 | 谁开工必读 |
|---|---|---|
| 宪法 | `CLAUDE.md`，目标 40 行以内 | 所有人 |
| agent 记忆 | `agents/<name>/memory/` | 只有该 agent |
| 共享方法 | `KNOWLEDGE.md` 与共享 method 条目 | 按需 |

坑账不再单独立文件：进 ROLE.md 变做法，或进 skill 变注意项，否则留在 runs/。

### 6.6 skill

- 公共库在 `.claude/skills/`，任何 agent 可列为必读。
- 每个 skill 头部写 `owner: <agent>`，只有 owner 改。
- ROLE.md 按 type 写死必读 skill；工人启动时塞进上下文，不赌 description 触发。
- 建 skill 走官方 skill-creator：先写 3 条 eval，再写正文，再做一次干净实例触发。
- 纠正来源两个：Andy 的话、审核员的否决意见，都回流进 skill 的裁决记录。
- 自动触发建 skill：守护进程数同一 type 第 3 次 done 且 ROLE.md 无对应 skill → 开任务给 owner「固化为 skill」。

## 7. 守护进程

### 7.1 循环

```
每 60 秒：
  git pull fluxus-ops
  按 schedule.yml 投到点的任务（复盘 09:00、周检周日、蒸馏厂每日……）
  找 status=open 且 owner 有空位的任务，按 P0 > P1 > P2、再按 created_at
  起工人： claude -p --model <config[type].model> --permission-mode <预授权> \
           --allowedTools <config> --disallowedTools <config>
           上下文：任务文件 + ROLE.md + ROLE.md[type] 列的 skill
  工人退出：从返回读 token 用量记入 ledger；结果由工人自己写回任务文件
```

不调用模型本身；空转一分钟零 token。

### 7.2 工人

一次性进程，一件任务，流程固定：claim → 在临时工作树里干活 → 跑两个测试根 → 按 gate 过审核员 → 合并或留分支 → 写回 status/result/review → 追加 runs/ 日志 → 退出。时长上限 45 分钟。

### 7.3 并发

全局同时 ≤ 3 个工人；每 agent 同时 ≤ 1；有 P0 open 时不起新 P2。

### 7.4 失效与对策

| 失效 | 对策 |
|---|---|
| 进程崩 | launchd KeepAlive |
| 活着但卡住 | 每分钟写心跳；每日页第 1 行读，>10 分钟标红 |
| 权限弹窗 | 预授权清单；触禁止项即失败，任务 blocked |
| 跑太久 | 45 分钟超时杀掉，回 open，第二次 blocked |
| Mac 睡眠 | 启动时 caffeinate |
| 额度用光 | §9 水位线 |

### 7.5 留在 App 的任务

`runtime=app` 的任务（X 日调研、睡前速报，需 Chrome 扩展）仍由 App 定时任务跑，产出写回任务板。健身等个人任务不进本体系。

## 8. 审核员

工人流程里的一道工序：改完、测试过，在同一进程内派只读子 agent 做对抗式核查，几分钟出结论。

| gate | 路径 | 结局 |
|---|---|---|
| none | data/、data/research/、night_reports/、tests/、material_inbox、agent 自己的 memory 与 runs | 测试过就合 |
| reviewer | .github/workflows/、frontend/、pipeline/screeners\|tickers\|adapters/、任何 ROLE.md、任何 skill、CLAUDE.md | 审核过才合 |
| andy | 花钱、对外发布、删数据 | 停下，needs_andy |

审核员四问，每问要证据：①是否删除 main 上已有可执行行，删了有无说明（Andy 09-05 批的判据）；②指出哪个测试改动前红、改动后绿；③是否越 owner 边界；④验收逐条对得上。

模型交叉：Sonnet 工人配 Opus 审核员；Opus 工人配 Fable 审核员。

不过：分支留着，任务回 open 附意见；两次不过 blocked。判词与证据写入任务文件 review 字段。

## 9. 额度水位线与模型

### 9.1 账本

每个工人退出时记 token，折成 Sonnet 当量（Opus ×5，Haiku ×0.3），按周滚动。Andy 的聊天用量计入同一账本。

### 9.2 三档

| 周用量 | 行为 |
|---|---|
| < 80% | 全速 |
| 80–95% | 只跑 P0 数据、复盘、每日页；其余 agent 每天两班批处理 |
| ≥ 95% | 只跑 P0 数据与每日页；每日页第 1 行「额度已封顶」 |

### 9.3 模型按 type

| 任务类型 | 模型 |
|---|---|
| 判断型：研究结论、复盘正文、审核员、改宪法与 ROLE.md | Opus 5 |
| 执行型：改代码、加测试、修数据、写文档 | Sonnet 5 |
| 机械型：归档、记账、格式检查、任务板巡检、素材箱追行 | Haiku 4.5 |
| Andy 在场的 OPS 窗口；审 Opus 工人产出的审核员 | Fable 5.1 |

估算（按本月班次）：每天约 20 个工人，Opus 5、Sonnet 10、Haiku 5。上线第一周按账本实测校准，每日页给「本周用量，按此速度周几封顶」。

## 10. 每日页、项目层、OPS 巡检

### 10.1 每日页（10:07，手机可读）

| 行 | 内容 | 来源 |
|---|---|---|
| 1 | 心跳、额度水位、昨天最慢一次领取耗时 | heartbeat、ledger、任务板 |
| 2 | dashboard 数据日期，是否 08:30 前落地 | 线上核对 |
| 3 | 每个进行中项目一行：剩几天、任务 done/open、唯一指标现值 | projects/ + 任务板 |
| 4 | 昨天各 agent done 几件、blocked 几件（只计数） | 任务板 |
| 栏 | 等你拍板：每件一句话 + 一个字的选项，≤5 件 | status=needs_andy |

agent 之间的事不出现。Andy 在任何窗口说「T-xxxx 加/不做」，该会话改任务状态。

### 10.2 项目层

`projects/<name>.md` 四字段：发布物、截止日、到期规则、唯一指标（数字权威归 gary/steve 的任务产出）。任务 `project` 字段关联。到期日工具按到期规则自动开任务。首批四个：课程、dashboard、市场营销、会员增长；规划本身另开一次谈话。

### 10.3 OPS 巡检

每日一班（Haiku）：回收超时 claimed；两次失败标 blocked；按路径改派错 owner；needs_andy 超 3 天在每日页加「第 N 天」。
每周三个数：新增方法比新增坑；审核员否决次数与原因；额度实测。

## 11. 退役清单

| 退役 | 取代 |
|---|---|
| 🔔 门铃、取铃命令、代按、↳ 回执 | 任务 status |
| 联邦看板、挂单板、48h 滞留提示 | 每日页第 4 行与「等你拍板」 |
| §七 派活部分 | 任务板 |
| 「待合分支 建议 y/n」 | gate=reviewer |
| Zac、Joe 班次名 | linda、alex 的时刻表任务 |
| 共享记忆 96 条坑账、「本会话＝」条目 | 进 skill/ROLE.md 者留，其余归档只读 |
| 技能留痕 hook、收工三问 hook | 启动强制读取；收工比对裁决落盘 |
| CLAUDE.md 53 条粗体规矩 | ≤40 行；可执行者变工具拒绝动作 |
| App 20 个定时任务 | schedule.yml；X 两班与个人任务留 App |

不动：数据管线、前端、CI 工作流、复盘出片流程、六个 skill 正文。

## 12. 迁移顺序（一次做完，有先后，每步有验收）

| 步 | 做什么 | 验收 |
|---|---|---|
| 1 | 建 fluxus-ops 私有仓库；taskboard.py 及测试；8 份 ROLE.md 初稿；把 20 份任务书拆成 skill 壳（正文原样搬，各写 3 条 eval，标 owner） | 工具测试全绿：并发 claim 唯一、格式错拒写、超时回收、gate 判路径、done 检查项 |
| 2 | 守护进程 + launchd + 心跳 + ledger | 假任务 60 秒内被领并 done；kill 后 10 秒内拉起；心跳断 10 分钟每日页标红 |
| 3 | alex 先跑真活一天：数据线全部时刻表任务走守护进程，云端哨兵停用 | 09-19 正班 08:30 前落地；每件任务有 result；账本有记录 |
| 4 | 其余 7 个 agent 按时刻表接入，App 定时任务逐个停用 | 每停一个，对应任务在守护进程下跑成一次 |
| 5 | 审核员接入，白名单外改动开始自动合 | 首次否决的证据留在任务文件 |
| 6 | 每日页改读任务板；projects/ 四个文件建好 | 10:07 页面顶部四行全部来自任务板与心跳 |
| 7 | CLAUDE.md 重写；旧机制退役；共享记忆归档 | CLAUDE.md ≤40 行；INBOX 一周内零新门铃 |

进度每天在每日页一行。

## 13. 上线第一周的三个数

任务从创建到领取的最慢一次（目标 < 5 分钟，Andy 可接受上限 1 小时）；额度周用量；审核员否决占比。量不出或不达标，回到本文档改设计。

## 14. 已知风险与代价

- 工人在 App 侧栏不可见；看日志与任务文件，或打开该 agent 窗口。
- 预授权即安全换速度；禁止清单必须含删数据、改系统配置、对外发送。
- 守护进程是自建工具，本月 12/17 事故根因是自建工具误判；对策是 §7.4 与第 2 步的验收，以及每日页第 1 行的心跳。
- 公共 skill 的纠正经 owner，有时间差，接受。
- X 调研仍依赖登录 Chrome，留在 App；接口方案（xAI x_search 约每千帖 5 美元）Andy 暂缓。

## 附录 · 首批 skill 壳（从已重复的活里来）

| type | 现在的家 | owner |
|---|---|---|
| data_recovery 闸红后从数据包恢复 | 哨兵任务书 | alex |
| failure_triage 失败班次分诊 | 哨兵任务书 | alex |
| branch_review 分支审核与合并 | OPS 手工 | ops（审核员读它） |
| daily_recap / weekly_recap | daily-recap（周模式并入） | ops |
| x_watch / x_nightcap | 两份任务书 | steve |
| chart_for_andy 给 Andy 画图 | method 记忆 | vera |
| incident_report 写事故档 | 各写各的 | ops |
| daily_page 出每日页 | 云端任务书 | ops |
| data_gap_study 数据缺口重报 | method 记忆 | 等第 3 次自动触发 |
