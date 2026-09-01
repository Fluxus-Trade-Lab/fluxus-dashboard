# 1,302 条测试没有任何自动触发点 —— 交接包（不是请求）

**Nighty Zac，2026-09-02。** `.github/workflows/` 不在夜间组边界，所以这里是**整包交出去**，
不是「请 Andy 决定要不要做」。接的人可以直接 copy 下面的 YAML。

---

## 一、事实（可复现）

```bash
ls .github/workflows/            # 6 个：content-reminder, daily-content-threads,
                                 # daily-data-update, gas-probe, premarket-digest, weekly-data-audit
grep -rniE "pytest|unittest|make test|tox" .github/workflows/     # 唯一命中是 "diag(nose)d" 这个词
ls .pre-commit-config.yaml Makefile .husky                        # 三个都不存在
```

**没有任何一处自动执行 `pipeline/tests`。** 这 1,302 条测试全靠会话自己想起来跑。

`DATA_RELIABILITY.md` §五.4 写的「改任何归档的写入者，先跑 `audit_archives`，再跑 `pytest`」
**是人的纪律，不是闸**——而本仓的整套方法论建立在「闸比纪律可靠」上。

**这条同时卡住了 §六.4**：那条要求「**CI 在 pytest 之后**加一句 `git diff --exit-code`」，
而 pytest 这一步不存在，所以那句话没有地方可加。

## 二、为什么它比看上去重要

我们这半个月造的每一道闸（`audit_archives` / `audit_ledger` / `audit_calendar_gaps` /
`audit_universe_shape` / `audit_regression_gate` / 变异普查）**都活在这套测试里**。
它们的价值 = 「有人跑了测试」× 「测试确实钉住了判据」。
第二项我们量了整整两晚（变异杀死率），**第一项一直是 100% 靠自觉，而且从没被量过。**

09-01 我自己就撞过这个的近亲：整晚的改动躺在未提交区，全绿的是工作区不是 main。
**「绿了」和「有人让它变绿过」是两件事。**

## 三、可直接合的 YAML（接的人 copy 即可）

`.github/workflows/tests.yml`：

```yaml
name: tests

on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

jobs:
  pytest:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: pip
      - run: pip install -r requirements.txt
      - name: pytest
        run: python -m pytest pipeline/tests -q --deselect pipeline/tests/test_content_processor.py
      - name: 跑完仓库必须还是干净的（DATA_RELIABILITY §六.4）
        run: git diff --exit-code -- data/history data/output
```

**最后那一步就是 §六.4 要的那句**，它现在终于有地方可放。

## 四、三个必须一起交出去的取舍（别让接的人自己踩）

1. **`--deselect test_content_processor.py` 是照抄本仓现行惯例**（夜间组任务书、多份晨报都这么跑）。
   我**没有查过它为什么被排除**——接的人若要收紧，先查这一条，别默认它可以直接去掉。
2. **不要挂在 `schedule` 上。** 它该由 push/PR 触发。挂定时=在没有变更的时候烧配额，
   而且会和 21:30 UTC 的数据 cron 抢跑。
3. **`git diff --exit-code` 这一步会在数据 cron 的 commit 上误报吗——不会**，
   因为它跑在 checkout 出来的干净树上，只有**测试自己写脏**才会红。
   这正是 08-23 那次事故（`test_quality` 写进真归档）会被它抓到的形状。
   ⚠️ 但**上线第一次可能就是红的**：先在 PR 上跑一次看结果，别直接推 main 分支保护。

## 五、成本

GitHub Actions：ubuntu-latest，全套本机实测 **212 秒**（1,302 passed / 1 skipped，2026-09-02）。
按 push + PR 触发，量级是每天几次 × 4 分钟。**我不花钱，这个数交给接的人判。**

## 六、归属

`.github/workflows/` 不属夜间组。**建议数据端（DATA ALEX）或 OPS 认领**——
两条线都已经在这个目录里落过东西。晨报「门铃待按」有对应行。
