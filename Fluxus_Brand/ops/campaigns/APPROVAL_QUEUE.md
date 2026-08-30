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

（空——首件 `2026-08-29_extension-arithmetic` 仍在 review，未过闸）

## 已批
