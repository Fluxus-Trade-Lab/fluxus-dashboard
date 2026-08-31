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

## 已批
