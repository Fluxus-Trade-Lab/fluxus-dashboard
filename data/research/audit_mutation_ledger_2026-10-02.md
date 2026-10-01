# 击杀率的家 — 四次转抄之后给它一个账本 · 2026-10-02（`T-1002-10` · linda）

ET now 2026-10-01 15:31 | last completed session **2026-09-30**

交给本班的第一件事是这句（10-01 晨报「没动的大件」）：

> `audit_ledger` 的变异存活清单仍没人逐条读过，**52.5% 是 09-02 的数**，已经四周。

**它是假的。** 今夜现场量：`audit_ledger` **78/80 = 98%**，而且从 **09-25** 起就是——
那晚的报告标题就写着「`audit_ledger` 66%→98%」。四周里没人读它的存活清单是真的，
因为 09-25 之后只剩 2 个，都判过。

---

## 一、这不是一次笔误，是第四次同一个形状

| 日期 | 被引的数 | 真相 | 代价 |
|---|---|---|---|
| 09-24 | `audit_ledger` 42/80=53%<br>`audit_archives` 54/101=53% | 66% / 57% | 两份报告都写成「54 **→** 57%」，转抄取了箭头**左边**那个数。两个数都错，于是「两道闸并列最低、先打哪个都一样」——**题选错了** |
| 09-27 | 三个「先复算再动手」的率 | 一个对、一个分子分母双错、一个洞早已补掉 | 复算花掉当晚第一段时间 |
| 09-28 | 「`audit_universe_shape` 有 18 个存活点没人读过」 | 09-02 写的句子 | 之后**三周**每份报告照抄一遍 |
| **10-01** | 「`audit_ledger` 52.5%，四周前的数」 | 98%，09-25 起 | **这句话就是本班的任务书第一行** |

共同的机制很简单：**一次全量变异扫描是小时级的，所以一个率量一次、然后被引用好几周——
而它只住在带日期的 markdown 散文里。** 散文没有「我过期了」这个字段。

四次，所以这轮不再写第五遍「下次先复算」，给机制（三次律）。

## 二、机制：`--ledger` 写，`--show-ledger` 读

```bash
python3 -m pipeline.tools.audit_mutation_sweep --module audit_tml --ledger   # 记一条
python3 -m pipeline.tools.audit_mutation_sweep --show-ledger                 # 读全表
```

账本是 [`data/research/audit_mutation_ledger.json`](audit_mutation_ledger.json)，每条读数带
`killed / mutants / total_sites / repeat / commit / uncommitted / measured_at`。

**切片不算读数。** `record()` 只收 `[0, total_sites)`；一个 `--index-from 0 --index-to 13`
的切片自己也有 `kill_rate`，把它写进模块名下就等于把 `12/13 = 92%` 当成那道闸的分数。
拒掉切片，意味着合并必须先做完才填得进去——而那一步正是让数变真的那一步。

## 三、新鲜度是问出来的，不是按日期算的

一条读数旁边写「2026-10-02」，读者还是不知道它还作不作数。所以判词由 git 出：

> **自这条读数记下的那个 commit 起，这道闸本身或它的测试，动过没有？**

两把尺子，因为各自都有瞎的地方：

| 尺子 | 它看得见 | 它瞎在哪 |
|---|---|---|
| `git log <sha>..HEAD -- 闸 测试` | 两边任何改动 | tarball 里没有 git，shallow clone 不全 |
| 变异点数 `total_sites` | 源码结构变了 | **看不见测试文件的改动** |

第二行不是假设。09-25 那次 `audit_ledger` 66%→98%，**源码一行没动**，全靠加测试——
只数变异点的新鲜度检查会把那条 66% 的旧读数判成 FRESH。击杀率是「闸 + 它的测试」两边的事实。

### ⚠️ UNKNOWN 这一档是承重的

```
$ git log 0000000000..HEAD -- pipeline/tools/audit_tml.py
$ echo $?
128                     # 退出码非零，stdout 为空
```

**把那个空输出当成「没有 commit 动过」，就会给一条根本无法定位的读数报 FRESH。**
与「拿一个本地不存在的 ref 去 grep，然后相信那个 0 命中」完全同形（09-27 吃过）。

> ⚠️ **复核员（PASS 判词附注）纠了本节原先的归因，这里按他的实测改过来**：
> 真正承重的是 **`git log` 那一步的返回码检查**，不是前面的 `git cat-file -e` 守卫。
> 他造了两个变异体：只去掉 `cat-file -e` → **16 条全绿**（rc 检查把它接住了）；
> 同时去掉 `cat-file -e` 与 `git log` 的 rc 检查 → **恰 1 红**。
> `cat-file -e` 的作用只是让 `why` 说得更具体（「这个 commit 本地没有」
> 而不是「没比成」），**它是冗余的第二道，不是那道闸**。
> 本节原文写「所以先 cat-file 再比」，把功劳记在了错的一行上。
三种进 UNKNOWN 的情况：commit 不在本 clone、读数没记 commit、**读数是在脏树上量的**
（commit 是真的，但量的那些字节从来没进过它）。

实测（真仓库，不是夹具）：

```
as filed        : FRESH   nothing touched the guard or its test since e1d79e104
the 55% reading : STALE   1 commit(s) touched the guard or its test since e44796e3b
unknown sha     : UNKNOWN commit 000000000 is not in this clone's history
site count moved: STALE   guard now has 45 mutation sites, the reading was taken over 44
```

### 排序：最不清楚的排最前

夜班开工问的是「今晚该打哪道闸」，而诚实的答案不是「账上最小的数」——
**没人量过的，或读数已经不描述现在这份代码的，比一个坐在 63% 的更不清楚。**
所以先按 NEVER → UNKNOWN → STALE → FRESH 分组，率只在组内排序。

## 四、今夜的基线：七道闸实测，十二道诚实地写着 NEVER

```
guard                        rate     killed  state
audit_tml                     84%      37/44  FRESH   （开工时 55%，见第五节）
audit_reads_declarations      65%      34/52  FRESH
audit_metric_names            68%      21/31  FRESH
audit_unpushed                90%      27/30  FRESH
audit_universe_freshness      93%      52/56  FRESH
audit_ledger                  98%      78/80  FRESH
audit_universe_shape          98%      48/49  FRESH
其余 12 道                     --         --  NEVER
```

两个顺带的事实：

- **`audit_universe_shape` 现测 48/49，与 09-28 收工读数逐字一致。** 账本与仪器在读数还新鲜时
  对得上，这是个独立交叉验证，不是自证。
- 全库 19 道闸共 1,563 个变异点。按今夜实测的速率（3–10 秒/点，模块间差三倍）
  跑满一次是**小时级**，这正是「量一次、引四周」的来源，也是账本必须存在的理由。

**余下 12 道写 NEVER 而不是留空**：`audit_regression_gate`、`audit_events_vs_bars`、
`audit_ci_test_coverage` 等几道在 09-26/09-27/09-28 的报告里有过读数，但那些读数在本账本里
**无法定位**（当时没记 commit），按第三节的判据就只能是 NEVER——
把它们填成当时的数，等于把这份账本变成下一个转抄源。

## 五、顺手打掉全库最弱那道：`audit_tml` 55% → 84%

它此前**从未被量过**（不在任何一份报告里）。首测 **24/44 = 55%**，是七道里最低。
20 个存活点里 **12 个挤在 `_fmt` 与 `main`** 两个函数里——而五条既有测试
**全部只调 `audit()`**，没有一条进过「把判词报出去」的那条路。

与 09-27 `audit_event_agreement` 同形：判词函数钉到 100%，而接住它判词的那几行零覆盖。
**人实际拿来行动的，是退出码和打印出来的那一行。**

补 11 条测试后 **37/44 = 84%**，12 个存活点被杀、**无新增存活点**：

| 存活点 | 它坏掉的是什么 |
|---|---|
| L122 `drop not` | 反过来：有完整产出时退 2（「这儿没有产出」），缺产出时反而往下跑 |
| L124 `2 -> 3` | 没人钉过的退出码，包装脚本可以一直误读 |
| L94 `drop not` | NOT-LIVE 的提示印在正常夜里，而真的没跑的那一夜被报成「今日 TML N 只」——这道闸最能误导人的输出 |
| L104 `drop not` | 两边对不上时的逐票差异，只在两边**一致**时才印（那时两个集合都空，于是什么也不印）——对它存在的唯一理由保持沉默 |
| L113 `100 -> 101` | 4/4 印成 101% |
| L120 `0 -> 1`<br>L121 `1 -> 2` | 位置参数错位一格：工具审的是 `data/output`，而调用者以为审的是自己点名那个目录 |
| L93 `Or -> And` | 表头丢掉这次检查是哪一天 |

另外 L73 / L82 `Gt→GtE` / L83 / L119 `Is→IsNot` 四个是走通 `main` / `_fmt` 的**连带收获**，
不是我点名要杀的。

**L113 的零分母那一档，测试写在渲染器那一侧**：`live` 分支只在 `weinstein_stage` 有命中时进入，
那意味着 universe 非空，于是每个分母都非零——这一档**从 `audit()` 不可达、从 `_fmt` 可达**。
所以它在 `_fmt` 那里拿到测试，而不是硬造一个 audit 进不去的场景。

仍存活 7 个（L55 / L68 / L71 / L75 / L82 `0→1` / L119 `1→2` / L121 `Gt→GtE`），
下一班可读；本轮时间盒到此。

## 六、阳性对照：三个失效方向各造一次

**没先验证一个检查能报出阳性，就不该信它的阴性**（Growth Gary 08-25）。
而「造一个方向」只能证明它认得出「什么都没做」——所以按**能坏的方式**分类造（09-18 判例）：

| 把实现改成 | 该红的测试 | 实测 |
|---|---|---|
| 去掉 `cat-file -e` 守卫，直接数 `git log` 的输出行 | 不可定位的读数必须报 UNKNOWN | **1 红**：`assert 'FRESH' == 'UNKNOWN'` |
| 不记 / 不理脏树 | 脏树上量的读数不可信 | **2 红** |
| 只看变异点数，永不问 git | 改源码、改测试都要判 STALE | **4 红** |

每一次都把文件复原后重跑：25 passed。

## 七、一个顺带发现的坑（已修，写在这里因为它会再来）

`--ledger` 第一次跑直接炸 `NameError: LEDGER_REL`。
原因：新代码**追加**在文件末尾，而 `if __name__ == "__main__": raise SystemExit(main())`
本来就在那儿——于是 `main()` 在新定义加载**之前**就执行了。

**测试全绿，CLI 全炸**，因为测试是 `import` 这个模块，永远走不到 `__main__` 那一支。
往一个带 `__main__` 守卫的脚本尾部追加代码时，守卫必须跟着挪到最后。

## 八、留给下一班

1. **`audit_reads_declarations` 65%（34/52，18 个存活点）是现在账上最低的 FRESH 行。**
   先 `--show-ledger` 现场看一眼再动手，**不要引用本文件里的数**——这份文档和
   09-02 那份一样会过期，区别只在于现在有个地方能告诉你它过期了。
2. 12 道 NEVER 里，`audit_regression_gate`(123) / `audit_events_vs_bars`(130) /
   `audit_ci_test_coverage`(165) 是三个大块，各自要独立的一晚。
3. `audit_tml` 还剩 7 个存活点。
4. 本账本还**没有登记进 `KNOWLEDGE.md` 数字权威表**（那份文件不在本线边界，走复核员）。
   「数字只有一个家」要真闭环，需要那张表指到这里——已开单 **`T-1002-15`**（owner=ops）。
5. `record()` 记的 commit 取自**扫完**那一刻而非开扫那一刻，中途 commit 能把脏树读数
   洗成干净读数（复核员判词附注查出，本轮未受影响）——已开单 **`T-1002-16`**（owner=linda）。
