# 夜间组收件箱（append-only；窗口外递活儿写这里，Zac 每晚开工先读）

## 🔗 收藏夹（Andy 扔链接处；任何会话代录，Zac 每晚整理）

> 格式：`- [日期] <链接> ——（Andy 的一句话，可空）`。Zac 处理后移进 `data/research/collection.md` 并附判定。

- [08-23] https://www.youtube.com/watch?v=1k3KRbktibQ ——（Andy）reversal setup，我们图书馆和课程里没有详细记录和了解的

## 等 Zac 下次窗口处理

（暂无）

## 已裁决（读过打 ✅）

- [08-23 OPS] 你问「四个全按还是转交」：**都不用**。你是无人值守会话，send_message 对你本来就是禁用的，ListAgents 那四个匿名名字别用（送达≠送对）。你把 audit_ledger 写进 §七 的那一刻投递就完成了，门铃 OPS 当天 17:1x 已代按（DATA ALEX 会话已收到指名消息）。新通讯录规矩已进根 CLAUDE.md：以后要按的门铃列在晨报「门铃待按」一节即可。

- [08-23 OPS·Andy 拍板] 你 08-23 晨报的三件事：
  1. **脏基线已清**——`breadth_last.csv` 经核实确如你诊断（仅 08-19 行被改成近全 1.0），OPS 已 `git checkout --` 恢复，主树干净。测试污染生产基线的病根（test_quality 写实文件）已由你修在 `auto/night-20260823-4b6905`，等合并。
  2. **audit_ledger 接 CI 不归你做**——已写进 DATA_CONTRACTS §七 转交 DATA ALEX（workflow 是数据端边界）。你不用动。
  3. **§2.5 预览稿恢复执行**——NOW.md 停做清单约束的是 **Andy 的时间**，不是 AI 的自动任务；你的任务书优先。今晚起照常出预览稿。规矩已写进根 CLAUDE.md。
