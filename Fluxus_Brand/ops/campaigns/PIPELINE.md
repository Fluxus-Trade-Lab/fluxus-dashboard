# 夜间内容流水线（Andy 2026-08-28 立项：「我睡觉时你可以 ship」）

> 本质：我们是媒体公司。媒体公司是一个 loop，不是一堆草稿：
> **信号 → 查证 → 角度 → 旗舰毛坯 → 分发变体 →〔Mia 成稿 → Vera 配图〕→ 审查 Gate → Andy 批 → 发布 → 表现回写 playbook**。断任何一环质量就掉。
> ⚠️ **闸在成稿与配图之后**（TEAM.md 08-31 接力链为准）：Gate 审的是**将要发出去的东西**，不是毛坯。
> 参考拆解：VibeMarketer 六角色模型 / Codila 状态-审批模型（收藏对账 2026-08-28，OPS）。

## 六站合约（每站：owns / reads / returns / must-not / done-when）

> **v2（08-31）：每站一份独立角色契约在 [`roles/`](roles/)，含精确的 reads 文件清单与 done-when 可观察条件——夜跑加载自己那份即可，不用整读本页。共享脑 index（路由+标准+人批边界）：[`../../BRAIN.md`](../../BRAIN.md)，每站开工先读。下面六行只是一览，与 roles/ 契约冲突时以 roles/ 为准：**
1. **信号站**：扫素材箱、receipts ⏳、raw/、posts 表现、收藏夹判定——返回 ≤3 个「现在值得做」的候选（各带：发生了什么/受众为何在意/衰减速度/否决理由）。**弃的必须多于取的。**
2. **查证站**：把选中信号变成证据包（3-7 条已核实主张+出处；数字一律现场读权威源——数字只有一个家）。不许先定标题再找证据。
3. **角度站**：一个编辑决策——读者/结果/张力/thesis/旗舰格式/**读者带走的可复用物**/分发入口清单。产出 angle brief 不是草稿，且要说明放弃的方向为何更弱。
4. **旗舰站**：按 brief+证据包+Voice Bible+**verdicts.jsonl 负面清单**产出毛坯。红线：只重组 Andy 的原料与立场，不发明他的观点；数字不许手打（从证据包带出处复制）；亲缘句闸必过。
5. **分发站**：**重建不是缩写**——每个变体独立成立。产出 ≥3 个 X 变体，各标**七入口号**（`brain/x.md` 菜单）与 hook 类型，互不重复。
6. **审查站（Gate）**：独立新上下文收全部资产一起审：重复 hook、无出处主张、AI 腔（负面清单逐条）、语气漂移、变体是否只是缩写。可批可退可毙，**不可发布**。

## Campaign Record（一张卡走全程，缺字段退回上一站，不许脑补）
`campaigns/YYYY-MM-DD_<slug>/RECORD.md`：signal / research / angle / flagship / distribution / review / decision / performance 八节。

## 人的边界（永不自动化）
发布、立场与观点的源头、对外承诺、否决理由（每个否决进 verdicts.jsonl 喂第二天）。

## Performance 回写（周日，Steve 周报新增第一节）
对照 posts.csv+verdicts 出三清单：**keep / test / stop**，写进 `Fluxus_Brand/brain/performance.md`（唯一写入口，append-only；每条提案点名支持它的帖子；一次好结果=假设≠规则）。Andy 批了才从那里升级进 brain/ 各 playbook。

## ⑥ 视觉站 · Visual Vera（08-31 拆线后补入产线）
契约 [`roles/07_visual.md`](roles/07_visual.md)。成稿齐备后配图；**缺视觉或缺「不配图＋理由」＝ Gate 退回**。

## ⚠️ 过渡条款（08-31 立；Mia/Vera 线还没有夜跑 routine）

**问题**：08-31 把闸移到成稿/配图之后，但 `~/.claude/scheduled-tasks/` 里**没有 mia / vera 任务**——这两站没有执行者。
叠加轮数上限后，每张卡的确定归宿变成被 `killed`（Gate 永远收不到 writing/visual 节 → 必退回 → 退给一条不会醒的线）。三处改动单独都不致命，叠起来是死锁。

**在 Mia/Vera 有 routine 之前，按此办**：
- 工头在 RECORD 的 `writing` / `visual` 两节各写一行「**暂缺执行者（本线无 routine），本卡按毛坯审**」。
- **Gate 不因缺这两节退回**（`roles/06_gate.md` 的相关退回规则在过渡期不生效）；仍按毛坯的标准审其余各项。
- 过闸后在 `APPROVAL_QUEUE.md` 那行注明「**未经 Mia 成稿 / Vera 配图**」——让 Andy 知道他看到的是毛坯不是成稿。
- **解除条件**：mia / vera 的 routine 建起来，或 Andy 明确说这两站由人工承担。解除时删掉本节。

## 断点续跑（退回≠新卡）
- 昨日 RECORD 的 `status ∉ {queued, approved, published, measured, killed}` → 今晚**续跑同一目录**，不开新日期目录、不重选信号。
- 工头按 `status` 路由：值=某站名→只 spawn 该站及其后必要环节；`review`→只 spawn Gate（按上轮「只审这几处」清单办，不重开轮）。已过闸的站不重做。
- 量上限：一晚=一个新 campaign **或** 一次断点续修。
- ⛔ **轮数上限（08-31 补；此前无上限，一张卡可以永久占用每一晚）**：同一张卡累计 **≥3 轮**仍未过闸 → 第 4 轮 Gate **只做二选一**：放行进 APPROVAL_QUEUE，或标 `killed` 留原地当案例。**不产生第 5 轮。**
- RECORD 顶部记 `rounds:` 计数，工头路由时先读它。
