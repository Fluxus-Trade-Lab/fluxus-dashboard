# 2026-08-31：一次「手工化解」冲突，把刚接上的闸整段删了，269 行测试没有一条红

**发现**：2026-09-03 夜班（Nighty Zac），在查另一件事（yfinance 缺 08-28）时顺手核
「哪些 `audit_*` 有自动触发点」，撞见 `pipeline/no_downgrade.py` 一个调用点都没有。

**影响期**：2026-08-31 14:03 JST → 2026-09-03（发现时约 **3 天 / 至少 2 个 session**）。
期间 `no_downgrade` 闸在生产里**一次都没执行过**。

---

## 事实（每条都可复现）

| # | 事实 | 怎么验 |
|---|---|---|
| 1 | `4f2fe309` 把闸接进写盘路径，同一个 commit 改了 3 个文件：模块 294 行 + 测试 269 行 + `run_all.py` **+31/−4** | `git show --stat 4f2fe309` |
| 2 | 同日 14:03 的 `8e4a64ef`（message：`merge(B2 手工化解): universe 补 prev_volume …`）把 `run_all.py` 里那 27 行**整段删除** | `git show 8e4a64ef -- pipeline/screeners/run_all.py \| grep '^-'` |
| 3 | 两个 commit 都在 `origin/main` 上，不是分支搁浅 | `git merge-base --is-ancestor 4f2fe309 origin/main` |
| 4 | 模块与它的 269 行测试**原封不动留在仓库里、全绿** | `pytest pipeline/tests/test_no_downgrade.py` |
| 5 | 四种拼法（`no_downgrade` / `check_overwrite` / `FLUXUS_ALLOW_DOWNGRADE` / `NoDowngrade`）在 `pipeline` `.github` `frontend` `scripts` 下、排除自身与测试后，**全部零命中** | 见下方复现块 |

```bash
for pat in no_downgrade check_overwrite FLUXUS_ALLOW_DOWNGRADE NoDowngrade; do
  echo "[$pat]"; grep -rn "$pat" --exclude-dir=.git --exclude-dir=__pycache__ \
    pipeline .github frontend scripts 2>/dev/null \
    | grep -v "pipeline/no_downgrade.py:\|pipeline/tests/test_no_downgrade.py:"
done      # 2026-09-03 跑：四段全空
```

## 它本来防的是什么

Andy 2026-08-31 的裁定（事故档 `2026-08-29_late_run_overwrote_healthy_data.md`）：
**「比数据 —— degrade, do not overwrite」**。
起因 08-27：主排程迟到 **485 分钟**，跑在一个已经健康落地两次的 session 上，
`universe_quality` `ok → degraded`、`bars_missing` 64 → **266**（×4.2）、
`unmeasurable` 75 → **277**、19 个面板里 15 个缩水约 5%，
**三次 run 全报 `success`，没有一道闸出声**。

所以这三天里，那个形状**没有任何东西拦着**。

## 为什么 269 行测试一条都没红（这才是可复用的部分）

> **那 269 行测的是模块，不是接线。它们从头到尾没有问过一句「有人调用它吗」。**

这和本仓已有的两条同族，构成**第三次**：

1. `pitfall_a_test_that_reads_its_own_constant` —— 测试读了它要测的那个常量，永远不会红。
2. 2026-09-02：**1,302 条测试没有任何自动触发点**（`ci_test_gap_2026-09-02/`）——
   测试是对的，没人跑。
3. **本条：闸是对的、测试是对的、没人调用。**

三次的形状是同一个：**我们反复验证「这个东西对不对」，而从不验证「这个东西在不在链条上」。**

⚠️ 特别值得记的一点：**删除发生在一次冲突的手工化解里。**
手工化解 conflict 时，人读的是「这两版哪个对」，
而被删的那段**在冲突的另一边根本不是争议内容**——它只是恰好在同一个 hunk 附近。
`git show` 的 numstat 看着完全正常（+31/−4 变成 −27），**diff 本身没有任何异常信号**。

## 已做（2026-09-03 夜班）

- `run_all.py` **逐字取回** `4f2fe309` 的那 27 行（`diff` 已核 verbatim，非重写）。
  ⚠️ `pipeline/screeners/` 不在夜间组 safe-merge 白名单，**留在分支上等 Andy / DATA ALEX**。
- 新增 `pipeline/tests/test_no_downgrade_is_wired.py`（3 条）：import / 被调用 /
  写盘落在闸的分支里。**阳性对照实测**：挂在 `origin/main` 那版（被摘掉的）上 **3/3 红**，恢复后 3/3 绿。
  ⚠️ 它是**结构断言不是行为断言**（`pitfall_read_the_source_took_it_for_the_behavior`）——
  它证明调用点写在源码里，不证明夜里真的跑了。这里够用，因为消失的正是源码里那一行。

## 建议的机制（不是我能定的，写给周检）

**任何「闸/守卫」类模块，测试必须包含一条接线断言。**
判据很好写：这个模块的入口函数，在生产代码里有没有调用点。
它比行为测试便宜得多，而这三天的空窗，一条 `assert` 就能堵上。

— Nighty Zac，2026-09-03
