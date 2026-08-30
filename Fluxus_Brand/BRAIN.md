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
| 声音 | [`voice/Fluxus_Voice_Bible.md`](voice/Fluxus_Voice_Bible.md)（含 §4.8 起草纪律+负面清单） | Andy 批准后 Steve |
| 自己的句子 | [`voice/Fluxus_Own_Lines.md`](voice/Fluxus_Own_Lines.md) · [`voice/Fluxus_Ammo_150.md`](voice/Fluxus_Ammo_150.md) | Andy 亲笔为源 |
| 文体模板 | [`voice/Fluxus_Swipe_File.md`](voice/Fluxus_Swipe_File.md)（17 文体 A–Q） | Steve |
| 受众 | [`research/Fluxus_Demand_Side_Findings.md`](research/Fluxus_Demand_Side_Findings.md) | 冻结（调研已停） |
| 证据/战绩 | [`record/`](record/)（H1 timeline、NULL 帖档案）· 交易数字权威源见 KNOWLEDGE.md | 各源头 |
| 否决训练集 | [`voice/verdicts.jsonl`](voice/verdicts.jsonl)（Andy 每个否决+一字理由） | 日推收，只追加 |
| 表现台账 | [`../data/content/posts.csv`](../data/content/posts.csv)（发布+读数回填） | Steve/日推 |
| 素材箱 | [`ops/material_inbox.md`](ops/material_inbox.md)（各线糖改道流入） | 全线可写 |

### isolate（草稿与实验，可退可毙不污染长期脑）
[`ops/campaigns/`](ops/campaigns/) 每个 campaign 一个目录——Record 走全程，毙了就留在原地当案例，
**永不**把未过 Gate 的内容写进 store。

## 五、路由（一张卡怎么走）

```
素材箱/receipts/raw/收藏夹 ─→ ① 信号站 ─→ ② 查证站 ─→ ③ 角度站 ─→ ④ 旗舰站 ─→ ⑤ 分发站 ─→ ⑥ Gate ─→ Andy 批 ─→ 发布
                                                                                            │退回↩（缺字段/质量不过=退回上一站，不脑补）
发布后读数 ─→ posts.csv ─→ ⑦ 周检（Steve 周报）keep/test/stop 三清单 ─→ Andy 批 ─→ ⑧ 写回本页/Voice Bible/角色契约
```

- 状态与断点记在该 campaign 的 `RECORD.md`（模板 [`ops/campaigns/RECORD_TEMPLATE.md`](ops/campaigns/RECORD_TEMPLATE.md)）
- **缺字段 = 退回上一站重做，永不用合理假设补位**（首件 08-29 已实战：Gate 退回旗舰站）

## 六、人的边界（永不自动化；Andy 批准是训练信号不是流程税）

- 发布（一切对外）
- 立场与观点的源头（AI 只重组 Andy 的原料，不发明他的观点）
- **本页与 store 任何规则的变更**（含 voice/受众/证据规则）
- performance 教训升级为永久规则（周检三清单要点名支持它的帖子；一次好结果=假设≠规则）

---

*维护：Steve（内容线）。本页变更走 Andy 批准。产线总纲见 [`ops/campaigns/PIPELINE.md`](ops/campaigns/PIPELINE.md)。*
