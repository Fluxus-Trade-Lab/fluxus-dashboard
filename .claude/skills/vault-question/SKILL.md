---
name: vault-question
description: 蒸馏厂搬运班——每天把口述原料（Fluxus_Brand/voice/raw/）搬进 vault 判断题，从口述桶里挑一问写进 VAULT_STATUS.md 顶部「今日一问」节。凡任务 type=vault_question、或班次 ops-vault-question 触发、或有人说「蒸馏厂今天问什么 / 口述原料搬了吗 / VAULT_STATUS 今日一问怎么写」都用本 skill，别重新发明搬运判据或今日一问格式。
owner: ops
---

# vault-question — 蒸馏厂搬运班

你是 **ops 线的蒸馏厂搬运班**（原 ops-vault-daily-question SOP 精简版，2026-09-19 迁入守护进程；旧版取门铃/发消息/技能留痕等定时任务壳层步骤已剔除）。≤15 分钟，子 agent 0 个。

**为什么有这一班**：09-17 发现两处断点：①Andy 09-06 已口述 C17 / C26（原料在 `Fluxus_Brand/voice/raw/`），11 天没人搬进 vault，09-17 晚上又问了他一遍同样的问题；②口述桶「另约时间」从来没约过。这一班把两件事变成每天自动发生：**搬原料**、**递一个问题**。

## 两个仓库
- 主仓库：`~/Documents/AI-Trading-System`（PUBLIC）。写入一律按 `_worker_protocol.md` 第 5–6 步：在自己的临时树提交、推分支、算 gate，gate=none 才自合，reviewer 就等复核：只 add 指名文件，`git diff --cached --name-only` 数一遍再 commit；合进 main 后 `git merge-base --is-ancestor HEAD origin/main` 核实。永不 `git stash`，永不在主树上 commit。
- vault：`~/Documents/AI-Trading-System/FluxusTrading_Obsidian`（独立私有仓库 `Fluxus-Trade-Lab/FluxusTrading-Obsidian`，含付费课程正文）。直接在它里面 commit + push。只 add 你改的文件，**不提交 `.obsidian/` 下任何文件**。

## 第 1 步：搬原料（先做）
1. 列口述原料，**两边取并集**（`voice/raw/` 主树工作区与 origin/main 各可能有对方没有的文件，同名取新）：
   `ls ~/Documents/AI-Trading-System/Fluxus_Brand/voice/raw/` 与 `git ls-tree --name-only origin/main Fluxus_Brand/voice/raw/`；另看 vault `90_Inbox/interview/`。
2. 读 vault `90_Inbox/candidates/_TO_REVIEW.md` **页底最新一节**，得到「口述桶」卡号清单（如 C14 / C19 / C21）。
3. 对每张口述桶的卡：原料文件名或正文里出现该卡号、且该卡 frontmatter 的 `source:` 还没引用这份文件 → **这份原料没人搬**。
4. 没人搬的原料：
   - 卡片 frontmatter：`review: dictate` → `review: judge`，加 `review_since: <今天>`，`source:` 追加原料路径；`evidence:` 按 vault `00_INDEX.md`「账本证据分级」三选一如实填，不许空；能挂研究委托就在 `90_Inbox/_RESEARCH_COMMISSIONS.md` 末尾追一条（写死验什么 / 用哪批数据 / 谁跑：未认领）。
   - 正文：**只整理他说过的话**，每条都要能在原料里找到；不加洞见、不补他没说的规则。和已批卡冲突的地方列出来让他定，不替他选。结尾一节「要你判的」≤2 问。
   - 原料只是提纲、没有正文 → 不蒸馏，只在卡上记「提纲已收到，正文未讲」，卡留在口述桶。
   - `_TO_REVIEW.md` 页底追加一节「<日期> 更新」，写清哪张从口述桶移到判断题；**不改旧节**。
5. 没有没人搬的原料 → 这一步什么都不写。

## 第 2 步：今日一问
从口述桶里挑**一个**问题（顺序：页底最新一节口述桶表的第一行；某张卡欠多段正文时一次只问一段）。口述桶空了就挑一道判断题，问法是「批 / 改 / 毙」。两个都空 → 今日一问写「蒸馏厂今天没有要问你的」。

把它写进主仓库 `data/reference/VAULT_STATUS.md` 顶部的 `## 🎙 今日一问` 节（没有这一节就在「最后更新」那行下面新建；整节覆盖，只保留今天的）：
```
## 🎙 今日一问（<日期> · 约 N 分钟 · 语音回答即可）
**<卡号>**：<一句话问题>
回答方式：在任何会话里直接说，或录音丢进 `Fluxus_Brand/voice/raw/`——第二天这一班会把它搬进卡里。
```
⛔ **VAULT_STATUS 所在仓库是 PUBLIC**：问题只写「问什么」，不写任何方法细节、数字阈值、课程正文。拿不准就只写卡号 + 卡标题 + 「按卡上的问题讲」。
同时把该文件的计数表按 vault 现场数刷新（`grep -rl '^status: <x>$' --include='*.md'`），「最后更新」改成今天。计数不许转抄。

## 第 3 步：落盘与汇报
- vault 有改动 → commit（message 写清搬了哪份原料、改了哪张卡）+ push。
- 主仓库 VAULT_STATUS → **不是「按第 5–6 步做」就够，是真的跑一次**：把本 prompt 最上方『工人流程』步骤 5 那条 `taskboard.py gate <本任务号> --worktree "$WT"` 命令原样执行（`<本任务号>` 换成任务文件 frontmatter 的 `id:`）——`data/reference/**` 现判 reviewer，只有 `data/reference/incidents/` 例外判 none，这一步**几乎每天都会算出 reviewer**，不许因为「只改了今日一问几行」就跳过。返回 `none` 才 `git push origin HEAD:main`；返回 `reviewer` → 推分支 `agent/ops/<本任务号>`，按工人流程步骤 6 派只读子 agent 走 branch-review，PASS 才合 main，FAIL 停在分支。09-19～09-22 连续 4 天这一步都直接推了 main——没有分支、没有 gate 记录、没有复核（T-0923-29 查出），这条改动是补这个漏，不是新加的可选项。commit message 以 `vault-status:` 开头。
- 最终回复 ≤5 行：搬了几份（卡号）· 今日一问是哪张 · 两个 commit 的 hash · 有无异常。
- 10:07 的每日页会扫 VAULT_STATUS 把问题端给 Andy，那是唯一出口，不额外通知。

## 红线
- 不代写 Andy 的声音：卡片正文只整理原话。
- 不移动卡片进正式目录（入册要 Andy 批过才做，不归这一班）。
- 读不到某个源 → 汇报写「<源> 读不到」，不拿旧的顶替。
- 有异常/踩坑 → `taskboard.py handoff --owner ops --type material` 或写进 `data/research/night_reports/INBOX.md` 一行。

## 验收
- [ ] 口述原料并集已核对，没人搬的都已按流程蒸馏或留卡说明
- [ ] VAULT_STATUS.md 今日一问节已整节覆盖更新，计数表已刷新
- [ ] vault 与主仓库两个 commit 都已确认在各自 origin/main 上

## 出处

正文原文迁自 `schedule.json` 班次 `ops-vault-question` 的 `body` 字段（该班次此前已 done 4 次，做法只活在 schedule body 里，T-0920-20 / T-0921-19 / T-0922-23 三次「固化为 skill」单因此各重写了一遍；T-0923-38 迁完后 schedule body 改成指向本 skill 的一句话，不再重复正文）。
