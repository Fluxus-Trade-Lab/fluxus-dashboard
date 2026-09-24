---
name: data-contract
description: data/output 或 data/history 里一个字段/名单要新增、改口径、停发或删除时用——凡任务 type=data_contract、或有人说「这个字段要停发」「新增一个字段要不要登记」「schema_snapshot --check 报了新增/缺失」「这只 ticker 退市了清不清」「这个指标该用什么口径」「细分行业名单/配色要改」，都先读本 skill 再动手，别现场现编流程。
owner: alex
---

# data-contract — 改一个数据契约字段的标准动作

已 `done` 6 次的活（T-0920-04 停发 gear、T-0921-57 登记 top20_industry、T-0921-70/71 清 EATZ、
T-0921-85 财报跳空按族群计数、T-0923-03 MCO 换池+MCSI、T-0923-63 补 ema5/UUP、T-0923-82 瘦身 breadth_panes）。
每次都在同一批坑上摔一次：口径没先查、schema 没先跑、gate 判成 none 结果是 reviewer、
Q2 红绿测试对纯数据改动无解、前端镜像该不该自己同步。这条把六次的答案钉死。

## 什么时候跑
任何一次要**新增、改口径、停发、删除** `data/output/`、`data/history/`、
`pipeline/constants/`（细分行业名单/配色）里的字段或条目。

## 五步

1. **先查口径，别自己造**（CLAUDE.md「先找口径」；METRIC_SOURCES.md 开篇 Andy 原话：
   「很多数据是有专业的衡量的，不需要你去计算去创造，只需要去哪里找」）。
   一次针对性检索（指标名 + definition/calculation）+ 至少一个权威源
   （StockCharts ChartSchool / 交易所官方口径 / 指数编制方法书 / 学术原文）。
   查不到也要在 `data/reference/METRIC_SOURCES.md` 留痕写「查过，无标准」；
   自造的量必须写明偏离了哪个标准、为什么，不得冒充标准读数。
   例：T-0923-03 MCO 池子从 Finviz 全池改标准 NYSE/纳指 100 口径，出处写进 METRIC_SOURCES 第 50/89/91 行。

2. **动手前全仓 `git grep <字段名/ticker名>`，含 `data/reference/` 不要漏**（09-17 事故：删
   `sentiment.json` 只查了代码引用，漏了 `schema_snapshot.json` 基线，09-16 正班被闸挡）。
   删除类任务（清 ticker、停发字段）尤其要连着 `data/output/`、`pipeline/`、`frontend/`、
   `.md` 文档一起搜，确认没有孤儿引用。

3. **改前改后各跑一次 `python3 -m pipeline.tools.schema_snapshot --check`**。
   记住判据（T-0921-57/85/96 反复踩）：**只有 `removed` / `FILE MISSING` 才 `return 1`，
   `added` 只是报告态、exit 0**。新增字段先在 `schema_snapshot.json` 登记、`data/output/` 实际
   还没写出该字段时，会看到 `added` 不是错；反过来如果基线被提前写了字段但产线还没跑出来，
   `--check` 会报 `removed` 且非零退出——这不代表你的改动错了，是基线登记的时机早于产线一次实跑，
   查是不是自己这次改动引入的（`git log` 定位是哪个 commit 写的基线），不是就在裁决里写清楚
   不阻断本次合并（T-0921-85 先例）。改完用 `schema_snapshot --update` 接受新基线。

4. **落三处文档，不是落一处**：
   - `data/reference/DATA_CONTRACTS.md` §七 记一行事实（谁、何时、改了什么、为什么），
     §七只是事实档案不是派活渠道——要别线动手必须带任务号。
   - `data/reference/METRIC_SOURCES.md` 对应行更新或标 🗑（写法照抄 `plus_n`/`gear` 那两行：
     删除原因 + Andy 原话 + 存活期间验证过什么）。
   - 若字段有**前端镜像**：`pipeline/constants/`（`tickers.py`/`colors.py`）改动带出
     `frontend/src/lib/etfGroups.js`、`etfNames.json`、`frontend/public/data/etf_data.json`
     三份快照——ROLE.md 窄口子授权允许你在同一提交里直接同步这三份，不必每次转交 Claire；
     `frontend/` 其余部分（组件、图表渲染）仍归 Claire，只转交不自己碰。

5. **过 gate，Q2 对纯数据改动要用替代证据**：gate 命令现场跑，别信任务文件里写的静态值
   （T-0921-70 教训：写的是 none，实跑是 reviewer）。纯名单删除/停发字段常常挑不出
   red→green 的测试载体（本仓测试目录压根没断言过具体 ticker/字段值）——用三件替代证据顶上：
   ①`schema_snapshot --check` 改动前后的输出对比 ②全量回归不掉绿（`pytest pipeline/tests tests
   --deselect pipeline/tests/test_content_processor.py`）③写清楚被验对象和断言为什么相关
   （别拿一个跟改动面不相交的命令充数，T-0921-71 那次栽过）。**新增字段**类改动则相反——
   Q2 会要求真测试，用现成的离线夹具（如 `fake_yf_download`）给
   `pipeline/tests/test_run_all_end_to_end.py` 补断言，成本低，默认先补，别等复核打回。

## 时机

Dashboard 死线 JST 08:30 前不要动 `data/output/`/`data/history/` 结构性改动，除非本身就是在修
死线故障。字段停发/新增这类非紧急改动排开死线窗口。

## 产出留痕

`DATA_CONTRACTS.md` §七 的那一行事实 + `METRIC_SOURCES.md` 的口径行，是这类任务唯一被
下一次审计/复盘引用的东西——两处都没写＝这次改动等于没发生过。
