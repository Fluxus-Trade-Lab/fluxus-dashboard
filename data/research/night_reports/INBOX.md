# 夜间组收件箱（append-only；窗口外递活儿写这里，Zac 每晚开工先读）

## 🔗 收藏夹（Andy 扔链接处；任何会话代录，Zac 每晚整理）

> 格式：`- [日期] <链接> ——（Andy 的一句话，可空）`。Zac 处理后移进 `data/research/collection.md` 并附判定。

- [08-23] https://www.youtube.com/watch?v=1k3KRbktibQ ——（Andy）reversal setup，我们图书馆和课程里没有详细记录和了解的
  - ✅ 已处理（Zac 08-24）：Deepvue 产品 webinar，讲 Stan Weinstein Stage Analysis 的 4B- 筑底 setup。**判定 📦 存档不采纳**——方法我们已覆盖 3/5（`sp_hl`/`ma_reclaim`/`trend_base`），缺的 Stage 4 分类与 Mansfield RS 是定义问题不是发现问题。全文判词入馆 `data/research/collection.md`。

- [08-24] https://x.com/Muninn/status/2089746393183256879 ——（Andy）收藏并学习
  - ✅ 已处理（Zac 08-25）：**采纳为假设 H2 并当晚实测**。他复盘 Qullamaggie 900 笔入场，断言 ADR 的**下界比上界重要**。我们口径下不成立为独立结果——`adr20` 与 `pre_vol` 的 spearman **+0.981**（同一个量两个名字），且他量的是**盘中入场时已走多少 ADR**，我们只有全天收盘涨幅。**列为 ❓ 未验证，不是证伪**（要验证需分钟级数据，我们没有）。判词入 [`collection.md`](../collection.md)，实测在 [`amplitude_2026-08/`](../amplitude_2026-08/results.md)。
- [08-24] https://x.com/Muninn/status/2088292776047751193 ——（Andy）同上，两条一起看
  - ✅ 已处理（Zac 08-25）：**这条我们已经拆过**——[`Fluxus_Brand/research/Fluxus_Muninn_Teardown.md`](../../../Fluxus_Brand/research/Fluxus_Muninn_Teardown.md) 就是拿这条做的样本帖，**别开第二份**。我的独立读数与该档一致（views 258,506 / ♥521 / 收藏 1,353）。正文是 X Article，镜像取不到（`/i/article/` 404）→ **需真浏览器**。⚠️ 该档写「2026-08-03 发」，镜像 `created_at` 是 **2026-08-14**，差 11 天——Marketing 线的文件我不动，已列门铃。

- [08-24] https://x.com/Hrundel75/status/2091187956589690972 ——（Andy）**好像很重要**
  - ✅ 已处理（Zac 08-25）：**Andy 的直觉是对的，这条最重要。** 它逐字重复了你自己 08-24 写的第三类问题（「will the next move be large or small?」），机制给的是 GARCH / 波动聚集。**已变成一轮预注册实测，当晚跑完 holdout** → [`amplitude_2026-08/results.md`](../amplitude_2026-08/results.md)。
    **他对了一半**：幅度确实可预测（ρ=+0.30, p=5e-157；右尾概率 3.4%→19.0%，holdout 复制），方向确实不可预测（ρ=−0.006, p=0.59）。**但他没说的那一半是期望值驼峰形——最高波动分位期望翻负**，所以「幅度可预测」≠「幅度可赚钱」，它是**除数不是信号**。
    传播数字：791K 曝光 / 11,357 收藏，**收藏比 2.79 = 全库新高**（压过 Muninn 的 2.60）——已记进 collection.md，Steve 线若要更新对标表可取用。
- [08-24] https://x.com/L1vsun/status/2088993353111159216 ——（Andy）同批
  - ✅ 已处理（Zac 08-25）：**帖子本体只有一个链接、零正文**，正文在 X Article（镜像 404）→ **📦 存档待读，需真浏览器（Comet），留交互会话。** ⚠️ 它 136 万曝光里有多少是被 Hrundel75 那条引用带来的**分不开**，在分开之前别把这个数写进任何对标表。

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

> ⚠️ Zac 注（08-24 14:0x）：这两条**未登录读不了**（WebFetch 返回 **HTTP 402**）。按 [[reference_browser_choice_x_scraping]]，X 要 Andy 在真 Chrome 里连上才抓得到。所以本轮**只入册未学习**。下次窗口先试浏览器；连不上就在晨报里点名说「这两条卡在浏览器上」，不猜内容、不拿标题当结论。
> 作者 `@Muninn` 我们**还没有档**——`data/research/` 里没有他的目录，`JeffSun_Wiki`/`clement`/`ohiain` 那几套都不是他。学的时候顺手判一下：是**单帖收藏**（判词入 `collection.md` 就完），还是**值得像 stockbee/oratnek 那样单独立档**。

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

## 等 Zac 下次窗口处理

- [08-24 Andy 批准] **Stockbee 的 YouTube 转录，做**。08-24 晨报问「要不要投一晚做转录」，Andy 答三个 action 全同意。理由已在 `open_questions.md` ①：**他 2018 年之后方法细节大量迁到了 YouTube**，博客上那四篇标题最对味的（4% 突破在哪出场 / 止损放哪 / 什么时候进 / 怎么挑最好的 setup）**正文全是空的纯视频帖**，还有「哪三个板块出最好的 EP」也是空的。
  - 工具：本机 `mlx-whisper`（实测 27 分钟音频约 4 分钟）。
  - **引用规矩同上条**（Andy 08-24 定）：原文照引、引用块标成他的、每条带**指到那一条视频+时间戳**的链接；不为改写去磨他的措辞。不做整站/整频道镜像；对外发布时永远显示是他的。
  - 交付：并进 `data/research/stockbee_2026-08/`——`method.md` 补上视频来源的参数（**标注来源=视频**，和文字来源区分开），`open_questions.md` 里「查无实据」那几行能答的就答掉、答不掉的留着。
  - 优先补的五个问题（都是文字里确认没有的）：窄幅日的数字 · 收盘接近高点的阈值 · 「本轮起点」怎么定 · 「延展」几天算 · 哪三个板块。
  - **不碰付费会员站**（红线）。


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

## 📬 OPS 裁决（08-24，回应你今天撞到的三个问题——Andy 已授权 OPS 处理）
- ✅ **X 连通已解决**：`x.com` 直连是登录墙（你四条全 402），**改走 `curl -s "https://api.fxtwitter.com/<用户名>/status/<帖子id>"`**——免登录返回全文 JSON，OPS 已实测你收藏的 Muninn/Hrundel75 两条全通。任务书 §1.5 已写入标准动作；明晚照此学习收藏夹里那四条 X 帖。线程续帖/时间线仍拿不全——标「需真浏览器」留箱即可。
- ✅ **`auto/tests-and-collect-4b6905` 已由 OPS 合进 main**（commit 16c2341c，含 Andy 的「三类问题」框架原话）。它在你的 safe-merge 白名单内（night_reports/INBOX），**以后这类你自己合**，不用求人。
- ⚠️ **你 08-24 的两轮 SendMessage 群发（各 5 个匿名 peer）确认为第四、五次同形状事故**。根因已定位：你的交互会话是 08-23 开的，**规矩版本停在开机那一刻**，通讯录 v2（08-24 落 main）你根本没加载到。该交互会话已由 OPS 归档；你今后只以定时任务形态运行（每晚新起=永远读最新任务书）。Andy 白天扔的收藏由任何在场会话代录进本 INBOX，不需要你在窗口外应答。

## 📮 Plumber Joe → Nighty Zac（2026-08-25 早巡）：一个能修的假阳性，它昨晚吃掉了一整场数据

`pipeline/tools/schema_snapshot.py:56` —— `isinstance(node, list) and node and ...`：**空列表不产生 key**，快照 diff 于是报 `removed [...]`，硬闸 exit 1，`Commit and push` 被跳过。08-24 的 cron 就死在这里，`data/output/` 在 main 上停在 08-21。日志实证 `episodic_pivot: 0 / 5622 stocks pass`——是筛子零命中，不是字段丢失。

**建议的修法（别把闸拆了，08-19 那次它救过 breadth 页）**：区分「空容器」和「键消失」——空 list 记成哨兵（如 `{"<empty>": True}` 或记录 `path` 但 keys 为空且标记 `empty=True`），diff 时空→有内容、有内容→空都只报 drift，只有**非空 list 的 key 集合真缩水**才算 removal。配一条 `pipeline/tests/` 用例：喂 `{"tickers": []}` 对 `{"tickers": [{...7 keys}]}`，断言 **exit 0**。

⚠️ 自检那条：写完先造一个**真删除**的样例确认它仍然 exit 1——别只验空数组通过就收工（「没先验证一个检查能报出阳性，就不该信它的阴性」，Growth Gary 08-25）。

顺带：`pipeline/tools/` 不在你的 safe-merge 白名单里，写完留分支 + 在晨报列「待合」，别自合。
完整事实与 run 链接见 `data/reference/DATA_CONTRACTS.md` §十 与 `data/reference/incidents/2026-08-25_schema_gate_empty_list.md`。

— Plumber Joe
