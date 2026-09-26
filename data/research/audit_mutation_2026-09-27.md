# 全库最弱那道闸的两次复算 · 2026-09-27（T-0927-08 · linda）

三件事，一条线索：**账上的读数会过期，而过期的读数会让你选错今晚的题。**

09-26 的晨报把三个数留给今晚，写着「先复算再动手」。复算的结果是
一个对、一个分子分母双错、一个真洞清零。

## 一、`audit_ci_test_coverage`：09-26 留账的三个真洞，补掉

09-26 那份把 11 个存活点逐个判过，其中 4 个判为「真洞，没补——时间盒到了」。
今晨补完，**154/165 → 158/165（93% → 96%）**。

三条测试，每条杀一个变异体，**每一个都先在变异体上跑过红再写下来**：

| 变异 | 杀它的那条测试 | 它坏掉的是什么 |
|---|---|---|
| L506 `And -> Or`<br>L506 `In -> NotIn` | `test_a_skipif_that_asks_the_machine_nothing_is_not_history_gated` | 两个一起。`skipif` 里没有向机器提问时 `history_gated` 必须是 `False` |
| L501 `GtE -> Gt` | `test_a_decorator_chain_that_ends_at_mark_is_read_without_crashing` | `@pytest.mark` 后面什么都不跟时，变异体在下一行 IndexError |
| L699 `3 -> 4` | `test_render_accounts_for_the_fourth_test_when_the_bucket_is_exactly_four` | 恰好四条是 `> 3` 与 `> 4` 唯一分家的宽度 |

### ⚠️ 已有的那条正向测试，从哪个方向都看不见这两个变异

`test_a_skipif_on_repository_history_is_flagged` 早就在，用的是
`skipif(not _has("abc"), reason="shallow checkout")`。它对 `In -> NotIn`
**两边都绿**——`any(h not in seg)` 只在 seg 同时含上**全部** hint 时才为假，
而真实条件永远不会同时含上 `cat-file`、`shallow`、`rev-parse`、`which(`。

> **一条只从「该报阳」那一侧写的测试，对「不该报阳」那一侧是瞎的。**
> 而这里不该报阳才是贵的那个方向：`skipif(False)` 被记成 `history_gated`，
> 就会被「浅 checkout 跳过了」写销账，从此不是任何人的问题。

### 剩 7 个，全是 09-26 已判过的

等价（L345 `Gt->GtE` / L345 `2->3` / L346 `2->3` / L636 `1->2`）·
帮助文本（L712）· 造不出真实 YAML 让两者分家（L390 / L400）。
**真洞清零**——这道闸（全库最大，723 行）现在没有一个未经检视的存活点。

## 二、`audit_universe_shape`：31/49 = 63%，账上那个数是对的

09-02 之后没再动过，复算逐位一致。18 个存活点仍未读（09-02 就写着「没人逐条读过」）。

## 三、`audit_calendar_gaps`：账上 61%，实际 63%，而站点数是 99 不是 92

| | 账上（09-02 读数） | 今晨复算 |
|---|---|---|
| 杀死率 | 61% | **62/99 = 63%** |
| 站点数 | 92 | **99** |

**分子分母都过期了**。这是三晚连着第三次转抄的读数不成立：
09-24 是数字错（53% 实为 66%/57%）· 09-26 是站点数错（162 实为 174）· 今晨是两个都错。
量一次五分钟，选错一晚的题贵得多。

### 37 个存活点里 19 个长在两个从没有测试的函数上

`read_archive_dates()` 和 `main()` 各一条测试都没有——
整条 `--archive` 入口路径，加上退出码。

⭐ **L423 `return 0 if out["ok"] else 1` 是同形第四次**
（`audit_archives` / `audit_ledger` / `audit_ci_test_coverage` 各活过一次，09-25、09-26 分别补掉）。
它坏的是安静那条路：每个干净的夜晚 CI 都 exit 1，仓库没毛病，
而**人学会的修法是不再看这个检查**。三次律早就触发过，这次钉住，不再记账了事。

### 三批测试，三个读数

| | 测试数 | 杀死率 |
|---|---|---|
| 开工（origin/main） | 50 | 62/99 = **63%** |
| + `read_archive_dates` 10 条（13 例） | 63 | 80/99 = **81%** |
| + `main()` 11 条 | 74 | （同上批一并量） |
| + `fetch()` 6 条 | **80** | 86/99 = **87%** |

#### `read_archive_dates` 那六个，坏法都是静默

- `column or next(...)` 的 `or` → `and`：不给 `--date-col` 时 col 变 `None`，
  于是一份**有** `as_of` 列的归档报「cannot find a date column」
- `c in rows[0]` → `not in`：第一个候选永远胜出，col 变成文件里没有的列，
  `r.get(col)` 每行都是 None，**整份归档静默读成空集** → D1 对我们写过的每一场都报红
- `rows[0]` → `rows[1]`：单行归档 IndexError
- `col is None` → `is not None`：每份健康归档都 SystemExit
- `if not rows` 掉 `not`：健康的返回空、空的崩在 `rows[0]`，两个方向都错
- `[:10]` → `[:11]`：多留一个 `T`，所有日期对不上日历网格

#### `main()` 十一条钉住的

退出码两个方向 · 空 feed 的早退与它的码 · `window` 打印的 start/end 次序
（**两个分支各有一份拷贝**，所以要两条测试）· `--days` 默认 30 ·
`--grace-sessions` 默认 1（默认 2 会吞掉一个真的漏写之夜）·
`fetch` 多取 3 天（C2 要看见收盘后的 bar 就靠它）·
C5 那句「check C5 before calling these survivors」只在 universal 缺口下印
（翻成 `or` 后每个零星缺口都挂一句没有幸存者可查的提示）。

#### `fetch()`：classify_bar 全钉住，接住它判词的那三行却是自由的

`classify_bar` 09-02 被抬出 `fetch()` 就是为了能被测到，它现在一个存活点都没有。
**但 L343 / L345 任一翻转，每个 placeholder 都进 `good`、真会话被整条丢掉** ——
2026-09-01 把 FBRX 的 `O=H=L=C / Volume=0` 读成「唯一还有数据的票」那个错，
在修好它的那一层**上面一层**原样重演。

> `fetch` 不需要网络，它需要一个 frame。
> `monkeypatch.setitem(sys.modules, "yfinance", 桩)` + 真 pandas DataFrame
> （单票平列 / 多票 `group_by` 分组列）。**桩给的是厂商的形状，不是厂商。**

杀掉 6 个：good/bad 路由两个 · 单票/多票那道叉两个
（`>= 1` 会让单票去查一个名叫 `"A"` 的列，KeyError 被 `continue` 吞掉，
`main` 然后把它报成「feed returned nothing at all」——**一个谎，两层楼**）·
`end` 多取一天（yfinance 的 `end` 是开区间）· `auto_adjust=False`。

`auto_adjust` 那条在测试正文里**明写了是 config pin，不是行为断言**。
留它的理由：`auto_adjust=True` 会按拆股/分红重写 OHLC，而 FBRX 判据是
四条腿的精确相等，调整后的价可能不再相等——**这面旗一翻，placeholder 检测是悄悄变弱，不是坏掉。**

### 剩 13 个，逐条归类

| 类 | 个数 | 位置 | 判 |
|---|---|---|---|
| `reconcile` 的算术 | **4** | L203 `LtE->Lt` · L250 `0->1` · L257 `1->2` · L258 `GtE->Gt` | **真洞，可达，没补**——下轮第一件 |
| 格式与精度 | 6 | L162 · L165 · L265 · L276 · L281 · L422 | `round(_,4)` / `*100` / json `indent` —— 不改判定 |
| 纯配置 | 2 | L330 `progress=False` · L331 `threads=True` | 进度条与线程数，不改判定 |
| **按构造不可达** | 1 | L159 `else 0.0` | 见下 |

#### L159 为什么不可达（而它为什么不该删）

```python
missing = [t for t in tickers if d not in present[t]]
if not missing:
    continue
frac = len(missing) / n if n else 0.0
```

到得了第 3 行就意味着 `missing` 非空；`missing ⊆ tickers`；`n = len(tickers)`。
所以 **`n ≥ 1`，`else 0.0` 永远取不到**。

它是一道除零守卫。09-26 我学到的是「存活点密集挤在一个小函数上，先当死代码查」——
那条判据对的是**假装自己活着的死函数**（`_marker_expr`，全仓零调用、九个存活点）。
这里是一个单 token 的兜底，**为了刷杀死率去删一道除零守卫是错的交易**，留着并记账。

## 四、可复跑

```bash
python3 -m pipeline.tools.audit_mutation_sweep --module audit_calendar_gaps
python3 -m pipeline.tools.audit_mutation_sweep --module audit_universe_shape
# 最大那道闸要切片（每段约 5 分钟，前台 10 分钟上限内）
python3 -m pipeline.tools.audit_mutation_sweep --module audit_ci_test_coverage \
        --index-from 0 --index-to 42        # 其余三段 42:84 / 84:126 / 126:165
```

改了被测源码，索引就不再对齐；`total_sites` 印在每份报告里，就是防止跨改动合并切片的那道闸。
**今晨只改测试、没改源码**，所以 165 与 99 这两个站点数在本轮内稳定。

## 五、读数汇总

| 闸 | 09-26 账上 | 今晨复算 | 今晨收尾 | 测试数 |
|---|---|---|---|---|
| `audit_ci_test_coverage` | 154/165 = 93% | — | **158/165 = 96%** | 98 → 101 |
| `audit_calendar_gaps` | 61%（92 站点） | 62/99 = 63% | **86/99 = 87%** | 50 → 80 |
| `audit_universe_shape` | 63% | **31/49 = 63%** ✅ | 未动 | 未动 |

两个测试根全量：**3681 passed / 1 skipped / 12 deselected**（6 分 32 秒）。
本轮新增 **33 个用例 / 30 个测试函数**。
