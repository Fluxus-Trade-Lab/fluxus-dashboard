# 研究报告：方法层的官方与权威机制盘点（供 OPS 与 Andy 用，不是提案）

**起因**：前端线报告《这个体系只长疤，不长手艺》（`2026-09-06_learning_only_grows_scars.md`）：
192 条共享记忆里 66 条坑账、方法类 0 条；三次律的「成功固化」款从未生效。
Andy 2026-09-06 指令（模型R&D线领）：「你研究下已有的官方或权威机制」「官方权威方法来作为指导和优先学习资源。这类问题很多，多了解。」
本报告只盘点**别人已经怎么做**，怎么改归 OPS。

## 一、Anthropic 官方机制（第一优先，全部本机可用或文档可查）

### 1. Agent Skills = 官方的方法层（procedural 载体）
官方 skill-creator（本机 `~/.claude/plugins/marketplaces/anthropic-agent-skills/skills/skill-creator/`）明文：

- **skill 的用途就是「怎么做」**：三级渐进加载（description 常驻 → SKILL.md 触发时载入 → references/scripts 按需）。
- **触发是 description 的工作**，且官方承认现状是 **undertrigger**（「Claude has a tendency to undertrigger skills」），
  官方修法是把 description 写得「pushy」——把触发场景全部写进 description，不写进正文。
  ↳ 直接解释了 Claire 的第 2/4 条成因：**memory 靠记性、skill 靠 description 敲门**——官方设计里方法自己会敲门。
- **「从当前会话提取 workflow」是官方明文流程**（Capture Intent 节）：
  「The current conversation might already contain a workflow the user wants to capture…
  extract the tools used, the sequence of steps, **corrections the user made**, input/output formats observed.」
  ↳ 我们 09-05/06 建 daily-recap 的做法（六轮纠正→裁决进账→skill）正是官方姿势；
  它不该是孤例，该是所有「被 Andy 改了 N 轮才批」的产出的标准出口。
- **官方 eval 回路**：写 2-3 个真实测试 prompt → with-skill 与 baseline 同时跑 → 断言分级
  （客观可验的写 assertion，主观的走人评）→ benchmark（pass_rate/时间/token，含 baseline 对照）→
  analyst pass（专查「永远通过的断言＝不判别」「高方差＝flaky」）→ 迭代。
  基建全在本机：`run_eval.py / run_loop.py / aggregate_benchmark.py / improve_description.py / eval-viewer`。
  ↳ fable-voice 09-05 跑过一轮 description 优化（read 无分辨率，教训已记）；正确用法是整套回路不是单脚本。
- **写作规范**：解释为什么而不是堆 MUST（「in lieu of heavy-handed musty MUSTs」）；
  例子用 Input/Output 对；SKILL.md < 500 行，超了加层级。

### 2. 官方对 memory 与 skill 的分工（官方文档原文，claude-code-guide 核查）
官方分工表（[Features Overview](https://code.claude.com/docs/en/features-overview.md)、[Memory docs](https://code.claude.com/docs/en/memory)）：
> "Put it in CLAUDE.md if Claude should always know it: coding conventions, build commands, project structure, 'never do X' rules. Put it in a skill if it's reference material Claude needs sometimes (API docs, style guides) or a workflow you trigger with /<name> (deploy, review, release)."

- **CLAUDE.md**：always-know 规则，官方建议 **<200 行**（我们的宪法早已数倍超标——另一个待 OPS 看的信号：多步过程官方说该出去当 skill）
- **auto memory**：Claude 自己学到的偏好/修正/背景
- **skill**：按需 reference + 可触发 workflow —— **多步过程属于 skill，不属于 CLAUDE.md，也不属于 memory**

### 2b. 官方创建流程的两条硬话（[Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)、[Lessons from building Claude Code](https://claude.com/blog/lessons-from-building-claude-code-how-we-use-skills)）
- **评估先行（Evaluation-Driven Development）**：「Create evaluations BEFORE writing extensive documentation. This ensures your Skill solves real problems rather than documenting imagined ones.」——识别缺口 → 建 3 个评估 → 基线 → 最小指令 → 迭代
- **官方内部实况**：「Most of our best skills began as a few lines and a single gotcha, then got better because people kept adding to them as Claude hit new edge cases.」
  ↳ **这句话是给我们坑账的判词**：官方最好的 skill 就是「几行字 + 一个 gotcha」起步、撞到新坑就往里追加——**坑本该长在 skill 里当养料，而不是躺在 memory 里当独立疤痕**。66 条 pitfall 里凡是同一个工作流的，官方姿势是收编进那个工作流的 skill。
- **双实例测试**：Claude A 从实际会话建 skill，**Claude B（干净新实例）测**——防「作者自己懂所以觉得写清了」
- 如实报告：官方文档**没有**明确「教训写哪 vs 方法写哪」的对照条款——这一格官方留白，SRE 的 postmortem→runbook 是最近的权威替代

### 3. Hooks / 任务书 = 官方的强制层
决定「必须发生」的事不靠自觉靠闸（我们已在用：PreToolUse/Stop hooks、CI 闸）。
方法层与强制层的分界：**skill 教「怎么做好」，hook 拦「不许做错」**——坑账天然通向 hook，方法账天然通向 skill。

## 二、权威行业机制（第二优先）

### 4. Google SRE：postmortem → action items → runbook
行业标准的双出口：blameless postmortem 不止防再发（我们的 incidents/ 只做了这半），
**每个 postmortem 的 action items 里包含更新 runbook/playbook**——事故是方法文档的更新触发器，
不是只进教训库。runbook = 值班者照着就能做的步骤书 = skill 的人类版。
对应缺口：我们的事故档没有「更新哪本方法书」栏。

### 5. 学术框架：CoALA 的三类记忆（Sumers et al. 2023）
- episodic（经历，含失败）→ 我们的坑账/incidents，健全
- semantic（事实）→ 我们的 KNOWLEDGE.md 权威表/registry，健全
- **procedural（怎么做）→ 官方载体是 skills，我们 09-06 之前为零** ——Claire 报告的「memory 类型只有四种、没有方法的地址」在学术框架里就是缺了 procedural 这一格

### 6. 学术先例：成功轨迹入库的两个经典
- **Voyager（Wang et al. 2023）**：skill library——agent 每完成一个新任务，把**验证过可执行的成功程序**存入技能库供检索复用；入库条件是「跑通过」，不是「觉得有用」。↳ 对应 Claire 附录（2）的「方法必须来自被接受的真实产出」——学术界同款护栏。
- **Reflexion（Shinn et al. 2023）**：失败→语言化反馈→下轮改进——这就是坑账的学术原型。**坑账健全恰是因为它有权威原型；方法账的权威原型（Voyager/skill library）同样存在，只是我们没建。**

## 三、映射表：缺口 × 官方答案（结论，不是方案）

| Claire 报告的成因 | 官方/权威的现成答案 |
|---|---|
| 1 计数器没有输入 | skill-creator：触发点不是「第3次」，是**会话里出现了值得固化的 workflow**（含用户纠正）——即「被批准的那一刻」，官方 Capture Intent 原文支持 |
| 2 方法不会敲门 | description 触发 + 官方「pushy description」修法；memory 不是方法的载体 |
| 3 方法没有落脚点 | 官方落脚点就是 skill（procedural memory）；CoALA 三分法佐证 |
| 4 终态选错 | 官方终态链：会话经验 → skill-creator（含 eval 回路）→ skill；memory 只配当草稿箱 |
| （补）事故只结疤 | SRE：postmortem 的 action items 必含 runbook 更新——事故也要喂方法层 |
| （补）坑账越攒越大 | 官方：best skills = 几行字+一个 gotcha 持续追加——同工作流的坑该收编进该工作流的 skill，不是继续开 memory |
| （补）宪法越写越长 | 官方：CLAUDE.md <200 行，多步过程出去当 skill |

## 四、本机已有、可直接用的基建（零新建）
- skill-creator 全套（eval/benchmark/description 优化/viewer）
- 已走通一次的活样本：daily-recap（六轮纠正→skill→9/4 实测→diff→裁决回流），可当模板
- superpowers 插件：brainstorming→writing-plans→SDD 是「方法即 skill」的官方形态参考
- ⚠️ 已知坑（fable-voice 09-05 实测）：优化器从错误目录启动会丢 CLAUDE.md 上下文；
  纯内容句不会靠 description 触发，要靠 hook 兜——两条都记在 fable-voice 裁决记录

