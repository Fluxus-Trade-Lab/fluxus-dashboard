# KNOWLEDGE.md — 真理地图（哪类问题去哪查）

> Andy 2026-08-27 立项：「目前还没有完整 absolute truth 的资料库」——对。真理**不集中迁移**（搬家=砸断全仓引用），但从今天起有这张地图。每个会话开工遇到「我该信哪份文件」时，答案从这里出。无人值守读权威版一律 `git show origin/main:<path>`（例外：内容台五件套以主树工作区为准，见 CLAUDE.md）。

## 权威层（规矩，冲突时以此为准；改动需 Andy 批）
| 文件 | 管什么 | 更新机制 |
|---|---|---|
| `CLAUDE.md` | 全会话宪法（git/通讯/回执/safe-merge/风格） | OPS 经 Andy 批后改 |
| `TEAM.md` | 花名册/文件边界/单一写入方 | OPS |
| `NOW.md` | Andy 的优先级/关卡/停做清单（只约束 Andy） | Andy 手改 + OPS 代记 |
| `PROJECTS.md` | 生意档案 P0–P7 / 生产线 | OPS |
| `data/reference/DATA_CONTRACTS.md` | 跨线契约与裁决（§七/§12…） | append-only 公箱 |
| `data/reference/DATA_RELIABILITY.md` | 数据可靠性机制 | ALEX 正文 / Joe §六追行 |
| `data/reference/RESEARCH_PROTOCOL.md` | 研究预注册/holdout 协议 | 研究线 |

## 结论层（量过的事实；引用必须带日期——结论会过期）
- `data/research/claims/claims.jsonl` — 研究结论台账（gate_basis / waiver / evidence_grade）
- `data/research/<课题>_*/report|results.md` — 各轮实测原始报告
- `data/research/night_reports/*.md` — Zac 晨报（含 NULL 结果）；`INBOX.md` = 收件与裁决
- `data/growth/weekly/*.md` + `metrics.csv` — 会员/收入的量化事实（PII 在 `private/` 不入库）

## 教训层（防坑账；同形状事故先查这里）
- memory/`MEMORY.md` 索引 + pitfall_* — 各会话共享的防坑账
- `data/reference/incidents/` — 事故档（else 重绑/测试写真树/群发系列…）

## 台账层（append-only 流水）
- `data/content/posts.csv`（发布记录·Steve）· `Fluxus_Receipts/`（交易收据）· `Fluxus_Brand/ops/material_inbox.md`（素材箱）

## 资料层（只读引用区，所有线不改）
- `JeffSun_Wiki/` · `Fluxus_References/` · `SqueezeMetrics/` · `_source_material/` · `data/output/library/`（对外 Library）· `data/research/collection.md`（收藏夹判定归档）

## 数字权威表（Andy 2026-08-27 立：「一个 agent 更新了另一个看不到还去 quote 旧的——完全避免」）
**每个业务数字只有一个家。引用任何数字前必须 `git show origin/main:` 现场读权威源，禁止转抄二手——包括你自己 memory 里的、昨天对话里的、别的文档里的。** 读到的与你记忆不符时，以权威源为准并顺手更正你正要发的内容；发现权威源本身过期，修权威源而不是在别处写新数。

| 数字 | 唯一权威源 | 读法 |
|---|---|---|
| 会员数 / MRR / Discord 人数 | `data/growth/metrics.csv` | 每列取**最后一个非空值并连它所在行的日期一起报**——稀疏表会静默混龄（实测 whop 38 来自 08-25、discord 39 来自 08-24、mrr 1052 来自 08-25，三个数两个日期）；跨列日期不一致时**禁止合并成一句话**。**`discord_members` 一律真人口径（不含 bot 与 owner）**——08-24 行的 39 是含 bot 的旧口径，已作废。列口径见 `data/growth/README.md`「metrics.csv 列口径」 |
| 会员明细 / 身份合并 | `data/growth/private/` 最新 members_master | PII 不出 private |
| 发布记录 / views | `data/content/posts.csv` | 按 post_id 行 |
| 研究结论 | `data/research/claims/claims.jsonl` | 引用带日期与 evidence_grade；**文件含 `#` 注释行，逐行解析前先 `grep -v '^#'`**，或直接用 `pipeline/tools/claim_registry` |
| **对外 YTD（账户口径，含在场浮盈）** | **Portfolio Tracker（前端/Sheet）当日读数** —— ⚠️ **仓库里复算不出来**：`portfolio_YYYY-MM-DD.csv` 只有 trim 腿，能算已实现（08-31 = **+114.36%**），差额是在场持仓浮盈需现价。**取数＝发布当日从 tracker 读并截图存证**，不许转抄上个月的。Andy 2026-09-02 选定此口径。⚠️ **它含浮盈，会往下走**——月度间下降是正常，不是记错 |
| 对外已实现口径（备用） | `data/portfolio/reviews/monthly_*.json` 的 `overall.return_pct`（H1=90.53%）· 或从 `portfolio_*.csv` 的 trim 腿累加 |
| 交易绩效 | `data/portfolio/` performance_review 产物 | ⚠️ 本地目录（gitignored），`git show` 不适用——只能本机读；H1 +90.5% 等口径以此为准 |
| 关卡进度 | 日推第一行 / NOW.md 🎮 节 | |

## SOP 登记处（三次律①的家；成功 ≥3 次的方法固化于此，照抄不重新发明）
| SOP | 全文在 | 登记日 |
|---|---|---|
| 直推 main 标准动作（临时树+丢弃重放+落地核实） | CLAUDE.md 同名节 | 08-29（存量补登） |
| X 单帖免登录抓取（fxtwitter 镜像） | zac-night-study 任务书 §1.5 | 08-29（存量补登） |
| substack_subs 取数 | `data/growth/README.md`（bbe9097c） | 08-29（存量补登） |
| 临时树验收合并（越界检查→测试→rebase→push→删名） | Joe 任务书第五节 + safe-merge 节 | 08-29（存量补登） |
| **一屏决策台（把要 Andy 拍的事收敛成可点的一屏）** | 本表下方〈一屏决策台 SOP〉 | **08-31（Andy 原话「以后都做成这样的，减少决策摩擦和成本」）** |
| **视觉方案选一（把可逆的设计决策做成可点的预览稿）** | 本表下方〈视觉方案选一 SOP〉 | **09-02（三次律①：轨迹图 / Today 版面 / STOP 格连续三次成功；Andy 原话「用了 artifact 非常的直观」）** |

## 一屏决策台 SOP（Andy 2026-08-31 定：「以后都做成这样的，减少决策摩擦和成本」）

**什么时候用**：任何一次要 Andy 拍 **≥3 件**事的场合——周日结算、蒸馏厂审卡、深检后的批量裁决、季度盘点。
**为什么**：他的原话是「入口太多，看不过来不知道在说什么，一个字乱」。摩擦不在「他不想决定」，在**他要先组织语言**。
这个屏把组织语言这件事从他身上拿走：**他只需要指，不需要写。**

**做法**：用 `mcp__visualize__show_widget`（先 `read_me` 取设计规范），页面内用 `sendPrompt(text)` 把选择合成一句话发回聊天。

**六条硬规矩**（不是风格建议，是这个屏能省时间的原因）：
1. **有默认值。** 低风险项默认勾/默认「批」——他改的是例外，不是逐项表态。没有默认＝把工作量还给他。
2. **要他真想的那几条单独隔开**（不同边框/底色），并且**不预设**。混在一起＝他要重新分辨哪些能扫过去。
3. **点不了的不放按钮。** 需要他动手的（发布、进 Discord 改设置）另起一区、灰底、无勾选框——混进按钮组会造出假的完成感。
4. **每条自带判据，不要指向别处。** 「票根是什么」「为什么建议批」写在那一行里。**任何一句「详见 X」都是把他推回入口太多。**
5. **底部一个按钮合成回复。** 他不写字。需要补充的（如「改什么」）用条件出现的输入框，不默认展开。
6. **诚实标注对我不利的项。** 判据会判死我自己的动作时，那一条必须由他按——不许我替他按（08-31 E2 即此例）。

**反例（做过的错）**：把 18 张候选卡混成一堆丢给他——第一张就要口述 8 分钟，那轮「审卡」变成了访谈第 7 轮。分诊后 8 道判断题 + 5 张待口述 + 5 张已自办，才是可点的形状。

**登记**：`fable-ceo-brief` 周日结算节 · `steve-content-weekly-batch` 周报 · 蒸馏站审卡 —— 三处都按此 SOP 出屏。

## 视觉方案选一 SOP（三次律①，2026-09-02 固化）

**什么时候用**：一次**可逆的视觉/版式决策**，选项之间是取舍而不是对错——布局、密度、一个格子里放几样东西、图表怎么画。
（要拍 ≥3 件**不同**的事用上面的〈一屏决策台〉；这条是「一件事、N 个长相」。）

**为什么**：CLAUDE.md 早就写着「前端 UI 永远是给预览挑，不是要不要改」。这条 SOP 是它的**执行形态**——
把"挑"变成一个 token 的回答。三次实测：主题轨迹图、Today 页版面（他选 A）、STOP 格版式（他选 V3）。

**六条硬规矩**：
1. **用他的真实数据画，不用示意数据。** STOP 格那次用的是他截图里那七行的真数；Today 版面那次用的是实测的卡片像素高度。
   假数据的方案对比是假的——差别往往只在真实值的分布里才显现。
2. **把最坏情况放进去。** 最挤的那一行、首屏被截断的那条线。方案的差别不在平均情况，在极端处。
3. **每个方案写代价，不只写好处。** 他挑的是取舍。只写好处＝把判断藏起来，他会退回来问，摩擦就回来了。
4. **答案必须是一个 token**（`A` / `V3`）。他不组织语言。允许混搭（「V2 但 init 放悬停」）但不要求。
5. **确定的部分先做掉，别一起拿去问。** 那次他同一条消息里既有明确指令（「去掉 no wk-20EMA data」）又有开放问题
   （「四个内容挤一格」）——指令当场执行并落 main，只有开放的那半做成预览。把已定的事拿去问是自造摩擦。
6. **给推荐，并说清理由。** 三次里两次他采纳了我的推荐，一次否掉（他选 V3 我推荐 V2）——两种都比"你看着办"快。

⚠️ **交付必须走 Artifact，不能走文件卡片。** 实测踩过：`SendUserFile` 发的 HTML 是**静态渲染，脚本不跑**——
滑块拖不动、悬停无效，他看到的是一张死图并以为是做坏了。发 `Artifact` 才是可交互页面。
（本机 dev server 的 URL 可以附在后面当第二条路，但不能当主路——它要求 App 和服务都开着。）

## 还不存在的（别假装有）
- 全文检索/向量索引：没有，检索靠 grep + 本地图。哪天真需要再立项，先过 MVP 闸。
