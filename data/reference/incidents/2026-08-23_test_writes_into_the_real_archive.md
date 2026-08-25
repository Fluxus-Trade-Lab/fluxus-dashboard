# 跑一次测试就把真归档的基线行改掉

**发现**：2026-08-23 夜间组（Zac），在 `auto/night-20260823-4b6905` 上跑全套测试后 `git diff` 有一个我没碰过的文件。
**状态**：**未造成损失**——`origin/main` 上的文件是干净的。但主工作树 `/Users/taolezhu/Documents/AI-Trading-System` 此刻这个文件就是脏的（本次会话开始时的 git status 里已经带着它）。雷已经装好，还没踩。

## 症状

```
$ python3 -m pytest pipeline/tests/test_quality.py -q
39 passed in 0.06s
$ git status --porcelain data/history
 M data/history/quality/breadth_last.csv
```

`data/history/quality/breadth_last.csv` 的 2026-08-19 行：

| | 前 20 列 |
|---|---|
| origin/main（真基线） | `2026-08-19,0.0,0.0,1.0,1.0,1.0,0.0,0.0,0.0,0.0,0.0,0.0,1.0,1.0,0.0,0.0,0.0,0.0,0.0,0.0,1.0` |
| 跑完测试后 | `2026-08-19,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0` |

这一行是**空值率基线**。被改成几乎全 1.0 = 「这些字段那天 100% 是空的」。基线越高，`check_source` 后面越不容易判 degraded——**污染的方向是让守卫变迟钝**，不是让它吵。

## 根因（一个默认参数）

`pipeline/quality.py:447`

```python
def check_site(output_dir: Path, date: str,
               history_dir: Path = QUALITY_DIR) -> Dict[str, Any]:
```

`history_dir` 默认是**真仓库**的 `data/history/quality/`。测试把 `output_dir` 换成了 `tmp_path`，以为整件事就沙箱了：

`pipeline/tests/test_quality.py:302` `TestRequiredBlocks::test_missing_block_grades_severe`

```python
rep = check_site(tmp_path, "2026-08-19")     # output_dir 沙箱了，history_dir 没有
```

于是 `check_site` → `check_source(..., history_dir)` 拿着真路径把基线写了回去。全套 746 个测试里**只有这一个**测试漏了这个参数（逐个测试二分确认）。

## 为什么之前没人发现

三件事同时成立才藏得住：

1. 测试**通过**。它断言的是返回值（`missing_blocks` / `status == "severe"`），返回值是对的；副作用不在断言里。
2. 症状是 `git status` 里多一个文件，而这棵树平时本来就有一堆改动（数据文件每晚变）。多一行 ` M data/history/...` 看上去和昨晚 cron 的产物没区别。
3. 它改的是**归档的一行**，不是 output。归档审计（`audit_archives`）查的是日期合法/无重复键/行数区间——**改一行的数值不违反任何一条不变量**。I3 只盯 breadth_archive 的 spx_close，不看 quality 基线。

和 [2026-08-19 breadth blackout](2026-08-19_breadth_blackout.md) 同族：那次是「状态说 ok，没人读它填的数」，这次是「测试说 pass，没人看它留下的脚印」。**都是判定本身没被验证。**

## 建议的修法（归数据端，夜间组没动）

一行：

```python
rep = check_site(tmp_path, "2026-08-19", history_dir=tmp_path)
```

但这只堵这一个洞。**下一个忘了写 `history_dir=` 的人会再踩一次**，所以建议同时加一道结构性的：

- 首选：一个 `conftest.py` 的 autouse fixture，测试期间把 `pipeline.quality.QUALITY_DIR` 指到 tmp，任何忘记传参的调用自动落进沙箱；
- 或者：CI 在 `pytest` 之后跑 `git diff --exit-code data/history data/output`，**测试跑完仓库必须还是干净的**——这条能一次性抓住所有「测试写进真树」的形态，不止 quality 这一处。

第二条我更推荐：它不是修一个 bug，是让这一类 bug 以后自己喊出来。

## 结案（2026-08-25，数据端）

诊断档的两条建议**都归数据端，我 08-23 cherry-pick 了这份档案却没做**——所以 08-25 原样复发第三次。
夜间组当晚已修调用行 + 加 AST 守卫（`0cfc2989`）；本轮补上结构性的两道，并**先验证能报阳性**：

| 对照 | 做法 | 结果 |
|---|---|---|
| ① 无守卫 | 干净基线 → 跑 `test_quality.py` | **污染发生**，39 passed 零报警（正是本事故的形状）|
| ② 会话级守卫 | 同上 | **报阳性**：teardown 失败并指名 `data/history/quality/breadth_last.csv` |
| ③ 沙箱 | 同上（带 bug 的调用行仍在） | **源头挡住**，跑完仓库干净 |

- `pipeline/tests/conftest.py`：autouse 沙箱把真实路径默认值指向 tmp + 会话级「跑完 `data/history`/`data/output` 必须干净」。
- ⚠️ **沙箱第一版无效，这本身是个教训**：`history_dir: Path = QUALITY_DIR` 的默认值在**函数定义时**就绑定了，
  事后 monkeypatch 模块变量改不动它。已把 `check_site`/`check_source` 改成 `Optional[Path] = None` **调用时解析**——
  「可被沙箱重定向」现在是这两个函数的性质，不是调用方的自觉。
- ⚠️ 另一个发现：**`pytest` 在 CI 里根本不跑**（六个 workflow 无一执行测试套件）。
  所以诊断档推荐的第二道（CI 跑完查仓库干净）目前**没有宿主**——会话级守卫是它在本地的替身。
  要不要建测试 workflow 归 Andy/OPS 定：现有 4 个失败（本机缺 `anthropic` 包）会让 main 常红，得先处理。

## 教训

**「测试通过」说的是断言，不是环境。**沙箱要沙箱到*每一个*出口——一个函数有两个路径参数，只换其中一个，另一个就是敞开的。判断一个测试是否隔离，不能读它的 `tmp_path` 有几处，要跑完看 `git status`。
