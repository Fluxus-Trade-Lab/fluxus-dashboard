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

## 已批
