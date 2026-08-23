# 夜间组收件箱（append-only；窗口外递活儿写这里，Zac 每晚开工先读）

## 🔗 收藏夹（Andy 扔链接处；任何会话代录，Zac 每晚整理）

> 格式：`- [日期] <链接> ——（Andy 的一句话，可空）`。Zac 处理后移进 `data/research/collection.md` 并附判定。

- [08-23] https://www.youtube.com/watch?v=1k3KRbktibQ ——（Andy）reversal setup，我们图书馆和课程里没有详细记录和了解的

## 等 Zac 下次窗口处理

- [08-24 Andy·本窗口首要] **Stockbee 网站学习整理**（他 00:05 在聊天里点的名，本轮优先于其他积压）。要的是三样：**他的思维方式** / **他的数据** / **他的交易细节**。点名三个题目：**EP（Episodic Pivot）**、**Momentum Burst**、**Anticipation Trade**。
  - **别从零开始** —— 仓库里已有这三条的实现，学习成果要落在「和我们已建的对不对得上」而不是复述他：
    - `pipeline/tools/delayed_ep_scan.py`（EP，每晚归档 `delayed_ep_log.csv`，`--review` 复盘一直没跑）
    - `pipeline/tools/anticipation_scan.py`（Anticipation）
    - `pipeline/screeners/stockbee_ratio.py` + `test_stockbee_ratio.py`（4% 双计；契约 08-23 记过「main 上两个 bug 都还活着，归档确被永久截在 5 行」）
    - `pipeline/screeners/gainers_4pct.py`、`breadth_metrics.py`（他的 breadth 口径）
    - 已证伪别重测：`project_b4_gates_null`（两道闸分得开 p=0.0022，但过闸中位仍跑输 SPY；「第一波」三种叠加没抬中位）
  - **交付形态**：`data/research/stockbee_2026-08/` —— ①`method.md` 把他的规则写成**可执行参数**（阈值/窗口/入场退出/持仓时间/加减仓），每条标他原文出处链接；②`diff.md` 逐条对我们现有实现的**逐格对照**（照 `oratnek_diff` 那个体例：一致 / 不一致 / 我们没有 / 他没有）；③`open_questions.md` 只能前瞻验的项。
  - **版权闸**：写成规则和参数的**综合**，不做原文搬运；引用每处 ≤15 字加出处链接。他的博客是公开站，不碰任何登录墙。
  - **立项三件套**（CLAUDE.md 要求）：①发布物＝素材箱至少一行（他的口径 vs 我们归档的实测差异，或一个 NULL 结果）+ `diff.md` 本身可直接改成一篇 teardown；②截止日＝**2026-08-30（周日）**；③到期规则＝到期未出 `diff.md` 就降级：只留 `method.md` 参数表，其余进停车场。
  - 体例参考：`Fluxus_Receipts/marketpulse_teardown.md`、`data/research/oratnek_diff/`

- [08-23] 收藏夹那条 YouTube reversal setup 链接（见上）——摘要+判定+入 `data/research/collection.md`

## 已裁决（读过打 ✅）

- [08-23 OPS] 你问「四个全按还是转交」：**都不用**。你是无人值守会话，send_message 对你本来就是禁用的，ListAgents 那四个匿名名字别用（送达≠送对）。你把 audit_ledger 写进 §七 的那一刻投递就完成了，门铃 OPS 当天 17:1x 已代按（DATA ALEX 会话已收到指名消息）。新通讯录规矩已进根 CLAUDE.md：以后要按的门铃列在晨报「门铃待按」一节即可。

- [08-23 OPS·Andy 拍板] 你 08-23 晨报的三件事：
  1. **脏基线已清**——`breadth_last.csv` 经核实确如你诊断（仅 08-19 行被改成近全 1.0），OPS 已 `git checkout --` 恢复，主树干净。测试污染生产基线的病根（test_quality 写实文件）已由你修在 `auto/night-20260823-4b6905`，等合并。
  2. **audit_ledger 接 CI 不归你做**——已写进 DATA_CONTRACTS §七 转交 DATA ALEX（workflow 是数据端边界）。你不用动。
  3. **§2.5 预览稿恢复执行**——NOW.md 停做清单约束的是 **Andy 的时间**，不是 AI 的自动任务；你的任务书优先。今晚起照常出预览稿。规矩已写进根 CLAUDE.md。
