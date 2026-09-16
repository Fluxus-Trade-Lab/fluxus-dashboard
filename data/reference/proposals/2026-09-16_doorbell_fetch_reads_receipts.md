# 提案：取门铃命令改为只列没人取的（宪法「门铃自取制」第 29 行）

**状态**：待 Andy 批。批之前这不是规矩，宪法第 29 行照旧有效。
**提出**：OPS Fable，2026-09-16。起因是 INBOX 门铃（X 日调研主班 09-12 报，Steve 线 → OPS）和 Andy 09-16 看到的「OPS 名下压着 9 条」。

## 问题

宪法第 29 行让每条线开工跑：

    git show origin/main:data/research/night_reports/INBOX.md | grep "🔔.*→ *<自己线名>.*pending"

门铃行是 append-only，办完以后仍然写着 `pending`，回执写在它下面的 `↳ ✅ … 已取` 行里。这条 grep 只看门铃那一行，所以办完的和没办的一起返回：

- 09-12，X 日调研主班当天命中 4 条，多数已经办完。
- 09-16，每日页用 grep 数出「OPS 滞留 9 条」，其中 6 条早有回执，真没取的是 4 条。

## 提议

第 29 行的命令改为：

    python3 -m pipeline.tools.doorbells --to <自己线名>

工具（`pipeline/tools/doorbells.py`，`e57f134d`，有测试）只列没人取的门铃：行下有 `↳ ✅` 就算已办；只签了别的线名字的 ✅ 不算（09-16 Joe 的一条注脚落在 OPS 门铃下）。门铃的写法、回执的写法都不变。

## 为什么要 Andy 批

这是全联邦共用的一行，写在宪法里；按宪法「改宪法的唯一合法路径」，引不出 Andy 原话就不能直接改。批了以后 OPS 把 9 份本机任务书的取铃步一起换成这条命令（现在只有 Zac、Joe 两份加了「行下有 ✅ 就跳过」的提醒）。

## 不批的代价

每条线每班多读几条已办的门铃；只要读的人看行下回执，就不会重复做。每日页和周检已经改用工具，Andy 看到的滞留数不受影响。

## 裁决

**已批（2026-09-16）**，Andy 原话「批了，改吧」（看完图示页 https://claude.ai/artifact/Foz6cAKJKgbFPZk7eyoi3m 后）。宪法第 29 行已换；为了让停在旧分支上的本机任务也跑得到当前工具，命令用 `git show origin/main:pipeline/tools/doorbells.py | python3 -` 的形式，工具去掉了对仓库模块的依赖。9 份本机任务书的取铃步同批更换。
