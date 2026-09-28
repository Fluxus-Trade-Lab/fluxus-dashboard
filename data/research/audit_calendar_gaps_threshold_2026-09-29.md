# 一个够不着的边界，底下藏着两个相反的判词

`audit_calendar_gaps` · 2026-09-29 · linda（T-0929-08）

昨夜（[`audit_mutation_2026-09-28.md`](audit_mutation_2026-09-28.md) 第 170 行）把
`reconcile()` 的 `have_feed >= (1.0 - universal_frac)` 记成「全仓唯一一个碰不到自己边界的闸」，
留作下轮第一件事。今晨先跑了一遍再动手，**够不着只是表层症状。**

## 一、真正的毛病：同一天，同一个阈值，两个函数给相反的判词

这个模块存在的理由写在它自己的 docstring 里：`check()` 分不清是谁错了，
在这个问题上它默认怪供应商；`reconcile()` 拿我们自己的归档来破这个平——
「right for 2026-08-28 and wrong for 2025-01-09」。

而在阈值那一点上，两个函数互相打脸。复现（10 只票，8 只缺 2026-08-26，缺失份额正好 0.80）：

```
check    : frac 0.8  universal True
           C1 2026-08-26: absent for 8/10 tickers (80%)
                          -- FEED LOST A SESSION
reconcile: D1 2026-08-26: the market traded (20% of tickers have a bar)
                          and our archive has no row
                          -- ARCHIVE HOLE, a writer missed a session
```

同一份数据，同一个 `universal_frac`。`check()` 说供应商丢了一场，
`reconcile()` 说市场开了、是我们的写入端漏了。**而 D1 是 violation，会去叫人。**
破平的那个函数，在边界上把账记到了被它保护的那一方头上。

成因是两边各自把边界点算进自己那一档：
`check()` 用 `missing_frac >= universal_frac` 判「供应商丢了」，
`reconcile()` 用 `present_frac >= 1.0 - universal_frac` 判「市场开了」——
`missing == universal_frac` 这一点同时满足两个条件。

## 二、⚠️ 一句必须说清的限制：按现在出厂的样本，这条今天打不出来

`DEFAULT_TICKERS` 是 8 只（SPY QQQ IWM AAPL MSFT JPM XOM JNJ）。
`k/8` 取不到 0.80（只能是 0、0.125、…、0.875、1.0），**边界落在两格之间。**
所以这个矛盾判词在出厂配置下不会触发；它在有人传 `--tickers` 且样本数是 5 的倍数时立刻活过来，
而那是再普通不过的一个动作。

**这一节是自查补上的**：第一版正文写成「D1 会冤枉写入端」就收尾了，
差一步就把一个复现得出、但产线配置下打不出来的矛盾写成了现行故障。
（同形的账：09-27 我把试跑里 `.clip(-1,3)` 的裁剪上界当成 p90 测量值写进正文，复核员一算就露馅。）

不受这条限制的是另一半：**闸够不着自己声明的那条边界，是无条件成立的**，
而且与样本数无关——`1.0 - 0.8` 是 `0.19999999999999996`，
任何真实份额都不落在它上面，所以那一行的 `>=` 和 `>` 是同一个程序。
四次变异扫描留下这个存活点，不是测试没写到，是**那条边界上两个算子观测不可分**。

## 三、修法：让两边用同一把尺子，而不是把 `1.0 -` 换成字面量

```python
-        have_feed = sum(1 for t in tickers if d in feed[t]) / n
-        feed_has = have_feed >= (1.0 - universal_frac)
+        carrying = sum(1 for t in tickers if d in feed[t])
+        have_feed = carrying / n
+        feed_has = not ((n - carrying) / n >= universal_frac)
```

换成字面量 `0.2` 只治得了「够不着」，治不了两个判词打架——那是昨夜设想的修法，今晨没照它做。
改成**问同一个量、用同一个算子、同一个方向**（缺失份额 `>=` 阈值），
两个函数就在构造上不可能给出不同答案，边界也顺带落到 `0.80` 这个精确可达的数上。

代价：`missing == universal_frac` 这一点的判词变了（原 D1 violation → 现 D2 warning）。
这是**有意的行为改动**，不是兼容性事故：那一点上 `check()` 早就判「供应商丢了」，
现在 `reconcile()` 跟它一致。

## 四、装上一条「两边不许打架」的断言

比逐个钉边界更管用的，是把那个不变式本身写成闸：

`test_check_and_reconcile_agree_on_who_lost_the_session`，
把 `k = 0…10` 全扫一遍，逐个比对两个函数对「供应商有没有丢这一场」的答案。

在 main 上跑它：**11 个用例里 10 个绿，只有 `k=2`（缺失 0.80）红。**
这个形状本身就是证据——不变式在别处都成立，**只在边界上破**；
手挑一个用例的测试得先知道是哪一个才写得出来。

## 五、变异核对（内存内改源码，跑整份测试文件）

| 变异 | 结果 |
|---|---|
| `>=` → `>`（四次扫描留下的那个存活点） | **KILLED** 1 failed / 84 passed |
| 改回旧式 `have_feed >= (1.0 - universal_frac)` | **KILLED** 1 failed / 84 passed |
| 去掉 `not` | **KILLED** 1 failed / 31 passed |
| `(n - carrying)` → `n` | **KILLED** 1 failed / 31 passed |

四个方向全死。第一行是重点：**默认阈值下这个算子现在判得出来了**，
不必再像旧测试那样被迫显式传 `universal_frac=0.5` 才能说话。

## 六、动了 main 上已有的可执行行（一处，写明）

`test_d1_fires_at_exactly_the_threshold_share_not_one_name_above_it` 整条改写，
新名 `test_a_share_exactly_on_the_threshold_reads_as_a_feed_loss_not_a_hole`。

它钉的正是被修掉的那个行为（原断言逐字：
`assert not out["ok"], "a share sitting exactly on the threshold counts as traded"`）。
行为既然判错，钉它的测试必须跟着翻——**留着它就是让闸继续为一个错判作证。**
新测试保留原来的 `universal_frac=0.5` 用例当独立见证（0.5 在二进制里精确，新旧写法都可达），
另加默认 0.80 一行，那是旧写法根本到不了的地方。
除此之外 diff 里没有其他删除行；`check()` C4 的 docstring 从
「only a share above」改成「AT OR ABOVE」，是让注释跟上早就是 `>=` 的代码。

## 七、留下的一句规矩

**别把阈值的补数在比较处现算。** `1.0 - u` 不只是精度问题——
它同时造出第二个语义（在场份额的下限），而第一个语义（缺失份额的上限）还在隔壁函数里用着，
两个语义在边界上重叠。写成同一个量的同一个比较，边界只有一条，也只归一边。

## 出处

- 源码：`pipeline/tools/audit_calendar_gaps.py` `reconcile()`
- 测试：`pipeline/tests/test_audit_calendar_gaps.py`（**91 → 103** 条，现场 `--collect-only` 两边各数一遍）
- 全量：两个测试根 `3772 passed / 1 skipped / 12 deselected`（355s）
