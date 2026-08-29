# [2026-08-30] Joe 记下「至今未发作」的那个潜伏 bug，五小时后发作了

**发现人**：Nighty Zac（04:4x JST 夜班）· **状态**：病因已在日志里确认，**修法已存在但没合**
**归属**：修法归 Plumber Joe（分支是他的）/ 合并归 OPS 或 Andy · **数据损害：零**（被另一道无关的闸挡住）

## 一句话

`daily-data-update` 的 backstop 闸用**执行时刻**的 ET 日期当「要找哪个 session」。
2026-08-29 那班迟到 390 分钟、跨过 04:00 UTC 的 ET 日期翻转线，于是它去 `breadth.json` 里
**找一个周六**（2026-08-29），当然找不到，于是判定「主排程掉了」并放行——
而主排程四小时前刚成功落地。放行的这一班算出 `universe_quality: severe`，
被 `run_all.py` 里一道**完全无关**的闸拦下，没有提交。

**我们这次没挨打，靠的不是拦它的那道闸设计得对，是这一班坏得够明显。**

## 这不是新病，是 24 小时前刚写下来的那个病

Joe 在 [`2026-08-29_late_run_overwrote_healthy_data.md`](2026-08-29_late_run_overwrote_healthy_data.md)
末尾「顺带发现的第二个缺陷（潜伏，已在修）」里写：

> 实测：01:30Z→`2026-08-27` ✅ / 03:59Z→`2026-08-27` ✅ / **04:01Z→`2026-08-28` ❌** / 05:35Z→`2026-08-28` ❌。
> **至今未发作**（backstop 是 `4f9b5262` 于 08-28T03:01Z 才提交的，一次都没真正触发过），
> 但昨晚主排程刚迟到 485 分钟，说明这个量级完全在分布内。修在分支 `fix/joe-backstop-gate-date-2026-08-29`。

他写这句话的时间是 08-29 07:5x JST（= 08-28T22:5x UTC）。
**发作时间：08-29T08:00:55Z。他写完到它发作，间隔约 9 小时。**
他判断「这个量级完全在分布内」是对的——只是比他预期的还快一班。

## 逐格证据（`gh run view --log`，不是猜的）

run `33242135272` 的 `gate` 步，**真输出行**（无 ANSI 前缀那两行；带 `[36;1m` 的是命令回显，
不是行为——[[pitfall_read_the_source_took_it_for_the_behavior]]）：

```
2026-08-29T08:00:55.4211581Z backstop: newest session in breadth.json = 2026-08-28, looking for 2026-08-29
2026-08-29T08:00:55.4233002Z ##[warning]Backstop firing — 2026-08-29 missing (newest is 2026-08-28). The 21:30 UTC run was dropped or failed.
```

**它自己打印的那句话是错的**：21:30 UTC 那班既没掉也没失败，它 03:17Z 就跑完并在 03:42Z 提交了 `807ccce9`。

| | 排程 | 实际开跑 | 迟到 | gate | 结果 |
|---|---|---|---|---|---|
| `33231009592` | 主 `30 21 * * 1-5`（08-28T21:30Z） | 08-29T03:17:15Z | **347 min** | 走 `!= '30 1 * * 2-6'` 早退分支（其 gate 日志里没有任何 `backstop:` 真输出行） | `universe_quality: ok` → 提交 `807ccce9` |
| `33242135272` | backstop `30 1 * * 2-6`（08-29T01:30Z） | 08-29T08:00:38Z | **390 min** | **误开**（找 2026-08-29） | `severe` → `SystemExit` → **零提交** |

## 为什么这次没造成损害，以及为什么那不是好消息

拦住它的是 `pipeline/screeners/run_all.py:912`，一道跟 backstop 毫无关系的闸：

```python
if quality['status'] == 'severe':
    ...
    raise SystemExit("Universe quality severe on ... — refusing to publish.")
```

它上面那行注释把这次的运气讲得很清楚：

> `Degraded only warns — one flaky vendor morning should not cost a day.`

**`severe` 拦、`degraded` 放行。** 08-27 那次进来的正是 `degraded`，所以它落地了；
这次进来的是 `severe`，所以它被挡了。**同一个洞，两次通过，两种结果，差别只在那一晚坏得多明显。**
一次 `degraded` 等级的坏夜从同一个洞进来，会和 08-27 一模一样地落在 main 上。

## 台账能看见的和看不见的

`run_ledger.jsonl` 现在 12 行 / 8 个 session，其中 **3 个 session 有重复班**（08-19 / 08-27 / 08-28）。
但这个「37.5%」是**下界，不是发生率**：

> 「失败夜晚也记台账」是 `abc18a54` 于 **2026-08-28T05:12Z** 才加的。
> 在那之前，**任何跑失败的班都不写台账行**——它们不是没发生，是没留下记录。
> 所以 08-28 这一对是台账**有史以来第一次**能够记下一次 `severe` 重复班。
> 更早的 `ok → severe` 覆盖发生过几次，**不可测，不是零**。

同理，本夜新建的 [`audit_regression_gate`](../../../pipeline/tools/audit_regression_gate.py)
（它把 08-27 和 08-28 两对都判 RED、把 08-19 的真修复判 GREEN）
对 `severe` 这一档的**有效覆盖只从 08-28 开始**——在那之前没有可比的两行。

## 该做什么（我不做，逐条挂给主人）

1. **合 `fix/joe-backstop-gate-date-2026-08-29`**（Joe 的分支，`.github/workflows/` 不在我白名单）。
   ⚠️ 它现在**没合**：main 上仍是 `WANT=$(TZ=America/New_York date +%F)`。→ **门铃：OPS / Andy**
2. **`degraded` 那一档怎么办**——就是 Joe 08-29 列的三个选项（降级不覆盖 / 迟到即让位 / 只记可见）。
   本夜的证据只加强一件事：**触发条件一点都不罕见，两天两次**。→ **Andy / DATA ALEX 拍板**
3. **backstop 放行时打印的理由是错的**（"The 21:30 UTC run was dropped or failed"）。
   一道闸在开的时候说了假话，会让读日志的人朝错的方向找。→ 随 1 一起修

## 教训

**「潜伏、未发作」是关于过去的陈述，不是关于风险的陈述。**
Joe 把触发量级量出来了（150 分钟窗口 vs 昨晚迟到 485 分钟），量完的结论正确、
修法也写好了，**只差没合**——然后它就在同一条管线的下一班发作了。
分支上的修法和没有修法，对 main 是同一件事（[[pitfall_branch_work_is_not_delivered]]）。

— Nighty Zac，2026-08-30 JST 夜班（ET 2026-08-29）
