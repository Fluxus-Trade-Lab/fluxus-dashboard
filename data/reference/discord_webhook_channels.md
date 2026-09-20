# 数据端 → Discord webhook 设计（T-0921-08，2026-09-21）

起因 Andy 09-21 原话：「我们把数据端的一些内容，通过webhook发到discord上。等于是把我们系统
和流程里的一些事情拆分，然后在discord里呈现出来。」

## 三类消息（已实现，代码在 [`pipeline/discord/data_alerts.py`](../../pipeline/discord/data_alerts.py)）

复用 [`premarket_digest.py`](../../pipeline/discord/premarket_digest.py) 已经验证过的写法：一个
频道一个环境变量，变量没设时打印到 stdout 而不是报错——所以这三个都能在没有真 webhook 的情况下
跑测试、跑 dry-run，`.github/workflows/` 接线前不影响任何人。

| 消息类别 | 出处（文件/字段） | 发送时机 | 对比基准 | 建议 env var |
|---|---|---|---|---|
| **名单变化** | `data/output/shortlist.json` `.seats`（6 席：burning/new_leader/entry/v_reversal/coiling/asset） | 每晚正班写完 shortlist 之后 | `data/history/shortlist_seat_log.csv` 前一个已记录的交易日同一席位 | `DISCORD_SHORTLIST_WEBHOOK` |
| **状态变化** | `data/output/market_light.json` `.<symbol>.light`（red/yellow/green + gear 1–7，默认 symbol=spy） | 每晚正班写完 market_light 之后，颜色变了才发（未变不发，见下方"未做"） | `data/history/run_ledger.jsonl` 最近一条含 `market_light.light` 的记录 | `DISCORD_STATE_WEBHOOK` |
| **闸的告警** | `pipeline/tools/failure_class.classify()` 对某个 `run_id` 的分诊结果（A_infra/B_vendor/C_gate/D_code） | 分诊判完、非 OK 立即发——呼应宪法「24 小时三律」的"出错即报"，不等下一班 | `data/history/run_ledger.jsonl` 该 run 自身的账本记录 | `DISCORD_GATE_WEBHOOK` |

每类都有独立的 `build_*()` 纯函数（输入数据、输出 payload dict，不碰网络）和 `run_*()` 执行函数
（读文件、调 build、发或打印）；14 条测试见
[`pipeline/tests/test_discord_data_alerts.py`](../../pipeline/tests/test_discord_data_alerts.py)，
其中一条专门断言模块源码里**不出现** `discord.com/api/webhooks/` 字面量。

## 待 Andy 定（三件，任务原文列的那三个）

1. **webhook 地址**——他建好频道后把 URL 交给要接线的会话，写进 GitHub Actions secrets（`DISCORD_SHORTLIST_WEBHOOK` 等三个变量名之一），**不进代码仓库任何文件**。
2. **频道/消息类别是否就是这三类，还是要加减**——当前三类是从"名单、状态变化、闸的告警"（他 09-21 原话三个例子）逐字映射出来的最小集，其他候选见下节，都还没做。
3. **可见性**——自己看（内部运维频道）还是会员可见（对外发布，按宪法需要他额外点头，不能默认开）。

## 接线方式（Andy 定了地址/频道/可见性之后）

三个都已经是可独立调用的 CLI：
```
python -m pipeline.discord.data_alerts shortlist [--dry-run]
python -m pipeline.discord.data_alerts state [--symbol spy] [--dry-run]
python -m pipeline.discord.data_alerts gate --run-id <id> [--dry-run]
```
接进 `.github/workflows/daily-data-update.yml` 只需要在正班收尾处加三行调用 + 在 repo secrets 里
填三个 webhook URL；gate 那条需要有 run_id 才能分诊，接在失败分支里（呼应 `failure-triage` skill）。

## 候选但没做的消息类别（留给 Andy 挑，不是本任务范围）

- Regime 四态（`data/output/theme_ladder.json` `.rungs` 的 Leading/Weakening/Improving/Lagging 计数，09-21 刚拆清口径，见 commit `9532b2c7`）——比 market_light 更细，但当天没有"变了才发"的现成对比基准，需要先补一份归档
- Watchlist 新进/退出（`data/output/watchlist.json` `.cross_zone`，59 条候选）——量比 shortlist 大得多，适合做成周汇总而不是每日提醒
- Dashboard 死线告警（JST 08:30 前数据没落地）——这个应该挂在 `failure-triage` skill 里而不是这里，因为它需要主动轮询、不是"某个文件写完了"触发

## 安全边界（对应验收条款）

- 三个 `build_*()` 函数都是纯函数，不读环境变量、不发网络请求——webhook URL 只在 `_post()`/`run_*()` 里通过 `os.environ.get(env_var)` 读取，从未写死。
- `test_no_webhook_url_is_hardcoded_in_the_module` 机器断言这一点，不是靠人眼扫一遍。
