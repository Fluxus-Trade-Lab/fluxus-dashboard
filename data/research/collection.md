# 馆藏 —— Andy 的收藏夹（Nighty Zac 整理）

> 来源：`night_reports/INBOX.md` 收藏夹节。每条：日期 · 链接 · 三五句摘要 · 判定（✅采纳→去向 / 📦存档 / 🗑丢弃+理由）。判定在晨报同步给 Andy。

---

## 2026-08-24 判定

### 📦 存档｜[08-23] How to Catch Powerful Stock Reversals (4B- Setup)

- **链接**：https://www.youtube.com/watch?v=1k3KRbktibQ
- **实为**：Deepvue 的产品 webinar（频道 Deepvue，2024-10-19，**69 分钟**，6,892 次观看）。不是独立教学，是**软件演示**——一半时长在讲怎么在 Deepvue 里加列、配指标、存 watchlist。
- **Andy 的话**：「reversal setup，我们图书馆和课程里没有详细记录和了解的」

**它讲的是什么**：Stan Weinstein 的四阶段分析（Stage Analysis），核心桥段是 **4B Minus 反转 setup** —— Stage 4 下跌末端的**筑底**买点。视频自己给的关键规则只有一句（时间戳 48:22 原文）：

> "Key rules for trading the 4B Minus setup (**higher low, reclaim 50-day MA**)"

配套还讲了 Mansfield Relative Strength 指标、Stage 2 vs 2A（早期 Stage 2）的区别、以及 Weinstein 本人在 Netflix 上用 4B- 的实例。

**和哪条线有关 —— 我们其实两个零件都有，只是没接起来**：

| 4B- 的成分 | 我们的现成实现 |
|---|---|
| higher low（下跌后的更高低点） | `sp_hl` / `ll_hl_1st` / `ll_hl_2nd` 面板（[structure_pivot.py:110](../../pipeline/screeners/structure_pivot.py#L110)、[watchlist.py](../../pipeline/screeners/watchlist.py)） |
| reclaim 50-day MA | `ma_reclaim` 面板（close 上穿 21EMA / 50SMA，[watchlist.py:130](../../pipeline/screeners/watchlist.py#L130)） |
| Stage 2 闸 | `trend_base` = close>SMA50 且周线 WMA10>WMA30 —— [screener_methods.md:38](../reference/screener_methods.md) 自己就注了这是「Stan Weinstein 式的在 Stage 2 闸」 |
| **Stage 4（下跌中）前置条件** | ❌ **我们没有**。我们只有「在 Stage 2」的正向闸，没有四阶段分类 |
| **Mansfield RS** | ❌ 没有。我们有 `rs_line_pctl_*`，不是 Mansfield 那个公式 |

**判定：📦 存档，不采纳**。理由三条：

1. **它的方法内容我们已覆盖 3/5**，缺的两块（Stage 4 分类、Mansfield RS）是**定义问题不是发现问题**——真要补，读 Weinstein 原书比看软件演示准。
2. **它是产品演示**。69 分钟里方法密度低，且所有 setup 都绑在 Deepvue 的界面上。
3. **`ll_hl_*` 链条正在被审**：08-23 的 waiver 裁决里，第一波链 holdout 失败已从 entry 席移除。现在往这条链上再加 setup **是规格先于证据**（[[pitfall_shipped_before_out_of_sample]]）。

**存档但记一条可测的问题**（给 Andy，不动工）：我们的 `ll_hl_1st` 和 `ma_reclaim` 现在是**两个独立面板**，Weinstein 的 4B- 说这两件事**必须同时**。我们的归档能直接回答「两个同时命中的票，和只命中一个的，前瞻收益差多少」——**零新数据、零新定义**。如果 Andy 想要一个便宜的实测，这是最便宜的一个。

---

## 2026-08-25 判定

> 本批四条全是 X 帖。走 OPS 08-24 定的镜像 `api.fxtwitter.com/<用户>/status/<id>` —— **四条全通**（08-24 直连 x.com 那次是 402 登录墙）。
> **两条是 X Article（长文）入口帖，正文镜像取不到**（`/i/article/<id>` 返回 404）——见下。

### ✅ 采纳｜[08-24] @Hrundel75 —— 「price direction is mostly noise. but volatility? predictable.」

- **链接**：https://x.com/Hrundel75/status/2091187956589690972 · 2026-08-22 · 2,710 粉
- **传播**：791,498 曝光 / 4,067 ♥ / **11,357 收藏** —— **收藏/赞 = 2.79，压过 Muninn 的 2.60，是我们量过的全库新高**。
  2,710 粉做到 79 万曝光 = **292× 粉丝数**。（「收藏比与粉丝无关」第七次复现，数据点归 [Fluxus_Muninn_Teardown.md](../../Fluxus_Brand/research/Fluxus_Muninn_Teardown.md) 那张表。）
- **Andy 的话**：「好像很重要」

**它说的是什么**（原文照引，他的话）：

> quant desks at citadel and D.E. Shaw don't ask "will it go up?" - they ask **"will the next move be large or small?"**
> because sizing correctly inside a vol regime is worth more than being right on direction

> the predictable part of markets was never price direction / it was the distribution of price. the size of the moves. which regime you're currently inside

**⭐ 这一句和 Andy 08-24 自己写的第三类问题逐字相同**，而他们互不相识。他给的机制是 Engle 的 GARCH / 波动聚集。

**判定：✅ 采纳 —— 已经变成了一轮预注册实测，当晚跑完。**
→ [`data/research/amplitude_2026-08/`](../amplitude_2026-08/results.md)

结果：**他的定性主张在我们自己的归档上成立，而且分离极干净**——事件前 20 日波动的五分位，
把事后 5 日右尾概率从 3.4% 拉到 19.0%（holdout 复制成 3.4%→17.5%）；
同一变量对方向的预测力 ρ=−0.006，p=0.59。**幅度 ρ=+0.30 (p=5e-157)，方向 ρ≈0。**

**但我们同时测出他没说的那一半**：期望值是**驼峰形**，最高波动分位的期望**翻负**——
右尾长大的同时左尾同步长大，payoff 比没跟着涨。**所以「幅度可预测」不等于「幅度可赚钱」。**
它的正确用法是**除数不是信号**（决定买几股，不决定买不买）。

**未验证的**：他帖里那两个 SPY 数字（低波状态 74% 续、波动尖峰 81% 续）**我们没查**——本轮测的是个股事件不是 SPY 状态机。别引用那两个数字当我们的结论。

---

### ✅ 采纳｜[08-24] @Muninn —— 复盘 Qullamaggie 900 笔入场，ADR 是最有解释力的变量

- **链接**：https://x.com/Muninn/status/2089746393183256879 · 2026-08-18 · 61,965 曝光 / 362 ♥ / 603 收藏（收藏比 1.67）
- **Andy 的话**：「收藏并学习」

原文（他的话）：

> After reviewing over 900 of Qullamaggies entries on breakouts and EPs the most insighftful and biggest epiphany is how important ADR is..
> He tells us to keep our entries <1 ADR... His sweet spot is 0.33 - 0.66 ADR.
> **But it turns out having a lower bound is better than a upper bound.** Entering stocks <0.25 ADR has a very low win-rate and negative expectancy..
> The other thing I was surprised by was that when he breaks this rule, cause he does.. its very profitable..

**判定：✅ 采纳为假设（H2），但实测下来在我们的口径里不成立为独立结果。**

两个理由，都要说清：
1. **口径不同**——他量的是**盘中入场那一刻已经走了多少 ADR**，我们只有**全天收盘涨幅 / ADR20**。
   一个是「进场时还剩多少路」，一个是「这天总共走了多远」。**我们这张表不能用来说他错了。**
2. **与 H3 混淆**——`adr20` 与 `pre_vol` 的 spearman = **+0.981**，是同一个东西的两个名字（[[pitfall_same_quantity_three_names]]）。
   `move_adr` 分桶大半是波动分位换了身衣服。holdout 上 `<0.25` 桶只剩 **n=19**，不下结论。

**要真正验证他这条，需要分钟级数据**——我们没有。列为 ❓ 未验证，不是 ❌ 证伪。

---

### 📦 存档（已有档，别重做）｜[08-24] @Muninn —— 「This is the article I wish I had when I started trading」

- **链接**：https://x.com/Muninn/status/2088292776047751193（正文在 X Article `2088143622180921344`）
- **⚠️ 这条我们已经拆过了**：[Fluxus_Brand/research/Fluxus_Muninn_Teardown.md](../../Fluxus_Brand/research/Fluxus_Muninn_Teardown.md)
  就是拿**这一条**做的样本帖（「收藏比 2.60 全库新高」那份）。**别再开第二份。**
- **我今晚的独立读数与那份档对得上**：views 258,506 / ♥ 521 / 收藏 1,353（该档记的是 258,040 / 521 / 1,355 —— 一天的自然漂移，一致）。
- **⚠️ 一处对不上，列进门铃**：该档写「**2026-08-03 发**」，镜像返回的 `created_at` 是 **Fri Aug 14 2026**。差 11 天。
  我不动 Marketing 线的文件，只报。
- **正文取不到**：X Article 长文镜像不支持（`/i/article/` 404）。**需真浏览器（Comet），留交互会话。**

---

### 📦 存档待读｜[08-24] @L1vsun —— X Article 入口帖

- **链接**：https://x.com/L1vsun/status/2088993353111159216 · 2026-08-16 · 5,235 粉
- **传播**：**1,366,198 曝光** / 401 ♥ / 1,543 收藏 —— 曝光是本批最高（**261× 粉丝数**），
  但**收藏/赞 = 3.85** 与 ♥/曝光 = 0.03% 这组合很怪：曝光巨大而互动极低。
  ⚠️ 上面 Hrundel75 那条**引用的正是这一条**，所以这 136 万曝光里有多少是被 Hrundel 带的、有多少是它自己的，**分不开**。
  在没分开之前，**别把这条的曝光数写进任何对标表**（[[pitfall_the_universe_chose_the_answer]]）。
- **帖子本体只有一个链接，零正文。** 正文在 X Article `2088966979189112832`，**镜像 404**。
- **判定：📦 存档待读 —— 需真浏览器（Comet），留交互会话。** 本轮不猜内容、不拿标题当结论。

---

### ✅ 采纳一条、其余存档｜[08-30] @huangruiteng —— 开源项目 LoopX（超长程 Agent 200+ 小时不漂移）

- **链接**：https://x.com/huangruiteng/status/2083904257494024425 · 2026-08-02 发 · 代码 https://github.com/huangruiteng/loopx
- **传播**：378,442 曝光 / ♥1,111 / RT 181 / 收藏 **1,735** —— **收藏比（收藏/♥）= 1.56**。
  对照本库：Hrundel75 2.79（新高）· Muninn 2.60。**技术主张帖的收藏比明显低于交易方法帖**，
  同一把尺子在两个题材上不可比 —— 别把这个 1.56 写进 Steve 的对标表当「差」。
- **Andy 的话**：改善控制台+loop 功能方向，他要看到「AI 自动干活提效，一人公司提效」。

**他的主张**：LLM 上下文有限 → **状态外置**，用完备的状态管理/监督/规划让 agent 无人干预时跑得稳。
外置成六件套控制面：Goal/Vision · Todo/Gate · Identity/Authority · Evidence/Receipt · Quota/Scheduler · Handoff/Recovery。
两条真实 trajectory 跨 220.7 / 272.9 小时，经过等待、人工决策、writeback 与 resume 后仍能找回目标与下一步。

**逐格对照我们已有的**（OPS 点名要看的三件在下面 ①②③）：

| 他的 | 我们的 | 有没有 |
|---|---|---|
| Goal / Vision | `NOW.md`（主线+停做清单）· MVP 闸三件套 | ✅ 有，且更贴一个具体的人 |
| Todo / Gate | 挂单板/待认领 · §七契约行 · INBOX | ⚠️ Todo 有，**Gate 弱**——Joe 08-28 实测 7 个任务只有 2 个有第③类真闸 |
| Identity / Authority | `TEAM.md` 线名 · safe-merge 白名单 · 主树保护六条 | ✅ 有，我们这块比他细 |
| Evidence / Receipt | `run_ledger.jsonl` · 回执制 · `incidents/` · commit | ✅ 有，且是仓库级不是进程级 |
| Quota / Scheduler | 定时任务 · 300 分钟时间盒 · 窗口守卫 | ✅ 有 |
| Handoff / Recovery | 晨报交接 · 分支 · git | ⚠️ 有，但**按时间恢复不按状态恢复**（Joe 08-29 那班迟到 485 分钟照跑，就是这个形状） |

**① 状态投影 —— 这是唯一真正的新东西，且我量得出我们缺它。**
他说「看板本身成为执行系统的一部分」：状态**约束并驱动**下一次 bounded turn。
我们的联邦看板是 git 状态的一次**只读投影**——**实测：仓库里没有任何程序消费它的输出**
（`grep -rln federation_board|board.html` 只命中生成器本身、它的测试、以及几份说「去读它」的文档）。
CLAUDE.md 叫各线开工去读它，那是**人读**，不是可执行依赖。
后果不是理论的：一块没有下游动作依赖它的看板，**错了也不会有任何东西坏掉**——
Zac 08-28 实测的分线准确率 38.5%、「待认领」91% 是坟头、首页「等你拍板」是假零，
三个都错了好几周，没有一个是被系统发现的，全是有人专门去查才查出来。
**→ ✅ 采纳为一个问题，不是一个功能**：看板每一列，问「有任何下游动作真的读它吗？」答不出的列就是装饰。
这个问题归 OPS（看板是他的文件），已列门铃。

**② writeback-resume**：我们的等价物是晨报+分支+§七，**已经有了**，形状不同不是缺口。
我们的恢复问题是别的：Joe 08-29 那条事故说明我们**按时钟恢复**（排程到点就跑），
不问「这个 session 是否已落地且健康」。这与他的 resume 不是同一件事，别混着抄。
**判定 📦 存档**——照抄他的 writeback 协议解决不了我们的病。

**③ 能力自进化**：「干活中发现缺能力→提 feature→开发验证→用新能力继续原任务」。
**我们已经在做，只是没起名字**：今晚这轮就是——查账本时发现「没有一道闸问『它比它替换掉的那份更好吗』」，
当场建了 `audit_regression_gate` 再继续。**判定 📦 存档，不采纳为新机制**——
给已经在发生的事加一套协议，是仪式不是杠杆。

**⚠️ 数字上的保留**：「200+ 小时不漂移」是作者自己的 showcase，**n=2 条 trajectory，无第三方复现**。
可以当方向读，**不可以当证据引用**（[[pitfall_borrowed_list_as_a_ruler]]）。仓库我没跑过，只读了帖。

---

## [08-30 收藏 · Zac 08-31 判定] threeui.com —— ✅ **采纳，但只能用 Community 那一半**

**Andy 的话**：「以后我们要往 3d 特效网站推进，threeui.com 是学习资料。」
前端 UI 线代录时留了三个「学完才发现不能用」的问题，我一条一条查了，**三条都有确定答案**。

### ① 许可证 —— **两套，别当成一套**（读的是 8 月 22 日更新的 Terms of Use 正文）

| | 许可 | 能不能进对外站点 |
|---|---|---|
| **Community** | **MIT**（站方原文：Community 包的代码按随代码附带的许可发布，目前是 MIT；**item-specific attribution / 第三方 notice 仍须保留**） | ✅ **能**，保留 notice 即可 |
| **Pro** | 付费期内的非独占许可，可商用、可交付给客户；但**不得**把 Pro 源码作为独立资产/组件库/源码集再分发，**不得**去掉署名 | 💰 要先买 |

**价格**：Pro $99/年（原价 $199）· Lifetime $199 一次性（原价 $399），Stripe 收款。
支持邮箱是 `support@designcode.io`（即 DesignCode 那一摊）。

⚠️ **一处我差点报错**：首页 `grep -i mit` 命中 4 次，看着像「有 MIT 声明」——
**四次全部是 `Yosemite` 里的子串**（组件名 "Temple Night — Yosemite Sunset"）。
首页正文零许可证声明，MIT 只在 Terms 正文里。[[pitfall_audit_greps_miss_the_other_spelling]] 又一次。

### ② 组件库还是教程站 —— **组件库**（所以问题确实是「抄哪几个」）

站方自述「copy-ready Three.js components / 完整网站模板 / WebGL 背景 / hero sections / UI effects」，
分类有 Landing Pages · Hero · Three.js · Backgrounds · Buttons · Text Animation · UI Elements · CSS · Motion Design。
**不是教程站**，没有讲解层。Pro 还附一个 MCP（能让 agent 直接取组件与源码）——
这一条对我们有额外价值，但它在**付费墙内**。

### ③ 代价 —— **比代录时估的小，因为 three 已经是懒加载的独立 chunk**

代录里写「首屏 1.5MB JS + 734KB three.module，three 已经在依赖里了」。查下来要改两个字：

- `three@^0.185.1` 确实在 `frontend/package.json` 里；
- **但它是动态引入**：`frontend/src/components/public/HeroField.jsx:110` 是
  `try { THREE = await import('three') } catch { return }`，用在 `LandingPage`（对外落地页）；
- 因此 `three.module-*.js`（主树 dist 实测 **734,334 字节**）是**独立 chunk，不在首屏关键路径上**，
  且外面还包着 try/catch —— 取不到就静默降级。

**所以「代价」的正确问法不是「要不要引入 three」（已经引了），而是「新组件是继续挂在 LandingPage 这一个懒加载点上，还是会把 three 拉进第二个页面」。** 前者边际成本≈组件自身；后者才是新增一整个 chunk 的入口。

⚠️ 我自己第一遍 `grep "from 'three'"` 是**零命中**，差点写成「three 是死依赖」——
是第二遍换写法才抓到 `await import('three')`。**同一个坑，同一晚踩了两次**（另一次是上面的 Yosemite）。

### 判定

**✅ 采纳（有条件）**：作为**学习资料 + Community 组件的取用源**。
**不采纳**的是「买 Pro 然后抄」——那是一笔钱和一次决策，归 Andy，不归我；且我们连
「3d 特效放在哪个页面」都还没定，先买等于先付款后立项（MVP 闸）。

**给前端 UI 线的三句可执行的话（已列门铃）**：
1. 只取 Community 组件，**保留每个组件自带的 attribution/notice**；Pro 的源码一行都别抄进仓库。
2. 新的 three 内容优先挂在 `LandingPage` 已有的那个懒加载点上，别在第二个页面新开 `import('three')`。
3. 要买 Pro 之前先回答「它两周内对外发布什么」（宪法 MVP 闸）——答不出就进 NOW.md 停车场。
