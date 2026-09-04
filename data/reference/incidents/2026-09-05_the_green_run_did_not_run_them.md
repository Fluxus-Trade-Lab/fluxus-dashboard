# 那次绿色的运行没跑到它们

**日期**：2026-09-05（夜间组 Nighty Zac）
**形状**：接线了 —— 接线的那次没跑到 614 个测试，其中一条已经红了 8 天半。
**同族**：`pitfall_tested_the_module_not_the_wiring` · `pitfall_a_negative_control_is_not_a_calibration_check` ·
`pitfall_my_gate_had_no_resolution`（都是「闸在，但它量的东西不在它眼里」）

---

## 一、一句话

`.github/workflows/tests.yml` 在 2026-09-04 落地，`audit_wiring.tests_have_ci()` 从 False 变 True，
`DATA_RELIABILITY.md` §六.5 那条「这 1,302 条测试没有任何自动触发点」的缺口被当作关闭。
**它没关闭。** 那次调用跑的是 `pytest pipeline/tests -q -m "not slow"`，在一个 depth-1 的 checkout 里 ——
按 ast 计，**仓库 1,988 个测试函数中 614 个不在任何自动运行里**。

## 二、614 是怎么分的（每个数都现场量过）

| 被漏掉的原因 | 条数 | 里面有什么 |
|---|---|---|
| `pytest pipeline/tests` 只指了一个测试根 | **607** | 整个 `tests/` 根。里面有一条**红的**。 |
| `-m "not slow"` | **3** | 含 `test_run_all_end_to_end` —— §六.0 记着「首跑就抓了三只真虫」的那条端到端 smoke |
| `actions/checkout` 没写 `fetch-depth` = depth 1 | **4** | `test_audit_regression_gate` 里唯一用**真实事故数字**复现 08-27 覆盖事故的四条 |

第三行是最难看的一行：**钉着我们最严重那次数据事故的检查，不在我们读它绿的那次运行里。**
而那次运行自己说了 —— `1327 passed, 4 skipped, 3 deselected`，然后 exit 0。
「skipped」和「deselected」不是错误，没有人读它们，也没有任何东西因为它们变红。

## 三、那条红了 8 天半的测试

`tests/test_no_naive_clock.py::test_no_bare_naive_clock_in_trading_code`

守卫本体建于 **2026-07-23**（`8efffad7`）：本机跑在 JST，比 ET 早约 13 小时，
裸 `date.today()` 在美股当天的大部分时间里返回「明天」。

它在 **`6f66f5f9`（2026-08-27 16:18 JST，联邦看板 v0 落地）** 转红。
**二分，不是推断**：

```
494f4689 (parent, 08-27)  1 passed
6f66f5f9 (08-27 16:18)    1 failed
a2494136 (08-27, board v3) 1 failed
882475da (origin/main, 09-05) 1 failed
```

红到今天：**8 天 12 小时**（日历日跨 9 天 —— 这两个数不一样，写「9 天」是把日历差当成了经过时长）。
没人看见，因为 09-04 之前 CI 一条测试都不跑，09-04 之后 CI 只跑另一个根。
**且中间一秒都没绿过**：对 `6f66f5f9^..origin/main` 之间碰过 `pipeline/`／`scripts/`／该测试文件的
**全部 75 个 commit** 复跑，flips=0，违规处数只增不减（1 → 3）。

三处违规里**只有一处是真错**（详见修复分支 `f0899fac`）：
`federation_board.py` 在 `marketcal` 取不到时的退路里用 `date.today()` 算「上一场完成的交易日」。
此刻实测 ET 是 `2026-09-04` 而 `date.today()` 给 `2026-09-05` —— 差一天，再 while 往回退，整体推后。
（潜在错：pandas 在时该分支不执行。）另两处本来就该是本地时钟，已按守卫自己的 opt-out 写法豁免。

**守卫三条报了一条真的。这恰恰是它该一直在跑的理由 —— 它没在跑。**

## 四、根因：一个 bool 没有分辨率

`audit_wiring` 问对了问题（「有东西调用你吗」），但对测试套件它只回答了一个 **bool**：

```python
def tests_have_ci(workflows: Path) -> bool:
    ...  # 某个自动触发的 workflow 里出现 pytest 这个词 -> True
```

「有人跑测试」和「跑到了这些测试」是两个问题，而第一个的答案是 True 时，第二个从来没被问过。
这与 09-04 那条 `pitfall_my_gate_had_no_resolution` 是同一形状：
**闸响不响，取决于它有没有分辨率去看它声称在看的那个东西。**

## 五、做了什么

1. `pipeline/tools/audit_ci_test_coverage.py`（+41 条测试，commit `aabf4d98`）——
   把那个 bool 换成一个**集合**：读 workflow（不跑 pytest），算出自动运行**不执行**哪些测试，
   按 `audit_wiring` 的棘轮形状把今天的 614 条以 owner／理由／发现日声明进 `DECLARED`，今天绿，
   T1–T6 任一变化就红。**声明条目是欠条，不是解决。**
2. 修复分支 `auto/night-20260905-805da3-fbclock`（`f0899fac`）—— 三处裸时钟。
   `pipeline/tools/federation_board.py` 不在夜间组白名单，**留分支待合**。
3. 新 guard 自己无自动触发，已按既有渠道登记进 `audit_wiring.KNOWN_UNWIRED`，owner 写在本线之外。

## 六、还没做的（欠条，都需要动 `.github/workflows/tests.yml`）

| 改动 | 收回什么 |
|---|---|
| `fetch-depth: 0` | 4 条复现真实事故的回归测试 |
| 目标加上 `tests` | 607 条，含这条红了 8 天半的守卫 |
| 去掉 `-m "not slow"`（或另开一个跑 slow 的 job） | 端到端 smoke |
| 把 `audit_ci_test_coverage` 挂进 `audit_wiring (reported)` 旁边 | 下一个盲点自己会喊 |

⚠️ 加 `tests` 之前先知道它会不会红 —— 已经替你跑过了，**在一个装了 `jinja2` 的干净 venv 里**
（`jinja2>=3.1` 本来就在 `pipeline/requirements.txt:27`，CI 会装；本机没装不算数），
命令就是 workflow 该写的那条：

```
pytest pipeline/tests tests --ignore=tests/gex/test_resting.py
```

| 在哪 | 结果 |
|---|---|
| `origin/main`（`e1e5ea21`） | **1 failed / 2161 passed / 6 skipped** —— 唯一那条就是本档案讲的守卫 |
| 修复分支 `…-fbclock`（同基） | **2162 passed / 6 skipped，零失败** |

所以顺序是：**先合修复分支，再改 workflow**。反过来 CI 首日就红，而且红的是一条
「已经红了八天半、和这次改动无关」的老账 —— 那种红最容易被当成噪声关掉。

**还有一件必须先办的**（现场量的，不是推断）：`tests/gex/` 有 79 条测试 + 5 个收集不了的文件。
其中 4 个缺的是 `jinja2`，而 `jinja2>=3.1` **已经在** `pipeline/requirements.txt:27` 里 ——
那 4 个只是本机没装，CI 装完就好。**第 5 个不一样**：`tests/gex/test_resting.py` 缺 `ib_async`，
而 `ib_async` **在任何 requirements / pyproject / workflow 里都不存在**
（`grep -rn "ib_async" --include=*.txt --include=*.toml --include=*.cfg --include=*.yml` 零命中），
且 `pipeline/gex/ibkr.py:10` 是**模块顶层** import。
所以只要把 `tests` 加进 CI 目标，那个文件就是一个 collection error，CI 直接红。

顺带一处不一致：`pipeline/ibkr.py:48` 把同一个 import 写在函数体里（懒加载），
`pipeline/gex/ibkr.py:10` 写在顶层。同一个可选依赖，两种写法，只有后者会在收集期炸。

→ 三选一，交给动 workflow 的那条线：把 `ib_async` 加进 requirements ·
把那个 import 改成 `pipeline/ibkr.py` 那样的懒加载 · 或在 CI 目标里显式 `--ignore=tests/gex/test_resting.py`
并把理由写在旁边（别静默 ignore —— 静默 ignore 正是这份档案在讲的病）。

## 六点五、⚠️ 独立验证推翻了我自己的三条（当晚，两个对抗性 verifier）

按宪法「研究结论走 fan-out，≥2 个不同视角独立验证」派了两个 verifier。**它们赢了三次**，
每一条我都自己复跑复核过之后才改：

**① 我转抄了一个过期的数。** 上面这份档案第一版写「1,950 个测试函数」——
那是我**在把自己那 41 条新测试加进去之前**跑出来的读数。工具此刻打印的是 **1,988**。
同一个坑账 `pitfall_i_quoted_a_stale_number_three_times` / `pitfall_a_measurement_expires`：
**我量的数也会过期，而且最容易过期的是我自己刚改动的那部分。**

**② 「红了 9 天」是日历日差，不是经过时长。** 实际 8 天 12 小时。
（verifier 还把我的验证做宽了：不只复跑碰过那两个文件的 commit，而是复跑了区间内碰过
`pipeline/`／`scripts/` 的全部 75 个 —— flips=0，中间一秒没绿过。结论更强，措辞更准。）

**③ `federation_board.py` 那三处裸时钟，我判错了一处。**
我说 `now = datetime.datetime.now()` 「本来就该是本地」，给它挂了 `# localtime-ok` 豁免。
verifier 指出：**错的不是 `now`，是减法的另一边。** 同文件取 git 日期用的是 `--date=format:`，
而 `%ad` 默认按**每个 commit 自己记录的时区**渲染，云端跑的班是 `+0000`。
我自己复核：近 14 天 686 个 commit 里 **8 个落在错的本地日**
（`ab3c0bd3` 09-03→09-04 · `f7b62b87` 09-01→09-02 · `2b8c4be5` 等四条 08-30→08-31 · …），
而错位的恰好是夜间数据班那批最有代表性的 commit。
→ **只挂豁免不改格式串，守卫会变绿而 bug 被冻在里面。** 已改 `--date=format-local:`（`d3fda100`）。

> 这一条值得单独记：**豁免让检查变绿，不让东西变对。**
> 一个带 opt-out 的守卫，opt-out 用错的时候比没有守卫更糟 —— 它给了那个 bug 一张通行证。

## 六点六、然后 verifier 把我这个新工具造成了假绿，五次

另一个 verifier 的任务是「证明这个审计器会 under-report」。**它成功了五次**，我逐个复现属实：

| 形状 | 首版结果 |
|---|---|
| `if: false` 挂在 pytest step 上 | **0 violations**，一条测试没跑 |
| job 级 `if:` | 同上 |
| `pytest $PYTEST_ARGS` | `$PYTEST_ARGS` 被当成**目标路径**，藏在里面的 `--ignore=` 彻底隐形 |
| `on: push: paths: ['frontend/**']` | `_triggers` 只读键名不读过滤器 |
| `pytest tests --collect-only` | **最毒**：清空 `tests` 桶 → 工具报 T2「这条声明现在不排除任何东西，删掉它」 |

最后一条是这份档案里第二严重的事：**工具亲自指挥人走进假绿。**
它的 anti-rot 机制（T2 逼你删掉已修好的借口）在被喂了一个「看着像跑测试其实什么都不跑」的
选项时，把「测试没被排除」和「测试根本没跑」当成了同一件事。

另有 5 个注射变异体在首版的 41 条测试下**全部存活**，方向清一色是 under-report——
其中 `test_render_names_the_owner_of_every_bucket_it_prints` 是**空断言**
（只数 `"owner:"` 出现次数，把 render 改成对每个桶都印 `owner: ?` 照样 41 绿），
正是坑账 `pitfall_a_test_that_reads_its_own_constant` 的形状。
另一条正对照 `test_two_checkouts_report_the_shallow_one_not_the_deep_one` 的 fixture 是 `[0, 1]`，
**而 0 在 `min` 之前就被过滤掉了，min == max == 1 —— 这条正对照测不出它命名的那件事。**

全部已修（`83dc972d`）：四种形状变成 caveat → T5 → `certified=False`，
报告顶部直接打「NOT CERTIFIED，下面每个数都是排除量的**下界**」；
`--collect-only` 移出已建模选项；测试 41 → 69；复跑 12 个变异体 11 个 KILLED。

**这一节本身就是那条教训的第二个实例**：我写了一个工具去问「那个绿覆盖了多少」，
而它自己的绿，在被人认真攻击之前，同样没有分辨率。

## 六点七、⚠️ 第五条：我写这个 bug 的散文，被守卫当成了这个 bug

写完上面这份档案之后，`audit_ci_test_coverage.py` 的 docstring 里逐字出现了那两个被禁的调用
（因为我在解释 `federation_board` 犯了什么错）。而 `tests/test_no_naive_clock.py` 匹配前
**只剥 `#` 注释，不剥字符串字面量** —— 于是**描述这个模式的 docstring 读起来就是这个模式**，
守卫对我这个新文件报红。

**没有用 `# localtime-ok` 去消音**，改成了转述。理由写在 `e1e5ea21` 里：
拿豁免去压一个误报，正是让那条真违规坐了八天半的那个习惯（见 §六点五 第 3 条）。

**真正的修法在守卫那边**：用 `ast` 跳过字符串字面量，不只跳注释
（那份守卫自己的 docstring 写着「skip the module docstring … is overkill here」——
09-05 之后不再 overkill 了，它已经产生了第一个假阳性）。
`tests/` 不属夜间组边界 → **只报不改，已列门铃。**

## 七、教训

> **「有人跑测试」是个 bool，「跑到了哪些测试」是个集合。**
> 一个 bool 变 True 之后，没人再问第二个问题 —— 而缺口就住在第二个问题里。
>
> 推论（可迁移）：任何写成 `has_X()` 的闸，都要问一次
> **「它 True 的时候，X 覆盖了多少？」**。这条同样适用于
> 「有备份」「有监控」「有告警」「有审计」。
