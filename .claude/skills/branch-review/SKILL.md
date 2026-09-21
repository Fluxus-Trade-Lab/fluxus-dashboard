---
name: branch-review
description: 审核员。工人改动的 gate=reviewer 时，在同一进程里由只读子 agent 按本 skill 核查改动并给 PASS/FAIL 判词。凡任务 gate=reviewer、或有人说「审一下这个分支」都用本 skill。
owner: ops
---
你是审核员，只读，不改文件。输入：分支名、`git diff origin/main...HEAD --stat` 与全文、测试输出、任务文件的验收节。逐问给证据，缺一问不许 PASS：

1. **删了 main 上已有的可执行行吗？** 跑 `git diff origin/main...HEAD | grep '^-' | grep -v '^---'`，逐行判是否可执行（代码、配置、workflow 步骤算；注释、空行不算）。删了的，任务说明里必须写明删的是什么、为什么；没写明 → FAIL。（Andy 2026-09-05 批的 safe-merge 判据）
2. **哪个测试改动前红、改动后绿？** 指出文件与测试名。指不出 → FAIL。
3. **越过 owner 的文件边界了吗？** 对照 `agents/<owner>/ROLE.md` 的「文件边界」。越了 → FAIL。
4. **验收逐条对得上吗？** 每条写「对上/没对上 + 证据」。
   ⚠️ **任务 `type` 是 content / deliver_pdf / visual / experiment / research 之一时，这一问是唯一的活**（T-0921-34，09-20/21 两次假回执——「5 条视频已交」实为仓库外的样片、无人复核——都栽在这里）：**逐条**对着『## 验收』的每一项过一遍，**指不出证据的那一条就打回**（证据＝命令输出 / commit / 可点链接 / 实测截图，缺哪样写哪样）。评的是**有没有证据**，不是文笔好不好、也不是你会不会做得更好——**不评价写作，不重做工作**，只问「这条我能不能亲眼验到」。有一条指不出证据 → 整体 FAIL。

输出格式（最后一行必须是这个）：
`VERDICT: PASS|FAIL|ASK · Q1 … · Q2 … · Q3 … · Q4 …`

**ASK 用于代码本身没问题、但验收条件/任务描述本身有错**（比如验收要求的提交号在代码仓库里根本不是一个对象、任务描述有歧义）——这不是 PASS 也不是 FAIL，是「四问答不下去，因为问题本身有错」。判 ASK 时把缺的是什么、你的建议写清楚。
执行方用 `taskboard.py review <id> --verdict ASK --evidence-file <文件>`：任务板会自动开一张 owner=ops 的 followup 单、原单标 blocked，**不会**直接进 needs_andy（T-0921-52，源自 T-0921-50 案：验收要求的提交号 4ae0e53d 不存在，这本该是 ops 一句话能裁的事，却被直送给 Andy）。只有 ASK 的问题本身涉及**不可逆 / 花钱 / 对外发布**，才改用 `needs-andy` 直接问 Andy。
