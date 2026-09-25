# 全库最大那道闸的第一次变异测量 · 2026-09-26（T-0926-21 · linda）

`audit_ci_test_coverage` 是仓库里最大的一道闸（720 行源码 / 641 行测试）。
它 09-05 上线，到今晚为止**一次都没被量过**——而原因不在它身上。

## 一、它量不了，是因为尺子缺了一条腿

`audit_mutation_sweep --module audit_ci_test_coverage` 返回的是：

```
audit_ci_test_coverage   baseline is already red; refusing to sweep
```

读起来像「这道闸的测试坏了」。实测不是：真树上 `pytest pipeline/tests/test_audit_ci_test_coverage.py`
**73 passed**。红的是尺子自己搭的那个沙箱。

沙箱（`Workspace.__enter__`）拷 `pipeline/`、软链 `data/`、拷 `.github/` 和四个配置文件。
**没有 `tests/`**——而 `tests/` 正是这道闸的全部主题：仓库有第二个测试根，CI 不跑它。
它的 `DECLARED` 表里声明了 `tests` 这个路径，沙箱里那个路径不存在，于是它自己的
**T3（「声明的路径已不存在」）**当场亮红：

```
E  assert [('T3', "declared path 'tests' does not exist")] == []
```

**闸是对的，沙箱是缺的。** 这是同一个形状的第二次——09-21 修过一次，那次缺的是 `.github/`，
受害者是 `audit_schedule_windows`（整个工作就是读 workflow 的 cron）。两次的共同判据写进注释了：
**凡是一道闸要读的、长在 `pipeline/` 外面的东西，沙箱必须有；否则尺子会把自己挖的洞算到被测者头上。**

修复 `audit_mutation_sweep.py`：沙箱补拷 `tests/`（344K / 61 个文件）。
配一条阳性对照测试 `test_workspace_carries_the_second_test_root_so_guards_that_read_it_sweep`：
撤回修复后它报的是**同一句** `baseline is already red; refusing to sweep`，加回修复后绿。

### 波及面：就这一道闸

对全部 20 道有测试的 `audit_*`，用**旧沙箱**和**新沙箱**各跑一次 baseline：

| | 旧沙箱 | 新沙箱 |
|---|---|---|
| `audit_ci_test_coverage` | ❌ red | ✅ green |
| 其余 19 道 | ✅ green | ✅ green |

盲区只有一个，但它盖住的正好是全库最大的那一道。

## 二、第一次读数：126/174 = 72%

站点数**不是 09-25 晨报转抄的 162，是 174**——那份读数在 09-23 `DECLARED_TRIGGERS` 扩表之后就过期了。
四段切片（0:45 / 45:90 / 90:135 / 135:174），逐段 80% / 78% / 71% / 59%。

48 个存活点，集中在三处：

| 簇 | 数量 | 是什么 |
|---|---|---|
| `-m` 标记解析 | 16 | 这道闸的**核心输入**：从 workflow 的 pytest 命令里读出「排除了哪些标记」 |
| `render()` | 13 | 报告本身——这个工具**唯一的产物**，只有两条测试 |
| `main()` 退出码 | 2 | `return 1 if violations else 0` |
| 其余 | 17 | `on:` 块边界 · `DECLARED` 校验 · checkout 深度 · 死代码（见第四节） |

### ⚠️ `return 0` 那一个，是同形状的**第三次**

`0 -> 1` 在 `audit_archives` 和 `audit_ledger` 里各活了三周，09-25 那晚一起补掉；
今晚在这里第三次。它是我们见过最难看的一个变异，因为它坏的是**安静那条路**：
**每一个干净的夜晚 CI 都会 exit 1**，仓库明明没毛病，而人学会的修法是不再看这个检查。

> 「测过 `main()`」和「测过 `main()` 的两条出口」不是一句话。三道闸连着证明了这件事。

按三次律，这条不再只记 memory：判据写进了 `test_main_exits_zero_on_a_clean_repo_and_one_when_it_finds_a_hole`
的正文，**下一道闸补测试时照抄**——先问干净那条路返回什么。

### 解析器那 16 个里最值得说的一个

已有的那条测试用的是真 workflow 的命令：`["pipeline/tests", "-q", "-m", "not slow", "--tb=short"]`。
`-m` 后面还有东西，所以 `i + 1 < len(rest)` 在**真边界和差一位的边界下都成立**。
把 `-m` 挪到倒数第二个（`["-m", "not slow"]`），两者就分家了：差一位的那个读不到值，
**「这次运行排除了哪些标记」变成空集**——一道报告「什么都没被排除」的闸。

## 三、补 26 条测试：72% → 88%（154/174）

| 簇 | 新测试 | 钉住了什么 |
|---|---|---|
| 退出码 | 1（建整个小仓库，干净/有洞各跑一次 `main()`） | 两条出口 |
| `-m` 解析 | 9 | 分离式 / 附着式 / 尾部空 `-m` 不崩 · `--maxfail=2` 这类只有 head 在表里的选项 · 表外选项仍要报 · `--ignore=tests` 不再多吃一个目标 · `python -X dev -m pytest` |
| `on:` 块边界 | 2 | 块外的 `branches:` 不算触发过滤器 · YAML 把 `on` 读成 `True:` 时仍是触发块 |
| checkout 深度 | 1 | `fetch-depth: ${{ }}` 按浅克隆的默认值 1 读 |
| `DECLARED` 校验 | 2 | T4/T8 对**缺理由**报警、对**缺日期**不报警（`entry[1]` 与 `entry[2]` 差一个字符，两边都没钉住：一张写满 `("DATA ALEX", "", "日期")` 的表——有主人没理由，正是「没人需要解释的借口」那个形状——以前能过 T4） |
| `render()` | 7 | 截断算术（7 条印 3 条 + 「... and 4 more」；正好 3 条不印「more」）· 深度措辞（None/0/1/2 三种）· `[declared]` 与 `[UNDECLARED]` 标签 · 已声明的触发过滤器不再报警而未声明的仍报 · `certified` 键缺失时**不**盖「NOT CERTIFIED」章 |

`render()` 那一簇值得单独记一句：**这个工具唯一的产物是那份报告，而报告只有两条测试。**
深度措辞的三个存活点坐在同一个表达式上（`is None` / `== 0` / 那个 `0`），
改错了就会在一个 depth-1 的浅克隆上印「full history」——**而这正是这道闸写出来要制止的那句谎**。

## 四、剩下的 20 个里，9 个长在一个跑不到的函数上

`_marker_expr()`（6 行）——**全仓零调用**。`parse_pytest_args` 后来在自己肚子里长了一份同样的实现，
这个早期草稿留在原地。9 个存活点全在它身上。

> **一个读法上的规矩**：变异存活清单**分不出「没测到」和「跑不到」**。
> 存活点密集地挤在一个小函数上，先当成第二种，别急着给它补测试——
> **把死代码钉住，正是让它看起来不像死代码的办法。**

删掉它（不是补测试）。站点数 174 → **165**，正好少 9 个。

## 五、收尾读数：154/165 = 93%

四段（0:42 / 42:84 / 84:126 / 126:165）：95% / **100%** / 90% / 87%。

剩 11 个，逐个判过：

| 位置 | 变异 | 判 |
|---|---|---|
| L345 `Gt->GtE` · L345 `2->3` · L346 `2->3` | `-m` 解析的长度边界 | **等价**：`head == "-m"` 那个或分支先短路，长度分支只有 `len(t)==3`（即标记表达式只有 1 个字符）时才分家，而 `not X` 至少 5 个字符 |
| L636 `1->2` | `key.split(":", 1)[1]` 的 maxsplit | **等价**：键只有一个冒号，`split(":",2)[1]` 同值 |
| L699 `3->4` | `if len(items) > 3` | 只在**恰好 4 条**时分家；我量的是 7 和 3 两个边界，漏了 4。下轮补一条 |
| L712 `0->1` | argparse 的 `__doc__.splitlines()[0]` | 帮助文本第一行，**不改判定** |
| L390 `Lt->LtE` · L400 `And->Or` | `conditional_run_blocks` 的缩进与空行 | 造不出真实的 YAML 让两者分家（job 级 `if:` 必然比 step 项浅），留账 |
| L501 `GtE->Gt` · L506 `And->Or` · L506 `In->NotIn` | `pytestmark` / `skipif` 的 ast 读取 | **真洞，没补**——时间盒到了。下轮第一件事 |

## 六、可复跑

```bash
python3 -m pipeline.tools.audit_mutation_sweep --module audit_ci_test_coverage --list-sites | tail -1
python3 -m pipeline.tools.audit_mutation_sweep --module audit_ci_test_coverage \
        --index-from 0 --index-to 42        # 其余三段 42:84 / 84:126 / 126:165
```
每段约 5 分钟（前台 10 分钟上限内）。改了 `audit_ci_test_coverage.py` 的源码，索引就不再对齐——
`total_sites` 印在每份报告里，就是防止跨改动合并切片的那道闸。
