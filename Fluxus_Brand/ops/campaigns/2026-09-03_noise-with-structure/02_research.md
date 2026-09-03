# 02 · 证据包 —— noise-with-structure（2026-09-03）

> ② 查证站产出。**本站不写稿、不定标题**，只交「这个 campaign 能证明什么」的边界。
> 全部数字**现场读权威源**（`git show origin/main:` / 原始 JSON / 外部文档），无一手打、无一转抄 signal 节。
> 凡我自己重算的，命令留在本页末节，任何人可再跑一次。

---

## 〇 · 一句话结论（给下游三站）

**机制层面 7 条主张全部核实通过，其中 3 条是我独立重算出来的（不是引用）；外部权威源已拿到（CPython 官方文档 + PEP 552 + CPython 源码，三处互证）。**
但 signal 节有 **1 处单位错**（6pp 被写成 6%）和 **1 处过头**（把「6pp 噪声」整体等同于「读数大面积是错的」，而源文自己写的是"错的判定一共 5 个"）。
另有 **6 条未证实项**，其中最重的一条是：**signal 节的三个交易类比一个票根都没有**。

---

## 一 · 已核实主张（7 条）

### C1 【常青】同一个 commit、同一台机器、同一个模块，这台仪器跑 4 次给出 43% / 47% / 49% / 43%，跨度是 **6 个百分点**

- **权威源**：`git show origin/main:data/research/audit_mutation_2026-09-01.md` §六（commit `a2e3132b`，2026-09-01 07:55:58 +0900，Plumber Joe）
- **原文口径**：4 次分别是 `--module` 第 1 次 21/49、全模块跑 23/49、`--module` 第 2 次 24/49、`--module` 第 3 次 21/49。commit 是 `02e387d1`，模块是 `audit_universe_shape`。
- **我的核实**：其中 **2 次有归档原始 JSON，我逐格核过**——
  - `data/research/audit_mutation_2026-09-01_single.json` → `killed: 21, mutants: 49, kill_rate: 0.429`
  - `data/research/audit_mutation_2026-09-01_all.json` → `killed: 23, mutants: 49, kill_rate: 0.469`
  - 第 3、4 次（24、21）**只在 Joe 的散文表里，无归档 JSON**（见 §四 未证实项 U1）。

> ⚠️ **单位更正（必须带到稿子里）**：Joe 的原文一律写 **6pp / 6 个百分点**。
> signal 节的标题写成「**6% 的随机噪声**」，素材箱 09-02 行（commit `94cbc57e`）也写成「6% 的随机噪声」。
> 43%→49% 是 **6 个百分点**，不是 6%（相对变化是 14%）。**这是 signal 节抄错了，以我读到的源为准。**

---

### C2 【常青】那 6 个翻转的判定，我从两份原始 JSON 独立重算出来，逐格与 Joe 的表一致

- **权威源**：同上 §六 的六行表 / 原始 JSON 两份的 `survivors` 数组
- **我算的（不是抄的）**：取两份 JSON 的存活集合做对称差 —— 结果 **恰好 6 个**：

| 变异体 | 单跑 | 全跑 | 方向 |
|---|---|---|---|
| L56 `20 -> 21`（`WINDOW = 20`） | 存活 | 被杀 | 存活→被杀 |
| L64 `0 -> 1` | 存活 | 被杀 | 存活→被杀 |
| L83 `0.0 -> 1.0` | 存活 | 被杀 | 存活→被杀 |
| L96 `100 -> 101` | 存活 | 被杀 | 存活→被杀 |
| L155 `0 -> 1` | 被杀 | 存活 | 被杀→存活 |
| L158 `Eq -> NotEq` | 被杀 | 存活 | 被杀→存活 |

- 顺带核到分母自洽：单跑 21 杀 + 28 存活 = 49；全跑 23 杀 + 26 存活 = 49。
- 并核过 Zac 警告的**描述符碰撞**在这次比对里不咬人：两份的 `(line, kind, change)` 三元组去重后个数 = 原列表长度（28/28、26/26），所以这个 6 是真的 6。
- **复算命令**：见 §六 R1。

---

### C3 【常青】48 对相邻变异体里，**恰好 22 对**的字节数完全相同 —— 我用工具自己的代码重新生成了这 49 个变异体

- **权威源（我们的）**：`data/research/night_reports/2026-09-02.md` §②甲（commit `deb7a0f5`）；同一个数也写在代码 docstring 里：`pipeline/tools/audit_mutation_sweep.py` 第 127–140 行 —— *"22 of the 48 adjacent pairs in audit_universe_shape"*。
- **我的独立复现**：取 `02e387d1` 上的 `audit_universe_shape.py`（7,082 字节）与同 commit 的 `audit_mutation_sweep.py`，调用它自己的 `sites()` / `build_mutant()` 生成全部变异体并量字节长度：

```
mutant count at 02e387d1: 49
adjacent pairs: 48 | pairs with byte delta 0: 22
delta histogram: [(0, 22), (-4, 5), (5, 4), (3, 3), (1, 3), (-1, 3)]
```

  → **49 / 48 / 22，与源文逐格一致。这一条不是引用，是重算。**
- ⚠️ **精度补正**：`22/48` 是**特指 `audit_universe_shape` 在 commit `02e387d1`**，不是全仓通例、也不是这个 bug 的普适比例。signal 节写「48 对相邻里 22 对」时没带这个限定条件，**稿子里必须带**（否则读者会以为这是一个关于 Python 的常数）。
- **复算命令**：见 §六 R2。

---

### C4 【常青】**6 个翻转的变异体，每一个与它前一个变异体的字节差都是 0（6/6）** —— signal 节没有这一条，它是本卡机制链上最关键的一环

- **权威源（我们的）**：`night_reports/2026-09-02.md` §②甲：*"与前一个变异体的字节差全部是 0"*
- **我的独立复现**（把 C2 的 6 个翻转映射回 C3 的变异体序列，量各自与前一个的字节差）：

| 变异体序号 | 行 | 变异 | 与前一个的字节差 |
|---|---|---|---|
| 1 | L56 | `20 -> 21` | **0** |
| 3 | L158 | `Eq -> NotEq` | **0** |
| 16 | L155 | `0 -> 1` | **0** |
| 35 | L83 | `0.0 -> 1.0` | **0** |
| 46 | L64 | `0 -> 1` | **0** |
| 47 | L96 | `100 -> 101` | **0** |

  → **6/6。**
- **我顺手算了这件事有多不像巧合**：48 对里有 22 对是零差（基础比例 45.8%），6 个翻转全部落在零差位置的**超几何概率 = 0.0061**（二项近似 0.0093）。
- ⚠️ **这是关联，不是因果**，n 也只有 6。**因果由干预实验给**（C5），不由这个概率给。稿子里若引这个 0.006，必须紧跟一句"真正的证明是把缓存关掉"。
- **复算命令**：见 §六 R3。

---

### C5 【常青】干预确认：关掉字节码缓存后离散度归零；**而且修复已经在 main 的代码里，还自带阳性对照**

**干预结果**（权威源：`night_reports/2026-09-02.md` §②甲 + `data/research/audit_mutation_2026-09-02.md` §五，commit `10991810`）：

| | 协议 | 结果 |
|---|---|---|
| 修正前 | `audit_universe_shape` 三次独立调用 | **41% / 45% / 47%，10 个变异体翻转** |
| 修正后 | 同模块连跑 3 次 | **45% / 45% / 45%，存活集合逐位相同** |
| 修正后 | 全模块基线独立跑两轮，475 个变异体 | 杀死数与存活集合（**按 `index` 比，不按描述符**）全部逐位相同 |

- **我的核实**：修正后基线 JSON `data/research/audit_mutation_2026-09-02_baseline.json` 里 `audit_universe_shape` = `{mutants: 49, killed: 22, kill_rate: 0.449}` → 印作 45% ✅。
- **⚠️ 归档缺口**：`data/research/` 下 09-02 只有**一份** baseline JSON。「连跑 3 次」的另外两轮、「独立两轮」的第二轮**没有原始文件**，只有散文。（见 U2）

**修复已落地（不只是写在报告里）** —— `git show origin/main:pipeline/tools/audit_mutation_sweep.py`：

```python
# 第 168–171 行
[sys.executable, "-B", "-m", "pytest", f"pipeline/tests/test_{module}.py",
 "-q", "-x", "--no-header", "-p", "no:cacheprovider"],
cwd=self.dir, capture_output=True, text=True, timeout=TEST_TIMEOUT,
env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
```

并且**这台仪器此前四晚一条测试都没有**，同一个 commit 补了 7 条，其中 3 条是注射式阳性对照 ——
`pipeline/tests/test_audit_mutation_sweep.py::test_no_bytecode_cache_is_left_for_the_mutated_module`
（拿掉 `-B` 必须报出残留 `.pyc`）、`test_unstable_mutant_is_reported_and_kept_out_of_the_kill_rate`（注射真 flaky 测试 → 必须报 UNSTABLE）、`test_a_timeout_is_no_verdict_not_a_kill`（注射 hang → 必须报 no_verdict）。
commit `deb7a0f5`（2026-09-02 04:55:59 +0900）：`+210` 行测试 / `+103 −21` 行工具。**我核过 commit 存在且 stat 相符。**

---

### C6 【常青，带版本范围】外部权威源 ✅ 已拿到 —— CPython 判 `.pyc` 是否失效，默认只看 **(源文件 mtime 取整到整秒, 源文件字节数)**

这是外部事实，**不引我们自己的夜报**。三处互证：

**① Python 官方语言参考 · 5.4.6 Cached bytecode invalidation**
<https://docs.python.org/3/reference/import.html#cached-bytecode-invalidation>
> "Before Python loads cached bytecode from a `.pyc` file, it checks whether the cache is up-to-date with the source `.py` file. By default, Python does this by storing the source's last-modified timestamp and size in the cache file when writing it."

**② PEP 552 — Deterministic pycs**（Python 3.7）
<https://peps.python.org/pep-0552/>
> "The current Python pyc format is the marshaled code object of the module prefixed by a magic number, the source timestamp, and the source file size."
> 并明写 hash-based pyc 是**可选**：*"The current timestamp invalidation method will remain the default"*。

**③ 「取整到整秒」在文档里没写，权威源是 CPython 源码** —— `Lib/importlib/_bootstrap_external.py`：

```python
source_mtime = int(st['mtime'])                                    # ← 截断成整秒
...
def _validate_timestamp_pyc(data, source_mtime, source_size, name, ...):
    if _unpack_uint32(data[8:12]) != (source_mtime & 0xFFFFFFFF):
        message = f'bytecode is stale for {name!r}'
    if (source_size is not None and
        _unpack_uint32(data[12:16]) != (source_size & 0xFFFFFFFF)):
```

我在**两处**核到同样的行：
- GitHub `python/cpython` 分支 `3.11`：<https://github.com/python/cpython/blob/3.11/Lib/importlib/_bootstrap_external.py>
- 本机 CPython **3.14.3**：`/usr/local/Cellar/python@3.14/3.14.3_1/.../importlib/_bootstrap_external.py`（`inspect.getsource` 现场读）

**版本范围（保质期）**：时间戳判据自 `.pyc` 存在起一直是默认；Python **3.7** 起有 hash-based `.pyc` 可选（`--check-hash-based-pycs`），但**默认仍是时间戳**。所以这句话在 3.7–3.14 上都成立，**前提是没人显式启用 hash-based pyc**。若哪天 CPython 把默认翻过去，本条失效——复查方式：重读上面 ①③ 两个链接。

**④ `-B` / `PYTHONDONTWRITEBYTECODE` 的确切语义**（<https://docs.python.org/3/using/cmdline.html>）：
> `-B`: "If given, Python won't try to write `.pyc` files on the import of source modules."
> `PYTHONDONTWRITEBYTECODE`: "If this is set to a non-empty string, Python won't try to write `.pyc` files on the import of source modules. This is equivalent to specifying the `-B` option."

⚠️ **它管的是「写」，不管「读」。** 这个精确度对写稿重要——见 §三「出处证明不了什么」第 4 条。

---

### C7 【⚠️ 有时效】任何「这道闸现在的杀死率是 X%」在稿子里都会过期 —— 09-02 一夜之内动了三个

| 闸 | 09-02 凌晨 | 同一夜补测试后 | commit |
|---|---|---|---|
| `audit_universe_shape` | 22/49 = 45% | **63%** | `753941d1` |
| `audit_calendar_gaps` | 40/92 = 44% | **61%** | `31bfbcf9` |
| `audit_archives` | 54/101 = 54% | **57%** | `bb88d995` |

- **保质期**：到下一次有人读一遍存活清单为止。**实测跨度＝几小时**。
- **复算方式**：`python3 -m pipeline.tools.audit_mutation_sweep --module <名> --json out.json`
- **权威源**：变异杀死率**不在** `KNOWLEDGE.md` 数字权威表里；唯一权威源＝当日归档的 `data/research/audit_mutation_<日期>*.json`，**引用必须带日期**。

> ✅ **给下游的取数建议**：整篇只用「**41/45/47 → 45/45/45 逐位相同**」这一组**关于仪器本身的离散度**数字（它已冻结、是历史事实），
> **不要引任何单个闸的当前杀死率**——那些是活的，发出去就开始腐烂。

---

## 二 · 矛盾与缺失证据（我在源里实际撞到的）

| # | 是什么 | 判定 |
|---|---|---|
| X1 | **单位**：Joe 原文一律 `6pp`；signal 节标题与素材箱 09-02 行都写成「6% 的随机噪声」 | **signal 节抄错，以 6 个百分点为准** |
| X2 | **源 A 自己不自洽**：`audit_mutation_2026-09-01.md` §二表把 `audit_universe_shape` 记为 `21/49 = 43%`，§五全模块基线表记为 `23/49 = 47%` | **两个数都对**（一个是单跑第 1 次、一个是全跑），但同一份文件用同一个模块名给了两个数且未互相说明。**引用必须带跑法** |
| X3 | **同一个 42/80 印成两个百分数**：`audit_ledger` 在 09-01 文件里是 **52%**、在 09-02 文件里是 **53%**（原始 JSON `kill_rate: 0.525`，两边舍入方向不同） | **数据没变，是舍入。** 别写成"从 52 涨到 53" |
| X4 | 舍入无统一规则：`audit_archives` 53.5% 两处都印 54%（向上），`audit_ledger` 52.5% 一处向下一处向上 | 记账噪声，不影响结论；但说明**百分数是印出来的，分数才是数据** |
| X5 | **signal 节把「6pp 噪声」整体等同于「它在测错对象」** | ⚠️ **过头。** Zac 自己在 `audit_mutation_2026-09-02.md` §四明写：修正后六个模块**五个逐位相同，错的判定一共 5 个，全在 `audit_universe_shape`**，并加了一句"我不想把它说得比实际严重"。机制是真的、干预确认了、离散度归零了——但"读数大面积是错的"**不成立** |

---

## 三 · ⛔ 出处证明不了什么（单列 —— 下游任何一站都不许把下列任何一条当前提）

1. **证明不了「所有杀死率读数都不可信」。** 实际杀伤是 **475 个变异体里 5 个判定**，全部集中在一个模块。修它的理由是"错得不可预测且是系统性的"，不是"错得多"。
2. **证明不了这个 bug 在别的仓库/别的工具里普遍存在。** Zac 全仓扫过"写文件 + 起 python 子进程"的同形状，`pipeline/` 里只有这一处（`federation_board.py` 的命中是文档字符串）。**样本 n=1**，而且我没有复跑这个扫描（见 U6）。
3. **证明不了「多跑几次看不见它」。** 恰恰相反：**三次独立调用就看见了**（41/45/47，10 个翻转）。看不见它的是**同一次调用里**重复跑——隔离连跑 12 次 12/12 一致、`--repeat 3` 零翻转。
   ⚠️ signal 节写「让它现形的不是多跑几次」**必须改精确**：不是"多跑几次没用"，是"**在同一次调用里**多跑几次没用"。否则读者带走一个错的动作。
4. **证明不了 `-B` 能救一个已经躺在磁盘上的脏 `.pyc`。** 官方文档原文只说它禁止**写**。这里之所以有效，是因为循环里不再产生新的 `.pyc`；工具另有一条测试专门盯残留（`test_no_bytecode_cache_is_left_for_the_mutated_module`）。
5. **证明不了「翻转 ⇒ 字节差为 0」是因果。** 它是关联（6/6，超几何 p≈0.006，n=6）。因果来自**关掉缓存后离散度归零**这个干预。
6. **⚠️ 最大的风险 —— 证明不了任何交易场景的类比。** signal 节举的三个（walk-forward 每折差 5 个点 / 三笔连亏 / 滑点翻倍）**一个票根都没有**，我们仓里没有任何一项的实测。它们是**修辞，不是证据**；写稿时必须以类比的语气出现，**不许带数字、不许写成"我们发现"**。
7. **证明不了「22 是真值」是无条件的。** 22/49 是"这台机器、这个 commit、缓存关掉后"的读数。Zac 自己加了保留：*"这只证明了在这台机器、这个 commit 上离散度为 0"*。"Joe 四次没有一次量对"这句锋利，但**必须带这个限定**。

---

## 四 · 未证实项（6 条，单列非空）

| # | 未证实的是什么 | 缺什么 |
|---|---|---|
| **U1** | Joe「4 次跑分」里的**第 3、4 次**（24/49、21/49） | 无归档 JSON，只有散文表。前两次有 JSON 我已核。**如要引"四次"，得接受其中两次是单源散文** |
| **U2** | 「关掉缓存后连跑 **3 次** 45/45/45」与「全模块独立**两轮** 475 个变异体逐位相同」 | `data/research/` 下 09-02 只归档了**一份** baseline JSON；其余轮次无原始文件 |
| **U3** | 「**同一秒内写完**」 | 我复算了字节数相同（22/48，C3），但**没有量过两次写入的时间间隔**。机制要求两条同时成立，**我只证了一条** |
| **U4** | signal 节的三个交易类比（walk-forward 折差 / 三笔连亏 / 滑点翻倍） | **零票根。** 属修辞 |
| **U5** | 「没人写过这个角度」 | signal 节自己已声明**未做红海扫描**。本站也没做（不在本站 reads 范围，且无留存红海源）。仍是未证实 |
| **U6** | 「同形状全仓只此一处」 | 我没有复跑 Zac 的那次扫描 |

---

## 五 · 2–3 个值得展开的机制（给角度站/旗舰站挑）

### M1 ⭐ 为什么所有「重复测量」式的自检都是绿的 —— 测量的边界没跨过被污染的那道缝

Zac 那张三行表是本卡机制上最强的一段（`night_reports/2026-09-02.md` §②甲）：

| 你会做的检查 | 它给的答案 | 为什么骗人 |
|---|---|---|
| 把单个变异体隔离连跑 12 次 | 12/12 完全一致 | 隔离时"上一版"就是它自己 |
| 同一次调用里连跑 3 次（`--repeat 3`） | 49 个变异体零翻转 | 同样因为上一版没变 |
| 三次**独立调用** | 41/45/47，10 个翻转 | ← **只有这个能看见** |

**可迁移的形状**：污染发生在「上一次」和「这一次」之间，而所有把上一次消掉的检查都看不见它。
这与本仓 `pitfall_having_a_row_is_not_having_data` 同族（按内容切一半的源，在所有**计数**维度下都完美）。
**读者能带走的动作**：不是"多测几次"，是"**换一个维度测**——你重复的那一维，正是污染消失的那一维"。

### M2 ⭐ 失效判据的两个字段，**都不在任何 diff 里**

mtime 和文件大小都不是源码内容。`git diff` / code review / 逐行对读，**物理上看不见它们**。
这条能直接接上弃选清单 #6（09-03「测试全绿因为它测的是模块不是接线」，那次 `git show --stat` 完全正常）——
**同一族的更强版本**：那次 diff 是正常的，这次是**判据根本不在 diff 的值域里**。
（若下游想合并两个族，这是接口；但注意 #6 是另一张卡的料，别提前烧掉。）

### M3 「真值是 22 —— Joe 四次没有一次量对」

- **我已双向核实**：修正后 baseline JSON `killed: 22`；Joe 四次是 21 / 23 / 24 / 21。**四次都不等于 22。**
- 这是全卡最锋利的一句，而且它**不是修辞，是两份归档文件相减**。
- ⚠️ 但必须带 §三第 7 条的限定（"这台机器、这个 commit"）。**去掉限定它就变成一句吹牛。**

---

## 六 · 复算留痕（任何人可再跑一次；全部只读，未写主树）

```bash
R="/Users/taolezhu/Documents/AI-Trading-System"

# R1 · 独立重算「6 个判定翻转」是哪 6 个
for f in single all; do git -C "$R" show origin/main:data/research/audit_mutation_2026-09-01_$f.json > /tmp/j_$f.json; done
python3 - <<'PY'
import json
def s(t):
    d=json.load(open(f'/tmp/j_{t}.json'))
    m=[x for x in d['modules'] if x['module']=='audit_universe_shape'][0]
    return [(x['line'],x['kind'],x['change']) for x in m['survivors']]
S,A=set(s('single')),set(s('all'))
print('killed-in-all-only :',sorted(S-A))
print('killed-in-single-only:',sorted(A-S))
print('TOTAL FLIPS:',len(S-A)+len(A-S))
PY

# R2 · 独立重生成 49 个变异体，量相邻字节差（C3）
mkdir -p /tmp/mutrepro
git -C "$R" show 02e387d1:pipeline/tools/audit_universe_shape.py   > /tmp/mutrepro/aus.py
git -C "$R" show 02e387d1:pipeline/tools/audit_mutation_sweep.py   > /tmp/mutrepro/sweep.py
python3 - <<'PY'
import ast, importlib.util
src=open('/tmp/mutrepro/aus.py').read()
sp=importlib.util.spec_from_file_location("sw","/tmp/mutrepro/sweep.py")
m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
n=len(m.sites(ast.parse(src)))
sz=[len(m.build_mutant(src,i).encode()) for i in range(n)]
print("mutants:",n,"| adjacent pairs:",n-1,
      "| zero-byte-delta pairs:",sum(sz[i]==sz[i-1] for i in range(1,n)))
PY

# R3 · 6 个翻转是否全部落在零字节差的位置（C4）—— 见本页 C4 表；脚本同 R2，多一步把 R1 的六元组映射回变异体序号

# R4 · 外部权威源本机核实（C6③）
python3 -c "
import importlib._bootstrap_external as b, inspect, re
s=inspect.getsource(b)
print(re.findall(r\"source_mtime = int\(.*\", s)[0])
print(re.findall(r'.*source_mtime & 0xFFFFFFFF.*', s)[0].strip())
print(re.findall(r'.*source_size & 0xFFFFFFFF.*', s)[0].strip())
"
```

**本站跑复算用的 Python 是 3.14.3**（本机）；被测代码在仓里标称 3.11。
两个版本上 `int(st['mtime'])` 与 `_validate_timestamp_pyc` 的实现相同（C6③ 双处核过），
且 R2 生成出的变异体个数（49）与 09-01 归档 JSON 的 `mutants: 49` 一致，说明 `ast.unparse` 的版本差异未影响本次复现。

---

## 七 · 门铃待按（本站只列不按）

- **Marketing Steve / 各线** · `Fluxus_Brand/brain/proof.md` **在册证据对象里没有这一条**。
  建议登记一行：**「变异仪器自噪声 → pyc 缓存」· 43/47/49/43 与 41/45/47→45/45/45 · 权威源 `data/research/audit_mutation_2026-09-0{1,2}*.json` + commit `a2e3132b` / `deb7a0f5`**。
  （本站按任务边界未写该文件。）
- **素材箱 09-02 行（commit `94cbc57e`）单位写错**：「6% 的随机噪声」应为「6 个百分点」。append-only 文件，建议由该行作者或 Steve 周日收割时更正，不由本站改。
