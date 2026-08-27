# 联邦看板 · lane 归属准确率实测（2026-08-28 夜间轮）

> OPS 08-27 二更挂单原话：「抽 20 张卡人工核对 lane 对不对，报个准确率数字」。
> 做法上有两处偏离，都是往严的方向：**普查全部 59 张卡而不是抽 20 张**；
> **由两名独立裁判盲判**（看不到 heuristic 的判定，也看不到彼此的判定），
> 我自己不参与打标——按 polydao gate 判据，agent 自审必然自我批准。

---

## 结论（一句话）

**在产的 v4 关键词版把 lane 判对 20/52 = 38.5%。** 也就是说：**看板上每 3 张卡有 2 张挂错了线。**
病根有两个，都不是「关键词不够多」：① 花名册顺序压过文本位置；② 顺带提到的人名被当成归属方。
改成路径优先后 **44/52 = 84.6%**（有 in-sample 折扣，见 §五）。

**但今晚更值钱的不是这个数**，是 §四那条：**「待认领」列 22 张卡里 20 张（91%）是坟头**，
最老两张来自 **2026-03-31**（五个月前）。lane 判对了也没用——那一列本身在说谎。

---

## 一、怎么量的

| | |
|---|---|
| 样本 | `python3 pipeline/tools/federation_board.py . board.html` 在 `origin/main@58fd7ecf` 上生成的**全部 59 张卡**（04:35 JST 快照）。不是抽样。 |
| 裁判 | 两个独立 agent，各拿同一份**去掉 heuristic 判定**的卡片表（`id / 来源 / 卡面文字 / 该 commit 或分支实际改动的目录`）+ `TEAM.md` 权威边界表 |
| 视角差异 | 裁判 A：「这件工作按 TEAM.md 边界归谁」；裁判 B：「Andy 想追进度该敲哪条线的门」。允许写「不确定」。 |
| Ground truth | **两裁判判一致**的卡。不一致的 7 张不计入分母（见 §三，它们暴露的是制度歧义不是代码 bug）。 |
| 两裁判一致度 | **52/59 = 88%** |
| 可用共识 | **52 张** |

## 二、两个版本的成绩

| 版本 | 对共识准确率 | 未归属（落「联邦」） |
|---|---|---|
| **v4 关键词版（在产）** | **20/52 = 38.5%** | 21/59 = **36%** |
| v5 路径优先版（本轮所写） | **44/52 = 84.6%** | 2/59 = 3% |

> 剔除 K004（我自己这条 in-flight 分支，测量期间内容被我自己的 commit 改了，属自指污染）：
> v4 = 19/51 = 37.3%，v5 = 44/51 = 86.3%。两种算法都列出来，不挑好看的报。

### v4 的 32 张错判，按病因分三类

| 病因 | 张数 | 样例 |
|---|---|---|
| **① 花名册顺序压过文本位置** | 8 | `→ 风险线(模型 R&D):…(数据端研究协议回填时发现` → 判给 **DATA ALEX**。收件人「风险线」在文本里排最前，但 DATA ALEX 在 ROSTER 里排最前，**先扫到谁算谁**。 |
| **② 顺带提到的人名当成归属方** | 6 | `task(挂单): Gate 声明制…建议 Joe 认领` → **Joe**（实为 OPS 派活）；`board(v2): …Zac 卡改为打分` → **Zac**（实为 OPS 出稿）；`verdict(adr): Andy 拍板…` → **Zac**（命中子串 `adr`）。 |
| **③ 关键词表压根不匹配实际提交习惯** | 18 | OPS 的键是 `rules(`（带括号），而实际 commit 写的是 `rules:` → `rules: 三次律`、`rules: 全会话前台制` 全部落「联邦」。`brief` 这个键把 `night(report): 2026-08-20 morning brief` 判给了 Marketing Steve，把 `growth: …不提供 daily briefing` 也判给了 Steve。 |

## 三、两裁判不一致的 7 张 —— 这不是代码问题，是**制度没定义**

| 卡 | 裁判 A | 裁判 B | 分歧点 |
|---|---|---|---|
| K028 / K029 | UI Claire | DATA ALEX | 一条 §七 契约行的 lane 是**「谁写的」**还是**「派给谁的」**？ |
| K044 | OPS Fable | Plumber Joe | 挂单卡归**派活人**还是**被提名人**？ |
| K047 | OPS Fable | Nighty Zac | 同上（`task(zac)` 立项卡） |
| K027 | 不确定 | OPS Fable | 一条行同时点名三条线（素材箱主人 / INBOX 主人 / 定夺人），天然不可归一 |
| K019 / K021 | Marketing Steve | 不确定 | 陈旧分支，diff 全是基线漂移，分支名与内容对不上 |

⚠️ **需要 Andy 或 OPS 拍一句**：看板卡的 lane 语义是「**谁欠这件事**（收件人 / 待办人）」还是「**谁做了这件事**（作者）」？
现在两种都有：`done` 列是作者语义，`claim`/`blocked` 列是收件人语义，而同一个 `lane_for()` 在两边都用。
**在定义之前，这 7 张卡的准确率是没法量的**——不是我量不出，是题目本身没答案。

## 四、⚠️ 比 lane 更严重的一条：「待认领」列 91% 是坟头

22 张待合分支卡，按最后提交时间排：

| 最后提交 | 张数 | 例 |
|---|---|---|
| 近 5 天内（08-23 起） | **2** | `feat/morning-three-pages`、`auto/night-20260828-*`（我自己的） |
| 08-19 ~ 08-22 | 12 | 九张是 08-22 大扫除时 `wip(archive): 大扫除前封存未提交工作` |
| 08-07 ~ 08-12 | 5 | `follow-traders`(+64)、`worktree-fluxus-data-art`(+4)… |
| **2026-03-31** | **2** | `marketing`(+63) 与 `pine-indicators`(+63) —— **五个月前，且两者 tip 是同一个 commit `f2fd51f1`**，`pine-indicators` 里没有任何 pine 改动 |

**91% 的「待认领」不是待办，是没删的分支。** 这一列现在的作用是把两张真待办埋进二十张噪音里——
正好撞 Andy 六条里最硬的那条「简洁整齐压倒一切」。

**建议（决定权不在我）**：待合分支卡加一个**保鲜期**，最后提交超过 N 天（建议 14）的移出「待认领」，
折叠进一个「陈年分支 · 20」的单行；或者干脆交给 `repo-janitor` 出删除清单等 Andy 点头。
⚠️ 这两条我都没做——`pipeline/tools/federation_board.py` 不在我的 safe-merge 白名单，且这是产品决策不是 bug。

## 五、v5 的 84.6% 要打折，以及它剩下的 8 张错

**折扣声明**：v5 是在看过 v4 的错判之后写的，属 in-sample。
唯一的抗辩是**路径规则表逐条抄自 `TEAM.md` 第 12–19 行的「文件边界」列**，不是照错误反推的——
唯一一次「看到错才补」的是 `Fluxus_DataArt/ → Studio Q`，而那也是我**漏抄**了 TEAM.md 明写的「数据艺术素材」，不是调参。
真正的检验要等下一个 14 天窗口的新卡，**今天给不出 out-of-sample 数**。

剩余 8 张错判，4 张是同一个结构性原因：

| 卡 | v5 判 | 共识 | 原因 |
|---|---|---|---|
| K036 / K037 / K038 | Joe / Joe / OPS | Studio Q | **只碰公箱**（`DATA_CONTRACTS.md`）→ 路径弃权 → 落到关键词，而 `contracts(§` 这个键给了 Joe |
| K043 | 联邦 | OPS Fable | 同上，且没有任何关键词命中 |
| K007 | UI Claire | RND Linda | 分支 diff 被 `frontend/public`(1549)、`data/output`(324) 的**生成物**淹没，真意图（GEX engine 计划）在前三个 commit 里 |
| K018 / K020 | Steve / Claire | ALEX / Steve | 陈旧分支，diff 相对 main 是基线漂移，不反映分支意图 |
| K004 | OPS Fable | Nighty Zac | 自指：我今晚的 commit 让自己这条分支变成了「改看板的分支」 |

### 结构性结论：**只碰公箱的 commit，从路径上不可归属**

全仓实测：`origin/main` 近 14 天 **596 个 commit**，路径判不出线的有 **142 个 = 24%**——
其中 **61 个只碰三个 append-only 公箱**（`DATA_CONTRACTS.md` / `night_reports/INBOX.md` / `material_inbox.md`）、
14 个两线平票、67 个路径规则没覆盖。

**这一段靠加关键词是补不上的**（v4 就是那么干的，得了 38.5%）。
真解是 OPS 自己在 08-27 那张卡里已经提过的那条：**commit message 的线名前缀规范落 TEAM.md**——
让作者在写 commit 时就声明自己是谁，而不是让看板事后猜。
猜的上限，就是这份报告里的 84.6%。

---

## 附：可复跑

```bash
python3 pipeline/tools/federation_board.py . /tmp/board.html   # 4.6s（一次 git log --name-only，不为每个 commit 起进程）
python3 -m pytest pipeline/tests/test_federation_board_lane.py -q   # 17 passed
```

**阳性对照**（三个 bug 逐个注射回 v5，确认测试能报红——见测试文件头 docstring）：
① `lane_of` 退回花名册顺序 → 1 红；② 公箱不再弃权 → 4 红；③ 箭头拿整行找别名 → 1 红。
注射 ③ **第一版全绿**，因为那条用例里收件人恰好排在发件人前面；补了「箭头之前有转投递人」的用例才报红。
**没先验证一个检查能报出阳性，就不该信它的阴性。**

---

# 六、⚠️ 今晚查出的最重一条：首页「等你拍板」是**假零**

控制台首页那格印着 **「现在没有等你的事」**。实测**至少三件在等 Andy**：

| 事 | 登记处 | 状态 | Andy 的原话 |
|---|---|---|---|
| T1 回收两个 Discord 付费角色 | `data/growth/weekly/2026-08-25-paypal-reconcile.md` | `status: 待办` | 「这个是要处理的，**提醒我**。」（08-25） |
| T5 `#welcome` 加升级入口 | 同上 | `status: 待办` | 「**要做！**」（08-26） |
| T3 PII 清史（跨两条线） | 同上 | `status: 待办` | 等 Andy 发话 |

**病因**：`blocked` 列只扫两个源——`DATA_CONTRACTS.md` 的契约行、`NOW.md` 的 `- [ ] 待你`。
而这三件挂在增长台账与 INBOX 的「📌 给 Andy 的待办」节。两处都是**有核销协议**的清单
（台账那节写明「每周一记账必须原样抄进当周周报置顶，直到 Andy 明确说做完了才改 ✅」），
只是没人把它们接上。

**这一格的全部价值就是宪法那条「⚠️ 需要 Andy 注意或决定的事置顶拉响」。印零等于把它们藏起来。**

**已修（在分支上，`pipeline/tools/` 不在我的白名单）**：新增这两个数据源 + 同事两处登记只出一张卡的去重。
修完首页由 0 变 3。

⚠️ **一条我特意没做**：**不接晨报的「六、建议 Andy 决定的事」**。
晨报是 append-only 快照，**没有核销协议**——接进来就会把 08-27 那条已经拍板的 ADR 闸当成还在等。
**假阳性比假零更快让人不再信这一列**：假零让他漏看，假阳性让他学会不看。

**阳性对照**：把这两个数据源撤回（= 本轮之前的状态），
`test_the_waiting_on_andy_column_is_not_a_false_zero` 精确报红，报的正是「台账有 3 条 status: 待办 而看板是空的」。
写这条守卫时特意做成**条件不变式**而不是钉死的期望值：Andy 全清完了它自动跳过，不会变成又一条要维护的假绿。

# 七、OPS 交办的第二件：每日自动生成挂法 —— **已经有了，我只报一个缺口**

卡面问「评估每日自动生成+republish 的挂法」。先读现状：**`ops-console-refresh` 定时任务已在跑**
（09:55 JST 生成 + republish 到固定 Artifact 链接，早报 10:07 引用的就是这版）。
所以不提新方案（宪法：先读已有规划再开口）。**只报一个缺口：**

⚠️ **它在共享主树里跑脚本**（任务书第 2 步 `cd /Users/taolezhu/Documents/AI-Trading-System`），
而主树现在停在 `feat/morning-three-pages`，**落后 `origin/main` 411 个 commit**。

- 今天恰好没事：主树里的 `federation_board.py` 与 `origin/main` 上的 **md5 一致**。
- 但那是**巧合不是保证**。脚本读的数据确实全来自 `origin/main`（8 处 `git show origin/main:`），
  **可脚本本身读的是工作区那一份**——ROSTER、PATH_RULES、blocked 数据源全在文件里。
- **后果具体化**：我今晚这两个修法一旦合进 main，09:55 那次刷新是否拿到新版，
  取决于有没有人把这个文件手动同步进主树。宪法主树保护第 5 条讲的就是这件事。

**建议改法（一行，OPS 的任务书我不动）**：第 2 步改成在基于 `origin/main` 的临时树里跑——
```bash
export WT=$(mktemp -d)/wt-board
git -C /Users/taolezhu/Documents/AI-Trading-System fetch origin
git -C /Users/taolezhu/Documents/AI-Trading-System worktree add "$WT" origin/main
python3 "$WT/pipeline/tools/federation_board.py" "$WT" <scratchpad>/board.html
git -C /Users/taolezhu/Documents/AI-Trading-System worktree remove --force "$WT"
```
脚本 4.6s 跑完，多一次 worktree add 也在 5 分钟时间盒内。

# 八、§2.5 打分：**这轮不出竞品稿**，只报两条量得出来的

看板 v0→v4 是 OPS 今天一天之内迭代四版、Andy 已当面评过分的东西。
再由我出三个「变体」去打分，正是宪法警告的**平行造稿**（08-24 Steve 事故）。所以只报可量的：

| Andy 的第几条 | 读数 | 判 |
|---|---|---|
| 不新增颜色 | 页面 **31 个** hex 字面量，与 `frontend/src/index.css` 的 58 个现网 token **交集 = 0** | ⚠️ 整套是新调色板。看板是独立台面、不是 Dashboard 页面，所以这不必然是错——**但立项卡硬约束里写着「现网 token」，事实与约束不符，该由 Andy/OPS 认一下** |
| 反多巴胺 / 无动效 | 全页 `transition` / `animation` / `@keyframes` **各 0 处**，只有 5 处 `transform` | ✅ 过 |
| 文案只留交易内容 | 首页有「发完就算赢，其余都是加分」这类激励语 | ✅ **不判负**——🎮 关卡制与「今天的一件事」是 Andy 亲自要的机制（NOW.md），不是我该删的鸡汤 |
| 简洁整齐压倒一切 | 「待认领」列 22 张里 20 张是坟头（§四） | ❌ 最大失分项，且不在视觉层在数据层 |
| 让推理被看懂 | 「等你拍板」印零而实际有 3 件（§六） | ❌ 已修（分支） |
| 决策优先 | 首页把「等你拍板」放在第一屏 | ✅ 结构对，内容之前是空的 |

**对比度**：未测量（file:// 在项目目录外只渲染静态快照，本轮拿不到渲染结果，不猜）。
