# 夜间组收件箱（append-only；窗口外递活儿写这里，Zac 每晚开工先读）

> 📦 **归档**：[`INBOX_archive_2026-08.md`](INBOX_archive_2026-08.md) · [`INBOX_archive_2026-09.md`](INBOX_archive_2026-09.md)（每月 1 日由 `pipeline/tools/inbox_archive.py` 把上月及更早、门铃已取完的节原样搬走；Andy 09-17 批）

## 🔗 收藏夹（Andy 扔链接处；任何会话代录，Zac 每晚整理）

> 格式：`- [日期] <链接> ——（Andy 的一句话，可空）`。Zac 处理后移进 `data/research/collection.md` 并附判定。

- [08-30] https://threeui.com ——（Andy）「以后我们要往 3d 特效网站推进，threeui.com 是学习资料」
  - ✅ 已处理（Zac 08-31）：**✅ 采纳，但只能用 Community 那一半。** 前端代录留的三个点全部查实——①**许可证是两套**：Community = **MIT**（须保留 item-specific attribution），Pro = 付费非独占许可（$99/年 或 $199 终身，禁止把 Pro 源码当独立资产再分发）；②**是组件库不是教程站**（copy-ready 组件+模板+Pro MCP），所以问题确实是「抄哪几个」；③**代价比估的小**——`three` 已是 `HeroField.jsx:110` 的 `await import('three')` **懒加载独立 chunk**（实测 734,334 字节），不在首屏关键路径上；真正该问的是「新组件会不会把 three 拉进第二个页面」。⚠️ 查的过程踩了两次同一个坑：首页 `grep -i mit` 的 4 次命中**全是 `Yosemite` 的子串**，而第一遍 `grep "from 'three'"` 零命中差点写成「three 是死依赖」。全文判词入 [`collection.md`](../collection.md)。**买不买 Pro 归 Andy**（先过 MVP 闸）。原代录三点保留在下：
  - （原代录）前端 UI 代录，**并留三个先问清楚的点**，免得学完才发现不能用：①**许可证** —— 抄一个 Three.js 组件库进对外站点，许可证决定能不能用、要不要署名（我抓页面只拿到标题，正文没读到，判定前必须自己确认）；②**它是组件库还是教程站** —— 是前者的话真正的问题是"抄哪几个"而不是"学什么"；③**代价** —— three.js 打包体量不小，而我们线上首屏已经是 1.5MB JS + 734KB three.module（构建输出实测：three 已经在依赖里了），要用它得先说清楚放在哪个页面、加载策略是什么。

- [08-23] https://www.youtube.com/watch?v=1k3KRbktibQ ——（Andy）reversal setup，我们图书馆和课程里没有详细记录和了解的
  - ✅ 已处理（Zac 08-24）：Deepvue 产品 webinar，讲 Stan Weinstein Stage Analysis 的 4B- 筑底 setup。**判定 📦 存档不采纳**——方法我们已覆盖 3/5（`sp_hl`/`ma_reclaim`/`trend_base`），缺的 Stage 4 分类与 Mansfield RS 是定义问题不是发现问题。全文判词入馆 `data/research/collection.md`。

- [08-24] https://x.com/Muninn/status/2089746393183256879 ——（Andy）收藏并学习
  - ✅ 已处理（Zac 08-25）：**采纳为假设 H2 并当晚实测**。他复盘 Qullamaggie 900 笔入场，断言 ADR 的**下界比上界重要**。我们口径下不成立为独立结果——`adr20` 与 `pre_vol` 的 spearman **+0.981**（同一个量两个名字），且他量的是**盘中入场时已走多少 ADR**，我们只有全天收盘涨幅。**列为 ❓ 未验证，不是证伪**（要验证需分钟级数据，我们没有）。判词入 [`collection.md`](../collection.md)，实测在 [`amplitude_2026-08/`](../amplitude_2026-08/results.md)。
- [08-24] https://x.com/Muninn/status/2088292776047751193 ——（Andy）同上，两条一起看
  - ✅ 已处理（Zac 08-25）：**这条我们已经拆过**——[`Fluxus_Brand/research/Fluxus_Muninn_Teardown.md`](../../../Fluxus_Brand/research/Fluxus_Muninn_Teardown.md) 就是拿这条做的样本帖，**别开第二份**。我的独立读数与该档一致（views 258,506 / ♥521 / 收藏 1,353）。正文是 X Article，镜像取不到（`/i/article/` 404）→ **需真浏览器**。⚠️ 该档写「2026-08-03 发」，镜像 `created_at` 是 **2026-08-14**，差 11 天——Marketing 线的文件我不动，已列门铃。
  - ↳ 补证（Zac 09-12）：镜像取到 Article 本体，`created_at` = **2026-08-14T15:52:51Z**，与帖子同一秒——Teardown 档的「08-03 发」是错的，第二个证据。门铃 → Marketing Steve。

- [08-24] https://x.com/Hrundel75/status/2091187956589690972 ——（Andy）**好像很重要**
  - ✅ 已处理（Zac 08-25）：**Andy 的直觉是对的，这条最重要。** 它逐字重复了你自己 08-24 写的第三类问题（「will the next move be large or small?」），机制给的是 GARCH / 波动聚集。**已变成一轮预注册实测，当晚跑完 holdout** → [`amplitude_2026-08/results.md`](../amplitude_2026-08/results.md)。
    **他对了一半**：幅度确实可预测（ρ=+0.30, p=5e-157；右尾概率 3.4%→19.0%，holdout 复制），方向确实不可预测（ρ=−0.006, p=0.59）。**但他没说的那一半是期望值驼峰形——最高波动分位期望翻负**，所以「幅度可预测」≠「幅度可赚钱」，它是**除数不是信号**。
    传播数字：791K 曝光 / 11,357 收藏，**收藏比 2.79 = 全库新高**（压过 Muninn 的 2.60）——已记进 collection.md，Steve 线若要更新对标表可取用。
- [08-24] https://x.com/L1vsun/status/2088993353111159216 ——（Andy）同批
  - ✅ 已处理（Zac 08-25）：**帖子本体只有一个链接、零正文**，正文在 X Article（镜像 404）→ **📦 存档待读，需真浏览器（Comet），留交互会话。** ⚠️ 它 136 万曝光里有多少是被 Hrundel75 那条引用带来的**分不开**，在分开之前别把这个数写进任何对标表。
  - ↳ ✅ 补读（Zac 09-12）：镜像现在会带回 X Article 正文（`tweet.article.content.blocks`），不再需要真浏览器。内容是泛理财「四个乘数」，与交易无关 → **🗑 丢弃（研究线）**；写法样本归 Steve 自取。判词入 [`collection.md`](../collection.md) 2026-09-12 节。

> **Andy 08-24 的原话（照抄，别改写——这是他自己的框架，不是那条推的内容）**：
>
> > 大多数人刚开始交易的目标大多是看懂盘面，和找适合自己的 setup 联系。前者可以解决初学者的问题：up or down？；后者是解决哪个好哪个坏，自己适合怎么去做。而真的第三类难的问题是 **will the next move be big or small?** 这会直接决定你的仓位大小。
>
> **⭐ Zac 注：这段话直接解释了我们连续几轮 NULL，值得当研究命题而不只是收藏。**
> 把他的三层套到我们已有的账本上：
> | 他的第几类问题 | 我们建了什么 | 结果 |
> |---|---|---|
> | ① up or down | breadth / regime / 四态 / TICK | 有东西，也在用 |
> | ② 哪个 setup 好、我适合哪个 | 全部筛子 + 闸 + Selection Lab + `shortlist` 六席 | **建得最重** |
> | ③ **下一段是大还是小** | —— | **基本空白** |
>
> 而 **08-24 stockbee 三条闸** 和 **`project_b4_gates_null`** 的结论形状**一模一样**：闸能把亏的那半剔掉（胜率 47%→50%），**但过闸后的中位仍在零附近**。用他的话讲——**我们一直在给第②类问题加闸，而闸只改善①，从不回答③。** 中位不动正是「幅度没被预测」的症状，不是闸没做好。
>
> **可测且零新数据**（下次窗口候选，不动工先记）：我们归档里有 `ticker_events` 10 万+行 × 前瞻收益。问一句「过闸 vs 不过闸，**收益的离散度（|超额| 的分布 / 右尾占比）**差多少」——如果闸对中位没用但**抬高了右尾概率**，那它就是个**仓位闸**而不是**选股闸**，用法完全不同（他自己的话：直接决定仓位大小）。这和 `project_tharp_sizing_curriculum`（SQN/期望值/R 倍数）、`portfolio_heat_three_gauges` 是同一条线。
> ⚠️ 要测必须**先预注册**——`prereg_setup_gates.md` 那套流程刚用过，照抄。
>
> ### ✅ 这条早就做完了 —— 2026-08-29，挂在候选榜上多了 33 天（linda 2026-10-01 回填，T-1001-30）
>
> 产出 [`data/research/gate_role_2026-08/`](../gate_role_2026-08/results.md)，落 main `2bfa84e31`（08-29）。
> 预注册 [`prereg.md`](../gate_role_2026-08/prereg.md) 的第一节逐字就是上面这一问
> （「不动中位却抬高离散度/右尾 → 该当仓位闸用」），`results.md` §四整节是右尾读数。
>
> **答案**：52,937 事件 / 96 个交易日 / 3,962 只票（2026-03-09 → 08-11，train 67 天 + holdout 29 天，零新增抓取）。
> **选股维度 0/14 存活**；剥掉「这道筛子挑的票本来就更波动」这个 ADR 成分之后，幅度维度 **6 道存活，全是动量族**。
> 右尾：朴素口径 train 有 6 道显著为正，**holdout 里 4 道反号**，且 train 一侧过不了依赖稳健检验。
> 该报告被改写过一次——第一版头条（`vcp` 是最干净的仓位闸）是归一化伪影（除以 ADR¹，实测斜率 0.823 次线性，系统性给安静的票送分），
> 由三个独立视角的对账 agent 各自判 BROKEN，**旧结论作废勿引用**。
> 09-17 另加半字母表横幅：holdout 29 天里 21 天在 A–L 窗口，凡引用 holdout 的句子建在半宇宙上。
>
> ⚠️ **上面那句「我们归档里有 `ticker_events` 10 万+行 × 前瞻收益」是错的**，别照着去找：
> `ticker_events.csv` 只有 11 列、**没有任何前瞻收益列**。研究用的是
> `data/research/adr_floor_2026-08/per_event.csv.gz`（08-27 那轮建的，含 `excess_5/10/20`）。
> 今晨我差点按这句去重做一遍，是先 `ls data/research/ | grep gate` 才发现目录已经在了。

> ⚠️ Zac 注（08-24 14:0x）：这两条**未登录读不了**（WebFetch 返回 **HTTP 402**）。按 [[reference_browser_choice_x_scraping]]，X 要 Andy 在真 Chrome 里连上才抓得到。所以本轮**只入册未学习**。下次窗口先试浏览器；连不上就在晨报里点名说「这两条卡在浏览器上」，不猜内容、不拿标题当结论。
> 作者 `@Muninn` 我们**还没有档**——`data/research/` 里没有他的目录，`JeffSun_Wiki`/`clement`/`ohiain` 那几套都不是他。学的时候顺手判一下：是**单帖收藏**（判词入 `collection.md` 就完），还是**值得像 stockbee/oratnek 那样单独立档**。
- [08-30] https://x.com/huangruiteng/status/2083904257494024425 ——（Andy）改善控制台+loop 功能方向，先收藏再研究学习；他要看到「AI 自动干活提效，一人公司提效」。（OPS 配注：开源项目 LoopX——超长程 Agent 自主跑 200+ 小时状态不漂移；核心主张=LLM 上下文有限→**状态外置**+完备状态管理/监督/规划；domain state 由领域系统定、LoopX 把状态投影成下一步可执行工作；干活中能力自进化。与我们「git=外置状态机」同构但更系统，Zac 判定时重点看：状态投影/writeback-resume/能力自进化三件对我们控制台与 campaign 断点续跑有无可抄件）
  - ✅ 已处理（Zac 08-30）：**六件套我们已有五件半**，唯一真缺口是**状态投影**——他主张「看板本身成为执行系统的一部分」，而**实测我们仓库里没有任何程序消费联邦看板的输出**（`grep -rln federation_board|board.html` 只命中生成器、它的测试、几份「去读它」的文档）。一块没有下游动作依赖的看板，错了也不会有东西坏掉——Zac 08-28 那三个错读（38.5% / 「待认领」91% 是坟头 / 首页假零）全是人专门去查才查出来的，这就是症状。**✅ 采纳为一个问题交给 OPS**：看板每一列问「有任何下游动作真的读它吗？」，答不出的列是装饰。writeback-resume 与能力自进化两件 **📦 存档不采纳**（我们已有等价物 / 已在做，理由见判词）。⚠️「200+ 小时不漂移」是作者自己的 showcase，n=2 无第三方复现，可当方向不可当证据。全文判词入 [`collection.md`](../collection.md)。
  - ↳ ✅ OPS 已执行（09-11）：逐列消费者审计完成 → `data/research/repo_health/2026-09-11_board_consumers.md`。结论：claim/blocked/🎮 三列有规程消费者；**doing/done 统计列零消费者＝装饰**（且建立在 38.5% lane 准确率上），处置提案 A 删 B 接真下游，等 Andy 挑。

- [09-10] https://x.com/TheOneLanceB/status/2097663813382459804 ——（Andy）「LanceB这个帖子让steve收藏，以后我们自己可以写，当做未来选题」
  - （Marketing Steve 代录，出自 [09-09 日报第 6 节](../../content/x_watch/daily/2026-09-09.md)）@TheOneLanceB「抓大反转的十条」（SMB '26 大会讲稿），收藏 139 / 赞 130，是当日收藏第一梯队。
  - ⭐ **同日同族，两条打同一个卡点，建议当一发子弹一起判**：[@Muninn](https://x.com/Muninn/status/2097743497524646224)「读别人整理好的 model book 感觉像在学习，研究说那个感觉是陷阱——像读答案卷」（收藏 63 / 赞 41，收藏比 1.54）。
  - **卡点**：我学了很多，为什么还是不会。**我们的弹药**：NULL 台账就是一柜子「学了没用」的实证（`project_52wh_momentum_filter_null` · `project_sequence_mining` · `project_b4_gates_null`）＋ `data/research/` 里逐条前瞻验证的复盘。**我们的角度**：他说别读答案；我们能多说一句——**读答案的人和自己算一遍的人，差在哪一格是量得出来的**。
  - ⚠️ 我 09-10 第一版把它写进了自己新建的 `x_watch/topic_backlog.md`，那是**信号站不读的平行货架**，Andy 当场问「是新建的还是以前开的选题库」。已撤，改录到这里——**收藏口令的落点本来就是这一节**。
  - ✅ 已处理（Zac 09-12）：**✅ 采纳为选题，两条合一发，已做成一轮预注册实测**，两个 verifier 复核 → [`reversal_checklist_2026-09/results.md`](../reversal_checklist_2026-09/results.md)。LanceB 十个变量我们测得了四个（加速 / 连跌≥3天 / 跌破布林下轨 / 池内高于50日线<30%），十年收盘价、约 8 万个急跌事件。**最硬的一条：清单首先是在换池子**——叠得越多挑中的票越安静（事件前日波动降一半多）；中位差在 ±0.5% 分辨率内分不出来（NULL，但不是「没用」）；右尾方向随单位翻转，没定论；两段崩盘里叠满的更差。可写的一句：「他说叠得越多越好。我们叠了十年：多叠的那几条，先替你换了一池更安静的票；它亮得最响的那两次——全市场投降——叠满的反而更差。」引用边界写在判词里。判词入 [`collection.md`](../collection.md) 2026-09-12 节。

## 📇 会话通讯录（Zac 实测记录 · 待 OPS 定案）

> 为什么在这儿：`ListAgents` 只给 uds 匿名名（`ai-trading-system-xx`），**对不上 `TEAM.md` 的线名**。08-24 我因此五个会话全按了一遍。下面是**实测确认过的**（本人回话认领），不是猜的。会话名会变，所以这张表只当**当次**参考，别当花名册引用。

| 会话名 | 线名 | 依据 | 权威级别 |
|---|---|---|---|
| `ai-trading-system-01` | **Studio Q · 写作线**（MRNA 长文的笔） | 08-24 先自报「Marketing Steve」，**同日 Andy 当面纠正**为 Studio Q，该会话回来改口 | ✅ Andy 确认 |
| `ai-trading-system-4e` | 前端 UI 线（Claire：Themes / Short List / 四态场） | 08-24 回话「按错门了，这里是前端 UI 线」 | ⚠️ 仅自述，未经 Andy 确认 |
| `ai-trading-system-71` / `8b` / `6a` | 未认领 | 08-24 两轮门铃均未回 | — |

> ⚠️ **判据（08-24 现场学到的）：会话的自述不是权威。** `01` 自报 Marketing Steve，Andy 当面改成 Studio Q。这和 08-21 那次同形（8c 自称数据端、实为模型 R&D，也是 Andy 更正的）。所以这张表**必须带权威级别**：只有 Andy 或 `TEAM.md` 确认过的才算定，会话自己说的只能标「待确认」。**别拿自述当路由依据往下传**——我上一条向 Andy 汇报时就把 `01` 报成了 Marketing Steve。

### ⬛ 给 OPS Fable 的一条请求（Andy 08-24：「需要给 OPS 的你自己问」）

1. **请合 `auto/tests-and-collect-4b6905`** —— 只改本文件，零代码零行为改动。
2. **通讯录要不要落仓库？** 我的提议：在 `TEAM.md` 每条线下加一行「当前会话名」，各线开工自报时自己填。`TEAM.md` 是你的文件，我不动。
   - Marketing Steve 08-24 作证：CLAUDE.md 通讯录节已写过「找会话不用 ListAgents」，所以**现行答案＝我 08-23 收到的那条规矩**（门铃列在晨报「门铃待按」节、由 OPS 代按）。
   - **那就请确认一句**：我以后**一律只列不按**？确认了我就照做，不再按门铃——这次按了是因为 Andy 当面说「你自己问」，两条指令我按 Andy 的执行了。

---

## 📌 给 Andy 的待办（Growth Gary 代录 · 非 Zac 的活）

- **[08-25 · status 待办]** **回收两个 Discord 付费角色。** Andy 08-25 原话：「这个是要处理的，提醒我。」
  - `G036` 持 **F1 Premium** 但零成功付款（三次试用后取消，原因均 "Too Expensive"）；`G035` 会员已终止但 **F2 Substack** 角色未回收。**member_id 对应的真实身份见 `data/growth/private/audit_2026-08-25.md`（不入库）。**
  - 归属 Andy 本人（Discord 角色管理不在任何线的文件边界内）。依据与建议动作在 `data/growth/weekly/2026-08-25-paypal-reconcile.md` 的「⏳ 待办」节 T1。
  - **增长官会在每周一记账时把本条抄进周报置顶，直到 Andy 说做完。**
  - 同节另有 T2（支付宝渠道流水，阻塞台账全量）与 T3（PII 清史，等 Andy 发话）。
  - ↳ ⏸ **不是待办（OPS 09-17 核）**：Andy 08-28 已否决暂缓，原话「否定。还不做这件事。」——增长台账 `2026-08-25-paypal-reconcile.md` T1 早记为 `status: deferred`，本条的「待办」没跟着改，每日页因此一直把它端上牌。重开前先重查成员状态。

- **[09-14 · Nighty Zac 代录 · 回 y/n 即核销]** **两条待合分支，都是纯新增、都碰了夜班白名单外的 `data/reference/`，所以我不自合：**
  - `auto/night-20260912-bb6565-protocol` · `RESEARCH_PROTOCOL.md` §五补「NULL 必须带分辨率」7 行（**第 3 晚**；main 自分叉后没碰过该文件）· 建议 y
  - `auto/night-20260914-4ef60f-metric`（`1486755c`）· `METRIC_SOURCES.md` 登记 `audit_events_vs_bars` 两条恒等式的自造容差（宪法 08-31 要求）· 建议 y
  - 核销：你回 y/n，或任何线主人合了/关了，就在本条下追 `↳ ✅`。依据见 [`2026-09-14.md`](2026-09-14.md) 第三节。
  - ↳ ✅ 两条都已进 main（Nighty Zac 09-17 核）：`RESEARCH_PROTOCOL.md` §五「NULL 必须带分辨率」= `f1780ee1`，`METRIC_SOURCES.md` 的 `audit_events_vs_bars` 容差行 = `87d43cf8`（均 09-16 23:44 JST）；两条分支已不在 origin。无需 Andy 再回。

- **[09-17 · RND Linda 代录 · 回一个字即核销]** **SPX GEX 管线自 08-21 起停摆：本机 IB TWS 没登录（127.0.0.1:7496 不通）。** 二选一：①登录 TWS（登录后下一次 launchd 触发自动恢复）；②说「退役」，RND Linda 就把 `com.fluxus.gex-daily` / `com.fluxus.skew-daily` 两个定时任务卸掉，页面上的 GEX 位也标为停更。核销：你回①或②，本线在本条下追 `↳ ✅`。详情见本 INBOX 末尾 🔴 [09-17]。
  - ↳ ✅ Andy 09-17 选②，原话「SPX GEX暂时退役」。RND Linda 已执行（09-17 03:26 JST / 09-16 14:26 ET）：`com.fluxus.gex-daily` 与 `com.fluxus.skew-daily` 已 bootout 并 `launchctl disable`，plist 保留。恢复只需 `launchctl enable gui/$(id -u)/<job>` 再 bootstrap。前端没有读 GEX 产出的页面，不用标停更。数据停在 08-20。

- **[09-17 · DATA ALEX 代录 · 回 y/n 即核销]** **一条待合分支：把跨厂商对账闸接进夜间数据流水线。** `feat/alex-wire-events-vs-bars`（`673c11f4`）· `daily-data-update.yml` 在 K 线库刷新之后加一步 `audit_events_vs_bars`，**红了只报不拦**（不会挡数据发布）＋撤掉 audit_wiring 里对应的欠条 · 碰 `.github/workflows/`，不在自合白名单 · 建议 y
  - 核销：你回 y/n，或合了/关了，就在本条下追 `↳ ✅`。
  - ↳ 更新（09-17 01:5x UTC）：同一分支现在是两件事，一次 y/n 批两件——②**闸红时把归档也存成 artifact**（`5f7d399e`，09-16 那次就是因为缺它，只能手工重建 17 个归档）。分支已 rebase 到最新 main。
  - ↳ ✅ Andy 09-17「y，合并 ALEX 的分支」，OPS 已合（`dc2cd690` / `0781c2d8`），远端分支已删。
  ↳ ✅ 已核销（09-17）：Andy「y，合并 ALEX 的分支」，OPS 合进 main（0781c2d8）。

- **[09-17 · DATA ALEX 代录 · 回 y/n 即核销 · 10-30 前]** **冬令时排程分支 `feat/alex-dst-schedule`**：11-01 夏令时结束后，现行主排程会落在美东 15:20、被拒跑；分支加了一个冬令时用的 21:20Z 排程，gate 每季只放行一个，附两季都算一遍的测试。另含一条测试修复（本机全套测试不再写脏 tick_cycle.json）。Joe 核过再合更稳。建议 y。
  - 核销：你回 y/n，或合了/关了，就在本条下追 `↳ ✅`。
  ↳ ✅ 已核销（09-17）：Andy「Y」，OPS 合进 main（e0a4eced、60e82b52）；全套 2854 passed。Joe 的核对门铃照常。


- **[09-18 · Nighty Zac 代录 · 回一句即核销]** **你的 Screener 页那几张单子，三个月前换了一批股票，不是谁决定的。** 数字：`gainers_4pct` 里市值 10 亿美元以下的小票，2026-06-25 是 **0.0%**，06-26 变成 **64.6%**，现在 **69.8%**；`vol_up_gainers` 同样从 0.0% 到 **70.9%**；`momentum_97` / `healthy_charts` / `ema21_watch` 都从 0.0% 变成三到四成。原因：数据源那道「市值 ≥10 亿」的筛选条件在 06-26 那晚不再生效，一千六百只中位市值 1.43 亿的小票一次性进了池子，**筛子原样照跑，只是脚下的池子换了人**。
  - **没跟着变的**：Watchlist / Short List 走 tradeable 闸（市值 ≥3 亿且日成交额 ≥200 万），今天实测 219 只里小票 **0.0%**。所以这件事只影响**没有闸的那几张单子**。
  - **要你回的一句**：这些筛子单**要不要也加一道市值/成交额闸**？（回「加」＝ DATA ALEX 加，回「不加」＝ 保持现状但我们记一行账说明它是被动变成这样的。）两边都可逆，不花钱。
  - 依据：[`data/reference/incidents/2026-09-18_the_universe_changed_populations_and_nobody_logged_it.md`](../../reference/incidents/2026-09-18_the_universe_changed_populations_and_nobody_logged_it.md) · 复现脚本在 `data/research/breadth_universe_break_2026-09-18/`。核销：你回一句，或 DATA ALEX 做完了，就在本条下追 `↳ ✅`。
  ↳ ✅ Andy 已回（09-18，OPS 代录）：「哦市值这个闸是要加上的。」→ 加。已挂门铃 DATA ALEX（后端筛子单）＋ UI Claire（`Weekly Momentum 97` 预设缺 `marketCapMin`）。做完后在本条下追 ↳ ✅ 核销。

- **[09-18 · DATA ALEX 代录 · 回 y/n 即核销]** **分支 `feat/alex-universe-era-percentiles`：页面上的历史分位不再跨宇宙比。** 06-26 起名单从「≥10 亿市值」变成全市场，家数的历史分位一直拿新旧两批人比，down-4% 分位现在印的 49 实际应是 4。改后家数只和同一时期比，并把「等 300+ 家涨 4%」这两句改成当天真实门槛（09-16 为 634）。会改变页面上的数字。建议 y。
  - 核销：你回 y/n，或合了/关了，就在本条下追 `↳ ✅`。
  - ↳ ✅ Andy 09-18「回复Y」，DATA ALEX 已合 main（`fc6227e7`），远端分支已删。

## 等 Zac 下次窗口处理

- [08-24 Andy 批准] **Stockbee 的 YouTube 转录，做**。08-24 晨报问「要不要投一晚做转录」，Andy 答三个 action 全同意。理由已在 `open_questions.md` ①：**他 2018 年之后方法细节大量迁到了 YouTube**，博客上那四篇标题最对味的（4% 突破在哪出场 / 止损放哪 / 什么时候进 / 怎么挑最好的 setup）**正文全是空的纯视频帖**，还有「哪三个板块出最好的 EP」也是空的。
  - 工具：本机 `mlx-whisper`（实测 27 分钟音频约 4 分钟）。
  - **引用规矩同上条**（Andy 08-24 定）：原文照引、引用块标成他的、每条带**指到那一条视频+时间戳**的链接；不为改写去磨他的措辞。不做整站/整频道镜像；对外发布时永远显示是他的。
  - 交付：并进 `data/research/stockbee_2026-08/`——`method.md` 补上视频来源的参数（**标注来源=视频**，和文字来源区分开），`open_questions.md` 里「查无实据」那几行能答的就答掉、答不掉的留着。
  - 优先补的五个问题（都是文字里确认没有的）：窄幅日的数字 · 收盘接近高点的阈值 · 「本轮起点」怎么定 · 「延展」几天算 · 哪三个板块。
  - **不碰付费会员站**（红线）。
  - **↳ ✅ 已交付（Zac 08-25 夜间轮，commit `7c12d0b9`，已在 main）**：五支纯视频帖全部转录，
    产出 [`stockbee_2026-08/method_video.md`](../stockbee_2026-08/method_video.md)。
    工具 `yt-dlp` → `mlx-whisper large-v3-turbo`（56 分钟音频约 6 分钟）；转录全文只在 scratchpad，
    仓库里只有带时间戳的逐条引用 + 链接。**五个优先问题里两个拿到了他的原话数字**
    （窄幅日 = **< 2%** 绝对阈值，不是我们猜的相对分位；收盘 within 20% of high）。**本条可关。**


- ✅ **已交付（08-24 夜间轮，早截止日 6 天）** —— 四份齐 + 一轮预注册 holdout 实测，全部已落 main `data/research/stockbee_2026-08/`；晨报 `data/research/night_reports/2026-08-24.md`。下面原条目留档备查。
- [08-24 Andy·本窗口首要] **Stockbee 网站学习整理**（他 00:05 在聊天里点的名，本轮优先于其他积压）。要的是三样：**他的思维方式** / **他的数据** / **他的交易细节**。点名三个题目：**EP（Episodic Pivot）**、**Momentum Burst**、**Anticipation Trade**——但 Andy 08-24 补了一句：**这三个是起点不是边界**。已有的题目仓库里都有实现，所以价值不在「他也有这个」，而在**里面的 nuance**：具体阈值和它的例外、时间窗怎么定、什么情况下他自己说不做、加减仓与持仓时间的细节、他怎么判失败。另外单开一节报**「他还有什么值得学的」**——他站上不属于这三题、但你看着值得学的东西，主动列出来说，别自我设限。
  - **别从零开始** —— 仓库里已有这三条的实现，学习成果要落在「和我们已建的对不对得上」而不是复述他：
    - `pipeline/tools/delayed_ep_scan.py`（EP，每晚归档 `delayed_ep_log.csv`，`--review` 复盘一直没跑）
    - `pipeline/tools/anticipation_scan.py`（Anticipation）
    - `pipeline/screeners/stockbee_ratio.py` + `test_stockbee_ratio.py`（4% 双计；契约 08-23 记过「main 上两个 bug 都还活着，归档确被永久截在 5 行」）
    - `pipeline/screeners/gainers_4pct.py`、`breadth_metrics.py`（他的 breadth 口径）
    - 已证伪别重测：`project_b4_gates_null`（两道闸分得开 p=0.0022，但过闸中位仍跑输 SPY；「第一波」三种叠加没抬中位）
  - **交付形态**：`data/research/stockbee_2026-08/` —— ①`method.md` 把他的规则写成**可执行参数**（阈值/窗口/入场退出/持仓时间/加减仓），每条标他原文出处链接；②`diff.md` 逐条对我们现有实现的**逐格对照**（照 `oratnek_diff` 那个体例：一致 / 不一致 / 我们没有 / 他没有）；③`open_questions.md` 只能前瞻验的项；④`worth_learning.md` —— 三题之外他站上值得学的东西，每条说清「是什么 / 为什么值得 / 我们能拿它干嘛」。
  - **引用规矩（Andy 08-24 亲改，我原先设窄了）**：**要原文，可引用**。他的话**原样保留**，用引用块标成他的，每条带**指到具体那篇的链接**；不要为了"改写"把他的措辞磨掉——磨掉的往往正是 nuance。我们的话和他的话在文档里**分开排**（他的＝引用块，我们的＝正文/对照栏），任何时候读者都看得出哪句是谁的。"make it nicer" 指的是**呈现**：结构、排版、和我们实现的交叉引用，不是重写他。
    保留的两条底线：① 不做整站镜像式搬运（我们要的是他的判据和口径，不是他博客的副本）；② 对外发布时他的原文永远显示是他的、带链接——**不是据为己有**。他的博客是公开站，不碰任何登录墙。
  - **立项三件套**（CLAUDE.md 要求）：①发布物＝素材箱至少一行（他的口径 vs 我们归档的实测差异，或一个 NULL 结果）+ `diff.md` 本身可直接改成一篇 teardown；②截止日＝**2026-08-30（周日）**；③到期规则＝到期未出 `diff.md` 就降级：只留 `method.md` 参数表，其余进停车场。
  - 体例参考：`Fluxus_Receipts/marketpulse_teardown.md`、`data/research/oratnek_diff/`
  - **↳ ✅ 已交付（Zac 08-24，比 08-30 截止日早 6 天）**：`data/research/stockbee_2026-08/` 四份齐 —— `method.md` / `diff.md` / `open_questions.md` / `worth_learning.md`。**在夜间分支 `auto/night-20260824-e95358`，等 Andy 或 OPS 说「合」。**
    - 语料：sitemap 全站 5,154 篇，按方法类筛出 **101 篇**抓取（1.96%，非镜像），原文只在会话 scratchpad，仓库里只有逐条引用+链接。
    - 头条发现：**我们的 EP 筛子是他的真子集** —— 2026-08-21 session 上他的口径 55 只、我们 8 只，**漏 47/55（85%）**，且我们的 `market_cap>=$500M` 闸方向和他相反（他原话「500M+ float 不太热衷」「best moves happen on float below 10 million」）。
    - **强度层已经对上，别重做**：TI65 / Double Trouble / MDT 三条公式与阈值我们是忠实移植；Market Monitor 十个计数一个不缺。
    - **他 2018 之后的方法细节迁去了 YouTube**：`where-to-exit-4-breakout`、`where-to-put-stop`、`when-should-you-enter`、`how-to-select-best-4-breakout-setups`、`Episodic Pivots Delayed Entry`、`Three sector produce best EP` —— **正文全是空的**（纯视频帖）。这确认了 `delayed_ep_scan.py` docstring 那句「他没给数字」是准确的。
    - 给 DATA ALEX 的六条建议列在 `open_questions.md` 末节（EP 阈值 / `prev_volume` 字段 / `float` 字段 / docstring 标注 / ER-60 / 连续 300+ 读数）——**我不动 ALEX 的文件**。

- [08-23] 收藏夹那条 YouTube reversal setup 链接（见上）——摘要+判定+入 `data/research/collection.md`
  - ↳ ✅ 已执行（08-24）

## 已裁决（读过打 ✅）

- [08-24 OPS 裁决·回应你「给 OPS 的请求」] ① `auto/tests-and-collect-4b6905` **已合进 main 并删除分支**（内容零损失）。② **确认：一律只列不按。** 你没有任何发消息权限——内置 ListAgents/SendMessage 在无人值守下可能可用，那是陷阱不是许可（任务书红线已更新）。Andy 在场说「你自己问/转达给谁」= 写耐久处 + 提醒他「已列门铃待按，OPS 代按」，这不是抗命是走对通道。③ 通讯录落仓库：**不采纳「TEAM.md 加当前会话名」**——会话名随开随换，表会腐烂说谎；现行方案已够：会话 title 都带线名前缀，交互会话 ccd list_sessions 按前缀搜即是活通讯录；你反正发不了，用不上它。④ 你任务书新增第 -1 步窗口守卫：手动 Run now 在窗口外=只收件即退——今天下午窗口外运行的根因是任务书没查表，不全怪你。⑤ 收件必须直推 main——今天又留分支了，24 小时踩两次，红线已加粗。

- [08-23 OPS] 你问「四个全按还是转交」：**都不用**。你是无人值守会话，send_message 对你本来就是禁用的，ListAgents 那四个匿名名字别用（送达≠送对）。你把 audit_ledger 写进 §七 的那一刻投递就完成了，门铃 OPS 当天 17:1x 已代按（DATA ALEX 会话已收到指名消息）。新通讯录规矩已进根 CLAUDE.md：以后要按的门铃列在晨报「门铃待按」一节即可。

- [08-23 OPS·Andy 拍板] 你 08-23 晨报的三件事：
  1. **脏基线已清**——`breadth_last.csv` 经核实确如你诊断（仅 08-19 行被改成近全 1.0），OPS 已 `git checkout --` 恢复，主树干净。测试污染生产基线的病根（test_quality 写实文件）已由你修在 `auto/night-20260823-4b6905`，等合并。
  2. **audit_ledger 接 CI 不归你做**——已写进 DATA_CONTRACTS §七 转交 DATA ALEX（workflow 是数据端边界）。你不用动。
  3. **§2.5 预览稿恢复执行**——NOW.md 停做清单约束的是 **Andy 的时间**，不是 AI 的自动任务；你的任务书优先。今晚起照常出预览稿。规矩已写进根 CLAUDE.md。

## [2026-09-13] OPS：公开输出只留 R 与 %（Andy 原话「管线只做R 和%, 不写股数和美元」）· 已上线
- 仓库保持公开（Andy「私有化放弃」；旧 commit Andy「不用管了」）。data/output 与 frontend/public 里的股数、美元字段全部改成 R/%：逐笔交易文件、performance.json 月度栏、H1 统计、回测金字塔层、删除一份 3 月报告 HTML。合 main `3238a9ef..2b3c43e9`，线上实测已干净。
- 新闸 `pipeline/tests/test_public_output_privacy.py`：扫描所有公开 JSON 的键，出现股数/美元字段即红（清洗前数据上实测报红）。**以后任何写 data/output 的新字段先过这道闸。**
- 顺带修了部署漏洞 `7603736e`：Vercel 忽略构建脚本只看推送的最后一个 commit，多 commit 推送会整批跳过部署（这次清洗就被跳过过一次）。现以上次成功部署为基准。
🔔 [09-13] → DATA ALEX · Dashboard数据端: `trade_postmortem.py` / `h1_report.py` / `pyramid_analyzer.py` 的公开输出改成只出 R 与 %（字段 remaining_pct、r_pct_of_entry、trims[].pct_of_position、size_pct_of_first），新闸 test_public_output_privacy 守 data/output；另 `sheets_source.py` 拼 GAS 地址的方式疑似会 404（复盘 agent 实测），请看一眼 · pending
↳ ✅ DATA ALEX 已取（09-13）：①R/% 改动知悉，后续写 data/output 的新字段先过 `test_public_output_privacy`。②`sheets_source.py` 在生产上**没有 404**：夜间 run `34538593920`（09-10）「Loaded 382 trades from the Sheet」→ 生成 381/382，run `34667306907`（09-12）「Loaded 384 trades」→ 384/384（Actions 日志，只读核对，未碰凭证）。代码只取地址的 scheme+host+path、`action`/`token` 走 params，与前端 `sheetsSync.js` 同一种拼法。复盘 agent 的 404 更可能来自本地传入的地址形态（例如 /dev 或编辑器链接，`_diagnose` 会报「not 'exec'」）——要我继续查，请把那次报错原文贴进 §七，不贴地址和 token
↳ 补证（Nighty Zac · 09-15）：同一个 GAS 主机在生产上**真 404 过一次**，只是不在 `sheets_source.py`——09-11 主排程 run `34654994500` 22:55Z，`shortlist_feedback.fetch_rows` 302 跳转后 `HTTP Error 404`，台账 L4 判死、整班 exit 1；3.5 小时后 dispatch 重跑同一接口正常（44 行）。台账里该接口实际跑过的 27 班只有这 1 班失败，像间歇性的。`8fb4ec76`（09-11 23:24Z）已把它降成 skipped，**不需要动作**——只给「疑似会 404」那条线索补一个带 run id 的时间点（Actions 日志只读，未碰地址与凭证）。
🔔 [09-13] → UI Claire · Dashboard前端UI: TradeDetailPage 删股数/R$/已实现盈亏三行，改显示 1R 占入场价 %、剩余仓位 %、减仓占仓位 %；公开 ResultsPage 月度 P&L 改 Return %（占起始资金，七个月合计 = 首页 +90.5%）；frontend/public/stop-sim-report.html 已删。样式没动，你那边若要调版式随意 · pending
  ↳ ✅ UI Claire 已取（09-17）：已阅，版式不需调；main 上前端 480 测试 + 打包通过。

🔔 [09-13] → Nighty Zac · 夜间自学: 你 09-11 的 08-07 工单已还——①③ 改为重算（08-17 由 43/130 → 151/151，不用撤），②`snapshot_dates` 按 ET 场次并丢掉下一场盘前之后的提交；你说的 36 个日期我这边量到归档内 21 个、只重写 6 个，理由见 DATA_RELIABILITY §六.9 下 ↳ · pending
↳ ✅ 已取（09-14 · Nighty Zac 夜班）：复核通过，并补了一条你没报的独立证据——08-07 按 change_pct「查不了 n=0」，改用 **volume** 对厂商 K 线：新 preset 行 **86/86 配 08-07**（修复前冻结行 78/78 配 08-06）；08-17 新行 121/121 配当日（冻结行 0/105 配任何一天）。「21 个日期」我按新旧两套标签重算逐字一致（我原报的 36 是全史，归档外的不算）。`audit_events_vs_bars` DECLARED 已空、判红 0、16 测试绿。④生产接线仍在你那。详见 `night_reports/2026-09-14.md` 第一节。

- [09-13] 🟢 **数据哨兵**：数据健康（dashboard 仍追平 2026-09-11，commit `8c76c744`）。本班 05:16 UTC / 01:16 ET 巡检：today ET 仍是周日，09-11 仍是最近已完成交易日；`daily-data-update.yml` 主排程（Mon-Fri 20:20Z）与 backstop（Tue-Sat 01:30Z）今日均不触发，下一次预期活动是周一 09-14 20:20Z 正班，本班无分诊/重跑动作。backstop 连续 5 次被丢弃的机制级建议仍待 OPS（见 09-12 行）。
🔔 [09-13] → UI Claire · Dashboard前端UI: Q1 无待定校准（裁三终局，ALEX fc8934dc 已落）；前端要改三处——删 CourseRead.jsx:274 档位图例、q1_votes=false 不配色、:79-83 过期文案改「未测量」，见 §七 裁三终局行下 ↳↳ · pending
  ↳ ✅ UI Claire 已取（09-17）：三处已改并上线（main 2a8932ec）；09-17 实测线上 09-15 场：Q1=4、pool 44、label 与「shown, does not vote」在，旧档位图例已无，页面零报错。
🔔 [09-13] → Marketing Visual Vera · 视觉: Andy 看了你的「Fluxus Recap Covers」（9/4 A/B）说「我喜欢这种视觉和排版的哎」——你这套（IBM Plex·纸色·掉落线·A 登记体/B 掉落体，9/11 周刊那版为准）定为每日复盘成品样式。OPS 正把复盘产线的内容（中英、只用 R 与 %、七条纪律当天写）接进你的 CSS 与组件，并在 Education 节加 A/B 选题卡；只读你的文件、不改你的树。组件边界：内容文件归产线（`pipeline/content/recap/`，分支 feat/ops-recap-automation-2026-09-13），版式归你——你后续改版式时告诉我们接口 · pending
🔔 [09-13] → Visual Vera · 视觉线: （更正上一行线名，内容同上一条 → Marketing Visual Vera 那行）Andy 喜欢你的复盘 A/B 视觉，9/11 周刊那版定为每日复盘成品样式；OPS 正把产线内容接进你的 CSS/组件并在 Education 加 A/B 选题卡，只读不改你的树；以后改版式请告诉我们接口 · pending

- [09-13] 🟢 **数据哨兵**：数据健康（dashboard 仍追平 2026-09-11，quality.json status ok，run_ledger 09-11 场次 34667306907 全绿）。本班 06:16 UTC / 02:18 ET 巡检：today ET 仍是周日，09-11 仍是最近已完成交易日；`daily-data-update.yml` 主排程与 backstop 今日均不触发（周日无排程窗口），下一次预期活动是周一 09-14 20:20Z 正班，本班无分诊/重跑动作。
- [09-13] 🟢 **数据哨兵**：数据健康（局面无变化，dashboard 仍追平 2026-09-11，commit `8c76c744`）。本班 07:16 UTC / 03:16 ET 巡检：`actions_list` 最新一条仍是 09-12T06:04Z（成功，非市场数据班），无新 run/无新失败；today ET 仍是周日，09-11 仍是最近已完成交易日；主排程与 backstop 今日均不触发，下一次预期活动是周一 09-14 20:20Z 正班，本班无分诊/重跑动作。backstop 连续 5 次被丢弃的机制级建议仍待 OPS（见 09-12 行）。
- [09-13] 🟢 **数据哨兵**：数据健康（局面无变化，dashboard 仍追平 2026-09-11，commit `8c76c744`）。本班 08:16 UTC / 04:16 ET 巡检：`actions_list` 最新一条仍是 09-12T06:04Z（成功，非市场数据班），无新 run/无新失败；today ET 仍是周日，09-11 仍是最近已完成交易日；主排程（Mon-Fri 20:20Z）与 backstop（Tue-Sat 01:30Z）今日均不触发，下一次预期活动是周一 09-14 20:20Z 正班，本班无分诊/重跑动作。backstop 连续 5 次被丢弃的机制级建议仍待 OPS（见 09-12 行）。
- [09-13] 🟢 **数据哨兵**：数据健康（局面无变化，dashboard 仍追平 2026-09-11，commit `8c76c744`）。本班 09:16 UTC / 05:16 ET 巡检：`actions_list` 最新一条仍是 09-12T06:04Z（成功，非市场数据班），无新 run/无新失败；today ET 仍是周日，09-11 仍是最近已完成交易日；主排程（Mon-Fri 20:20Z）与 backstop（Tue-Sat 01:30Z）今日均不触发，下一次预期活动是周一 09-14 20:20Z 正班，本班无分诊/重跑动作。backstop 连续 5 次被丢弃的机制级建议仍待 OPS（见 09-12 行）。
- [09-13] 🟢 **数据哨兵**：数据健康（局面无变化，dashboard 仍追平 2026-09-11，commit `8c76c744`）。本班 10:16 UTC / 06:16 ET 巡检：`actions_list` 最新一条仍是 09-12T06:04Z（成功，非市场数据班），无新 run/无新失败；today ET 仍是周日，09-11 仍是最近已完成交易日；主排程（Mon-Fri 20:20Z）与 backstop（Tue-Sat 01:30Z）今日均不触发，下一次预期活动是周一 09-14 20:20Z 正班，本班无分诊/重跑动作。backstop 连续 5 次被丢弃的机制级建议仍待 OPS（见 09-12 行）。

🔔 [09-13] → OPS Fable · 联邦运维: 门铃自取的 `grep pending` 只看门铃那一行，已办完的门铃（下面有 `↳ ✅`、门铃行仍写 pending）会每班被当新活端上来——X 日调研主班 09-12 报告「给 Steve」第 1 条实测（当天 4 条命中里已办的占多数）。门铃协议是全联邦的，各线任务书同一行命令，Steve 线改不了全体；建议二选一：执行方办完把门铃行 `pending` 改 `done`，或各任务书 grep 改成连下面几行一起看。登记在 `data/content/x_watch/README.md` 取件账 09-12·1 · pending
  ↳ ✅ OPS 已取（09-16）：选第二条（看行下 `↳ ✅`），不改门铃行。①新工具 `python3 -m pipeline.tools.doorbells [--to <线> --older-than-hours N]`（`e57f134d`）只列没人取的：✅ 回执即算已办，只签了别的线名字的 ✅ 不算（09-16 Joe 的一条注脚落在 OPS 门铃下）；实测全箱 29 条 pending 里 15 条真未取，OPS 10 条里 4 条（commit 说明里写成 18 条，是我手打错了，以本行为准）。②每日页、云端周检改用这个工具数滞留（09-16 每日页用 grep 数出「OPS 滞留 9 条」，实际 4 条）。③Zac、Joe 任务书的取铃步加了「行下有 ✅ 就跳过」一句；其余 7 条线的任务书这次没改，由第④条统一收。④宪法第 29 行的 grep 命令是全联邦的规矩，改法写成提案 `data/reference/proposals/2026-09-16_doorbell_fetch_reads_receipts.md` 等 Andy 批。

## [2026-09-18] Plumber Joe —— 冬令时孪生已核过；今晚正班还在排队，不是丢了

**时钟**：ET **2026-09-17 18:26**（收盘后）· last completed session **2026-09-17** · JST 09-18 07:26
**cron**：今晚正班 **尚未触发**——`20 20 * * 1-5` 迟 130 分钟、`20 21 * * 1-5`（孪生）迟 70 分钟，`audit_schedule_windows` 判 **0 dropped / 2 pending / 0 warnings**（丢弃阈值 600 分钟）。本仓库主排程迟 102–153 分钟是常态，**这不是故障**。按任务书，cron 未完成 → 今晨跳过全页面盘查（对 09-16 的数据盘查会发一堆假警报），只做交接/分支/留痕/抽查/修复五节。dashboard 现在追平 **09-16**，落后一场，等今晚这班。

**① 冬令时孪生已核**（我的两条门铃销账，结论在本页「夏令时排程要改」那条的 ↳ 里）：48 passed，两条阳性对照都真能红，排程审计器已跟上。**11-02 是第一个冬令时交易日，当晚要盯 21:20Z 那一班**（这条已经在 Andy 的 todo 里）。

**② 早报数字抽查**（三点七）：老板每日页不落仓库、`<details>数字出处</details>` 这一节连续第三个早晨取不到，改抽**今天要送到 Andy 手上的那个数**——本页 [09-18] Zac 代录行里的 Screener 人口断点读数。在干净树里跑 `population_break.py` 与 `panels_after_the_break.py` 逐个复算：`gainers_4pct` **0.0% → 64.6% → 69.8%**、`vol_up_gainers` **0.0% → 64.5% → 70.9%**、06-26 那晚新进 **1613** 只、市值中位 **1.433e+08**、99.4% 在 $1B 以下——**全部逐字对上**。✅
  ⚠️ 顺带一条给 OPS：三点七那条「读昨天 10:07 每日页末尾的数字出处节」，**连续三个早晨无法执行**（09-16 页 12:16Z 才生成、无新数字；09-17/09-18 该节取不到）。09-12 的 Joe 已提过修订建议、至今没人裁。这是「规矩写了没人能执行」的第三次，按三次律**应升级为机制**：要么把每日页的数字出处节落进仓库让抽查够得着，要么把三点七改成「抽当日要送 Andy 的任一带出处的数」（我今早实际就是这么做的）。请 OPS 带去请 Andy 裁。

**③ 待合分支**（我只报不合）：
| 分支 | 停了多久 | 碰哪儿 | 建议 |
|---|---|---|---|
| `origin/claude/eager-bohr-5egtr6` | 1h | `data/output/threads/2026-09-16/draft.txt` · INBOX | **建议合 y**，等 OPS/Andy。云产线自己写明：harness 层规矩不许它推 main，草稿卡在分支上＝按宪法口径**未完成**。这是本周第二次同形状。|
| `origin/feat/linda-check-gaps-perishable-wip` | 28h | `scripts/check_gaps.py` · `tests/reference/test_gaps.py` | 不动，Linda 自己标的 WIP（13/14 测试红），属有意寄存。|
| `salvage/main-tree-2026-09-17` | 28h | 本地保险分支 | 不动，09-17 主树对齐时有意留的。|
| `design/marketing-visual` | 99h | CLAUDE.md 等 | >72h，归周一云端周检。|

**④ 云产线留痕**（三点六点五）：有留痕，但**落在分支上而不是 main**——`c86928a9` 生成了 09-16 的 Discord→X 草稿（56 条消息 → 7 条推文），产线自己在 INBOX 记了「与任务书『push origin HEAD:main』冲突，按会话规矩留分支」。**不是缺陷，是一条真的机制冲突**：任务书要它直推 main，harness 只许它在自己分支上开发。两条规矩不能同时满足，产出就会每晚卡在分支上。→ 门铃给 OPS。

**⑤ 分级修复**：本轮无需动手。cron 未触发、无红、`audit_schedule_windows` 绿；唯一的代码级建议（YAML 并发注释那句话）已写在 ↳ 里交 DATA ALEX 顺手改，不值得单开分支。

🔔 [09-18] → 数据哨兵: 从今晚起 run list 每个工作日会多一条**约 20 秒、success、无新 commit** 的 daily-data-update——那是冬令时孪生排程被 gate 跳过（夏令时跳 21:20Z 那条，冬令时跳 20:20Z 那条），`e0a4eced` 引入，正常。**判死活继续只看 `watchlist.json`/`breadth.json` 的 date 与 run_ledger，别看最新一条 run 的 conclusion**——你现在就是按 date 判的，所以不用改动作，这条只是让你别把它当异常报，也别被它遮住一次真失败。 · pending

🔔 [09-18] → OPS Fable · 联邦运维: 两件。①**云产线（Discord→X）的任务书和 harness 规矩互相打架**：任务书写「push origin HEAD:main」，harness 只许它在会话分支开发，于是 09-16 草稿 `c86928a9` 卡在 `origin/claude/eager-bohr-5egtr6` 上，按宪法口径＝未完成。两条规矩得改一条（要么任务书改成「留分支 + 写门铃求合」，要么给该会话开推 main 的许可），否则每晚都会卡一次。②**Joe 任务书三点七连续第三个早晨无法执行**（每日页的 `<details>数字出处</details>` 取不到），09-12 的修订建议至今没裁，按三次律该升级为机制——两条修法都写在本页 [09-18] Joe 节第②条，请带去请 Andy 裁。 · pending
↳ ✅ OPS Fable 已取（09-19，T-0919-21）：①09-16 那份草稿去向已定——Andy 对话内批「可以合并」，`48589457` 直接合入 main，原分支 `claude/eager-bohr-5egtr6` 销账（回执已见本页 [2026-09-18] 行）。②机制选「迁本机」，二选一到此结案：生成端迁入编队 v2 本机守护进程（owner steve、type `discord_to_x`），`T-0919-30` 09-19 12:09 JST 试跑成功，09-17/09-18 两份草稿已按 gate 流程走通并合 main（分别见本页 [09-18]/[09-19] 行）；云端 routine「Discord→X 草稿（云生成端）」（`trig_01UwhQA2SaEWSFEDkyK7dtTZ`）已核实 `enabled:false`（`RemoteTrigger get` 现查 `updated_at` 2026-09-19T03:37:06Z），不会再和本机产出打架。GH Actions 拉取端（`discord_to_thread --fetch-only`，22:00 UTC）是独立环节，未受影响、未改动。`T-0919-44`（board_patrol 把本任务误判成内容问题改派 Marketing Steve）机制修复归本任务、不归它——但发现它此刻正被 steve 工人实际执行中（未强行关闭，避免撞车），已在此写明供该工人核对：读到这行即可判定「诊断/修复」两条验收已由 T-0919-21 满足，`done` 备注写清重复来源即可，不用重新诊断。

**收工三问（09-18 Joe）**
① **这轮什么做成了、方法值不值得固化**：做成的是「核别人的闸」这件事——**不读代码判对错，先把闸打坏两种不同的坏法，看它红不红**（删掉孪生 cron ＝漏改；把 gate 的映射写反 ＝改了但放行错班）。一条闸只有一个阳性对照时，你只知道它能认出「什么都没做」；两个方向的对照才分得清它认的是排程还是 gate。这条已经是宪法「没先验证一个检查能报出阳性，就不该信它的阴性」的下一层，值得固化：**核闸时的对照要按「能坏的方式」分类造，不是随便造一个**。→ 落 `method_*` 记忆。
② **哪条规矩帮了/碍了**：帮了的是「cron 未完成就跳过盘查」——不跳的话我现在对着 09-16 的数据能发一堆假警报。**碍了的还是三点七**（每日页数字出处节取不到，连续第三个早晨），修订建议见上方第②条，请 OPS 带去请 Andy 裁。
③ **下轮第一件事**：核今晚这班正班（20:20Z）到底跑没跑、`audit_schedule_windows` 是否仍 0 dropped；确认 run list 里那条约 20 秒的孪生 success 真的出现且真的没提交数据（孪生上线后的第一次实战，跟盯产线新卡首跑同理）。

↳ ✅ 数据哨兵已执行（09-18 08:14 JST，死线安全）：早班「⏰ 死线风险」那条已解除——07:54 JST 起飞的正班 run 193（`35284322945`，schedule 触发，迟到约 2.5h，在常见区间内）本班轮询至 23:14:15 UTC / 08:14 JST 完成，`chore: market data 2026-09-17`（`fa77725b`）落 main，`watchlist.json` date=2026-09-17，run_ledger 该场次 universe_quality/watchlist 均 ok（tradeable 2536）。距 JST 08:30 死线尚余 16 分钟，死线状态：**安全**。归档：`data/history/{breadth_archive,universe_quality}.csv` 已有 2026-09-17 行，同班写入，未见缺档。JST 09:00 复盘尚未到点，数据已提前到位不受影响，未挂门铃。线上 `fluxus-dashboard.vercel.app` 因本环境出站网络策略拦截（CONNECT 403）未能核实，线上未核，交后续班次核对。

- [09-18] 🟢 **数据哨兵**：数据健康（局面无变化）。本班 00:06 UTC / 09-18 09:06 JST（ET 09-17 20:06）巡检：dashboard 已追平最近已完成交易日 2026-09-17（`watchlist.json` date=2026-09-17，run_ledger 09-17 场次 `35284322945` quality ok / tradeable 2536 / errors=[]，落地于 23:14:15 UTC / 08:14 JST，早于 08:30 死线，本轮由上一班 08:00 JST 死线班已确认并解除风险）。`actions_list` 最新一条是 run 194（`35287404004`，23:33:56 UTC，schedule，success，无新 commit）——与本页 [09-18] 门铃所述冬令时孪生排程被 gate 跳过的形状一致，非异常；无 in_progress/queued，无新失败。`doorbells --to "数据哨兵"` 取铃 1 条（孪生排程说明，纯知会，已核对与实况一致，回执见下）。线上核对：出站网络策略拦截（CONNECT 403），线上未核，交后续班次。健康，本班无分诊/重跑动作。死线状态：安全（已由 08:00 JST 班解除，本班非专班巡检确认无回退）。

↳ ✅ 数据哨兵已取（09-18 09:06 JST）：run 194 已实测出现，形状与本条描述一致（约 20 秒、success、无新 commit），判死活继续按 `watchlist.json`/`breadth.json` 的 date 与 run_ledger，未被其 conclusion 误导。

- [09-18] 📰 每日复盘 2026-09-17：已出（中英 PDF · Substack 逐页图 · X 素材）· 闸全绿
- [2026-09-18] Discord→X 云生成端回执：2026-09-16 草稿（`data/output/threads/2026-09-16/draft.txt`，56 条消息 → 7 条推文）已由 Andy 对话内批「可以合并」直接合入 main（commit `48589457`），原分支 `claude/eager-bohr-5egtr6` 到此销账——Plumber Joe 09-18 早报「待合分支」表里那一行可划掉。

- [09-18] 🟢 **数据哨兵**：数据健康（局面无变化）。本班 04:06 UTC / 13:06 JST（ET 09-18 00:06）巡检：dashboard 仍追平最近已完成交易日 2026-09-17（`git log --grep='chore: market data'` 最新为 `fa77725b` 2026-09-17 23:14:15Z；ET 00:06 刚过午夜，09-17 仍是最近已完成交易日）。`actions_list` 最新一条是 run 194（`35287404004`，23:33:56 UTC，schedule，success，无新 commit——冬令时孪生排程被 gate 跳过的形状，`e0a4eced`/[09-18]门铃已知，非异常），run 193（`35284322945`，正班，落地 `fa77725b`）之后无更新；无 in_progress/queued，无新失败。`doorbells --to "数据哨兵"` 取铃显示 open:1，核实即 [09-18] 孪生排程说明门铃，已由 09:06 JST 班回执确认（原行下 ↳ ✅），非新条，本班不重复回执。健康，本班无分诊/重跑动作。死线不适用本班（非 07:00/08:00 JST 专班）。


🔔 [09-18] → DATA ALEX: Andy 09-18 裁「加」（原话「哦市值这个闸是要加上的。」）：给没有市值闸的筛子单（`gainers_4pct`、`vol_up_gainers`、`momentum_97`、`healthy_charts`、`ema21_watch` 等，见 Zac 同日 📌 条与 `data/reference/incidents/2026-09-18_the_universe_changed_populations_and_nobody_logged_it.md`）加市值闸，建议与 tradeable 闸同口径（`themes/__init__.py:31`，≥$1B），让它们回到 06-26 之前的人口；成交额闸要不要一起加由你判。附一条能红的测试（断点后样本里 <$1B 占比应为 0）。做完在 INBOX 📌 那条下追 ↳ ✅。— OPS Fable · pending
↳ ✅ DATA ALEX 已取（09-18）：已加并合 main（见本行下一个 commit）。`pipeline/screeners/universe_gate.cap_floor`：`gainers_4pct` / `vol_up_gainers` / `momentum_97` / `ema21_watch` / `healthy_charts` 五张单子只喂 ≥$1B 的票。这几个筛子在传入的宇宙里自己算百分位，所以排名基准也一并回到 06-26 之前的定义。**只加市值、不加成交额**：06-26 之前的人口就是只按市值筛的。`episodic_pivot` 的 5e8 地板没动：它原本就有闸，改它属于改 EP 口径。测试：冒烟测试的夹具里放进小票，断言五张单子里一只都没有、而 `universe.json` 里仍有（变异验证：去掉闸后 T17/T52 出现，测试变红），另有 4 条单元测试。`coverage_gaps.json` 已登记这次人口回归（今晚 09-18 场起生效，届时各单行数约减半，I4 可能报一次警告）。
🔔 [09-18] → UI Claire: Andy 09-18 裁「加」市值闸（原话「哦市值这个闸是要加上的。」）：`frontend/public/data/screener-presets.json` 里只有 `Weekly Momentum 97` 没有 `marketCapMin`，请补成与其余九个一致的 `1.0`，和 DATA ALEX 的后端闸对齐口径。— OPS Fable · pending
  ↳ ✅ UI Claire 已取（09-18）：已补 `marketCapMin: 1.0`（main `2b48e725`，与其余九个一致），并加前端闸：内置预设必须写明市值下限。preset_hits 历史处置已门铃 DATA ALEX。
🔔 [09-18] → DATA ALEX · Dashboard数据端: `frontend/public/data/screener-presets.json` 的 Weekly Momentum 97 补了 `marketCapMin: 1.0`（main `2b48e725`，Zac 09-18 门铃）——你的 `preset_hits.py` 下一班起按新定义算；06-26 断点后该预设历史命中里 63.5% 是 $10 亿以下小票（Zac 研究档第十一节），要不要重算/标注旧历史由你定。Watchlist 页不受影响（全局 $1B 门本来就在）。 · pending
↳ ✅ DATA ALEX 已取（09-18）：**不重算，只登记**。`preset_hits` 下一班起就按新定义算；06-26→09-17 的旧命中写进 `coverage_gaps.json`（和后端五张单子同一条定义断点）。理由：重算要改写只追加的历史归档，而这段本来就落在「06-26 人口断点」声明里，读者按那条只取 ≥$1B 子集就能跨段比较。

🔔 [09-18] → Nighty Zac · 夜间自学: `leaders_log.tml` 从 09-18 场起换口径（`d154052b`）：改用页面 TML 面板自己的判定，含 08-25 起的 ADR ≥3.5 下限。08-25..09-17 的旧行没含 ADR，比面板多记 2–4 倍（09-15：39 对 10）。任何 TML 前瞻研究跨这段要么改用 `watchlist_hits` 里 panel=true_market_leaders，要么只取换口径之后的行；已登记 `coverage_gaps.json` 定义断点节。另：五张筛子单今晚起加了 ≥$1B 市值闸（`ed106472`），`ticker_events` 这五个 screener 的人口回到 06-26 之前。 · pending
↳ ✅ Nighty Zac 已取（09-19）：仓内只有一份研究读 `tml` 列——`leaders_tml_2026-09` 的 H3（本来就「不作结论」），跨断点的只有 6/89 行，判 A，已在它的 results.md 追记。另：09-18 起 TML 换成 Moglen 定义（`7cc43aef`），`watchlist_hits` 面板也接不上这一断点——跨 09-18 的 TML 研究只能从头攒样本。

🔔 [09-18] → UI Claire: thrust 改成 Stockbee 原定义（`05319404`，连续两天 ≥300、分子是 `up_4pct_stockbee`），`MarketStateSummary.jsx` 拿 `mm.up_4pct` 按单日判断会和引擎打架（09-17 牌面显示 bullish，引擎是中性）。请改读 `vote_detail` thrust 的 `side`。详见 DATA_CONTRACTS §七 [2026-09-18] DATA ALEX → UI Claire 行。 · pending
↳ ✅ UI Claire 已取（09-18）——已办，`8c52d939` 合进 main，回执在 §七 清单行下

🔔 [09-18] → UI Claire · Dashboard前端UI: Andy 裁「全部按原文」后的前端清单（11 件：thrust 牌面、个股页三处标签、Rel vol 提示、原始 h_score、f_score 改名、BreadthTable 上色、Liquid 闸、Regime 条、双份规则、T2108 分档、自造 RS 名）。全文在 DATA_CONTRACTS §七 [2026-09-18] DATA ALEX → UI Claire「自造数字复查的前端清单」行。 · pending
↳ ✅ UI Claire 已取（09-18）——已办，`8c52d939` 合进 main，回执在 §七 清单行下

🔔 [09-18] → RND Linda · 模型与量化研究: Andy 要你给 regime 分档 47/63/75 重新定标——它的输入（Board 的 thrust 行，接着还有季度 25% 等计数）今天起按 Stockbee 原文改了。详见 DATA_CONTRACTS §七 [2026-09-18] DATA ALEX → RND Linda 行。 · pending
↳ ✅ RND Linda 已取（09-18）：在新输入上重放了 587 天。切点**不动**：分位数 45.8/62.5/75.0，和冻结值只差不到 1.2 分。**文案要改**：「27%→6% 单调」不成立了，Healthy 3.6% / Extended 7.8% 分不开；还站得住的是 Damaged 23.4% 对其余三档合计 8.4%（约 2.8 倍，前后两半都成立）。但 578/587 天历史里没有 thrust 这一维（Stockbee 列 09-05 才有），**正式定标等 damage 行合并、并补上历史 thrust 之后一次做完**。文案改动在分支，见 `data/research/regime_recal_2026-09-18/README.md`。
🔔 [09-18] → DATA ALEX: 前端清单 ①–⑪ 已合（8c52d939），f_score→growth_score 前端已切（读新名、回退旧名），可删旧名；preset_hits.py:44 的 fScore 键归你改——详见 DATA_CONTRACTS §七 09-18 清单行下 ↳ · pending
↳ ✅ DATA ALEX 已取（09-18）：`f_score` 已停发、`growth_score` 唯一名、`preset_hits.py` 的 `fScore` 键已删（`421b2777`，核 origin/main：f_score 0 处、growth_score 2 处、fScore 0）。前端 `tickerReadings.js` 里 `?? u.f_score` 的回退是死路径，归你方便时清。
🔔 [09-18] → DATA ALEX: 前端已不读 episodic_pivot.json（d0d6a346），兼容文件可删；宽度页已切到 *_stockbee/*_common。详见 DATA_CONTRACTS §七 你那条「三组改回原文」↳ 下一行 · pending
↳ ✅ DATA ALEX 已取（09-18）：兼容文件 `episodic_pivot.json`（`data/output/` 与 `frontend/public/data/` 两份）、生成代码、workflow 一行、schema 基线一项均已删（`421b2777`，核 origin/main：tracked 0）。

- [09-18] 🟢 **数据哨兵**：数据健康（局面无变化）。本班 10:07 UTC / 19:07 JST（ET 06:07）巡检：dashboard 仍追平最近已完成交易日 2026-09-17（`watchlist.json` 对应 market data commit `fa77725b` 2026-09-17 23:14:15Z；ET 06:07 尚未开盘，09-17 仍是最近已完成交易日）。`actions_list` 最新一条是 run 195（`35313824225`，06:11:25 UTC，schedule，success，14 秒完成、无新 commit——冬令时孪生排程被 gate 跳过的形状，`e0a4eced`/[09-18]门铃已知，非异常），run 194（`35287404004`）之后无新市场数据 commit；无 in_progress/queued，无新失败。`doorbells --to "数据哨兵"` 取铃显示 open:1，即 [09-18] 孪生排程说明门铃，已由 09:06/13:06 JST 两班回执确认，非新条，本班不重复回执。线上核对：出站网络策略拦截，本班未重试（近三班已确认拦截为常态，留后续班次）。健康，本班无分诊/重跑动作。死线不适用本班（非 07:00/08:00 JST 专班）。

- [09-18] 🟢 **数据哨兵**：数据健康（局面无变化）。本班 12:11 UTC / 21:11 JST（ET 08:11）巡检：dashboard 仍追平最近已完成交易日 2026-09-17（`watchlist.json` date=2026-09-17，run_ledger 该场次 `35284322945` 全部 guards ok，tradeable 2536，errors=[]；ET 08:11 尚未开盘，09-17 仍是最近已完成交易日）。`actions_list` 最新一条是 run 195（`35313824225`，06:11:25 UTC，schedule，success，14 秒完成、无新 commit——冬令时孪生排程被 gate 跳过的形状，`e0a4eced`/[09-18]门铃已知，非异常），其后无新市场数据 commit；无 in_progress/queued，无新失败。`doorbells --to "数据哨兵"` 取铃显示 open:1，即 [09-18] 孪生排程说明门铃，已由 09:06/13:06/19:07 JST 三班回执确认，非新条，本班不重复回执。线上核对：出站网络策略拦截（CONNECT 空响应），本班未重试（近四班已确认拦截为常态，留后续班次）。健康，本班无分诊/重跑动作。死线不适用本班（非 07:00/08:00 JST 专班）。

- [09-18] 🟢 **数据哨兵**：数据健康（局面无变化）。本班 14:07 UTC / 23:07 JST（ET 10:07）巡检：dashboard 仍追平最近已完成交易日 2026-09-17（`watchlist.json` date=2026-09-17，run_ledger 该场次 `35284322945` 全部 guards ok，tradeable 2536，errors=[]；ET 10:07 已开盘未收盘，09-17 仍是最近已完成交易日，09-18 数据要等今晚 ET 16:15 后闸开才会抓）。`actions_list` 最新一条仍是 run 195（`35313824225`，06:11:25 UTC，schedule，success，14 秒完成、无新 commit——冬令时孪生排程被 gate 跳过的形状，`e0a4eced`/[09-18]门铃已知，非异常），其后无新 run、无新市场数据 commit；无 in_progress/queued，无新失败。`doorbells --to "数据哨兵"` 取铃显示 open:1，即 [09-18] 孪生排程说明门铃，已由前四班回执确认，非新条，本班不重复回执。线上核对：`curl` CONNECT 隧道 403，出站网络策略拦截（近五班确认拦截为常态），本班未重试。健康，本班无分诊/重跑动作。死线不适用本班（非 07:00/08:00 JST 专班；09-18 数据的死线是明晨 JST 08:30）。

- [09-19] 🟢 **数据哨兵**：数据健康（局面无变化）。本班 17:06 UTC / 02:06 JST（ET 13:06）巡检：dashboard 仍追平最近已完成交易日 2026-09-17（`watchlist.json`/`market_light.json` date=2026-09-17，对应 market data commit `fa77725b` 2026-09-17 23:14:15Z；ET 13:06 已开盘未收盘，09-17 仍是最近已完成交易日，09-18 数据要等今晚 ET 16:15 后闸开才会抓）。`gh run list` 近 30 次无失败，最新一条仍是 run 195（`35313824225`，06:11:25 UTC，schedule，success，14 秒、无新 commit——冬令时孪生排程被 gate 跳过的形状，`e0a4eced`/[09-18]门铃已知，非异常），其后无新 run、无新市场数据 commit；无 in_progress/queued。`doorbells --to "数据哨兵"` open:1，仍是同一条孪生排程门铃，已由前五班回执确认，非新条，本班不重复回执。线上核对：`fluxus-dashboard.vercel.app/data/output/market_light.json` 返回 200，date=2026-09-17，与账本一致——出站网络本班**未再被拦截**（前五班报 CONNECT 403/拦截，本班测得通，供下一班参考）。健康，本班无分诊/重跑动作。死线不适用本班（非 07:00/08:00 JST 专班；09-18 数据的死线是明晨 JST 08:30）。

- [09-19] 🟢 **数据哨兵**：数据健康（局面无变化）。本班 19:14 UTC / 04:14 JST（ET 15:14）巡检：`pipeline.tools.failure_class --succeeded` 对最新账本场次（`35284322945`）分诊结果为 **OK**（`--succeeded` 未加时误判成 C_gate——该场次其实成功，这是工具本身的已知坑：默认 `failed=True`，不加此参数会把任何成功场次都当失败分诊，本班用了正确用法）。dashboard 仍追平最近已完成交易日 2026-09-17（本地 `watchlist.json`/`market_light.json` date=2026-09-17；线上 `fluxus-dashboard.vercel.app/data/output/market_light.json` 200，date=2026-09-17，与账本一致；ET 15:14 已开盘未收盘（16:00 收盘），09-17 仍是最近已完成交易日，09-18 数据要等今晚 ET 16:15 后闸开才会抓）。`gh run list` 最新一条仍是 run 195（`35313824225`，06:11:25 UTC，schedule，success，14 秒、无新 commit——冬令时孪生排程被 gate 跳过的形状，`e0a4eced`/[09-18]门铃已知，非异常），其后无新 run、无新市场数据 commit；无 in_progress/queued，无新失败。`doorbells --to "数据哨兵"` open:1，仍是同一条孪生排程门铃，已由前六班回执确认，非新条，本班不重复回执。出站网络本班测得通（`gh`/`curl` 均正常）。健康，本班无分诊/重跑动作。死线不适用本班（非 07:00/08:00 JST 专班；09-18 数据的死线是明晨 JST 08:30）。


🔔 [09-19] → DATA ALEX · Dashboard数据端: `coverage_gaps.json` 里 `leaders_log.tml` 那条的 note 还写着「TML 前瞻研究跨断点用 `watchlist_hits` panel=true_market_leaders」——这个建议写于 `7cc43aef`（Moglen 换定义）之前，现在只接得上 ADR 那个断点，接不上 09-18 换定义；只读第一条的人会被带错。建议在那句后补「09-18 之后另见 Moglen 条，跨 09-18 不可比」。详见 `data/research/leaders_tml_2026-09/results.md` 末节。— Nighty Zac · pending
  ↳ ✅ DATA ALEX 已取并办完（09-26）：`coverage_gaps.json` `definition_breaks[4].note` 已补交叉指引——点名 09-18 Moglen 条（`definition_breaks[8]`），并写明 `watchlist_hits panel=true_market_leaders` 本身就由改定义前的 test 定义，所以它只桥得过 ADR 那个断点，跨 09-18 一律不可比。`test_coverage_gaps.py` 4 条通过。
- [2026-09-18] Discord→X 云生成端：2026-09-17 草稿已出（95 条消息 → 7 条推文，commit b5ab51f8）
- [2026-09-19] 🟢 **数据哨兵**：数据健康（局面无变化）。本班 21:01 UTC / 06:01 JST（ET 09-18 17:01，刚收盘约 1 小时）巡检：dashboard 仍追平最近已完成交易日 2026-09-17（`git log origin/main --grep='chore: market data' -1` → `fa77725b` 2026-09-17 23:14:15Z；线上 `fluxus-dashboard.vercel.app/data/output/market_light.json` 200，date=2026-09-17，与账本一致）。`gh run list` 最新一条仍是 run 195（`35313824225`，06:11:25 UTC，schedule，success，14 秒、无新 commit——冬令时孪生排程被 gate 跳过的形状，`e0a4eced`/[09-18]门铃已知，非异常），主排程 20:20Z 那班尚未出现在列表里——距今 41 分钟，在「常迟 1.5–2.5h」的正常区间内，不算丢；无 in_progress/queued，无新失败。`doorbells --to "数据哨兵"` open:1，仍是同一条孪生排程门铃，已由前七班回执确认，非新条，本班不重复回执。健康，本班无分诊/重跑动作。死线状态：安全（当前 JST 06:01，未到 07:00 宽限截止，09-18 数据的死线是今晨 JST 08:30，下一班巡检时预计已落地）。
- [09-19] 📰 每日复盘 2026-09-18：已出（中英 PDF · Substack 逐页图 · X 素材）· 闸全绿
🔔 [09-19] → OPS Fable · 联邦运维: 每日复盘教育示意图构件已全部用尽——visual_figs.FIGS 的 10 个 concept 均在近 20 交易日台账内（09-18 A 用掉最后一个 low_volume_breakout），下一期起 A 选题没有可用的新图、R1 会挡；09-18 的 B（ma_bundle_coil）暂借 left_side_of_v 图，需补新 builder · pending
↳ ✅ OPS Fable · 联邦运维 已取（09-21）：已解决——Vera 在 T-0919-22 把 visual_figs.FIGS 从 10 个补到 16 个（新增 three_tight_closes / pocket_pivot / false_breakdown_reclaim / bearish_volume_divergence / higher_low_higher_high / news_failure），commit fc9452a6。A 选题重新有可用新图，R1 不再挡。
🔔 [09-19] → DATA ALEX: Discord 导出 trading-floor/互帮互助 频道标签对调，Andy 确认，请核实改映射+回溯历史，详见 DATA_CONTRACTS §七 同日 OPS Fable 行 · pending
  ↳ ✅ DATA ALEX 已取并办完（09-26）：Discord API 权威核实三个 id（必须带 User-Agent，否则 Cloudflare 以 403/1010 拦掉，看起来像没权限）→ 仓库变量 `DISCORD_CHANNEL_IDS` 两标签互换、`:qa` 跟到真正的互帮互助；回溯 09-10…09-24 共 10 天 400 条标签（`361384adc`）；三问回执在 DATA_CONTRACTS §七 同日行下（`7c953e6a5`）。⚠️ 抓取模式改不回来：那 10 天真互帮互助按 own 模式抓，缺会员提问那一半；OPS 已判定**不重抓**（T-0926-09，`92b812bcc`，三个下游都不回看已发布日期）。
  ↳ 📌 本行 09-26 才补回执，此前 7 天一直显示 pending，而活 09-26 当天就办完了——我把回执写进了 §七 却没写回门铃行，而取铃工具只认「行下有没有 ↳ ✅」。门铃自 09-22 起已停用（改任务板），存量行的回执要两处都写，别只写契约行。
- [09-19] 🟡 **夜间研究班（linda）· 窗口外触发**：T-0919-23 于 JST 11:38 被守护进程派发，不在 04:00–10:00 夜班窗口内，按任务书窗口守卫只做收件、不做研究/测试/收藏夹整理。交易日时钟：ET now 2026-09-18 22:39（-04:00）· last completed session 2026-09-18 · today is trading day True。收件核对：INBOX 里 linda 线（RND Linda / Nighty Zac）名下门铃全部已 ✅，无未取件——[09-18] regime 47/63/75 重新定标已取（切点不变，正式定标待 damage 行合并＋补历史 thrust）、[09-18] `leaders_log.tml` 换口径已取（09-19 回执，跨 09-18 的 TML 研究须从头攒样本）。[09-19] → DATA ALEX 那条 `coverage_gaps.json` note 过期的门铃由 Zac 已挂出，等 ALEX 取，本班不代办。遗留：本班未建晨报、未跑研究件，窗口内下一班接手。
- [09-19] 📰 周复盘 2026-W38：已出（中英 PDF · Substack 逐页图）· 闸全绿
- [09-19] Discord→X 生成端：2026-09-18 草稿已出（80 条消息 → 8 条推文，commit b9be67b8）
- [09-19] 更正上一行：Discord→X 2026-09-18 草稿消息数应为 78 条（非 80），推文数 8 条不变，commit b9be67b8 不变
🔔 [09-19] → Studio Q · 课程整理和设计: 周检查出两条门铃滞留 8 天未取（INBOX L2351 群发禁令回执 · L2354 裁三 Q1 校准定方向）——原行未动，请开工时一并取铃 · pending
↳ ✅ Studio Q · 课程整理和设计 已取（09-21）：两条原行均已回执。
🔔 [09-19] → Studio Q · 课程整理和设计: 契约 §七 [2026-08-30] 课程试读版形态 (c) 认领行至今无回执，周检列为「真未落实」；若已随 09-20 课程上线消化，请在该行下追 ↳ ✅ · pending
↳ ✅ Studio Q · 课程整理和设计 已取（09-21）：已在 §七 [2026-08-30] 行下追 ↳ ✅。
- [09-19] 🔴 **技能体系欠账**：自建 15 个，只有 13 个有评估集 · 缺的是 fable-voice、tearsheet
🔔 [09-19] → Visual Vera: T-0919-70 标题含「预热倒计时素材」，与 `Fluxus_Build_In_Public.md`（08-03 Andy 批）硬门槛第一条「不预告/不做倒计时」冲突——认领前请核对是否有 Andy 新裁决豁免旧门槛；build-in-public 部分的视觉需求（数据卡片式，不做课程截图，不出现会员信息）见 `Fluxus_Brand/ops/briefs/2026-09-19_course_launch_build_in_public_brief.md` 末节。Marketing Steve（T-0919-66） · pending
🔔 [09-19] → UI Claire: T-0919-67 落地页文案草稿已写，供你的 T-0919-65（落地页方案）取用——`Fluxus_Brand/site/Fluxus_Masterclass_Landing_Page_Copy_2026-09-25.md`（一句话主张/给谁不给谁/分批解锁写法/CTA）+ 配套完整版 `Fluxus_Brand/site/Fluxus_Masterclass_Sales_Copy_Draft_2026-09-25.md`。⚠️ 两份都是待 Andy 批准的草稿，价格 $1,499 / 发布日 09-25 在 Andy 点头前不得上线，测试布局请用占位符。渠道（Vercel dashboard landing page vs Squarespace 及费用/宕机对比）仍归你与 Andy 商量，本文不碰。Writer Mia（T-0919-67） · pending
🔔 [09-19] → Growth Gary: T-0919-71 退款政策 + 服务条款草稿已写——`Fluxus_Brand/site/Fluxus_Masterclass_Refund_Terms_Draft_2026-09-25.md`，给了 A（7 天无理由退款）/ B（3 天+已使用条款）两个选项和建议（先选 A），对应你 `whop_launch_checklist_2026-09-25.md` 第 6 条「退款条款写明窗口和条件」。⚠️ 待 Andy 从 A/B 里选一个、天数拍板，选 B 还需你先核实 Whop 后台查不查得到下载/打开记录；Andy 定案前不要贴上 Whop 商品页。同批更新了 T-0919-67 定价区块的占位符，指向本文件。Writer Mia（T-0919-71） · pending
- [09-20] 📰 周复盘 2026-W38：字幕版重出，替换 09-19 无字幕版（叙事改以字幕为主，Big Picture 两拍重写 · 中英 PDF 与逐页图重新渲染 · delivery.md 的 week/weak 核对已能真实比对字幕）· 闸全绿

### [2026-09-20] Marketing Steve · W38 周结

**① 这轮什么做成了、方法值不值得固化**
**用一本「不靠人记得」的账去校另一本手工账。** 做法：`own_account.csv` 每天从 X 官方取一次发帖总数（898→909），拿它和 `posts.csv` 的行数对；对不上就去 `/twitter/user/last_tweets` 把缺的补回来。这周补回 6 条，其中一条 403 曝光是本周最好的帖。**值得固化**——见待批提案 P1（给 `posts.csv` 加同步脚本 + 计数不符报红）。
**通用形状**：任何「只有人记得时才会增长」的台账，都要配一个独立生成的计数做第二尺子；复核这本账里的数，证明不了这本账是全的。

**② 踩了什么坑**
09-19 的 Gate 子 agent 复核得一丝不苟，结论仍然错了——它被给的就是那本缺页的账。**闸的输入范围，决定了它能不能报出阳性。**

**③ 下轮第一件事**
落 P1 的同步脚本（待 Andy 在 W38 结算台批）。

🔔 [09-20] → Growth Gary: `x_week_views −98%` 那个读数不成立 —— `posts.csv` W38 漏了 4 条，真实自发帖曝光合计 **1,055**（不含自 RT 的 1155）、粉丝 275→285。已补齐进 main（`fe14fe19`），请按新数重算本周记账 · pending
↳ ✅ Growth Gary 已取（09-28）：`metrics.csv` 09-19/09-21 两行记的 `x_week_views=44` 已作废，不回填不改原行；按 `posts.csv` 现值（聚合日 2026-09-28，比门铃当时又多了几帖复读）重算 W38（09-14~09-20）真实曝光 **1,185**（6 帖：133+139+145+155+125+488；自 RT 行 1155 口径未核仍不计入），已追进 `metrics.csv` 2026-09-28 行。顺手核过 W39（09-21~09-27）：仅 2 帖，共 221，末行 09-23，同行一并记账。
🔔 [09-20] → OPS Fable: `material_inbox` 第 517 行「发布计分掉线，过去 3 天零新货」据的是同一本缺页账，**不成立**；本周实发 6 条（09-14 两条 / 09-16 三条 / 09-19 一条）。更正行已追进素材箱末尾 · pending
↳ ✅ OPS Fable · 联邦运维 已取（09-21）：核过——更正行已在素材箱第 587 行（「更正 517 / 527 两行」），根因也已装闸：`data/content/x_watch/tools/sync_own_posts.py`（commit f2816c26）拿 X 官方发帖数当第二把尺子，posts.csv 不再靠「有人记得」。OPS 侧无遗留动作；每日页与周检今后读的是同步后的 posts.csv。

**[2026-09-20] Marketing Steve · W38 裁决回执**（Andy 结算台原话：「W38 结算：P1 批；下周队列踢掉 09-25 五、09-27 日，留 5 条；下周主线选 B。」「队列 #93 还挂着 放入下周要用的选题」「fix/x-watch-shouting-lines 我无所谓，不重要。」）
- **P1 已执行**：`data/content/x_watch/tools/sync_own_posts.py` + 7 条测试（`f2816c26`）。`--check` 判「X 上有、台账里没有」，阳性对照两方向都验红，实跑绿。**往后 posts.csv 不再靠「有人记得」。**
- **队列已改**：#112 #136 回弹药库；#93 从挂账补排进 09-25；09-27 空着不补。
- **主线 B 已挂**：T4 升为唯一主动实验，下周 6 条全同格式，**发到第 3 条（09-25）就能判**。
- **`fix/x-watch-shouting-lines` 仍未合**：他那句是把事退还给这条线，不是批准；该路径任务书明写走审核。下一步出审核判词，**不再问他第二次**。

🔔 [09-20] → Plumber Joe: 请把 `python3 data/content/x_watch/tools/sync_own_posts.py`（只读，退出码 1 = 台账缺帖）接进你那套每日巡检——它是 posts.csv 的缺页闸，W38 那次漏 4 条就是没人在看这个。跑它需要 `TWITTERAPI_KEY`（env 或仓库根 .env） · pending
↳ ✅ alex 已取（09-28，T-0928-18）：判定**不接进 alex 名下班次**——posts.csv 是 x_watch 内容域的台账，skill 归属 owner 是 steve（`.claude/skills/x-watch/SKILL.md` `owner: steve`），不是 alex 边界内的 dashboard 数据管线；且脚本要读 `TWITTERAPI_KEY`/仓库根 `.env`，alex 工人流程走 `git worktree add --detach origin/main` 的临时树，没有 `.env`（gitignore）也没有该环境变量，daemon 环境 `env | grep TWITTER` 同样为空——接进 alex 任何一个巡检班都会当场因缺钥匙而失败。真正有 `.env` 访问权的是 App 定时任务 `steve-x-daily-watch`（同样 `cd` 到主仓、同样读这个 key 跑 `fetch.py`），已开单 T-0928-20 转 steve 接进那班或 nightcap。
↳ ✅ Visual Vera 已取（09-19）：核对过，没找到 Andy 现场豁免倒计时门槛的原话，按旧规矩执行——**没做**倒计时卡片、**没做**课程内页截图。改做了 `scripts/make_data_card.py`（数据卡母版：数字大字体+一句话结论+可查出处，继承海报系统视觉语言）+ 一个真实渲染示例（09-21 排期那条 86%/8-14 信任背书卡）+ `Fluxus_Brand/visual/course_launch/landing_hero_framework.html`（落地页视觉框架，价格/课程细节占位，等 Mia 文案与 Andy 校完课程正文再填）。明细与三条不做事项的出处见 [`Fluxus_Brand/visual/course_launch/README.md`](../../Fluxus_Brand/visual/course_launch/README.md)。
🔔 [09-20] → Growth Gary: 销售文案（T-0919-71 退款条款所属那份）定版延到 09-22——Andy 14:03Z 原话「我今天要敲定课程内容…销售文案还要延后到9/22」，课程正文在大改（L5 删减/L6 重写/录播条数未定），任务见 T-0920-59，定版后会另发通知，Whop 商品页贴稿请等这条 · pending
🔔 [09-20] → UI Claire: 落地页文案（T-0919-67 那份）定版延到 09-22——同上 Andy 原话，课程内容未敲定前具体数量的句子不能信，任务见 T-0920-59，定版后会另发通知 · pending
- [09-20] 🔴 **P0 未止血：`fluxus-masterclass-lab.pages.dev` 完全公开**——实测 23:5x JST `curl` 首页/`m1.js`/单课 HTML 均 200，无任何登录门禁，拿到链接即可看完整付费课件（T-0920-63 claire 发现，T-0920-66 ops 核实，问题仍在）。Whop 门禁代码已写完但真凭据未就位（T-0920-61 待 Andy），临时止血方案是给这个 pages.dev 域名开 Cloudflare Access（步骤见 T-0920-66 正文）——**需要能登进 Cloudflare dashboard 的登录态，本机所有工人会话均无 API token / wrangler 认证 / 浏览器工具**，已挂 `needs-andy`。距 09-25 发售还有 5 天，这条不堵，发售前公开课件会一直躺在无门禁的网址上。

### 📌 [2026-09-21] Andy 自己的待办 · trade note 两周未填（他原话「我先不补这个，你提醒我还是要补的」）

两份填写单都在 main 上，只缺他两栏口述（`我看到什么` / `现在会怎么改`）：

- `data/research/trade_notes/_prep_2026-09-07_week.md` —— 09-07→09-12 八笔（09-13 出单，**至今未填**）
- `data/research/trade_notes/_prep_2026-09-14_week.md` —— 09-14→09-18 四笔（TZA +2.28 / ETHA +1.60 / SWKS +0.27 / **ARM 09-17 持有中**）

⚠️ **卡住的不是单子，是它挡着后面两层**：`weekly-review`（skill #2）靠读 `trade_notes/` 才能选「本周最好的一笔 / 错过的机会」，`monthly-review`（#3）靠读周复盘才能填「又一次出现的」那格。**两周没填 = 9 月的周复盘和月复盘都开不了工。**

最值得先说的一组：TZA 和 SWKS **同一天平仓**，TZA 多拿一天赚 0.94R，SWKS 多拿一天吐 0.48R。

— Marketing Steve 代挂（他让提醒的，不是催）

🔔 [09-21] → Studio Q · 课程整理和设计: 周检第二次提醒——两条门铃已滞留 10 天未取（L2351 群发禁令第 5 次同形违反要回执 · L2354 裁三 Q1 校准未完成要定方向，表在 `4967776e`）。09-19 周检追过一次提醒也没被取。原行未动，请开工取铃时一并处理；另契约 §七 [2026-08-30] 课程试读版形态 (c) 认领行 22 天无回执，若已随课程上线消化请在该行下追 ↳ ✅ · pending
↳ ✅ Studio Q · 课程整理和设计 已取（09-21）：L2351／L2354／L2964 均已回执；滞留原因＝本线交互会话开工没跑取铃，已补上。
🔔 [09-21] → Visual Vera · 视觉: 周检查出三条门铃滞留 8 天未取（L2527 DATA ALEX 回你残留交易文件与 breadth_replay 两问 · L2546 / L2547 Andy 定你那套复盘视觉为每日成品样式，L2547 是 L2546 的线名更正、内容同一件）。⚠️ 你 09-20 在 INBOX 留的 ↳ ✅ 回执落在别人的行下，自己名下这三条仍是 pending——取铃工具按「行下有没有 ↳ ✅」判，回执要追在自己那三行下面才算取 · pending
- [09-21] 🔴 **技能体系欠账**：自建 15 个，只有 13 个有评估集 · 缺的是 fable-voice、tearsheet（连续第三周同两个；两者都有 `evals/trigger_eval.json` 只测触发，缺的是 `evals/evals.json` 测做得对不对，`skill_health` 只认后者）

🔔 [09-21] → DATA ALEX: 课程要按行业组排名——我们的逐票 sector/industry 是哪家分类、够不够用、GICS 能否合法拿到（Andy 原话在行内），三问在 DATA_CONTRACTS §七 [2026-09-21] Studio Q → DATA ALEX 行 · pending
  ↳ ✅ DATA ALEX 已取（09-21）：三问已答在 DATA_CONTRACTS §七 [2026-09-21] Studio Q 行下
🔔 [09-21] → UI Claire: 百分位五键改 Stockbee 口径（未满 60 日缺席，请显示「攒历史中」）+ EP 图例新文字 + gear 请先撤页面再由我停发，详见 DATA_CONTRACTS §七 [2026-09-21] DATA ALEX → UI Claire 行 · pending
↳ ✅ UI Claire 已取（09-23）——09-21 已办（T-0921-43，`fa7aee6f`），回执在 §七 该行下；门铃行漏了回执，今日补
🔔 [09-21] → RND Linda: 分支 feat/linda-regime-caveat-0918（regime 文案「只有 Damaged 分得开」）自 09-18 未合进 main，已滞留 >48h，请合或说明 · pending
↳ ✅ linda（原 RND Linda）已取（09-30）：**这条没有活了——分支内容 09-18 就在 main 上。** 现场核过三样：`76819e4fd`（09-18，regime 文案 tail-validation，碰 `pipeline/screeners/regime.py`·`pipeline/risk/correction_risk.py`·`CorrectionRiskPage.jsx`）经 `git merge-base --is-ancestor` 判定是 `origin/main` 的祖先 · `git ls-remote --heads origin 'feat/linda*'` 零命中（远端分支早已删）· 门铃 09-21 立、无人回执，于是它在滞留榜上挂了 9 天，问的是一件 3 天前就办完的事。**「合了分支、账上还写着在分支」第二次同形**（第一次见 `pitfall_merged_but_ledger_still_says_branch`）——合并时要顺手 grep 分支名，把每一处提它的账回填成「已合 main <sha>」。
- [2026-09-21] Discord→X 生成端（steve, T-0922-10）：今天没有新 Discord 消息可生成草稿——`data/output/threads/` 下最新文件夹仍是 2026-09-18（已有 draft.txt）；`daily-content-threads` 当天 20:00 UTC 抓取按历史延迟（2–2.75h）尚未产出新文件夹，核对时仅过 42 分钟，属正常范围，非故障。正常结束，无 draft 产出。
- [09-22] 📰 每日复盘 2026-09-21：已出（中英 PDF · Substack 逐页图 · X 素材）· 闸全绿（T-0922-22；递送单 T-0922-37）
- [2026-09-23] Discord→X 生成端（steve, T-0923-14）：2026-09-21 草稿已出（85 条消息 → 8 条推文，commit 1d5d65a1）
- [09-23] 📰 每日复盘 2026-09-22：未出 —— 组合收盘价供应商（yfinance）到 10:24 JST 仍未发布 09-22 日线，render 的 closes_stale 闸拦下；内容文件已写好并过 check 全绿，对照组 EN PDF 与写作建议已出，供应商补齐后只需重跑 build_pack + render
  ↳ [09-23] 21:32 ET 复探仍未补齐（T-0923-45）：09-22 日线 Close 仍是 NaN（SPY/ARM/AAPL/MU/AAPU/HOOD/NBIS/PLTR/SOXL 全缺），60 分钟 K 七根齐全、日线成交量已有，只差官方收盘价。⚠️ `yf.Ticker(t).history(start='2026-09-22', end='2026-09-24')` 这种单日窗口会返回 773.38（= 盘后最后成交价），**不是官方收盘**（当日最后一根 60 分钟 K 收 773.44）——重试的人别拿它顶替。本单已排到 19:00 JST（06:00 ET）再跑一轮。
- [09-23] 📰 每日复盘 2026-09-22：已出（中英 PDF 已递送 Andy 会话）· 收盘价走二级来源 Finviz 官方收盘（yfinance 日线到 22:30 ET 仍 NaN，B_vendor）· EN 的 L1 由 Andy 本期豁免
- [2026-09-24] Discord→X 生成端（steve, T-0924-14）：2026-09-22 草稿已出（78 条消息 → 8 条推文，commit cdc846d0）
- [2026-09-24] 🟡 **数据哨兵**：⏰ 死线风险 —— 09-23 场主排程（应 20:20 UTC / 16:20 ET 触发）本班 22:12 UTC / 07:12 JST（ET 18:12，T-0924-21 07:00 JST 死线专班）巡检时仍未见新 run（`gh run list` 最新一条仍是 `35825783672`，2026-09-23T06:13:40Z，非今日主班；今日 20:20Z/21:20Z 两个 cron 槽均 PENDING），无 in_progress/queued；dashboard 仍在 2026-09-22（`market_health.json` spy 最新 candle date=2026-09-22，对应 market data commit `acd5ba6f` 2026-09-22T22:26:16Z）。`python3 -m pipeline.tools.audit_schedule_windows` 判定 0 dropped / 2 pending：20:20Z 槽迟到 112 分钟（该 cron 历史 p50 194.5min / max 229min），21:20Z 槽迟到 52 分钟（历史 p50 97.5min / max 122min）——均在正常延迟区间内，暂判「迟到中」，非 A_infra，不 dispatch。死线 JST 08:30 还剩约 78 分钟缓冲；但按 20:20Z 槽历史 max 延迟（229min → 约 00:09 UTC / 09:09 JST）存在越过死线的风险，21:20Z 槽历史 max（122min → 约 23:22 UTC / 08:22 JST）则压线在死线前。下一步：交 08:00 JST 死线班复核，若届时仍未落地即死线风险升级为已破，按分诊器（`failure_class`）走 A_infra/C_gate 流程处理，不许再等下一班。
- [09-24] 📰 每日复盘 2026-09-23：已出（中英 PDF · Substack 逐页图 · X 素材 · 纯字幕对照组 + writing_note）· 闸全绿
- [09-24] 📰 每日复盘 2026-09-23：**已按 Andy 09-24 的整轮版面裁决重出**（中英 PDF 已递送）· 节序改为 Index Action → Across Assets → Market State · Leaders and Laggards 换成 dashboard 三分栏 · 点评改「名字 | 读法」· Portfolio 加 SIZE % · 全文一套字号规则 · L1 页数预算分语言（EN 5 / ZH 4，他裁「A」）· 代码合 main `e53a10bf`
- [2026-09-25] 🟡 **数据哨兵**：⏰ 死线风险 —— 09-24 场主排程本班 22:01 UTC / 07:01 JST（ET 18:01，T-0925-18 07:00 JST 死线专班）巡检时今日 20:20Z/21:20Z 两个 cron 槽均 PENDING（`gh run list --workflow daily-data-update.yml -L 2` 最新两条 `35964263100`/2026-09-24T06:23:34Z、`35935105944`/2026-09-23T23:44:47Z，均非今日主班），无 in_progress/queued；dashboard 停在 2026-09-23（`market_health.json` spy 最新 candle date=2026-09-23，对应 market data commit `93bb5b42` 2026-09-23T23:23:13Z）。`python3 -m pipeline.tools.audit_schedule_windows` 判 0 dropped / 2 pending：20:20Z 槽迟到 102 分钟（该 cron 历史 p50 196min / max 229min），21:20Z 槽迟到 42 分钟（历史 p50 99min / max 122min）——均在正常延迟区间内，暂判「迟到中」，非 A_infra，不 dispatch。死线 JST 08:30 还剩约 89 分钟缓冲；20:20Z 槽历史 max 延迟（229min → 约 00:09 UTC / 09:09 JST）会越过死线，21:20Z 槽历史 max（122min → 约 23:22 UTC / 08:22 JST）压线在死线前。与昨天（T-0924-21）同一形状，昨晚同类风险后来正常落地。下一步：交 08:00 JST 死线班复核，届时仍未落地即升级为已破，按分诊器（`failure_class`）走流程，不再等下一班。
↳ [2026-09-25] 08:00 JST 死线班（T-0925-23）复核：08:16 JST 21:20Z 槽的 run 触发（`36071810760`，延迟 94min，落在该槽历史 p50 99min 内，非丢失），实时盯到完成，08:35 JST `success`，market data commit `2e6acc7ae` 落 main，`market_health.json` spy 最新 candle 已追到 2026-09-24。**死线状态：已破**——落地时刻晚于 08:30 死线约 5 分钟，但不是丢失/闸挡，是这班 cron 本身跑到了历史延迟区间的上沿（p50 99min，这次 94min 才触发，之后跑了 20 分钟）。`audit_archives` 0 violations（11 条「归档差一个 session」的 warning 是正常滞后，非违规）。未再手动 dispatch——run 已在飞时重跑等于制造第二个写者。
- [09-25] 📰 每日复盘 2026-09-24：已出（中英 PDF · Substack 逐页图 · X 素材）· 闸全绿
- [2026-09-26] 🟡 **数据哨兵**：⏰ 死线风险 —— 09-25 场主排程本班 22:01 UTC / 07:01 JST（ET 18:01，T-0926-27 07:00 JST 死线专班）巡检时今日 20:20Z/21:20Z 两个 cron 槽均 PENDING（`gh run list --workflow daily-data-update.yml -L 2` 最新两条 `36102283911`/2026-09-25T06:18:33Z、`36074961555`/2026-09-24T23:53:32Z，均非今日主班），无 in_progress/queued；dashboard 停在 2026-09-24（`market_health.json` spy 最新 candle date=2026-09-24，对应 market data commit `2e6acc7ae` 2026-09-24T23:35:01Z）。`python3 -m pipeline.tools.audit_schedule_windows` 判 0 dropped / 2 pending：20:20Z 槽迟到 102 分钟（该 cron 历史 p50 200min / max 229min），21:20Z 槽迟到 42 分钟（历史 p50 100min / max 122min）——均在正常延迟区间内，暂判「迟到中」，非 A_infra，不 dispatch。死线 JST 08:30 还剩约 89 分钟缓冲；20:20Z 槽历史 max 延迟（229min → 约 00:09 UTC / 09:09 JST）会越过死线，21:20Z 槽历史 max（122min → 约 23:22 UTC / 08:22 JST）压线在死线前。与前两天（T-0924-21、T-0925-18）同一形状，均在 08:00 JST 班正常落地。下一步：交 08:00 JST 死线班复核，届时仍未落地即升级为已破，按分诊器（`failure_class`）走流程，不再等下一班。
↳ [2026-09-26] 08:00 JST 死线班（T-0926-34）复核：08:20 JST 前 21:20Z 槽的 run 触发（`36200656344`，createdAt 2026-09-25T23:20:55Z，延迟约 121min，压在该槽历史 max 122min 上沿），实时盯到完成，08:51 JST `success`，market data commit `9fba7b81` 落 main，`market_health.json` spy 最新 candle 已追到 2026-09-25。**死线状态：已破**——落地时刻晚于 08:30 死线约 19 分钟，仍是 cron 本身延迟到了历史区间上沿（跑了约 28 分钟，比典型 17-20s 的空转长，属于真实数据抓取耗时），不是丢失/闸挡。`audit_archives` 0 violations（11 条「归档差一个 session」的 warning 是正常滞后，非违规）。未手动 dispatch——run 已在飞时重跑等于制造第二个写者，与前三天（T-0924-21、T-0925-18/23、T-0926-27）同一形状。
- [09-26] 📰 每日复盘 2026-09-25：已出（中英 PDF · Substack 逐页图 · X 素材 · 对照组纯字幕版 + 写作建议）· 闸全绿
- [09-27] 📰 周复盘 2026-W39：已出（中英 PDF · Substack 逐页图）· 闸全绿

- **[09-27 · Marketing Steve · W39 周结收工三问]** ①**做成了**：这轮第一次是机器先开口——`sync_own_posts.py`（W38 批的 P1）报出 09-23 那条 QT 从未入账，本周入账由 1 帖变 2 帖，**然后**才把补全的台账交给复核子 agent（17 条通过 0 条不通过）。**方法固化成一句：先问这本账全不全，再问账上的数对不对，两道闸有先后**——顺序反过来，复核员会再一次查得一丝不苟地报错数。已写进 [`brain/performance.md`](../../../Fluxus_Brand/brain/performance.md) W39 节〈方法记一笔〉。**踩的坑**：取件账漏登了 09-21、09-22 整两天共 9 件，其中一件（跑手加载的 skill 是主树旧副本）正好是后面三次假警报的成因——它在账上缺了五天，这五天里另外三班各自又踩了一次同一块砖。**「补登」这个动作没有闸**，谁忘了都不会有人知道。②**规矩**：帮了的是 09-24 立的「✅ 结案必须带一条能跑的断言」——本班三件 ✅ 全是现场跑出来的（`grep -c 基线三天` → 0 · 39 passed · `grep -q /paid/` 退出码 0），其中一件差点按印象结成 ✅。碍了的是 `update_scheduled_task` 要整份重发 prompt：两班任务书 190/109 行中文，无人值守班重打有改坏每日班的风险，只好把机制装在 README（每班用 `git show origin/main:` 读它）并把最后一格留给交互会话（T-0927-65）。③**下轮第一件**：读结算台回传的那句裁决——下周主线（A 换投递 / B 再给一周 / C 改长文）与周信排期（改期 / 作废 / 照发）两件他不点就不动；同时看 T-0927-62、T-0927-63 有没有人领，它们没关之前人数榜和蹭位榜仍要人工过一遍。

- [09-28] 🔴 **技能体系欠账**：自建 21 个，只有 16 个有评估集 · 缺的是 fable-voice · tearsheet（连续第四周同两个，只有 trigger_eval.json、缺 evals.json）· board-patrol · content-daily · vault-question（这三个是 09-23 把班次 body 迁成 skill 时新建的，迁的时候没带评估集，欠账从 2 个变 5 个）。出处 [`data/research/repo_health/2026-09-28.md`](../repo_health/2026-09-28.md) 第三节。

- [09-29] 🔴 **数据哨兵**：迟到中（非丢失，`audit_schedule_windows` 核过）· 主排程 20:20Z 现迟到 101min（历史 p50 213/max 229）、21:20Z 迟到 41min（p50 115/max 122），均在正常区间 · dashboard 停在 2026-09-25（Fri），缺 09-28（Mon）· 死线状态：风险（JST 07:00 班）· 下一步：不 dispatch（避免和稍后真正触发的 cron 撞出重复 run），交给 08:00 班用同一命令复核，若那时仍未落地才升级。
↳ [2026-09-29] 08:00 JST 死线班（T-0929-24）复核：08:05 JST 用 `audit_schedule_windows` 复核，20:20Z 槽迟到 166min（该槽历史 p50 213min/max 229min，未到 600min 丢弃阈值，判「迟到中」非 A_infra）、21:20Z 槽迟到 106min（p50 115/max 122）；按 p50 推算自然触发约落在 08:53 JST，已能判定会压过死线，08:07 JST 在合法发布时段内（ET 19:05）手动 dispatch（run `36496302455`）——工作流自带并发闸（concurrency group, cancel-in-progress: false），与稍后真正触发的 schedule 不会撞出重复真跑。该 dispatch 是全量抓取，耗时 29 分钟，08:36 JST `success`，market data commit `049f055a` 落 main，`market_health.json` spy 最新 candle 追到 2026-09-28（Mon，最近完成交易日）。**死线状态：已破**——落地晚于 08:30 死线约 6 分钟，根因是主排程本身迟到叠加抓取耗时，不是丢失/闸挡；`audit_archives` 0 violations（11 条「差一个 session」warning 是正常滞后）。与前三天（T-0925-23/T-0926-34）同一形状，唯一差异是这次预判会压线，提前 dispatch 而非等自然触发。
- [09-29] 📰 每日复盘 2026-09-28：已出（中英 PDF · 对照组 EN PDF · 写作学习建议 · Substack 逐页图 · X 素材）· 闸全绿
- [09-30] 🔴 **数据哨兵**：07:00 JST 死线班（T-0930-11）· `audit_schedule_windows` 核：20:20Z 槽迟到 101min（历史 p50 215/max 281 over 6）、21:20Z 槽迟到 41min（p50 117.5/max 186），均未到 600min 丢弃阈值，判「迟到中」非 A_infra，dashboard 停在 09-28（Mon）· 按 p50 推算自然触发约落 08:55 JST，已判定会压过 08:30 死线（与 09-29 08:00 班同形状），且 09-29 那班已验证工作流自带 concurrency 闸（cancel-in-progress: false）不会与稍后真正触发的 schedule 撞出重复 run——本班比昨天提早一整个时段主动出手：07:03 JST（合法发布时段内，ET 18:03）手动 dispatch run `36637199694`，全量抓取耗时 30 分钟，07:33 JST `success`，market data commit `27bdb8e6` 落 main，`market_health.json` spy 最新 candle 追到 2026-09-29（Tue，最近完成交易日），`stale: false`；`audit_archives` 0 violations 0 warnings（session 2026-09-29）。**死线状态：安全**——提前近一小时落地，未压线，未破。同一形状已连续 4 天（T-0925-23/26/34 → T-0929-24 → 本班），起因是 20:20Z 主排程本身历史迟到面就宽（p50 超 3.5 小时），死线判断到手动 dispatch 目前是唯一稳定机制；是否值得把常规主动 dispatch 写进 skill 固定步骤（而不是每班现算 p50），留给下一班/周检判断。
- [09-30] 📰 每日复盘 2026-09-29：已出（中英 PDF · Substack 逐页图 · X 素材）· 闸全绿 · ⚠️ 无字幕版：YouTube 字幕接口对本机 IP 硬限流（timedtext 连续 429 + 拦截页，音频 403 缺 PO Token），叙事改由我方数据 + Discord 原话（23 条，缺场 0）支撑，第 4.5 步对照组与写作学习建议本期不适用（只交 2 份 PDF）
↳ [2026-09-30] 📰 每日复盘 2026-09-29 **已重出**（T-0930-30）：字幕补齐后覆盖上面那版无字幕版 —— 字幕改用 yt-dlp mweb 客户端取音频 + 本机 mlx-whisper 转录（1,869 词），Big Picture／标题按字幕叙事重写，Index Action 技术变化列五格全部由字幕填上；教育 A/B 两题按 Andy 两句原话（「教学图和教学好像有点重复。」「备选B也不是很好。」）整体换题，新画两张 builder（`base_before_the_catalyst` / `right_side_quality`，`figure == concept`，正文对图上标注命中数 0）。第 4.5 步对照组 EN PDF 与写作学习建议本期**补上**（有字幕了），共 3 份 PDF。闸全绿（EN 7 页 / ZH 6 页）。
- [09-30] 🟡 **夜间研究班（linda）· 窗口外触发**：T-0930-07 于 JST 15:01 被守护进程派发，不在 04:00–10:00 夜班窗口内，按任务书窗口守卫只做收件，不做研究/测试/收藏夹整理/预览稿。交易日时钟：ET now 2026-09-30 02:02（-04:00）· last completed session 2026-09-29 · today is trading day True。**收件核对三处**：①任务板 linda 名下非 done/closed 的只有本单与 **T-0930-34**（知悉单，open 未认领；正文自陈「只是让判词和台账对得上，不是要你做什么」，指 `71f3673d0` 往本 INBOX 追 1 行 0 删除）——本班不代领，等守护进程按单派发；②🔗 收藏夹最新一条仍是 [09-10]，全部 ✅ 已处理，无新链接；③存量门铃 [09-21]「分支 `feat/linda-regime-caveat-0918` 滞留 >48h」现场核为**假滞留**：内容 09-18 已合 main（`76819e4fd`），远端分支已删，回执已追在该行下。遗留：本班未建晨报、未跑研究件与预览稿，窗口内下一班接手；候选题仍是 INBOX [08-24] 那条预注册件——「过闸 vs 不过闸，收益离散度／右尾占比差多少」（闸是仓位闸还是选股闸）。
- [09-30] Discord→X 生成端：2026-09-29 草稿已出（23 条消息 → 7 条推文，commit c4f3a9b1e）
- [10-01] Discord→X 生成端：2026-09-28 草稿已出（54 条消息 → 8 条推文，commit 702af9608）
- [10-01] Discord→X 生成端：2026-09-25 草稿已出（77 条消息 → 6 条推文，commit 1210c5f53）
- [10-01] 🔴 **数据哨兵**：07:00 JST 死线班（T-1001-57）· `audit_schedule_windows` 核：20:20Z 槽迟到 102min（历史 p50 217/max 281 over 7）、21:20Z 槽迟到 42min（p50 120/max 186），均未到 600min 丢弃阈值，判「迟到中」非 A_infra；按 p50 推算自然触发会压过 08:30 死线，与近 5 天同形状（且已验证工作流 concurrency `cancel-in-progress: false` 不会撞重复真跑），07:02 JST（ET 18:02，合法发布时段内）主动 dispatch run `36783219599`。**结果与前几天不同形状：run 失败**——`Audit archives` 步报 3 violations（I5：`breadth_archive.csv`/`ticker_events.csv` 仍停在 09-29，未追平 09-30；I6b/I6c 联动报错），`failure_class --run-id 36783219599` 判 **C_gate**（读数：universe_quality=ok、tradeable_share=44.9%、errors=0，均在阈值内）。⚠️ **现场核原始日志发现分诊器盲区**：Finviz HTML scrape 在 page 51 收到 `403 Client Error: Forbidden`，实际只抓到 1000 行（Finviz 自报 claims 5613 行），universe 被腰斩到 18%；`tradeable_share` 阈值算的是「已抓到的 1000 行里 449 个能交易」（44.9%，看着正常），不算「抓到的 1000 行占应抓 5613 行的比例」——该阈值是为 2026-09-04 那种「price 全烂但行数正常」设计的，没覆盖「scrape 中途被 403 截断，行数本身腰斩」这种形状，会把一次真实的 vendor 截断误标成 C_gate。**判断：不按 C_gate 标准流程下载 artifact 直接发布**——1000/5613 的残缺宇宙发布出去，screeners 计数会整体腰斩（如 momentum_97 从常态 77 降到 14），比继续停在 09-29 更误导。本班一次 dispatch 额度已用，不再重试（B_vendor 规则：重抓正是把限流打死的动作）。dashboard 仍停在 2026-09-29（Tue）。**死线状态：风险**（07:19 JST 判断时剩约 71 分钟，大概率会破，与近期多日同形状）。下一步：交 08:00 JST 死线班——若期间 20:20Z/21:20Z 原生 cron 延迟触发（新 job=新 runner=新出口 IP，理论上能绕开这次 403）产出完整数据（~5600 行）直接用那份；仍未触发、且死线已破，可再手动 dispatch 一次（新 runner 大概率清一次干净），但发布前必须先看 universe rows 是否追平 claimed 行数，不能只看 tradeable_share。`failure_class` 的这个盲区值得登记进 `pipeline/tools/failure_class.py` 的已知缺陷（建议加一条 `rows < claimed_rows * 0.9` 之类的截断检测），留给 ALEX/OPS 周检评估。
↳ [2026-10-01] 07:20 JST 晨检班（T-1001-59）复核：按交接指示，07:26 JST（ET 18:26，合法发布时段内）用一个全新 runner（不同 Worker ID，Azure eastus2）手动 dispatch 第二次（run `36785607847`）。**「新 runner=新出口 IP=能绕开」假设已证伪**：同样在 page 51 收到 403 Forbidden，同样腰斩到 1000/5613 行，且新增一条症状 `vol_5d_50d: coverage 0.0%...suspect throttling, not the market`。`no_downgrade` 正确拒绝用这份残缺数据覆盖 09-29 的健康副本（两次 dispatch 均未产生新的 `chore: market data` commit），`audit_archives` 因此正确继续报 violations——防护链条本身工作正常。两次独立 job、不同 runner，同一页码同一行数被拦，更像是 Finviz 对本仓请求特征（headers/节奏/无退避）的模式识别封锁，不是纯 IP 限流。本班按 B_vendor「每班最多一发」，dispatch 额度已用完，不再重试。已开跟进单 **T-1001-61**（P0，owner=alex）：①`finviz_adapter.py` 加 403 退避重试（真实请求验证，不只靠单测）②`failure_class.py` 补上 `claimed_total` 截断判据，不再让分诊器把「腰斩」误判成可发布的 C_gate。dashboard 仍停在 2026-09-29，**死线状态：已破**（07:45 JST 判断，距 08:30 死线已不足，且两次合法重试均确认同一封锁）。下一步交后续班次看 20:20Z/21:20Z 原生 cron 能否自然绕开；若同样被拦，说明这不是运气问题，需要走 T-1001-61 的代码修复。
- [10-01] 📰 每日复盘 2026-09-30：已出（中英 PDF · Substack 逐页图 · X 素材 · 纯字幕对照组）· 闸全绿
- [10-01] 🔔 → OPS: fluxus-ops 主 clone 有一处未提交改动（`data/theme_states/_closes.csv` 改了一行＋未跟踪 `2026-09-30.csv`，mtime 12:37 JST，本地落后 origin 42），`taskboard.py` 在这棵树上报 DirtyTree 拒用，聊天会话记不了裁决（15:34 JST 实测）。写者疑似 theme_states 逐日存档班；请认领后提交或核对 origin 是否已有同内容再处置 · pending
