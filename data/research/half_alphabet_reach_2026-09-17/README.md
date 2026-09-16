# 半字母表缺口 · 研究重报（2026-09-17）

**Nighty Zac 夜班，认领 DATA ALEX 09-17 门铃**（事故档 [`2026-09-01_half_the_alphabet_missing_for_six_weeks.md`](../../reference/incidents/2026-09-01_half_the_alphabet_missing_for_six_weeks.md) 第 2 条：样本跨这段的研究要重报宇宙）。

**结论**：13 个研究目录加 1 份归档、共 20 行判定里，**没有一项的结论方向被字母截断翻过来**。有 7 行判 C，涉及 5 份文档，已在各自文档顶部加上（见第二节）。另外查出 **3 处 `coverage_gaps.json` 没有声明的污染**：`breadth_archive` 的 30 场、`shortlist_log`/`shortlist_seat_log` 的 heat 席位（08-19..08-28）、研究 K 线缓存 `event_bars.pkl` 的票池。这三处归 DATA ALEX，已挂门铃。

窗口按研究运行时的状态算：**2026-06-26..08-07**（08-07 到 09-13 才由快照重算，此前也是 A–L only）。

---

## 一、判定表

判定：**A** = 不受影响 · **B** = 碰到窗口、剔除后方向不变 · **C** = 需要标注（已加）

| 研究 | 窗口内样本 | 依赖宇宙完整？ | 剔除窗口后 | 判定 |
|---|---|---|---|---|
| `scanner_validation_2026-08/b4_gates` | fwd20 样本 152/3,205 = 4.7% | 基本不依赖（命中内部分组比较） | gated vs dropped 方向不变，MW p 0.0051→0.0308 | **B** |
| `scanner_validation_2026-08` 面板 C2（`asof_all_panels`） | 11 个截止日里 4 个是 3,000 行快照；有 fwd20 的行 42.8% | **依赖**（横截面分位在半宇宙上排） | PP 三格 −0.8%→+1.5~+2.9%，anticipation −1.7→+1.6；LL-HL 仍为正 | **C** |
| `scanner_validation_2026-08` 老 7 个筛子 | fwd20 18.9% | momentum_97 依赖 | gainers_4pct −0.46→+1.46 | **C** |
| `scanner_validation_2026-08` 预设回填 | fwd20 10.2% | — | sugar_babies −9.5→−11.4 | B |
| `scanner_validation_2026-08/leaders` | K 线独立重建，窗口内 M–Z 39.0% | 不依赖 | — | A |
| `tightness_2026-08` | K 线独立重建，窗口内外 M–Z 相同 | 不依赖 | — | A |
| `momentum97_shadow.csv` + 读它的研究 | 0 天（08-19 起，当晚宇宙完整） | 依赖，但宇宙是完整的 | — | A |
| `oratnek_diff` | 0 天 | 主对照用完整宇宙 | `momentum97_pool_4days.csv` 候选池缺约 9 只 M–Z（K 线缓存的票池问题） | **B** |
| `leaders_log.csv` + `leaders_tml_2026-09` | 0 天，无回看 | 票级配对检验 | — | A |
| `adr_floor_2026-08` | 13,247/64,384 = 20.6% | 同日配对比较，不依赖 | H1 仍 NULL；H3a/H3b 75/75 天为负；R 反转仍成立 | **B** |
| `amplitude_2026-08` | 3,537/10,913 = 32.4% | — | 幅度 ρ 0.296→0.267，仍成立；**方向 ρ −0.006→+0.057（p=3.8e-5）** | **C** |
| `delayed_ep_window_2026-08` | 30/392 = 7.7% | — | P1–P3 仍 NULL | **B** |
| `gate_role_2026-08` | train 0 个脏日；**holdout 13,245/18,297 = 72.4%**（29 天里 21 天） | — | 干净 holdout 只剩 8 天，低于 `MIN_DAYS=20` | train **A** · holdout **C** |
| `delayed_ep_review_2026-08` | as_of 358/358 = 100% 在继承脏区 | — | 窗口外无样本 | **C** |
| `delayed_ep_review_2026-09`（09-01） | as_of 在脏区 95.7% | — | `ep>08-07` 子集 n=14 对 13，方向同但太小 | **C** |
| `delayed_ep_review_2026-09`（09-09） | 已按 `ep_date` 逐行剔除 | — | 干净子集逐位复现；若按场次剔除 `breaking` 三个 horizon 都是 n=0 | B |
| `events_vs_bars_2026-09` | 20/112 天 | 逐行恒等式，不依赖 | 窗口内 20/20 天命中率 1.000 | A |
| `screener_overlap_2026-09` | 每对 15–20 天 | 实测对截断基本中性 | 「中位数会骗人」仍成立 | **B** |
| `session_replay_2026-09` | 19 对相邻场 | 不依赖 | 窗口内外基线中位 69.2% / 68.1% | A |
| `what_changed_2026-08` | 读 `breadth_archive` 22 场 3,000 行 | — | 头名百分位 0.984→0.983 | A（见第三节①） |

### 怎么分开「缺了 M–Z」和「换了时段」

剔除窗口后读数变了，不等于是截断造成的——窗口本身是一段特殊行情（6 月见顶、7 月领头崩）。三个 agent 各自独立用了同一个对照：**在窗口外的干净日期里只保留 A–L，再算一遍**。

- 面板 C2、老 7 个筛子、amplitude 的方向 ρ：只留 A–L 后读数和全样本同号、接近 → **变号来自时段，不来自字母截断**。
- screener_overlap：窗口外只留 A–L，三对包含度 0.600→0.618、0.800→0.812、0.620→0.600 → 截断对这个量基本中性。

所以本表的 C 级大多是「结论建在一段特殊行情上」，不是「结论被半个宇宙扭曲」。标注照加，因为读者分不出这两种。

## 二、已加的标注（本班，直接改在各文档顶部）

- [`scanner_validation_2026-08/summary.md`](../scanner_validation_2026-08/summary.md) · [`presets.md`](../scanner_validation_2026-08/presets.md)
- [`amplitude_2026-08/results.md`](../amplitude_2026-08/results.md)
- [`gate_role_2026-08/results.md`](../gate_role_2026-08/results.md)
- [`delayed_ep_review_2026-08/README.md`](../delayed_ep_review_2026-08/README.md)
- [`delayed_ep_review_2026-09/results.md`](../delayed_ep_review_2026-09/results.md)
- 09-02 我自己那份 [`dirty_window_reach_2026-09-02/README.md`](../dirty_window_reach_2026-09-02/README.md) 追了更正（见第三节②）

## 三、声明表外的三处污染（归 DATA ALEX，门铃已挂）

**① `breadth_archive.csv` 的 30 场**：06-26..08-07 的 `universe_size` 全在 3000±30（其中 07-15..07-24 八行 backfill 是 2974–2980）。`up_4pct`/`down_4pct`/新高新低这些全宇宙计数，这 30 场都是 A–L 半宇宙的读数。`breadth_signals.py:58-67` 知道这件事（`TRUNCATED_UNIVERSE = 3000`），但判据是**恰好等于 3000**，那八行 backfill 认不出来；`coverage_gaps.json` 里也没有这一条。继承：`ratio_5d` 脏到 08-13，`ratio_10d` 脏到 08-20；`ad_line` 是累加量，绝对水平永久带着这段。
另有一处**没量**：宇宙在 08-10 从约 2,590 跳到约 5,620，这个跳变比截断大得多，计数类历史百分位跨 08-10 在比不同规模的宇宙。

**② `shortlist_log` / `shortlist_seat_log` 的 heat 席位，08-19..08-28**：`run_all.py:1322` 调 `compute_heat(events_all, …)`，`ticker_heat.py:47` 回看 15 个归档日，决定 `heat_rank` 和 burning 席位（`name_cards.py:250-253`）。agent 按当时归档状态重算，heat 前 50 的 M–Z 占比 08-19 是 .10，逐日爬到 08-28 的 .58（此后 .50–.62）。这两份归档按日期看全在窗口外，09-02 的扫描因此判它们干净——**那是错的**。（该表为单 agent 实测，我只独立核了 `HEAT_WINDOW=15` 与调用链。）

**③ 研究 K 线缓存 `event_bars.pkl`（主树本地，不在 git）**：票名单取自 `ticker_events`，3,617 只里 M–Z 只占 27.3%，869 只只在窗口期亮过、全是 A–L。拿它当基线池/横截面池的研究（b4_gates 基线、leaders 分位、tightness 基线、oratnek_diff 四天池）都带这个构成偏差。它不随日期变，不是窗口独有，但会让「同池随机基线」偏向 A–L。

## 四、复现

```bash
python3 data/research/half_alphabet_reach_2026-09-17/measure_all.py   # 全部归档，跳过的文件也列出
```
其余读数来自四个只读 agent 的复算脚本（本班 scratchpad，未入库）。本班独立抽验过：gate_role holdout 72.4%（21 脏日 / 8 干净日）、`breadth_archive` 30/30 场 3000±30、`HEAT_WINDOW=15` 的调用链。其余数字是单 agent 实测，引用前按上面的口径复算。

## 五、方法（可复用）

1. **日期干净 ≠ 没继承污染**：派生归档的脏区要读**写入代码里的回看常量**（`HEAT_WINDOW`、`rolling(n)`、lookback 天数），再用当时的归档状态重算。只数行级首字母占比，09-02 就是这么漏了 shortlist。
2. **扫描器不能静默跳过**：09-02 的 `measure.py` 跳过没有代码列的文件，于是 `breadth_archive` 从没被看过。看不了就要打印「看不了」。
3. **剔窗对比之后，再在干净时段只留 A–L 重算一遍**，才能分开「缺字母」和「换时段」。
