# 时钟对了，货可以不对 —— universe 快照的第四个维度

**2026-09-20 夜间研究班（linda）· T-0920-10**
ET now 2026-09-19（周六）· last completed session 2026-09-18 · 今天不是交易日

上一轮（[`ep_qullamaggie_baserate_2026-09-20`](../ep_qullamaggie_baserate_2026-09-20/README.md)）
在反驳 verifier 的逼问下临时加了一道闸，救回一个把 08-14 印成 15/0 的读数。
那道闸当时只活在一个研究脚本的私有函数里。今晚把它搬成仓库的常驻闸，
顺手量了量它到底咬到了谁。

产出：`pipeline/tools/audit_universe_freshness.py` + 16 条测试 ·
`violations.json`（全历史逐条读数）。

---

## 一、一句话

管线给 **2026-08-10 05:31 那份盘前 payload** 盖的章是 `quality.status: "ok"`，
给同周一份真收盘（`d2337e85`，08-19 晚）盖的是 `"degraded"`。
不是质检失灵——**质检量的是「有没有值」，从来没有人量过「这批值是哪一刻的」。**

## 二、这是同一条家谱的第四节

| 闸 | 量的维度 | 它抓到的那一次 |
|---|---|---|
| `audit_archives` | 数量 | 行数、空值率、日期连续性 |
| `audit_universe_shape` | 内容 | 06-26 起归档丢掉了所有 L 之后的票，行数反而涨了 |
| `audit_universe_population` | 人口 | 同一晚 $1B 闸不再生效，宇宙尺寸没变但换了个市场 |
| **`audit_universe_freshness`（新）** | **时点** | **字段齐全、数值自洽，只是周一早上 5:31 的** |

前两把闸的开场白是同一句话换身衣服：
**沿着没人量的那一维坏掉，会在所有有人量的维度上满分通过。**
这次没人量的那一维是钟。

> 一份 05:31 的快照，21:03 那份有的字段它全有。
> 它没有的是**身后那一天的交易**。

## 三、尺子

    aggregate RVOL = sum(volume) / sum(avg_volume)   全宇宙加总

RVOL（当日量 ÷ 同期均量）**是标准指标**，StockCharts ChartSchool / TradingView /
Finviz 都有；平台文档还都说它正常要做**按时段校正**（早上的量只跟历史上早上的量比）。
我们的 payload 没有这个校正——**所以一个未校正的 RVOL 逼近 0，正好就是「这不是一整天」。**

⚠️ **自造部分明写**（宪法 2026-08-31）：RVOL 的标准口径是**逐票**的。
检索过市场聚合版，**查无公开标准口径**，所以「全宇宙加总成一个份额加权比值」这个聚合方式、
以及下面两条阈值，都是我们自造的，不是任何人的标准。
仓库里 `rel_volume` 的口径登记见 `METRIC_SOURCES.md:103`（那条也是自造，窗口 20 日 vs Finviz 3 个月）。

**两个设计决定，都是量出来的不是拍出来的：**

1. **不加市值闸。** 私有版只在 ≥$1B 人口上算。全历史 156 份快照，
   全宇宙口径与 ≥$1B 口径**逐份零分歧**——闸不买账，而去掉它让这把尺子
   **对 06-26 那次人口换血免疫**。一把分母会跟着宇宙一起动的闸，
   正好在出事的时候变哑。
2. **缺失值两边都记 0。** 这是 F2 能成立的原因：07 月 `avg_volume` 断供那八天，
   分母塌了而分子照来，比值离开区间；若把缺失行剔掉，它会安静地停在 1.0。

**阈值取自空档，不取自理论。** 156 份快照：

| 档 | 份数 | 区间 |
|---|---|---|
| 正常 | 143 | 0.611 – 1.969（中位 0.980） |
| 盘前 | 5 | 0.0059 – 0.0241 |
| `avg_volume` 断供 | 8 | 95.4 – 347.2 |

好区间下边最近的坏值是 0.024（空档 25 倍宽），上边是 95.4（48 倍宽）。
0.5 / 3.0 落在空档中间——空档里任何一对数行为相同，
**看的是落在空档哪一侧，不是落在哪个点**。测试里钉了这条（阈值挪一倍不改判）。

## 四、读数

`python3 -m pipeline.tools.audit_universe_freshness` → **156 份快照 / 141 场，22 条违规**

- **F1 盘前** 5 份：`0b7dfe1c`·`8fb939f4`（08-10 05:31）· `fbf2c0fb`·`65bbb080`（08-17 04:17）· `a9e3d319`（08-19 05:19）
- **F2 分母塌** 8 份：07-15 … 07-24，每天一份
- **F4 整场没有可用的货** 9 场：上面那八天，**加上 2026-08-10**

**08-10 是唯一一场「本该有好货却只剩坏货」的**：它在 git 里仅有的两份快照都是那对盘前的，
08-17 / 08-19 各自旁边还站着一份干净的收盘快照，所以它们是 F1 而不是 F4。

那两份 08-10 的快照不是正班提交的，是手敲的 commit——其中 `8fb939f4` 的标题是
**「a clean run, and the guard's first baseline row」**。
`data/history/universe_quality.csv` 的**第一行**就是它。

## 五、它在被人看着的那一维上有多干净

`universe_quality.csv` 里 2026-08-10 那行（盘前算出来的）对比相邻四场收盘的中位：

| | |
|---|---|
| 可比列 | 11 |
| **最大偏差** | **0.33 个百分点**（`perf_1w` / `avg_volume`） |
| 中位偏差 | 0.22 个百分点 |
| 偏差 > 5pp 的列 | **0** |

**不是 null 率账本漏看了它。在那一维上本来就没什么可看。**

## 六、它咬到了谁（data-gap-study 四步）

回放 universe.json **git 历史**的消费者共 5 个，逐个判：

| 消费者 | 用快照干什么 | 判定 |
|---|---|---|
| `backfill_preset_hits.py` | 回放 preset 命中，**写进 `data/history/ticker_events.csv`** | ✅ **未受污染**（见下） |
| `audit_universe_population.py` | market_cap 分布 | ⚠️ **暴露但未受损**——市值 05:31 和 21:03 一样 |
| `breadth_universe_break/population_*.py` | market_cap 分布 | ⚠️ 同上 |
| `oratnek_diff.py` | 取 `asof` 之后最近一份晚间快照 | ⚠️ **暴露**：若当晚没提交，它会取到次日清晨那份；实际调用日期无记录，无法回溯判 |
| `content/recap/build_pack.py` | 周线字段（`wk_ema10/20`、`three_weeks_tight`） | 🟢 低暴露：它自带 stamp 不符就撤字段的守卫，且周线字段对盘中不敏感 |

**归档为什么没脏**（逐条量过，不是推断）：

- 9 场 F4 在 `ticker_events.csv` 里**一行都没有**（含非 preset 行）——那些天归档本身就没收，
  `backfill_preset_hits` 的 `date not in archive_dates` 把它们全跳了。
- `preset:*` 行的 `(date, ticker, screener)` 重复键：**0**。119 个日期有 preset 行，
  08-17 的 559 行、08-19 的 636 行高于干净日中位 310.5，但那是行情不是重写。

## 七、留下的那个真问题：现有的闸挡不住它

`backfill_preset_hits.payload_disagrees()` 已经有**两个时钟**——payload 的 `timestamp`
和逐行的 `bar_date`——专门用来拒绝「这份货是别的场次的」。
把三份盘前 payload 按它们**真会拿到的标签**喂给它：

| 快照 | 标成 | 双时钟闸 | 新闸 |
|---|---|---|---|
| `a9e3d319`（08-19 05:19） | 2026-08-18 | **None＝接受** | F1，rvol 0.0083 |
| `fbf2c0fb`（08-17 04:17） | 2026-08-14 | **None＝接受** | F1，rvol 0.0059 |
| `0b7dfe1c`（08-10 05:31） | 2026-08-07 | **None＝接受** | F1，rvol 0.0241 |

三份全部放行。**因为它们的时钟本来就是对的**：一份 08-19 清晨 5:19 的 payload，
`last_completed_session` 就是 08-18，`bar_date` 也是 08-18——两个时钟一致，
而货是周三早上还没开盘的。
这就是上一轮那句话的可复现版本：**时钟对了，货可以不对。**

## 八、复现

```bash
python3 -m pipeline.tools.audit_universe_freshness                  # 全史，22 条违规
python3 -m pipeline.tools.audit_universe_freshness --since 2026-08-01 -q
python3 -m pytest pipeline/tests/test_audit_universe_freshness.py -q  # 16 passed
```

阳性对照**按失败方式分类造**（`method_positive_controls_by_failure_mode`）：
分子塌（F1）、分母塌（F2）、整场没好货（F4）三个方向各造一条，
外加一条口径对照——同一份数据用「逐只求比再平均」读出 49.5（红）、
用「加总求比」读出 1.05（绿），差 47 倍，所以口径不是风格问题。

## 九、没做的 / 欠的

- **没接线**：它现在只在有人手敲时才响。已按规矩记进 `audit_wiring.KNOWN_UNWIRED`
  （owner **DATA ALEX**，理由与读数写在条目里），W2 会在有人接上的那天逼着删掉那条欠条。
  接线位置：每晚写完 `data/output/universe.json` 之后自查一次——那是 ALEX 的文件。
  **它比人口闸便宜得多**：一份 payload 两个加总，不回看任何历史，接进去是真正的三行。
- **`oratnek_diff` 的暴露没结案**：它取「`asof` 之后最近一份」，实际调用日期无记录，
  没法回溯判它有没有取到过坏货。建议它改调 `classify()`，取到 F1/F2 就换下一份。
- **08-10 收盘那场的快照，git 里不存在**。是当晚正班没提交，还是提交了但没进 universe.json，
  没查——归 DATA ALEX 的产线账。
