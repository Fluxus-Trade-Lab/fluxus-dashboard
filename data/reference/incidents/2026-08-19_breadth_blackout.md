# 事故复盘 · 2026-08-19 Breadth 全黑（严重）

*Andy 2026-08-20："再次分析检查事故背后原因，作为严重事故做成 case study，以防以后这样的事情再次发生。"*
*无责复盘（blameless）：改动全部出自数据端 Claude；分析对事不对人，但事实全名记录。*

## 一、影响

正式 cron（08-19 21:52 UTC，commit d2337e8）产出的 `breadth.json` 丢失 `regime` / `state_board` / `verdict` / `conditions` 四个顶层块，`market_health.json` stale:true。**前端 Breadth 页的 Regime Band、状态板、裁决、Time Machine 全部空白**，从 08-20 06:52 JST 持续到当日午后修复重建（约 6–7 小时用户可见）。同夜 `delayed_ep_log` 又静默写 0 行（独立问题，修复在 `auto/night-20260819` 分支待 merge）。

## 二、时间线（JST）

| 时刻 | 事件 |
|---|---|
| 08-19 19:23 | 760d7ca 提交：给 run_all 接 run_ledger。其中一处编辑把 `ledger.note` 用 `if breadth_result is not None:` 插在 breadth `try/except` 与 **`else:`（富集全在里面）** 之间 |
| 19:24 | 本地验证：`ast.parse` 语法通过、715 个测试全绿 → 推 main |
| 08-20 06:52 | 正式 cron 用 760d7ca 跑：`Saved breadth.json`（无四块）；**schema 巡检逐行打印了 "breadth.json top: removed [conditions, regime, state_board, verdict]" 然后照样 commit**（当时设计为只报不拦）；audit_archives 0 违规（归档确实没坏）；run_ledger 记下 `breadth: ok, regime_score: None`（**证据在案，无人读**）；site_quality: ok（不检查块级完整性）；Discord 报"成功" |
| 07:20 | 晨检定时任务发现四块缺失，定位到 run_all.py:551，追加到 todo_cron_check |
| ~12:00 | Andy 转发晨检结论 |
| 12:10–12:30 | 确认机制 → 修复（else 绑回 try + AST 结构测试 + schema removals 改为致命）→ 894fccc 推 main → 23:10 ET 窗口内 dispatch 重建 |

## 三、根因链（五个为什么）

1. **直接原因**：Python 的 `try/except/else` 里，在 `except` 块和 `else:` 之间插入任何 `if` 语句，`else:` 会**静默重绑**到那个 `if`。语法合法，语义反转：富集从"成功才跑"变成"失败才跑"（而失败路径上 `run_signals(None,…)` 必抛，等于永不跑）。
2. **为什么会插在那**：编辑方式是**文本替换**（锚定 `breadth_result = None` 后追加），编辑者（我）的心智模型里下一段是普通顺序代码，没有向下多看一行确认 `else:` 挂在谁身上。`try/else` 在整个 run_all 里只有这一处，模式罕见 = 心智模型里不存在。
3. **为什么测试没拦**：717 个测试**没有一个执行 `run_all.main()`**。它是 900 行的编排器，所有失败域用 try/except 打包，单元测试全测被它调用的纯函数。编排层的控制流 = 测试盲区。
4. **为什么闸门没拦**：当晚每道闸都按设计工作了——但没有一道的**职责**覆盖"输出 JSON 丢整块"：audit_archives 只看归档（I1–I6），quality.py 只看列缺失率，site_quality 只看文件级新鲜度，**schema 巡检看到了却设计成只报不拦**（我当天下午定的设计，理由"新增列是常态"——没有区分新增与删除的不对称性：新增=演进，删除=断裂）。
5. **为什么直上产线**：cron 即产线，没有 staging；改动 19:23 推 main，第一次真实执行就是 06:52 的正式 cron。**编排器的改动没有任何"上线前跑一遍"的环节。**

## 四、这不是孤例——24 小时内第四次同型事故

| 事故 | 表面原因 | 共同形状 |
|---|---|---|
| 08-19 stash 收走前端未提交文件 | 共享树上 git stash | 对**共享状态**动手，只验证了自己关心的那一半 |
| 08-19 盘前 dispatch 覆盖 08-18 归档 | 手动触发没查 ET 时钟 | 心智模型（"重跑=安全"）替代了验证步骤 |
| 08-19/08-18 delayed_ep 静默 0 行 | 整批 429 被当"无候选" | "没报错"被当成"没问题" |
| **本次 breadth 全黑** | else 静默重绑 | 语法级验证（parse+单测绿）替代了行为级验证 |

**共同根因：验证的范围 = 我改动时想到的范围，而不是改动实际影响的范围。**（memory 里已有同名教训：`审计范围 = 我记得的地方`、`grep 干净 ≠ 代码干净`——这次是它的控制流版本。）

## 五、已落地的防线（对应根因逐条）

| 根因 | 防线 | 位置 |
|---|---|---|
| else 重绑 | **AST 结构测试**：run_breadth_metrics 的 try 必须有非空 orelse 且 run_signals 在其中（把 bug 形状注回去验证过测试抓得住） | `pipeline/tests/test_run_all_breadth_structure.py` |
| 巡检只报不拦 | **schema removals = exit 1 = 不 commit**；新增仍只报。故意删列 = 同一 commit 里 `--update` 快照 | `schema_snapshot.py` + daily workflow |
| 证据在案无人读 | ledger 的 breadth note 移到富集之后，带 `enriched` 四块清单；晨检任务每天读 ledger 末行 | run_all + 晨检 SKILL |
| cron 即产线 | 已有：审计违规不 commit = plan B；本次新增：removals 也不 commit | workflows |

## 六、行为规则（写给未来的每一次编辑）

1. **改编排器（run_all 及一切 try/except/else/finally 附近）：文本替换后必须把改动点前后各 20 行重读一遍**，专门回答"每个 else/except/finally 现在挂在谁身上"。语法通过不算数。
2. **验证的最小单位是行为不是语法**：改 run_all 后，除了 pytest，跑 `python3 -m pipeline.tools.schema_snapshot --check` 对最近一份真实输出（改动若影响输出形状，本地先能看见）。
3. **闸门的默认值是拦，例外才是报**：新建任何检查时，先问"它发现问题时敢不敢让 job 失败"；不敢 = 说明检查的信噪比还不够，修检查而不是降级为打印。
4. **"成功"必须携带证据**：任何 `status: ok` 旁边必须有一个非空的实质字段（如 regime_score、enriched 清单）；ok + 空证据 = 报警形状（晨检已加）。
5. 高危清单（碰之前默念）：共享树、归档、编排器控制流、时钟/日期、批量下载的空返回。

## 七、开放项

- run_all.main() 至今没有端到端 smoke（小夹具宇宙跑通全链、断言输出块齐全）——中期最有价值的一道防线，量级半天，待排。
- site_quality (`check_site`) 加"关键文件必备块"清单（breadth: regime/state_board/verdict/conditions；watchlist: zones/cross_zone…），双保险。
- `delayed_ep` 修复在 `auto/night-20260819` 分支，待 merge。
