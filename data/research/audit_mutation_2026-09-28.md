# 两道闸的未检视存活点清零 · 2026-09-28（T-0928-07 · linda）

| 闸 | 开工时 | 收工时 | 未检视的存活点 |
|---|---|---|---|
| `audit_calendar_gaps` | 86/99 = 87% | **95/99 = 96%** | 4 → **0** |
| `audit_universe_shape` | 31/49 = 63% | **48/49 = 98%** | 18 → **0** |

两个测试根 **3751 passed / 1 skipped / 12 deselected**（5 分 51 秒）。本轮源码一行没动，只加测试：
`test_audit_calendar_gaps.py` 80 → 91，`test_audit_universe_shape.py` 19 → 33。

`audit_universe_shape` 那 18 个，09-02 的晨报就写着「没人逐条读过」，此后三周每份报告都把这句照抄一遍。
今晨读完：**17 个是真洞，1 个不追。**

---

## 一、今晚的主线：有一类存活点不是「没人写测试」，是**写不出来**

三个存活点栽在同一件事上，而它跟测试勤不勤快无关——
**用这道闸自己的默认参数，那个边界物理上到不了。**

| 存活点 | 判据 | 默认值下发生什么 |
|---|---|---|
| `calendar_gaps` [22] L258 `GtE -> Gt` | `have_feed >= (1.0 - universal_frac)` | `universal_frac=0.80` → 阈值是 `1.0-0.8` = **0.19999999999999996**。`2/10 = 0.2` 既 `>=` 它也 `>` 它 |
| `universe_shape` [39] L92 `Gt -> GtE` | `abs(sh - base) > tolerance` | `tolerance=0.15`，而 0.15 在二进制里不是 0.15，**任何真实份额都落不到线上** |
| `universe_shape` [43]/[48] `100 -> 101` | `f"{tolerance*100:.0f}pp"` | `0.15*100` 印 "15"，`0.15*101 = 15.15` 也印 **"15"** |

> **一个没有任何输入能落在上面的边界，`>=` 和 `>` 是同一个程序。**
> 测试写得再多也判不了它——除非显式换掉那个参数。

三条测试因此都显式传了参数，并在 docstring 里写明**这是发现不是取巧**：
`universal_frac=0.5`（5/10 正好落线）· `tolerance=0.25`（0.25 二进制精确）· `tolerance=0.6`（60 vs 61）。

**这给 sweep 加了一条读法**：一个比较符的变异体连着好几轮活着，先别问「谁忘了写测试」，
先问**这道闸的默认阈值是不是一个可以被踩到的数**。踩不到就不是欠测试，是欠一个参数。

⚠️ 顺带一个不动手的观察：踩不到的阈值在生产里也不算错（`>=` 与 `>` 在实际输入上永远同义），
但它意味着代码写着的那句话——「share may drift this far」——**在它自己声明的那个边缘从没被执行过**。
记一笔，不改。

### 同一个坑 09-02 记过，形状一模一样

09-02 Zac 写过：漂移 0.2692 在 `*100` 下印 "27"，`*101` 下**也印 "27"**，
「对真代码和变异体都绿」。今晨我自己现场又栽了半次——
`test_the_share_a_d1_reports_is_the_share_that_was_measured` 断言 `"30%"`，
看着像在钉那个乘数，**其实杀不掉 `100 -> 101`**：`0.3*101 = 30.3`，`:.0f` 照样印 "30"。
断言一个百分数，和钉住那个乘数，是两件事。
能分开的份额要**算出来**：`f == 1.0` 对任何 n 都分得开（100 vs 101），
D3 只在阈值下方触发所以 100% 不可达，改用 `1/8 = 0.125`（印 12 vs 13）。

---

## 二、`audit_universe_shape` 18 个逐条判词

### 真洞，已钉住（17 个）

**⭐ [32] L64 `Gt -> GtE` —— 这一个就是统计量的定义**

```python
return sum(1 for t in ts if t[0].upper() > split.upper()) / len(ts)
```

翻成 `>=`，L 开头的票被算进「L 之后」。**全套测试对它是瞎的**：
`AL` 是 A 开头、`MZ` 是 W 开头，两个在 `>` 和 `>=` 下都不换边，
`test_the_split_letter_is_not_baked_in` 用 split="B" 配 A/C 名，同样不换边——
**19 条测试里没有一只 L 开头的票。**

为什么不是吹毛求疵：L 是盘上最忙的首字母之一（LLY / LIN / LMT / LOW / LRCX）。
把它们算到远侧，**份额和它要比的滚动中位一起被抬高**，于是漂移反而变小——
一次 M–Z 截断会被「还算在远侧的 L 票」部分吸收。
这道闸存在的全部理由是 docstring 那句：

> A source that is cut in half along a CONTENT dimension is flawless under every COUNT dimension check.

**把内容维量偏一个字母，就是同一个失败往里一层。**

**⭐ [29] / [37] L89 `len(prior) < 3` —— 第四场是第一场有资格被判的**

两个变异体（`< -> <=` 和 `3 -> 4`）做同一件事：把「可以开口」推到第五场。
而 U3 是 warning、**永不致命**——所以落在任何归档**第四场**的截断，
会被报成「历史不够，不判」然后放过去。
docstring 自己说这是最坏情形：一开头就截断的归档，毒化其后**每一场**的基线。

**⭐ [16] / [17] L155 `return 0 if out["ok"] else 1` —— 同形第五次**

`audit_archives` · `audit_ledger` · `audit_ci_test_coverage` · `audit_calendar_gaps` L423
各活过一次（09-25、09-26、09-27 分别补掉），这是第五个模块。
`0 -> 1` 是安静那条路：**每个干净的夜晚 CI 都红**，仓库没毛病，
而一道常年红的闸没人再读。`1 -> 2` 比看着严重——argparse 用 exit 2 表示「你命令行敲错了」，
变异后「归档坏了」和「你调用错了」合并成同一个码。

其余：

| 存活点 | 坏的是什么 | 钉它的测试 |
|---|---|---|
| [2] L57 `MIN_ROWS 50->51`<br>[20] L83 `GtE -> Gt` | 硬零算作证据的最小样本上移一行。50 是声明的地板，50 就得响 | `test_u2_fires_at_exactly_min_rows` + 49 行那条反向 |
| [9] L143 / [10] L148 `drop not` | `-q` 与默认**互换**：表头和 U3 警告只在 quiet 下出现 | 两条 capsys，正反各一 |
| [14] L119 `And -> Or` | 有票没日期的行开出一个叫 `""` 的 session；有日期没票的行把空符号记进真 session。两者都静默 | `test_load_needs_both_a_date_and_a_ticker_to_keep_a_row` |
| [26] L80 `Is -> IsNot` | 有份额的场次报 `None`，没份额的场次 `round(None, 4)` 崩。`rows` 是给机器读的那一半，没人读过 | `..._are_the_numbers_measured` |
| [33] L80 / [34] L81 `round(x,4)->5` | 声明的精度。50/50 夹具下每个份额都是精确值，四位与五位在**任何**输入上相同——要 1/3 才看得见 | `..._carry_the_four_decimals_they_declare` |
| [39] L92 `Gt -> GtE` | `--tolerance` 是「允许这么多」还是「这么多就算越界」 | 见第一节 |
| [43] L145 / [48] L97 `100->101` | 表头与 U1 里的容差读数 | 见第一节 |
| [45] L112 `0 -> 1` | `if c in rows[0]` 读成 `rows[1]`——**只有一行的归档 IndexError**，什么都没检查就崩。与 `calendar_gaps.read_archive_dates` 09-27 补的那条同形 | `..._in_a_single_row_archive` |

### 判过，不追（1 个）

**[41] L154 `json.dumps(out, indent=1) -> 2`** —— 写出 JSON 的空白。
钉住它等于冻结一个无害的排版选择。

---

## 三、`audit_calendar_gaps` 剩下 4 个存活点的判词

| 存活点 | 判词 |
|---|---|
| [38] L159 `frac = ... if n else 0.0` → `1.0` | **构造上不可达**，我自己验了一遍：过了 L157 的 `if not missing: continue` 就意味着 `missing` 非空，而 `missing` 是从 `tickers` 里筛出来的，所以 `n >= 1`，`else` 分支永远走不到。它是一道除零守卫，**为刷杀死率删它是错的交易** |
| [54] L330 `progress=False->True`<br>[55] L331 `threads=True->False` | yfinance 的显示与并发配置，返回的数据不变。钉它等于断言「传给厂商的 kwargs」，测的是调用不是行为 |
| [86] L422 `indent=1->2` | 同 universe_shape [41] |

四个已被 09-27 那轮判过一次，本轮**自己重验了 [38]**（09-27 那份是转抄的，
而三天内已有三次转抄读数不成立）。

---

## 四、本轮新补的 4 + 5 条（calendar_gaps）

| 存活点 | 测试 | 它坏掉的是什么 |
|---|---|---|
| [65] L203 `LtE -> Lt`（左比较符） | `test_c5_counts_a_degenerate_bar_on_the_first_day_of_the_window` | C5 只有落在窗口**第一天**的假 bar 能把 `<` 和 `<=` 分开。原有的 `..._ignores_degenerate_bars_outside_the_window` 用 2026-07-01，两种边界下都被排除——对它是瞎的。而窗口左沿正是截断的厂商响应最可能补假 bar 的地方 |
| [43] L250 `0 -> 1` | `..._reports_the_ticker_count_it_actually_audited`（k=0/1/10） | C0 说「一只票都没返回，什么都没检查」，同一份报告里 `tickers: 1`——两个互相矛盾的事实，而计数是脚本读的那个 |
| [22] L258 `GtE -> Gt` | `test_d1_fires_at_exactly_the_threshold_share_...` | 见第一节（不可达边界） |
| [81] L257 `1 -> 2` | `..._short_of_the_threshold_is_a_calendar_warning_not_a_hole` + `..._is_the_share_that_was_measured` | 分子翻倍把 4/10 读成 8/10，越过阈值去**指控写入端丢了一场从没发生的会话**。这道闸的 docstring 自己说：怪错边是贵的那一半（「right for 2026-08-28 and wrong for 2025-01-09」） |
| [75] L165 / [95] L265 / [98] L276 `100->101`<br>[74] L162 / [82] L281 `round 4->5` | 四条 | 见第一节 |

---

## 五、下一轮

1. **`audit_archives` 与 `audit_ledger` 的存活清单也没人逐条读过**（09-02 基线：54% / 53%；
   09-25、09-26 只各补了 exit-code 那一个）。按今晚的收获，先跑一遍现场复算——
   账上那两个数已经三周了，而本月已有三次转抄读数当场被推翻。
2. **拿「默认阈值可不可达」这条读法扫一遍全部六道闸**：
   每个 `>=` / `>` 判据问一句「它的默认参数是一个真实输入能踩到的数吗」。
   踩不到的那些，存活点不是欠测试，登记成「边界不可达」另立一档，别混在真洞里逐年重读。
