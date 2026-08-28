# [2026-08-29] 迟到 485 分钟的主排程，把一份健康数据覆盖成 degraded

**发现人**：Plumber Joe（07:2x JST 晨检）· **状态**：病因已定位，修法未定（是设计取舍，不是 bug 修补）· **归属**：DATA ALEX / Andy

## 一句话

`daily-data-update` 的**主排程没有任何新鲜度闸**（这是**有意**的设计）。2026-08-27 那班迟到 **485 分钟**才跑，
彼时该 session 的数据已经落地两次且健康；它照样又跑了一遍，**把 `universe_quality` 从 `ok` 覆盖成 `degraded`**。
现在 `origin/main` 上 08-27 的数据就是这份更差的。

## 时间线（全部取自 `data/history/run_ledger.jsonl` 与 GitHub run 元数据）

| run | 触发 | 触发时刻 UTC | session | `universe_quality` |
|---|---|---|---|---|
| `33138813133` | workflow_dispatch | 08-28T03:25Z | 2026-08-27 | ok |
| `33141646318` | workflow_dispatch | 08-28T04:23Z | 2026-08-27 | ok |
| `33145206555` | **schedule**（`30 21 * * 1-5`，排期 08-27T21:30Z） | **08-28T05:35Z（迟到 485 min）** | 2026-08-27 | **degraded** |

三条都 success，最后一条赢，因为它最后写。

## 逐格损害（04:23Z 那份 → 05:36Z 覆盖后）

| 指标 | 覆盖前 | 覆盖后 | 变化 |
|---|---|---|---|
| `universe_quality.status` | ok | **degraded** | — |
| `degraded` 字段 | `[perf_ytd]` | `[bar_date, bar_scale_mismatch, bars_stale, perf_ytd, vol_5d_50d]` | +4 |
| `bars_missing` | 64 | **266** | ×4.2 |
| `tradeable` | 2562 | 2465 | −97 |
| `unmeasurable` | 75 | **277** | ×3.7 |
| `watchlist.gated` | 2069 | 1996 | −73 |
| `true_market_leaders` | 45 | 43 | −2 |
| `liquid_leaders` | 114 | 110 | −4 |
| `bullish_4pct` | 66 | 61 | −5 |
| `momentum_97` | 169 | 169 | 0 |

19 个面板里 15 个缩水，量级 ~5%。`bars_missing` 266 仍在「>300 = 429 夜」的报警线之下，所以**没有任何闸拦它**。

## 为什么迟到的那班反而更差

未定论。`bar_date` / `bar_scale_mismatch` / `bars_stale` / `vol_5d_50d` 四个字段同时 degraded，
形状像是取数侧在 05:36Z 那个时段被限速或拿到了半截响应。**「更晚 = 更新 = 更好」在这条管线上不成立。**

## 为什么现有防线一条都没响

- 主排程**故意**没有闸。`.github/workflows/daily-data-update.yml` 的 `gate` job 注释写得很清楚：
  「a gate that can silently skip the main run would be worse than the problem it fixes」。
  这个判断在「闸只会误关」的假设下是对的；它没有考虑「**这一班会把已经落地的好数据换成坏的**」这种情形。
- `universe_quality` 只把 degraded **记进台账**，不阻止写盘。
- `audit_archives` 的 I1–I7 检查的是归档的自洽性，**没有一条比较「新写的这份比在库的那份差」**。
  这是个**结构性空洞**：我们所有的闸都在问「这份数据自己对不对」，没有一个在问「它比它替换掉的那份更好吗」。

## 修法（三个选项，是设计取舍，请 Andy / DATA ALEX 定，我不代决）

1. **降级不覆盖**：写盘前比对同 session 的在库版本，若新版 `universe_quality.status` 从 `ok` 掉到 `degraded`
   而在库版本是 `ok`，则**保留在库版本**并把新版记进台账当影子。风险：真正的修复班也会被挡（需要一个 `--force`）。
2. **迟到即让位**：主排程在启动时检查「这个 session 是否已落地且健康」，是则空转退出（**与现注释的设计取向冲突**，需要 Andy 推翻）。
3. **什么都不做，只把它变得可见**：在 `run_ledger` 里显式标出「本班覆盖了一份更健康的同 session 数据」，
   让 Joe 的晨检能报出来。成本最低，但坏数据仍然在线。

我的建议是 **1**，因为它是唯一一个既不放弃「主排程永远能跑」又能防止实际损害的。

## 顺带发现的第二个缺陷（潜伏，已在修）

同一个 workflow 的 backstop 闸 `WANT=$(TZ=America/New_York date +%F)` 用的是**执行时刻**的 ET 日期。
排程 01:30 UTC 距 ET 午夜只有 150 分钟，迟到超过就翻成下一个日历日，那个日期永远不在 `breadth.json` 里 → **闸恒开**。
实测：01:30Z→`2026-08-27` ✅ / 03:59Z→`2026-08-27` ✅ / **04:01Z→`2026-08-28` ❌** / 05:35Z→`2026-08-28` ❌。
至今未发作（backstop 是 `4f9b5262` 于 08-28T03:01Z 才提交的，一次都没真正触发过），
但昨晚主排程刚迟到 485 分钟，说明这个量级完全在分布内。修在分支 `fix/joe-backstop-gate-date-2026-08-29`。

## 教训

**我们的闸全是「自洽性闸」，没有一个是「回归闸」。** 一份结构完好、字段齐全、通过全部 I1–I7 的数据，
可以比它替换掉的那份差 4 倍，而整条防线一声不吭。
下次加闸时先问：这道闸能不能看见「今天比昨天差了」？

— Plumber Joe，2026-08-29 07:5x JST（ET 2026-08-28 18:5x）
