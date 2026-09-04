# 那次绿色的运行没跑到它们

**日期**：2026-09-05（夜间组 Nighty Zac）
**形状**：接线了 —— 接线的那次没跑到 614 个测试，其中一条已经红了 9 天。
**同族**：`pitfall_tested_the_module_not_the_wiring` · `pitfall_a_negative_control_is_not_a_calibration_check` ·
`pitfall_my_gate_had_no_resolution`（都是「闸在，但它量的东西不在它眼里」）

---

## 一、一句话

`.github/workflows/tests.yml` 在 2026-09-04 落地，`audit_wiring.tests_have_ci()` 从 False 变 True，
`DATA_RELIABILITY.md` §六.5 那条「这 1,302 条测试没有任何自动触发点」的缺口被当作关闭。
**它没关闭。** 那次调用跑的是 `pytest pipeline/tests -q -m "not slow"`，在一个 depth-1 的 checkout 里 ——
按 ast 计，**仓库 1,950 个测试函数中 614 个不在任何自动运行里**。

## 二、614 是怎么分的（每个数都现场量过）

| 被漏掉的原因 | 条数 | 里面有什么 |
|---|---|---|
| `pytest pipeline/tests` 只指了一个测试根 | **607** | 整个 `tests/` 根。里面有一条**红的**。 |
| `-m "not slow"` | **3** | 含 `test_run_all_end_to_end` —— §六.0 记着「首跑就抓了三只真虫」的那条端到端 smoke |
| `actions/checkout` 没写 `fetch-depth` = depth 1 | **4** | `test_audit_regression_gate` 里唯一用**真实事故数字**复现 08-27 覆盖事故的四条 |

第三行是最难看的一行：**钉着我们最严重那次数据事故的检查，不在我们读它绿的那次运行里。**
而那次运行自己说了 —— `1327 passed, 4 skipped, 3 deselected`，然后 exit 0。
「skipped」和「deselected」不是错误，没有人读它们，也没有任何东西因为它们变红。

## 三、那条红了 9 天的测试

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

红了 **9 天**。没人看见，因为 09-04 之前 CI 一条测试都不跑，09-04 之后 CI 只跑另一个根。

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
| 目标加上 `tests` | 607 条，含这条红了 9 天的守卫 |
| 去掉 `-m "not slow"`（或另开一个跑 slow 的 job） | 端到端 smoke |
| 把 `audit_ci_test_coverage` 挂进 `audit_wiring (reported)` 旁边 | 下一个盲点自己会喊 |

⚠️ 加 `tests` 之前先知道它会不会红。本机实测（两次都排除 `tests/gex`，本机缺 `jinja2`/`ib_async`，
那是环境不是代码）：

- `origin/main` 上单跑 `tests` → **1 failed / 528 passed**（就是上面那条守卫）
- 修复分支上跑 `pipeline/tests + tests` → **2004 passed / 6 skipped，全绿**

所以顺序是：**先合修复分支，再改 workflow**。反过来会让 CI 首日就红。

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

## 七、教训

> **「有人跑测试」是个 bool，「跑到了哪些测试」是个集合。**
> 一个 bool 变 True 之后，没人再问第二个问题 —— 而缺口就住在第二个问题里。
>
> 推论（可迁移）：任何写成 `has_X()` 的闸，都要问一次
> **「它 True 的时候，X 覆盖了多少？」**。这条同样适用于
> 「有备份」「有监控」「有告警」「有审计」。
