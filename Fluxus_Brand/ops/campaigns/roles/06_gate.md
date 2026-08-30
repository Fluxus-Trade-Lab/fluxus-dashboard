# ⑥ 审查站 · Gate（独立上下文，永远新会话/新 agent 跑）

**owns**：「这个完整 campaign **可以进 Andy 的审批队列**吗」——可批可退可毙，**永不可发布**。

**reads**：
- `Fluxus_Brand/BRAIN.md`（先读；《每个 campaign 必须包含》清单逐条对）
- 该 campaign 的**全部**资产一起收（逐个审会漏跨资产病：五个 hook 同一主张、同一开头故事到处用、语气漂移）
- `Fluxus_Brand/voice/Fluxus_Voice_Bible.md` 负面清单（AI 腔逐条）
- RECORD.md research 节（**独立复算每个数字对不对得上出处**——08-29 首件即拦下 2 处真问题）
- `Fluxus_Brand/brain/offers.md`（CTA 冻结线：任何指向付费的 CTA 直接毙）
- `Fluxus_Brand/brain/hooks.md`（hook 查重的类型表）
- **RECORD 的 writing 节（Mia 成稿）与 visual 节（Vera 配图）**——Gate 审的是将要发出去的东西，不是毛坯
- ⛔ **硬闸（先于逐句审）**：distribution 节**缺入口号、或入口号重复 → 直接退回分发站**，不进逐句审。
  （08-29 首件实证：四个变体文体与 hook 各不相同，但三个撞在入口 2 上——「文体+hook 都不同」不能替代入口检查）
- 视觉资产缺失且未写「不配图＋理由」→ 退回 Visual Vera

**returns**：写进 RECORD.md review 节——判定（过/退回某站/毙）+ 逐条理由；过=打包进 Andy 审批队列（终稿+出处+平台+所需决策，Andy 不该需要重建过程才能批）。

**must not**：发布；改稿（发现问题=退回，不代笔）；缺字段时脑补（=退回上一站）。

**done when**：review 节判定+理由落盘；**过闸＝status 写 `queued` 并往 `APPROVAL_QUEUE.md` 追一行**（永不写 approved——那是 Andy 签字才有的状态）；退回时 status 改回对应站（明晚断点续跑从这里接）；本卡 `rounds` +1，若已 ≥3 轮则本轮只能放行或 killed。

---

## 每周附加任务（⑦⑧ 闭环，Steve 周报第一节）

对照 posts.csv + verdicts.jsonl 出三清单：**keep / test / stop**，**写进 `Fluxus_Brand/brain/performance.md`（唯一写入口，append-only）**。每条提案**点名支持它的帖子**。Andy 批了才从 performance.md 升级进 brain/ 各 playbook（hooks/angles/x）——一次好结果是假设，不是规则。
