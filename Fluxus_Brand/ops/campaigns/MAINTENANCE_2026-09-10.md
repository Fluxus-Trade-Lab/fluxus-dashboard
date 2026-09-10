# 维修单 2026-09-10 · 信号站 reads 全查

*起因：Andy 09-10「信号站的 reads 还有没有别的漏的，全查一遍」。*
*两条独立枚举（本会话按写入频率机械扫 + 一个不给它看清单的 agent 独立列举），结果合并后逐条现场核实。*
*✅ **2026-09-10 已裁决并执行**。Andy 原话：「**以 roles/01_signal.md 为准，三条都接上**」。*
*本单从审计单转为**已结**；下面「一句话」以下是审计原文（保留不改），执行结果见文末〈八〉。*

---

## 一句话

**漏了。但主要问题不是清单短，是三处「双向声明」对不上，而且断的方向永远是同一个：被读方写了「谁读我」，读者的契约里没登记。**

## ⭐ 三处双向声明断裂（这是同一个 bug 的三个实例，不是三件事）

| 被读方 | 它自己头部写的 | `roles/01_signal.md` 里 |
|---|---|---|
| `Fluxus_Brand/brain/performance.md` | 「谁读：**信号站（弃选前置）** · 分发站（选型）」 | 提到 performance **0 次** |
| `Fluxus_Brand/voice/verdicts.jsonl` | `brain/signals.md` 弃选案例库：「**verdicts 是信号站的前置过滤**，别重复送」 | 只在 04/05/06 三站的 reads 里，**信号站没有** |
| `brain/signals.md`〈信号来源优先级〉 | 自称「契约 reads 的扫描顺序」 | 与契约 reads **双向差集**，见下 |

### 这条断裂已经有代价了，不是理论问题

`verdicts.jsonl` 2026-09-06 那条是**全库第一条「题目级」否决**：

> `{"date":"2026-09-06","cid":"2026-09-06_autumn-effect-decay/flagship","verdict":"rejected",`
> `"reason":"olden September, silver October这个话题删除",`
> `"note":"整卡 killed。Andy 09-06 直接毙**题目**，不是毙某一条文案——四条变体与配图占位一并作废，零发布。"}`

**毙的是题目，能执行「这个题目不许再进来」的角色只有信号站——而信号站读不到 verdicts.jsonl。**
这条禁令现在唯一的执行者是「有人记得」。`brain/signals.md` 的弃选案例库里那行「已被 Andy 否过 → verdicts 是信号站的前置过滤」写得明明白白，接线没做。

（同形坑账：`pitfall_tested_the_module_not_the_wiring` · `pitfall_the_ruling_was_in_the_doc_the_tool_was_not`）

## 一、真漏（活着、有内容、信号站没读）

| 路径 | 为什么是选题原料 | 最近写 |
|---|---|---|
| ⭐ `Fluxus_Brand/brain/performance.md` | KEEP/TEST/STOP 就是「什么形状的题该做/该停」，正是信号站缺的弃选前置。**它自己声明了信号站是读者。** | 09-06 |
| ⭐ `Fluxus_Brand/voice/verdicts.jsonl` | 题目级否决的唯一执行点（见上）。09-08 那条还给了可量化病征（零数字/零具体交易＝空）。 | 09-08 |
| ⭐ `data/output/threads/<日期>/messages.json` | **Andy 每天在 Discord 的实时盘面原话**，workflow 每日抓、多频道 + qa 模式。reads 里的 `voice/raw/`（他的口述）只有 6 个文件、停在 09-06；这条每天都在灌。**全仓零个角色契约读它。** | 09-10 |
| `data/research/night_reports/YYYY-MM-DD.md` **正文** | 全库最勤的内容源之一，装 NULL、被复核推翻的结论、自捉的错——现成 BUILD 帖。信号站只读了这个目录的 `INBOX.md` 一节：**订了信箱，没订报纸。** | 09-10 |
| `data/growth/weekly/*.md` | reads 只取 `metrics.csv`（7 行数字），**判断在周记里**（「有锚的周高一个量级，锚一停就回落」）。CASH/BUILD 帖要的是这句，不是那行数。 | 09-07 |
| `data/content/x_watch/scoring/mood_daily.csv` + `scoring/*.md` | 已列的 x_watch 四项都是「谁在说哪个票」；scoring 是**圈子情绪时间序列**（守/攻比、Top3 集中度、圈外起量）。契约第七件要的「屋子多满」其实住在这里。 | 09-10 |
| `Fluxus_Brand/ops/weekly/*_W*.md`（Steve 周报） | 弱一档但真漏：W6 置顶「产线出了四张卡，X 上一条都没出去」本身就是 BUILD 素材；且周报是 signals/performance 的上游。 | 09-06 |
| `data/reference/DATA_RELIABILITY.md` §六缺口台账 | 与 `incidents/` 高度重叠，但**没立档的活缺口只在这里**。弱真漏。 | 09-09 |

## 二、在 reads 里，但已经空转（读了拿不到东西）

⚠️ 这一节比第一节更值钱：**清单长度是 bool，缺口住在集合里。**

| 路径 | 读数 | 问题 |
|---|---|---|
| `Fluxus_Receipts/receipts.md` | 12 行 · mtime **2026-08-08** | **33 天零写入**。契约靠它做「判断到期＝天然选题」，而最后两行是 08-01/08-03 的 ⏳，讲一笔从没成交的交易。它是五件套之一（读主树工作区），主树也没动。 |
| `brain/signals.md` 弃选案例库 | 4 行，全是 08-29 首件 | 之后跑了 3 张卡，**零回填**。契约写着「弃的必须多于取的」，而弃选的记忆没在累积。 |
| `brain/signals.md` 红海记录 | **1 行** | 还是它自己批注为「n=5 单日目测、无留存原始数据」的那一次。13 天 3 张卡零新增。 |
| `brain/authority-clips.md` | 19 行 · 08-31 停 | 上游 `data/research/collection.md` 也停在 08-31 —— **搬运断了**，两头都不动。 |
| `data/content/posts.csv` | 19 行 | 表现回写的全部样本。 |

## 三、逻辑已经过期（裁决改了，判据页没改）

1. `brain/signals.md` 第 3 问（空位）仍写着「**reads 清单里没有任何红海来源**」，并据此留了「没做就声明」的免跑通道。
   而 09-08 维修单已把 **x_watch（正是红海源）**接进契约 reads。**闸的免跑通道还开着，而堵它的数据 09-08 就到了。**
2. `[reader-q]` 这个标签**全仓只出现在发明它的那一行**（signals.md 自己），素材箱 0 条。
   声明过的「读者问题与异议」通道**从没被用过一次**——而 `data/output/threads/` 每天在抓的正是这个。

## 四、两份 reads 清单的双向差集

| | `roles/01_signal.md`（契约） | `brain/signals.md`〈信号来源优先级〉 |
|---|---|---|
| x_watch · claims · incidents · growth · authority-clips · BRAIN | ✅ | ❌ 六项全漏 |
| 挂单板三源（标「建议 Steve」优先） | ❌ | ✅ |
| 读者问题 `[reader-q]` | ❌ | ✅（但从没用过） |

**得先定哪份是权威，否则补哪份都是补一半。**

## 五、查过但判定「不该进」（留痕，免得下次有人重查）

- `brain/hooks|angles|proof|x|newsletter|offers.md` · `voice/Swipe_File|Own_Lines|Ammo_*` —— 各自声明的消费者是分发/角度/查证/旗舰站，是「怎么写」层。信号站不读是对的。
- `campaigns/*/RECORD.md` · `APPROVAL_QUEUE.md` · `data/content/today_draft.md` —— **产线自己的产物/队列**。信号站读它们会形成自循环。
- `data/research/collection.md` —— 与 INBOX 收藏夹节的 `✅ 已处理` 行内容重复，且设计路径是 Steve 周报搬进 `authority-clips.md`（已在 reads）。⚠️ 但那条搬运现在是断的（见第二节）。
- `data/reference/learning_log.jsonl` —— 83 条带 falsifier 的假设账，**全库最像「未兑现的判断」的东西**，但 **08-17 停写**，所属那条线（GEX/期权）不活跃。**那条线复活时它应第一时间进 reads。**
- `docs/trade_analysis/*`（373 笔 Monster 实证）· `Fluxus_Brand/research/*` 拆解档 —— 已由素材箱 / authority-clips 覆盖。
- `data/gex/` · `data/centaur/` · `data/flow/` · `data/snapshots/` · `copybook/*_Ledger.md` —— 死文件（最近写 08-11 ~ 08-18）。

## 六、判断不了（照实写，不猜）

- `Fluxus_Brand/research/Fluxus_Macro_LongEnd_2026-09.md`（09-10 立档，仅一次写入）：意图上是耐久档，但**判断不了会不会被持续追加**。若它变成常写档，它是「外部宏观 → 选题」的入口，而 reads 里没有任何同类来源。
- `BRAIN.md` 有没有已经转述了 performance/verdicts 的要点：没有逐节读完。**即便转述了，转述件不是 append-only 权威源，仍应直连。**

## 七、建议的机制（不只是补清单）

补 8 条 reads 只治这一次。**真正该做的是让「双向声明」可机械对账**：
任何文件头部写了「谁读：X」，X 的 reads 清单里必须出现它——这是一条 `grep` 就能跑的闸。
今天这三处断裂全部符合这个模式，且**没有任何计数维度会因为它而变红**（清单看起来是满的）。

⏸ 等 Andy 点头再动 `roles/01_signal.md` 与 `brain/signals.md`。


---

## 八、✅ 执行（2026-09-10，Andy 裁决后）

**裁决原话**：「以 roles/01_signal.md 为准，三条都接上」。

### 做了什么

1. **三条 reads 接进 [`roles/01_signal.md`](roles/01_signal.md)**：
   - `brain/performance.md`（KEEP/TEST/**STOP**，弃选前置）
   - `voice/verdicts.jsonl`（判决账，含 09-06 那条题目级否决）
   - `data/output/threads/<最近日期>/messages.json`（Andy 每日 Discord 原话）

2. **⛔ 同时立了两道硬闸**——今天全查最大的教训是「**不设闸的 read 是装饰**」：
   `verdicts.jsonl` 被声明为信号站前置过滤已经很久，缺的从来不是声明，是接线和闸。
   - **判决账闸**：取用题目对 verdicts 全量查，命中**题目级**否决即弃，不许改措辞重送。
   - **STOP 闸**：取用形状对 performance.md 的 STOP 列查，命中即弃。
   - 两闸结果写进 RECORD 的 `signal` 节，**查过没命中也要写**；答不上＝没查，退回重做。

3. **`brain/signals.md` 不再是第二份 reads 清单**（这是「以契约为准」的必要动作）：
   - 〈信号来源优先级〉降为**只管扫描顺序**，明写清单以契约为准。
   - 它独有的两项**迁入契约**，不做无声删除：**联邦挂单板三源** · **读者问题 `[reader-q]`**。
     ⚠️ `[reader-q]` 留了痕：全库只出现在发明它的那一行，素材箱 0 条——**声明过、从没用过一次**。
   - 第 3 问（空位）那句「reads 清单里没有任何红海来源」**已过期，更正**：09-08 起 x_watch 就是红海源。
     「③没做就声明」**从今起只在 x_watch 当日无数据时成立**；有数据而没扫＝退回。

### ⭐ 接线时现场量到的一个坑（差点写反）

`data/output/threads/` 必须读 **`git show origin/main:`**，**不能**读主树工作区——**和 x_watch 那条相反**：

| | 谁写 | 哪边新 |
|---|---|---|
| `data/content/x_watch/` | 本机每日跑 | **主树工作区**（契约已注明） |
| `data/output/threads/` | 云端 workflow `daily-content-threads.yml`（22:00 UTC cron，直接 commit） | **origin/main** |

实测：主树那份停在 **2026-07-28**，origin/main 是 **2026-09-10**——**差 44 天**。
照着 x_watch 那条的写法照抄「读主树工作区」，信号站每晚会拿到一份两个月前的快照，**而且不会有任何东西报错**。

### 还没做的（第七节那条机制建议）

「任何文件头部写了『谁读：X』，X 的 reads 里必须出现它」——一条 grep 就能跑的闸。
今天这三处断裂全部符合该模式，且**没有任何计数维度会因为它变红**。
本轮把三个实例修了，**没有修产生它们的机制**。Andy 未裁，留提案。
