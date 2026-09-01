# 🧠 BRAIN.md — 内容共享脑（每个内容站开工先读这页）

> **这是内容产线的 index：路由 + 标准 + 边界。** 每个站（人或 agent）开工第一步读这页，
> 然后只读自己角色契约里 `reads` 列出的文件。角色契约在 [`ops/campaigns/roles/`](ops/campaigns/roles/)。
> 参照系：VibeMarketer 六角色模型（2026-08-28 帖，全文存档见 OPS）；我们不装 Hermes——
> 会话联邦=bot mode，任务书=profiles，git+看板=kanban，每样都更强。抄的是组织方式，不是软件。

---

## 一、我们发布什么（定位，Andy 2026-08-24 定，源 [`CONTROL.md`](CONTROL.md) §二）

- **判断的兑现记录**：说过什么 → 后来怎样，带票根。receipts 是文体不是装饰。
- **NULL 结果**：测了没用的东西如实报——「不动」是主证据。
- **build in public**：过程当内容，落在数字或 NULL，不预告只报过去式。
- **How Much（周信）**：波动的盟友；voice-as-product。

**不发布**：预测、荐股、没有票根的观点、任何 AI 腔（负面清单见 Voice Bible §4.8）。

## 二、为谁发布

想学会**怎么判断**（而不是抄答案）的交易者。他缺的是留白不是信息
（实测结论：[`research/Fluxus_Demand_Side_Findings.md`](research/Fluxus_Demand_Side_Findings.md)）。

## 三、每个 campaign 必须包含（Gate 按此清单毙稿）

1. 一个明确的**读者结果**（读完他多会了什么）
2. 一个**中心主张**（thesis），不许两个
3. 重要主张**逐条带出处**（数字永不手打——数字只有一个家，权威表在根 [`KNOWLEDGE.md`](../KNOWLEDGE.md)）
4. 一个**可复用物**（框架/规则/清单，读者能带走的）
5. 每个分发变体**独立成立**（重建不是缩写）

## 四、共享脑地图（store＝长期脑 · isolate＝可弃区）

### store（被验证的知识，只增不腐；改动走人批）
| 域 | 文件 | 谁写 |
|---|---|---|
| 声音 | [`voice/Fluxus_Voice_Bible.md`](voice/Fluxus_Voice_Bible.md)（含 §4.8 起草纪律+负面清单） | Andy 亲笔或亲批（Mia 提案） |
| 自己的句子 | [`voice/Fluxus_Own_Lines.md`](voice/Fluxus_Own_Lines.md) · [`voice/Fluxus_Ammo_150.md`](voice/Fluxus_Ammo_150.md) | Andy 亲笔为源 |
| 文体模板 | [`voice/Fluxus_Swipe_File.md`](voice/Fluxus_Swipe_File.md)（17 文体 A–Q） | Writer Mia |
| 受众 | [`research/Fluxus_Demand_Side_Findings.md`](research/Fluxus_Demand_Side_Findings.md) | 冻结（调研已停） |
| 证据/战绩 | [`record/`](record/)（H1 timeline、NULL 帖档案）· 交易数字权威源见 KNOWLEDGE.md | 各源头 |
| 否决训练集 | [`voice/verdicts.jsonl`](voice/verdicts.jsonl)（Andy 每个否决+一字理由） | 日推收，只追加 |
| 表现台账 | [`../data/content/posts.csv`](../data/content/posts.csv)（发布+读数回填） | Steve/日推 |
| 素材箱 | [`ops/material_inbox.md`](ops/material_inbox.md)（各线糖改道流入） | 全线可写 |

### store · playbook 域（`brain/`——各站的操作知识，每站 reads 指定读哪几份）
| 文件 | 是什么 | 主要读者 | 谁写 |
|---|---|---|---|
| [`brain/signals.md`](brain/signals.md) | 好信号四问＋弃选案例库 | 信号站 | Steve 周报回填 |
| [`brain/authority-clips.md`](brain/authority-clips.md) | 借势片段库（带机制+差异句才入库） | 信号/分发站 | Steve 周报搬运 |
| [`brain/proof.md`](brain/proof.md) | 证据对象清单（票根登记处，指针不抄数） | 查证/旗舰站 | 各线登记 |
| [`brain/angles.md`](brain/angles.md) | 已验证 angle 模式＋反模式 | 角度站 | Steve 周报提案，Andy 批 |
| [`brain/hooks.md`](brain/hooks.md) | hook 类型×实测＋三行骨架规范 | 分发站/Gate | Steve 周报回填 |
| [`brain/x.md`](brain/x.md) | X playbook＋**七入口周序列** | 分发站/日推 | Steve 周报提案，Andy 批 |
| [`brain/newsletter.md`](brain/newsletter.md) | Substack「How Much」playbook | 分发/角度站 | Steve |
| [`brain/offers.md`](brain/offers.md) | 产品阶梯＋漏斗＋CTA 冻结线 | 角度站/Gate | Gary 记账 |
| [`brain/performance.md`](brain/performance.md) | keep/test/stop 台账（⑦→⑧ 回写唯一的家） | 全站 | **Steve 周报（周日）唯一写入口** |

### isolate（草稿与实验，可退可毙不污染长期脑）
[`ops/campaigns/`](ops/campaigns/) 每个 campaign 一个目录——Record 走全程，毙了就留在原地当案例，
**永不**把未过 Gate 的内容写进 store。

## 五、供料层：内容不是四条线自己生的（**联邦全线都是供料方**）

> **糖改道（宪法）**：任何线完成一件像样的建设/研究后，**必须往素材箱追加一行可发布素材**，否则不算完成——
> 这是「完成=合进 main」之外的第二个完成条件。**建完没投一行 = 没建完。**
> 格式（照抄，别自创）：`- [MM-DD] [线名] 一句话 + 出处链接`，追加到文件最末尾的「📥 追加到这里」节。

| 供料方 | 投什么 | 投到哪 | 内容侧谁消费 |
|---|---|---|---|
| **Andy 本人** | 口述、每笔交易的思考、收藏的链接、判断兑现 | `voice/raw/`（工作区）· `Fluxus_Receipts/receipts.md` · INBOX 🔗 收藏夹 | 信号站（**最高优先级**——他的原料是唯一能长成立场的东西） |
| **DATA ALEX** | 盘面读数、数据腐烂/修复故事、口径 NULL | 素材箱 · `data/output/` git 历史（按日 `git show`） | 信号站选题 · 查证站取快照 |
| **RND Linda** | 研究结论与 NULL 结果 | `data/research/claims/claims.jsonl`（带 evidence_grade）· 素材箱 | 查证站（引用带日期与等级） |
| **Nighty Zac** | 事故档、踩坑故事、**收藏夹判定** | 素材箱 · `data/research/collection.md` · INBOX | 信号站 · 借势库（Steve 周报搬运入 `brain/authority-clips.md`） |
| **Plumber Joe** | 巡检发现、闸审计、静默失败案例 | 素材箱 · `data/reference/incidents/` · INBOX | 信号站（BUILD 帖矿脉） |
| **Growth Gary** | 漏斗读数、会员数、转化 | `data/growth/metrics.csv`（**offers.md 的数字权威源**） | 角度站（CASH 帖）· offers.md |
| **UI Claire** | 前端上线的功能与改版 | 素材箱 | 信号站（BUILD 帖） |
| **OPS Fable** | 架构/机制建设、事故复盘 | 素材箱 · INBOX 裁决 | 信号站（BUILD 帖） |
| **Studio Q** | 课程进展、试读本、视频工作流 | 素材箱 | 角度站（引流资产） |
| **Writer Mia** | 写作过程本身：被 Andy 改掉的地方、成稿前后的 diff | 素材箱 · `voice/verdicts.jsonl` | 信号站（写作 build-in-public）· 旗舰站负面清单 |
| **Visual Vera** | 视觉实验、被否的稿、图像语料新矿 | 素材箱 · `visual/Fluxus_Visual_Library.md` | 分发站（入口 7 压缩图）· 角度站 |

### 内容三层 × 四线归属（Andy 2026-09-01 定案落地；此前只有层没有主人）

| 层 | 是什么 | 收费 | 谁产 | 出口 |
|---|---|---|---|---|
| **① generic** | 机器出的、可被发现的 | 免费 | **夜间六站产线**（Steve 线）→ Mia 成稿 | X · Substack 系统区 |
| **② 半深度** | **Andy 每天说的话与发的数据**（盘前/盘中/盘后 · 四类：数据 / 总结 / 判断力 / 教学） | 会员 | **Andy 本人产**，Mia 只做形态转换 | Discord（原产地）→ 1–3 天后迟发钩子上 X |
| **③ 深度** | 每月 3–5 次 deep dive · 复盘 · 月度 Top 5 | 付费档案 | Mia 执笔 + Vera 配图，Steve 审 | Substack 档案区 |

⚠️ **第 ② 层是全场空位**（Steve 08-29 判词），而它恰恰是唯一「只有 Andy 能产」的一层——
①③ 我们能替他做，② 不能。**所以整条产线的真瓶颈在 ② 的捕获，不在 ①③ 的产量。**

⚠️ **迟发钩子两条硬规矩**（不做则会员制不成立，定案原文）：
**必须把时间差露出来**（`Members saw this on Aug 28. Here's what it did.`）——不露时间戳，它对陌生人只是一条免费 tip，证明不了会员值什么钱；
**只发已兑现的，不发还活着的**——发还在跑的，会员会立刻觉得「我付钱买的他免费给了」，那是最容易掉会员的动作。

**唯一消费者是 Marketing Steve**：素材箱每周日收割（判据是行下面有没有 `↳ ✅`，**不是它在哪一节**）。
供料方**只投不催**——投完就算送到，选不选是信号站的决策（弃比取多是常态）。

## 六、路由（一张卡怎么走）

```
素材箱/receipts/raw/收藏夹 ─→ ① 信号站 ─→ ② 查证站 ─→ ③ 角度站 ─→ ④ 旗舰站（毛坯）─→ ⑤ 分发站
                                                                              │
   ⑦ Gate ←── ⑥ Visual Vera 配图 ←── Writer Mia 成稿 ←──┘
     │  过闸 → status=queued → 📤 APPROVAL_QUEUE.md ─→ Andy 批（签字才 approved）─→ 发布
     └─ 退回↩（缺字段/质量不过=退回对应站，不脑补；可退回到 Mia/Vera）
发布后读数 ─→ posts.csv ─→ ⑦ 周检（Steve 周报）keep/test/stop 三清单写 brain/performance.md ─→ Andy 批 ─→ ⑧ 升级进 brain/ 各 playbook
```

- 状态与断点记在该 campaign 的 `RECORD.md`（模板 [`ops/campaigns/RECORD_TEMPLATE.md`](ops/campaigns/RECORD_TEMPLATE.md)）
- **缺字段 = 退回上一站重做，永不用合理假设补位**（首件 08-29 已实战：Gate 退回旗舰站）

## 七、基准与写权限矩阵（谁写什么、何时写、谁批——冲突时以本表仲裁）

**读的基准**：规矩/契约/playbook 一律读 `git show origin/main:<path>` 权威版；**唯一例外**＝内容台五件套（Week_Plan / Queue / Own_Lines / Ammo / receipts）与 `voice/raw/`、NOW.md 读主树工作区（Andy 手改不总 commit）。数字引用前现场读 KNOWLEDGE.md 权威表指定的源。

| 文件 / 区域 | 谁写 | 何时写 | 批准 |
|---|---|---|---|
| `Fluxus_Brand/ops/campaigns/<日期>/` 各站自己的节+资产 | 对应站（只写自己 owns 的节）；**例外：Gate 可往 distribution 节补标入口号**——登记不是改稿（改了读者会看到的字才叫改稿） | 夜跑当晚 | 无需——isolate 区 |
| RECORD.md `status` 行 | 各站推进 / Gate 退回（**Gate 过闸只写 `queued`**） | 交接时 | `approved` **只有 Andy** |
| `Fluxus_Brand/ops/campaigns/APPROVAL_QUEUE.md` | **Gate 唯一写入口**（过闸追一行）；Andy 批完自己追 ↳ | 过闸当晚 | append-only |
| `Fluxus_Brand/brain/performance.md` | **周检唯一写入口**（Steve 周报第一节） | 每周日 | 追加无需批；**升级进 playbook 需 Andy** |
| hooks/angles/x.md **实测读数回填** | Steve 周报 | 每周日 | append 无需批 |
| hooks/angles/x.md **规则与判定（✅/⛔）变更** | Steve 执行升级写入 | Andy 批了 performance 提案后 | **Andy** |
| `Fluxus_Brand/brain/signals.md` 弃选案例库 | Steve 周报回填（Gate 只在当晚 RECORD 记验证线索） | 每周日 | — |
| `Fluxus_Brand/brain/authority-clips.md` | Steve 周报搬运入库（Zac 夜判照旧写 `data/research/collection.md`，不直接写本目录） | 每周日 | append-only |
| `Fluxus_Brand/brain/offers.md` | Gary 挂单、Steve 执笔（Gary 不直接写 Fluxus_Brand/）；**档位/价格/承诺变更** | 变更时 | **Andy（人批边界）** |
| `Fluxus_Brand/brain/proof.md` | 各线登记新证据对象（一行入表） | 产出时 | — |
| `Fluxus_Brand/brain/newsletter.md` | Steve | 规则变更 | **Andy** |
| **本页 BRAIN.md ＋ `roles/` 六契约** | 提案：任何线挂单；执笔：Steve | 机制变更 | **Andy（人批边界）** |
| `Fluxus_Brand/voice/Fluxus_Voice_Bible.md` `Fluxus_Own_Lines.md` `Fluxus_Ammo_150.md` | **只有 Andy 亲笔或亲批** | — | Andy |
| `Fluxus_Brand/voice/verdicts.jsonl` | 日推收录 Andy 否决 | 否决当天 | append-only |
| `data/content/posts.csv` | Steve / 日推 | 发布登记+读数回填 | — |
| 素材箱 `Fluxus_Brand/ops/material_inbox.md` | 全线（糖改道） | 完成建设时 | append-only |

**三条仲裁规则**：
1. 不在表里的文件＝内容线 agent **不写**（跨线边界以根 `TEAM.md` 为权威；想改＝挂单给对的线）。
2. append-only 文件两写者撞行＝**丢弃重放**（CLAUDE.md 直推 main 标准动作），永不 rebase 硬解。
3. 谁写谁核实落地（`git log origin/main` 看到自己的 commit 才算写完）；**写完≠送到，合进 main 才算**。

## 八、人的边界（永不自动化；Andy 批准是训练信号不是流程税）

- 发布（一切对外）
- 立场与观点的源头（AI 只重组 Andy 的原料，不发明他的观点）
- **本页与 store 任何规则的变更**（含 voice/受众/证据规则）
- performance 教训升级为永久规则（周检三清单要点名支持它的帖子；一次好结果=假设≠规则）

---

*维护：Marketing Steve（编辑部线）。**内容侧四线分工见根 `TEAM.md`：Steve 选题/审稿 → Writer Mia 执笔成稿 → Visual Vera 配图 → Andy 批发布。** 本页变更走 Andy 批准。产线总纲见 [`ops/campaigns/PIPELINE.md`](ops/campaigns/PIPELINE.md)。*
