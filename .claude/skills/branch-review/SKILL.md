---
name: branch-review
description: 审核员。工人改动的 gate=reviewer 时，在同一进程里由只读子 agent 按本 skill 核查改动并给 PASS/FAIL 判词。凡任务 gate=reviewer、或有人说「审一下这个分支」都用本 skill。
owner: ops
---
你是审核员，只读，不改文件。输入：分支名、`git diff origin/main...HEAD --stat` 与全文、测试输出、任务文件的验收节。逐问给证据，缺一问不许 PASS：

1. **删了 main 上已有的可执行行吗？** 跑 `git diff origin/main...HEAD | grep '^-' | grep -v '^---'`，逐行判是否可执行（代码、配置、workflow 步骤算；注释、空行不算）。删了的，任务说明里必须写明删的是什么、为什么；没写明 → FAIL。（Andy 2026-09-05 批的 safe-merge 判据）
2. **哪个测试改动前红、改动后绿？** 指出文件与测试名。指不出 → FAIL。
   ⚠️ **两类改动没有 red→green 载体，改用三件替代证据**（T-0921-70/71，2026-09-21 ops 裁；T-0921-71 自审第二轮补第②类）：**①** `type: data_contract` 且改动只删/改名单或映射条目（不新增行为、不改分支逻辑）；**②** 改动只碰无测试载体的治理文档（`TEAM.md` / `CLAUDE.md` / `.claude/skills/**/SKILL.md`），无论任务 `type` 是什么——生效前必须先 `git grep <文件名> pipeline/tests tests` 确认真的没有测试读它；不是每份都空手，比如 `test_daily_recap_skill_dryrun_guard.py` 就断言 `daily-recap/SKILL.md` 的真实内容，那种文件不适用本条，仍按上面 Q2 原文办（T-0921-71 第二轮复核指出「三份都没测试」这句原表述有误，改成现查）。三件替代证据：①验收命令实跑的完整输出 ②全量回归前后都通过（不掉绿即可，不要求本条改动让它翻） ③**改动面与被验对象的相关性说明**——执行者必须写清楚被跑的验收命令读的是不是这次改动碰的文件/路径，读的是别处（比如改了 `frontend/` 却验 `data/output/`）就不算数，视同 FAIL。三件缺一不可；缺哪件按 FAIL 处理，不要放宽成 ASK。
3. **越过 owner 的文件边界了吗？** 对照 `agents/<owner>/ROLE.md` 的「文件边界」。越了 → FAIL。
   ⚠️ **任务 `priority: P0` 时例外（Andy 2026-09-22 裁，T-0922-68：「P0 单复核员只判代码对不对，对就合」）**：越界不判 FAIL，改为在判词 Q3 里写明「越界（P0 放行）：`<越界文件>` 归 `<owner 线名>`」，继续走 Q1/Q2/Q4；合进 main 后由工人对每条被越界的线开一张 `type=followup` 知悉单（见 `agents/_worker_protocol.md` 第 6 步）。**此例外只免 Q3**——Q1（删 main 已有可执行行）、Q2（red→green 证据）、Q4（验收逐条对得上）不受影响；**删数据（gate=andy）与对外发布不在此例外范围内，仍按原规矩走**（本条不改变 gate 判定，只改变越界这一问的判词）。非 P0 任务越界照旧 FAIL。
4. **验收逐条对得上吗？** 每条写「对上/没对上 + 证据」。
   ⚠️ **任务 `type` 是 content / deliver_pdf / visual / experiment / research 之一时，这一问是唯一的活**（T-0921-34，09-20/21 两次假回执——「5 条视频已交」实为仓库外的样片、无人复核——都栽在这里）：**逐条**对着『## 验收』的每一项过一遍，**指不出证据的那一条就打回**（证据＝命令输出 / commit / 可点链接 / 实测截图，缺哪样写哪样）。评的是**有没有证据**，不是文笔好不好、也不是你会不会做得更好——**不评价写作，不重做工作**，只问「这条我能不能亲眼验到」。有一条指不出证据 → 整体 FAIL。

输出格式（最后一行必须是这个）：
`VERDICT: PASS|FAIL|ASK · Q1 … · Q2 … · Q3 … · Q4 …`

**ASK 用于代码本身没问题、但验收条件/任务描述本身有错**（比如验收要求的提交号在代码仓库里根本不是一个对象、任务描述有歧义）——这不是 PASS 也不是 FAIL，是「四问答不下去，因为问题本身有错」。判 ASK 时把缺的是什么、你的建议写清楚。
执行方用 `taskboard.py review <id> --verdict ASK --evidence-file <文件>`：任务板会自动开一张 owner=ops 的 followup 单、原单标 blocked，**不会**直接进 needs_andy（T-0921-52，源自 T-0921-50 案：验收要求的提交号 4ae0e53d 不存在，这本该是 ops 一句话能裁的事，却被直送给 Andy）。只有 ASK 的问题本身涉及**不可逆 / 花钱 / 对外发布**，才改用 `needs-andy` 直接问 Andy。
