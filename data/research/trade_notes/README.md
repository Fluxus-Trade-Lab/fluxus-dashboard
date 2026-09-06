# trade_notes/ — 每笔交易的思考（Andy 的话，机器只搬运）

写入规则见 `.claude/skills/trade-note/SKILL.md`。按开仓月归档（YYYY-MM.md），append-only。
消费者：weekly-review（选「本周最好的一笔/错过的机会」时读此处）。

落点说明：对账表原案 `data/portfolio/trade_notes/` 不可用——`data/portfolio/` 被 .gitignore
整目录排除（「Live position data must never enter the repo」），笔记落那儿永远进不了 main。
本目录在 safe-merge 白名单（`data/research/**`）内，各会话可代录直推。五字段不含仓位大小
与金额，与该隐私设计不冲突；⚠️ 代录时也**不许**顺手把仓位 %、股数、金额写进「我看到什么」。
