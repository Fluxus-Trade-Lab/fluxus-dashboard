# Delayed EP —— 第一次前瞻复盘（数据截至 ET 2026-08-20 收盘）

**结论先写：阈值现在判不了，而原因不是「n 太小」，是整份日志只有一个市场窗口。**

`pipeline/tools/delayed_ep_scan.py --review` 的原始输出会让人读出一个不存在的样本量。
本目录的 [replay.py](replay.py) 把同样的数重算一遍，加三样原版没有的东西：
**SPY 同窗基准**、**秩检验**、**独立性诊断**。三样里最要紧的是第三样。

## 一、原始 `--review` 说什么

```
     basing + 5d: median -0.7%  n=32  >0: 47%
     failed + 5d: median -2.9%  n=27  >0: 26%
   breaking + 5d: median +18.2% n=1   >0: 100%
```

照字面读会得到两句话：①「守住缺口」这道闸把 basing 和 failed 分开了，胜率 47% vs 26%；
②breaking 一战成名 +18%。**两句都不能这么读。**

## 二、加了基准之后

| stage | RAW 中位 | RAW >0 | **EXCESS vs SPY** | **EXCESS >0** | n |
|---|---|---|---|---|---|
| breaking | +17.9% | 100% | +19.2% | 100% | **1** |
| basing | −0.7% | 47% | **+1.2%** | **53%** | 32 |
| drifting | −0.8% | 17% | +0.5% | 50% | 6 |
| failed | −2.9% | 26% | **−0.9%** | **44%** | 27 |

同窗 SPY 中位 **−2.0%**（区间 −2.0% ~ −1.3%）。

- **中位差几乎没变**：2.2pt → 2.1pt。这一半是真的。
- **胜率差塌了一半**：21pt → 9pt。原始的 47% vs 26% 里有 12pt 只是「那一周市场在跌」。
  `>0` 这个口径对市场漂移最敏感，偏偏它最像结论。
- drifting 的 `>0` 从 17% 跳到 50%（n=6，别当回事）。

## 三、秩检验：**不显著**

```
basing (n=32) vs failed  (n=27): p=0.1484
basing (n=32) vs drifting (n=6): p=0.4962
breaking vs basing: n=1/32 -- 太小，不报 p
```

双尾 Mann-Whitney U（含并列修正），跑在 excess 上。**basing vs failed 在 0.05 上分不开。**

## 四、独立性诊断 —— 这一节才是本次复盘的产出

```
distinct start dates: 2 (2026-08-13 .. 2026-08-14, 1 calendar days)
every 5-session forward window overlaps every other by at least 4/5 sessions.
```

「首次穿上某 stage 的那天」几乎全落在日志的第一天。日志 08-13 开张，5 个交易日后就是
08-20（最后完成的交易日），所以**够 5 日前瞻的只有 08-13 和 08-14 两个起点**。

于是：**59 个名字、2 个起点、窗口重叠 4/5**。有效样本接近「窗口数」而不是 n。
上面那个 p=0.1484 是**显著性的上界**，不是显著性——真实的更不显著。

换句话说，现在拿到的不是「Delayed EP 在 59 次机会里的表现」，是
**「Delayed EP 在 2026 年 8 月第三周这一个星期里的表现」**。这一周 SPY −2%。

## 五、那要等多久

- 要判 **basing vs failed 这道闸**：需要若干个**互不重叠**的 5 日窗口。每周给 1 个，
  10 个窗口 ≈ **10 周**（到 10 月底）。这还只够做「闸分不分得开」，不够做阈值调优。
- 要判**方法本身**（basing → breaking 的第二次突破是不是更好的交易）：`breaking` 的
  n 现在是 **1**。转移计数里 `basing -> breaking` 一共 4 次，六个交易日出 4 个触发，
  约每天 0.7 个。攒到 n=30 需要 **~45 个交易日 ≈ 9 周**。

**两条线都指向 10 月底。在那之前，`--review` 的输出请当监控读，不要当证据读。**

## 六、附带发现（未修，只报）

1. `--review` 的前瞻收益用的是 `Close` 且 `auto_adjust=False`。窗口里若有拆股/除息，
   收益会是错的。当前 6 天窗口里大概率没有，但日志越长越会咬人。
2. `--review` 不打印起始日期的分布，所以「n=32」看起来像 32 个独立机会。
   **建议**：给 `--review` 也加一行 distinct-start-dates（本目录的 replay 已有实现可抄）。
   工具本身不在夜间组的地盘，没动。

## 复现

```
python3 data/research/delayed_ep_review_2026-08/replay.py --horizon 5
```

只读 `data/history/delayed_ep_log.csv`，不写任何文件。SPY 与候选票同一次
`yf.download` 取回，基准和标的走同一份日历。
