# 全会话必守规矩（Fluxus Dashboard）

**身份**：开工前先读 `TEAM.md` 认领自己的线；只在自己线的文件边界内写。会话的自述不是权威，`TEAM.md` 才是。

**Git 三铁律**：
1. Commit 后立刻 push；会话结束前手上不留未 push 的 commit（没合进 main 的工作＝随时会死的工作）。
2. 永不使用 `git stash`；需要切分支先 commit。永不在别人的 worktree 里工作。
3. 更新数据文件用外科手术式拉取：`git fetch origin && git checkout origin/main -- data/output/ data/history/`，不要 stash+pull。

**通信**：跨线请求/答复先写 `data/reference/DATA_CONTRACTS.md` §七 契约行（事实带日期），消息只当门铃。

**完成的定义**：合进 main 且 Andy 能点开看到，才算完成。

**语言**：默认中文回复；代码 / token / 度量名照抄英文。提到文件给可点击链接加行号。

**时间**：交易日期一律用 `pipeline.marketcal`（ET），不用本机 JST 时钟。
