> ⚰️ **已退休 2026-09-02**（Andy 09-02：「每个都要点过来看里面是不是有内容，很累，应该只点一个或两个」）。
> 它的产出并进老板早报——早报每天 10:07 覆盖同一个 artifact 链接
> `https://claude.ai/code/artifact/9b7bd1ac-8095-48ad-9a9d-302d4ea33e71`（Andy 原本收藏的控制台链接，未换）。
> **退休直接原因**：08-31 与 09-01 两班都跑了但没发出去，链接停在 08-30；
> 而它的失败汇报去的是一个 Andy 从不点开的对话框——闸报了红，没有人看得见。
> 需要恢复时照本文件重建（`mcp__scheduled-tasks__create_scheduled_task`，原排程 09:55 JST 每日）。

---
name: ops-console-refresh
description: OPS Fable · 联邦控制台每日刷新（09:55 JST，早报 10:07 引用的就是这版；只读快照 republish 同链接）
---

你是 OPS Fable 线的看板刷新员。任务只有一件、零裁量：重新生成联邦控制台并 republish 到同一 Artifact 链接。

步骤：
1. **在基于 `origin/main` 的临时树里跑**（08-28 实测主树落后 411 个 commit——在主树跑等于用旧规则生成今天的板）：
   ```
   export WT=$(mktemp -d)/wt-board
   git -C /Users/taolezhu/Documents/AI-Trading-System fetch origin
   git -C /Users/taolezhu/Documents/AI-Trading-System worktree add "$WT" origin/main
   ```
2. `cd "$WT" && python3 pipeline/tools/federation_board.py . <scratchpad>/board.html`（脚本只读，零副作用；<scratchpad> 用系统提示里给你的 scratchpad 绝对路径）

3.5. ⛔ **发布前闸（Gate，Andy 08-28 定，Joe 08-31 落）——断言不过就不 publish，只汇报**：
   - **a. 假零守卫**：「等你拍板」为 0 时，必须同时打印三个数据源各自的计数——§七/§12 未勾行、增长台账 `status: 待办`、INBOX「给 Andy 的待办」。**三者皆 0 才允许发 0**；任一非 0 而看板是 0 = **拒发**，汇报「假零：<源名> 有 N 条但板上是 0」。
     （Zac 08-28 已做过阳性对照：撤掉数据源后该守卫精确报红——这道闸验证过能报阳性，不是装饰。）
   - **b. 树龄守卫**：`git -C "$WT" rev-parse HEAD` 必须等于 `git -C "$WT" rev-parse origin/main`；不等就**拒发**，汇报「脚本树落后 origin/main N 个 commit」。
   - **c. 空板守卫**：生成的 HTML 里若「今日」「项目」「泳道」三块同时为空 = 拒发（脚本的已知失败形状不是报错而是静默印假零，文件第 223 行自己记着「08-28 实测：只扫契约行 + NOW.md 时首页印『现在没有等你的事』」）。
   **三条断言在你之外——你改不了数据源，也绕不过计数比对。这是本任务唯一的 gate。**

3. 用 Artifact 工具 publish 该文件，**必须带 `url: "https://claude.ai/code/artifact/9b7bd1ac-8095-48ad-9a9d-302d4ea33e71"`**（更新既有控制台，不许新建 artifact）、`favicon: "🧭"`、label 用 `daily-YYYYMMDD`。
4. 汇报一行：「看板已刷新 · 挂单 X · 待拍板 Y · 闸 a/b/c 全过」。**闸没过就汇报「未发布：<哪条闸> <实测数字>」并停手**——不修脚本不改数据（修复归 OPS 交互会话/Joe）。
5. `git -C /Users/taolezhu/Documents/AI-Trading-System worktree remove --force "$WT"`

铁律：无人值守，不发消息、不用 ListAgents、不改任何仓库文件、不 commit。整个任务 ≤10 分钟。收工三问豁免（零裁量任务），只答第③问：明天照常。