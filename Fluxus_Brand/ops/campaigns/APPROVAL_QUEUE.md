# 📤 APPROVAL_QUEUE — 过闸待 Andy 批的东西（append-only）

> **Gate 是唯一写入口**（`roles/06_gate.md` done-when）。过闸＝RECORD status 写 `queued` ＋ 在此追一行。
> **Andy 批完在该行下追 `↳ ✅ 已批（日期）· 发了哪个 · 否了什么+一字理由`**，然后 RECORD status 才写 `approved`。
> 建于 2026-08-31：此前六站全部跑通之后，最后一米没有落点——Gate 的 returns 写着「打包进 Andy 审批队列」，而那个队列不存在。
> Andy 只需要看这一页就知道有什么在等他；**他不该需要重建整个过程才能批**。

格式（一卡一行）：

```
- [MM-DD] <slug> · 终稿 <路径> · 平台 <X/Substack/…> · 需你定的 1–2 件事：<…>
  ↳ ✅ 已批（日期）… ／ ↳ ❌ 否（一字理由）
```

---

## 待批

- **[08-31] `2026-08-29_extension-arithmetic`** · 终稿 [`Fluxus_Brand/ops/campaigns/2026-08-29_extension-arithmetic/`](2026-08-29_extension-arithmetic/)
  （旗舰＝[`04_flagship.md`](2026-08-29_extension-arithmetic/04_flagship.md) §一 · V1 与 V4 见 [`05_distribution.md`](2026-08-29_extension-arithmetic/05_distribution.md)；**V2 / V3 已由 Gate 下架，不在本包**）
  · 平台 **X**（旗舰＝长推＋读数表图 · V1 与 V4＝短帖）· 入口 **1 / 2 / 5**，无重复
  · ⚠️ **未经 Writer Mia 成稿 / Visual Vera 配图**（两线尚无夜跑 routine，按 PIPELINE〈过渡条款〉以**毛坯**过闸）——你看到的是毛坯，不是成稿
  · ⏰ **窗口**：旗舰与 V4 **只在 08-31（周一）ET 盘前成立**，周一收盘后作废；**V1 常青，随时可发**。发前跑 05 的复算命令 ① 与 ⑤，**在仓库根目录跑**（别用 04 §二 里那个已蒸发的 `cd /var/folders/…` 路径）
  · **需你定的 2 件事**：
    1. **周一盘前发不发，以及旗舰怎么发** —— 旗舰的载体写的是「长推 + 一张读数表图」，而**那张图不存在**（Vera 无 routine），它又正是本卡唯一的可复用物。裸发长推（读者拿不走那张表）／等图（错过唯一窗口，只剩 V1 能发）。
    2. **V4 里这句留不留**：`Including mine, which is why the stop convention is written into every one of these.` —— 这是一条**新的对外方法承诺**（今后每条仓位帖都写明止损约定）。Voice Bible §3 的风险台账 tic 是邻居，不是同一条。对外承诺是你的边界，AI 不替你立。
  · 顺带（不用回，但你的否决会成为 `verdicts.jsonl` 的第一条真记录）：旗舰收口 `Conviction doesn't change the division.` 是被点名三轮仍未定的最后一句巧话，重话备选见 04 §三选择 4。
  · 判定全文：[`06_gate_review.md`](2026-08-29_extension-arithmetic/06_gate_review.md) §第 4 轮（终轮）
  ↳ ❌ **V1 否（Andy 2026-09-04 每日页批注，原话「太ai slop了，也不行」）**——旗舰与 V4 已于 08-31 窗口作废，V1 是最后活着的一条。**本包就此全灭，零发布。** 判例已入 `voice/verdicts.jsonl`（首条 rejected）。

- **[09-02] `2026-09-01_august-scorecard`** · 终稿 [`Fluxus_Brand/ops/campaigns/2026-09-01_august-scorecard/`](2026-09-01_august-scorecard/)
  （旗舰＝[`04_flagship.md`](2026-09-01_august-scorecard/04_flagship.md) §一 · 四条变体见 [`05_distribution.md`](2026-09-01_august-scorecard/05_distribution.md) §一）
  · **本包＝4 条变体 + 1 篇旗舰**（V1/V2/V3/V4；**V5 已由 Gate 第 1 轮判死、⑤ 站第 2 轮撤下，不在本包**）
  · 平台 **X**（旗舰＝Article 长文，发布后 Pin · V1＝三行骨架入口推 · V2/V3/V4＝长推）· 入口 **1 / 2 / 4 / 5**，无重复；hook 反高潮 / 同名两表 / 反面先行 / 翻译，无重复
  · ⚠️ **未经 Writer Mia 成稿 / Visual Vera 配图**（两线尚无夜跑 routine，按 PIPELINE〈过渡条款〉以**毛坯**过闸）——你看到的是毛坯，不是成稿
  · ⏰ **窗口：常青。** 本卡取的是一个**已经关账的月份**，且**全篇一个累计回报百分比都没用**（Gate 两轮均 grep 验证，带阳性对照）——与你 08-31 那条「对外一律以 tracker 现读为准」的裁决**零冲突面**
  · **需你定的 2 件事**：
    1. **旗舰最后一段（收口）是空槽，等你亲笔。** 这是**故意**留的——`feedback_no_mirrored_aphorism_closings`：①对仗格言 ②复述正文，连栽两次，所以这次不由 AI 填。边界条件写在 [`04_flagship.md`](2026-09-01_august-scorecard/04_flagship.md) §四末。**不写这一段，旗舰发不出去。**
    2. **旗舰散文 704 词（连三张表 1160 词），砍不砍。** 你 08-28 的第一条驳回理由就是「你废话太多」；可砍点已在 04 §四.2 逐处指名。砍／照发，你定。（第 2 轮因修 G1 的切法句，比第 1 轮的 673 词长了 31 词。）
  · **发布前必做（一条命令）**：在**仓库根目录**跑 `python3 Fluxus_Brand/ops/campaigns/2026-09-01_august-scorecard/_derive_05.py`，比对月报指纹 `2026-08-31 15:25 / 1,645,532 bytes`。
    **一致** → V1 的三个数与 V4 的 40.5%+四档格直接用；**变了** → 这两条的数**全部作废按新输出重写**，**V2 与 V3 不受影响、可照发**（两条零读数，完全常青）。
  · 顺带（不用回）：本卡对外**不再引用 SQN**，故 `METRIC_SOURCES.md` 缺 SQN 口径行**已不是发布前阻塞**，降为常规挂单转数据线。另 `05_distribution.md` §六.1 前两格的记账数没跟着撤下更新（仍写「5 个 / 1-2-4-5-6」）——**读者不可见**，不影响发布。
  · 判定全文：[`06_gate_review.md`](2026-09-01_august-scorecard/06_gate_review.md) §第 2 轮（过闸）

- **[09-04] `2026-09-03_noise-with-structure`**（云端夜间产线，断点续跑第 2/3 轮）· 终稿 [`Fluxus_Brand/ops/campaigns/2026-09-03_noise-with-structure/`](2026-09-03_noise-with-structure/)
  （旗舰＝[`04_flagship.md`](2026-09-03_noise-with-structure/04_flagship.md) · 六条 X 变体 + newsletter 骨架见 [`05_distribution.md`](2026-09-03_noise-with-structure/05_distribution.md)；**V7 已由 Gate 裁定撤下独立帖，改列为 V1 配图规格，不在本包变体表内**）
  · 平台 **X**（旗舰＝Article 长文，发后 Pin · V1–V6＝短帖）+ **Substack「How Much」**（NL 骨架，交 Mia 成稿）· 入口 **1/2/3/4/5/6**，无重复；hook 六型（反高潮 / 翻译钩 / 时差票根钩🆕 / 反面先行钩 / 自拆钩 / 能不能变红钩🆕）互不重复
  · ⚠️ **未经 Writer Mia 成稿 / Visual Vera 配图**（两线尚无夜跑 routine，按 PIPELINE〈过渡条款〉以**毛坯**过闸）——你看到的是毛坯，不是成稿；V1 需要的配图（三行对照表，原 V7）也还没画
  · ⏰ **窗口：常青。** 全部引用数字已关账（41/45/47→45/45/45、43/47/49/43、22/48 等），零处引用当前杀死率（C7，保质期仅几小时），不随仓库当前读数过期
  · **需你定的 2 件事**：
    1. **等 Mia/Vera 有 routine 再发，还是这次也按毛坯直接发**——本卡不含时效窗口（不同于上一张因等窗口错过发布的卡），等待成本较低，但拖延成本仍在你
    2. **V1 长文的配图（三行对照表，原 V7）谁来画**——Vera 无 routine，若要按计划带图发布，需你亲自出或指派
  · 判定全文：[`RECORD.md`](2026-09-03_noise-with-structure/RECORD.md) `## review` 节（round 1 退回 → round 2 退回窄范围一处 → round 3 独立新上下文 Gate 过闸，三轮均为不同子 agent 独立复审）

- **[09-06] `2026-09-06_autumn-effect-decay`** · 终稿 [`Fluxus_Brand/ops/campaigns/2026-09-06_autumn-effect-decay/RECORD.md`](2026-09-06_autumn-effect-decay/RECORD.md)
  （旗舰＝`## flagship` 节正文 · 四条变体见 `## distribution` 节 V1–V4）
  · **经过 3 轮修改，第 4 轮（终轮）过闸**——按 `roles/06_gate.md`/`PIPELINE.md` 断点续跑节明文，`rounds=3` 达上限后本轮只能放行或 killed，不产生第 5 轮；四轮均为互不知情的独立新上下文子 agent
  · 平台 **X**（旗舰＝长推，200 词内，无 Article，随 08-29 先例 · V1＝三行骨架入口推 · V2/V3/V4＝长推）· 入口 **1/3/4/5**，无重复；hook 四型（验证回收钩🆕/时间戳锚/反面先行钩/能不能变红钩）互不重复
  · ⚠️ **未经 Writer Mia 成稿 / Visual Vera 配图**（两线尚无夜跑 routine，按 PIPELINE〈过渡条款〉以**毛坯**过闸）——你看到的是毛坯，不是成稿；flagship 配的样本内/样本外对照小表目前只是文字占位，尚未画图
  · ⏰ **窗口**：机制本身常青（"发表即失效"的判据不随盘面变）；唯一时效物是稿子里"我们现在正处在九月"的紧迫感，本月内发不受影响，过了 9 月这句开场仍可用但需改措辞
  · **需你定的事**：本卡零 CTA（比"停在订阅"更保守），无需你在 CTA 上拍板；主要待你决定的是**发不发、什么时候发、要不要等 Mia/Vera 有 routine 再配图**
  · 顺带（不用回）：research 源文件 `data/research/gold_autumn_2026-09/results.md` 开头「一句话」摘要段写"16 个九月只有 4 个是涨"，与下方详表及本卡全篇统一引用的"4/15"不一致，疑为源文件自身笔误——已挂门铃给 Nighty Zac 线核对，不影响本卡数字（本卡统一用与详表一致的 15）
  · 判定全文：[`RECORD.md`](2026-09-06_autumn-effect-decay/RECORD.md) `## review` 节 round 3（终轮）
  ↳ ❌ **整卡否（Andy 2026-09-06 日推会话，原话「olden September, silver October这个话题删除」）**——毙的是**题目**不是某一条文案，flagship 与 V1–V4 全部作废，**本包零发布**。RECORD `status=killed`，decision 节已转录；判例 3 行已入 `voice/verdicts.jsonl`。**本产线第一条题目级否决**（09-04 那条毙的是写法）。

## 已批
