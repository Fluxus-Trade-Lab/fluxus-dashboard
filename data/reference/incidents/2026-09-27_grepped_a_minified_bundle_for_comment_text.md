# 报了一起「线上停在 09-25」的 P1，其实货在店里——探针取的是注释，minify 早把它剥了

**日期**：2026-09-27（ops）
**形状**：判「线上是哪一版」时，探针字符串只存在于源码注释里。打包会剥注释，所以它对**任何**构建版本都返回 0 命中——这个探针没有分辨率，而同轮的阳性对照走的是另一条通道（代码里的字符串），证不了它。
**同族**：`method_positive_controls_by_failure_mode`（阳性对照要按「能坏的方式」分类造）· `pitfall_grep_against_a_ref_that_does_not_exist`（0 命中先问这个 grep 本身站不站得住）· `pitfall_a_fix_that_turns_red_into_blank`（报绿的是「空」不是「对」）

---

## 一、时间线

- **2026-09-27 20:15 JST** —— 前一班现场复核，结论「线上前端停在 `7d27d69a7` 之前那一版，其后八个前端提交一个都没上线」，开 T-0927-60（P1，incident）。判据两条：阳性对照 `The Fluxus Method` → 1、`Profit Factor` → 2（命中，判 grep 有效）；09-26 新版落地页串「业绩这个卖点不会持久」→ 0、「四是每日复盘」→ 0（未命中，判未上线）。
- **2026-09-27 20:31 JST** —— ops 工人接手，按本单第四节「下一步查什么」去查 `scripts/vercel_ignore_build.sh` 的跳过判定与产物 alias。
- **2026-09-27 20:36 JST** —— 换探针重测，`975690fa1` 的改动**全部命中**线上 bundle；再用静态文件哈希独立复核，线上等于 `origin/main`。**结论翻转：线上是最新的，没有事故。**

## 二、根因

两个探针走的不是同一条失败通道。

那两个「09-26 新版落地页串」在源码里都只出现在注释里：
- `frontend/src/components/public/LandingPage.jsx:8` —— 「四是每日复盘pdf」在文件头的 `/* … */` 块里（Andy 2026-09-25 口述原话，抄进注释备查）
- `frontend/src/components/public/LandingPage.jsx:121` —— 「业绩这个卖点不会持久。」在 JSX 的 `{/* … */}` 里

`vite build` 走 esbuild minify，默认剥注释。**这两个串不可能出现在任何版本的 bundle 里**，包括正确构建的最新版。它们返回 0，说的是「注释被剥了」，不是「代码是旧的」。

阳性对照 `The Fluxus Method` / `Profit Factor` 是 JSX 里真正渲染出去的文本，它证明的是「这个 bundle 里 grep 找得到东西」——而**要证的那件事是「注释文本会不会活到 bundle 里」**。对照选在了另一条通道上，于是一个必然为 0 的探针拿到了「判据有效」的背书。

再往下一层：这一步没有阴性对照。若同时拿**老版**注释里的一句去 grep（比如 `2903f6dad` 注释里的 `NOT BetaLock'd, on purpose`），它也会是 0，当场就能看出「注释在这个 bundle 里一律是 0」，探针立刻作废。

## 三、影响

- **线上没有任何问题**。爆炸半径 = 0 个用户可见缺陷。
- **成本**：一张 P1 incident 单 + 一个工人轮次（本轮）。已确认受影响的只有这两项。
- **模式命中**：同形状（用一个自己没验证过能报阳性的探针去下否定结论）在本仓记忆里已登记过两条（见「同族」）。

## 四、修法

没有代码要修——线上是对的。要修的是**判据**。

现场复核的四条证据（2026-09-27 20:36–20:40 JST，命令与读数逐条抄在这里，下一个人可以原样重跑）：

线上只有一个 JS bundle，`https://fluxus-dashboard.vercel.app/` 的 `index.html` 引 `/assets/index-CfzGZYML.js` + `/assets/index-Dl47FXXh.css`。

1. **`975690fa1`（落地页换他自己的话）在线上** —— 取它 diff 里真正渲染的文本：
   `The market is a game` → 1 · `their feelings` → 1 · `measurements instead` → 1 · `got humbled` → 1 · `event score` → 1；
   同时它**删掉**的旧文案已不在：`No 10-baggers` → 0 · `a sharp discretionary` → 0。
2. **`7d27d69a7`（从「看我的成绩」改成「你进来能用什么」）在线上** ——
   `Open Model Books` → 2 · `Read the market` → 1 · `1,400 past leaders` → 1；被它删掉的三块业绩看板 `H1 2026 Return` → 0 · `Payoff Ratio` → 0。
3. **`2903f6dad`（Model Books 解锁）、`c2e2f7b9c`（三态锁表）、`a3d11e4a4`（点进去看得见是糊的）、`14d071941`（一个黑）全在线上** ——
   `Education — Model Books`（被删的 BetaLock label）→ 0 · `这块还没做完` / `Not finished yet` → 各 1 · `这页暂时只给会员` → 1 · CSS 里 `#0b0c0f` → 1、旧的 `0a0a0a` → 0。
4. **不依赖 grep 的独立复核（最强的一条）** —— `frontend/public/` 下的静态文件逐字节进 `dist`，不经 minify，所以它的哈希能直接对上 commit：
   ```
   curl -s https://fluxus-dashboard.vercel.app/data/modelbooks/ohlcv/oneil-msft-1986.json | shasum -a 256
   ```
   线上 `bec82c105549aa31…`（26,580 B）＝ `origin/main` ＝ `d680ac9b4`；`975690fa1` 那一版是 `eff4d9595e36d0d1…`（17,738 B）。
   **线上不止有 `975690fa1`，还有比它更新的 `d680ac9b4`。** `d680ac9b4` 之后落 main 的前端提交只有 `7c8f61dbb`，它只加了一个 `*.test.js`，不进 `dist` —— 所以线上 = 当前 `origin/main` 的前端，一个提交都不欠。

本单第三条验收「线上 bundle 里『业绩这个卖点不会持久』grep 命中」**永远不可能满足**，原因就是第二节：它是注释。该条按「验收条件本身有误」处理，用上面第 1 条的五个串替代，意图（`975690fa1` 的落地页文案在线上）已满足。

## 五、机制升级

1. **判线上前端版本的标准探针（本文件即出处）**：
   - 探针只取**会被渲染出去的字符串**——JSX 文本、i18n 的 value、className、报错文案。**永不取注释**（`//`、`/* */`、`{/* */}`）。
   - 反向探针必须同时跑：新版**加**的串要命中，新版**删**的串要 0。只跑一个方向，命中和不命中都解释得通。
   - 想完全绕开 minify：比 `frontend/public/**` 里某个随该轮改动变过的静态文件的 `shasum`。它逐字节进 `dist`，能把线上直接对到 commit 上，是本轮唯一一条不经 grep 的证据。
2. **阳性对照要走被质疑的那条通道**（`method_positive_controls_by_failure_mode` 的第二个实例，非新条）：本轮的对照测的是「grep 在这个文件里能不能命中」，要证的是「注释能不能活到这个文件里」。**对照和探针不在同一条通道上，对照就是装饰。** 一句可自问的：*我这个探针，在「一切正常」的世界里会返回什么？* 答不出来就别拿它下否定结论。
3. **已开单** T-0927-69 给 claire（`frontend-preview-loop` skill 的 owner），把第 1 条作为一条 gotcha 追加进那本 skill——线上版本核对是前端工序的收尾动作，规矩该长在那本书里（`.claude/skills/**` 是 reviewer 档，ops 不自改别人线的 skill）。
4. **未咬到但记一笔**：本单第四节那条假设（Deploy Hook 触发的部署里 `VERCEL_GIT_PREVIOUS_SHA` 可能为空 → `scripts/vercel_ignore_build.sh` 退回 `HEAD^` → 跳过构建）本轮**证伪于结果**——线上是最新的，说明 09-25 那几次 hook 部署的构建真跑了。假设本身仍然成立得住（hook 部署没有 push 事件），只是没咬到。它要被证实需要一份 Vercel 构建日志（本班取不到，部署 URL 有 SSO 墙，且 09-26 05:46 之前的部署都已被 Vercel 回收，`x-vercel-error: GONE`）。**不开单**：没有证据说它正在坏，线上就是判据。

## 六、教训

- **一个探针在「一切正常」的世界里返回什么？** 答不出来，它的 0 就不是证据。
- **阳性对照要按「被质疑的那条通道」造**，不是随便找个能命中的串。命中证明的是 grep 会工作，不是探针会分辨。
- **编译过的产物里找不到源码的话，先问是不是编译吃掉了它**——注释、`console.log`、类型标注、dead code 都会在 minify/tree-shake 里消失，它们在产物里一律是 0。
- **有一条不经处理的通道就走它**：`public/` 的静态文件逐字节进 `dist`，一个 `shasum` 就把线上钉到 commit 上，比任何字符串探针都硬。
- 翻转别人的 P1 结论之前，把两份读数并排贴出来（他的探针 + 我的探针），让下一个人看得出分歧在判据上，不在谁更细心。
