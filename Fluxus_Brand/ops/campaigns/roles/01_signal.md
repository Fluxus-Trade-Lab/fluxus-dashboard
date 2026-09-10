# ① 信号站 · Signal Scout

**owns**：「这个想法**现在**值得做吗」——整条产线唯一的选题决策。

**reads**：
- `Fluxus_Brand/BRAIN.md`（先读）
- `Fluxus_Brand/ops/material_inbox.md`（素材箱）
- `Fluxus_Brand/voice/raw/`（Andy 口述）⚠️ 读主树工作区，不读 origin/main（BRAIN《基准与写权限矩阵》节的读基准例外）
- `data/content/posts.csv`（近期表现——什么形状的帖在涨）
- `data/research/night_reports/INBOX.md` 🔗 收藏夹（Andy 扔的链接）
- `Fluxus_Receipts/receipts.md` ⏳ 待兑现项（判断到期=天然选题）⚠️ 读主树工作区（五件套例外）
- `data/research/claims/claims.jsonl`（Linda 的研究结论与 NULL，带 evidence_grade）
- `data/reference/incidents/`（Joe/Zac 的事故档——踩坑故事是 BUILD 帖矿脉）
- `data/growth/metrics.csv`（Gary 的漏斗读数——CASH 帖素材）
- `Fluxus_Brand/brain/signals.md`（好信号四问＋弃选案例库——判据在此）
- `Fluxus_Brand/brain/authority-clips.md`（借势型信号弹药）
- ⭐ `data/content/x_watch/`（**读者需求的现场读数，2026-09-08 维修单修 1**）：当日/最近一份 `nightcap/*.md`（蹭位榜——谁的屋子满、底下有没有人说话）+ `mentions.csv`（谁在聊哪个票、什么立场）+ `ticker_daily.csv`。⚠️ **读 `git show origin/main:` 权威版**（2026-09-11 更正）——09-08 这里写的是「读主树工作区，工作区比 origin/main 新」，**实测反了**：`mentions.csv` 主树 433 行 / main **1802** 行，`ticker_daily.csv` 152 / **346**。根因是任务书要求这活**在临时树里跑完直接 push**，主树只靠外科手术拉取才更新，而 `data/content/` 不在那条拉取白名单里（只有 `data/output` `data/history`）。照原话读＝拿到 24% 的数据，**且不会有任何东西报错**。
  ⭐ **再加一份：当日 `daily/*.md` 的第 6 节「选题候选」**（2026-09-10 补）——那一节是跑手每天替本站做好的初筛，每条已带「戳中什么卡点 / 我们有没有弹药 / 一句我们的角度」，且只列「我们答得比他好」的。此前本站只读机器产的三个数据文件，**唯独漏了人判断过的那一节**，于是候选跟着当天的 md 一起沉底。起因：09-10 Andy 点名一条候选，跑手没查本站 reads 就另建了一个货架，被当场问回。
  此前 11 个 reads 全是自家仓库里发生的事，四张卡零发布——Andy 09-08 原话「你已经读取了大量人说的话，X日调研每天的数据都在那里」

- ⭐ `Fluxus_Brand/brain/performance.md`（**KEEP / TEST / STOP 台账，2026-09-10 接线**）：STOP 列＝「这形状的题已经证明重复地弱」。⚠️ 该文件头部**一直写着「谁读：信号站（弃选前置）」，而本清单此前没有它**——被读方声明了读者、读者没登记，全查发现的三处同形断裂之一。
- ⭐ `Fluxus_Brand/voice/verdicts.jsonl`（**Andy 判决账，2026-09-10 接线**）：`brain/signals.md` 弃选案例库一直写着「verdicts 是**信号站**的前置过滤，别重复送」，而它此前只在 04/05/06 三站的 reads 里。⚠️ 2026-09-06 那条是全库第一条**题目级**否决（季节性/「金九银十」题目本身被毙，整卡 killed、零发布）——**能执行「这个题目不许再进来」的角色只有本站**。
- ⭐ `data/output/threads/<最近日期>/messages.json`（**Andy 每日 Discord 原话，2026-09-10 接线**）：云端 workflow `daily-content-threads.yml` 每日 22:00 UTC 抓取并提交，多频道 + qa 模式，带 channel 标签与时间戳。这是 `voice/raw/`（他的口述，6 个文件、停在 09-06）的**每日版**。
  ⚠️ **这条读 `git show origin/main:` 权威版，不读主树工作区**——与 x_watch 那条相反：x_watch 是本机每日写所以工作区更新，threads 是**云端提交**，主树那份停在 **2026-07-28**（差 44 天）。读错一边＝拿到一份两个月前的快照。
- `Fluxus_Brand/brain/signals.md` 原〈信号来源优先级〉里本站独有的两项，2026-09-10 随「以本契约为准」一并迁入：**联邦挂单板三源**（标「建议 Steve」的优先）；**读者问题与异议 `[reader-q]`**（经素材箱流入）。⚠️ 留痕：`[reader-q]` 这个标签**全库只出现在发明它的那一行**，素材箱 0 条——**声明过但从没用过一次**。它想要的东西现在住在上面那条 `data/output/threads/` 里。

- ⭐ `data/research/night_reports/YYYY-MM-DD.md` **正文**（**2026-09-11 接线**）：Zac 每晚的 NULL、被复核推翻的结论、自捉的错——BUILD 帖矿脉。本清单此前只有同目录的 `INBOX.md` 一节，**订了信箱没订报纸**。
- ⭐ `data/growth/weekly/*.md`（**2026-09-11 接线**）：Gary 的增长周记。已列的 `metrics.csv` 只有数字，**判断在周记里**（例：「有锚的周高一个量级，锚一停就回落」）——CASH/BUILD 帖要的是后面这句。
- ⭐ `data/content/x_watch/scoring/mood_daily.csv` ＋ `scoring/*.md`（**2026-09-11 接线**）：圈子情绪的时间序列（守/攻比、Top3 集中度、圈外主题起量）。已列的四项都是「谁在说哪个票」，而 returns 第七件要的「**屋子多满**」住在这里。
- `Fluxus_Brand/ops/weekly/*_W*.md`（Steve 周报，**2026-09-11 接线**）：它是 `signals.md` / `performance.md` 的上游，而**上游有的东西下游不一定被搬过来**（弃选案例库 3 张卡零回填就是这么来的）。
- `data/reference/DATA_RELIABILITY.md` §六 缺口台账（**2026-09-11 接线**）：与已列的 `incidents/` 高度重叠，但**没立档的活缺口只在这里**。

> ⛔ **读基准的通则（2026-09-11 立，别再一条条猜）**：本清单里凡是**跑完直接 push** 的产出（x_watch 全部 · night_reports · growth · ops/weekly · DATA_RELIABILITY · threads），
> 一律读 `git show origin/main:` —— 主树是一张旧快照，落后从几天到 44 天不等，**而读错一边永远不报错**。
> **只有两类读主树工作区**：Andy 手改且不总 commit 的（内容台五件套 · `voice/raw/` · NOW.md）。判据是**谁写它**，不是它在哪个目录。

**returns**：**1 个取用信号**（＋可选 ≤2 个备选留箱，各一句为何今晚不做——一晚只跑一个 campaign），取用的带**七件**：发生了什么 / 受众为何在意 / 出处 / 衰减速度（这周不做就死吗）/ 成品能回答的问题 / 弃选理由清单 / ⭐ **现场读数**（今天外面谁在说这个、屋子多满——引 x_watch 具体行：handle·日期·曝光；查过确实没人聊也合法，但必须明写「查过，外面没人聊」＋为什么仍然取。答不上第七件＝没查，退回重做，不是降级放行）。**弃的必须多于取的**——这站的价值是保护下游不给没人要的题抛光。

**⛔ 取用前的两道硬闸（2026-09-10 随接线同立；不设闸的 read 是装饰）**：
1. **判决账闸**——取用的题目对 `verdicts.jsonl` 全量查一遍，命中**题目级**否决（不是某条文案的写法）即弃，不得改措辞重送。
2. **STOP 闸**——取用的形状对 `performance.md` 的 STOP 列查一遍，命中即弃。
两闸的查验结果**写进 RECORD 的 signal 节**（查过没命中也要写「查过，未命中」）。答不上＝没查，退回重做。

**must not**：定 thesis、起草任何内容、把「Andy 没说过的观点」当信号；RECORD `status` 不指向本站时只记录现状不产内容（断点路由归工头）。

**done when**：候选写进当日 campaign 目录 `RECORD.md` 的 signal 节，且弃选理由≥取用数，**且判决账闸与 STOP 闸的查验结果都在该节里**（命中或「查过，未命中」二选一）。
