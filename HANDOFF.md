# HANDOFF — 打开这个项目，先读这一页

*一句话用途：**下次开工不用重新解释**。这里只装两样——「现在到哪了」和「下一步是什么」。*
*⚠️ 这份是**索引**，不是第九个信箱。真内容全在下面点名的那些文件里，本页只负责把人送过去。*

**谁维护**：OPS（Fable）在每次有跨线状态变化时改这一页；各线只改自己那一格。
**怎么判断它过期了**：看「最后核对」那一行的日期。超过 3 天没动 = 当参考不当权威，去读它指向的原件。

**最后核对：2026-09-04 · 由 OPS Fable**

---

## 一、这个项目是什么

Fluxus Capital 的市场看板 + 选股器 PWA，外加一整套内容/品牌运营。
Python 管线 → 静态 JSON → React 前端；GitHub Actions 每晚跑数据，Vercel 自动部署。

- 仓库 https://github.com/Fluxus-Trade-Lab/fluxus-dashboard · 线上 https://fluxus-dashboard.vercel.app
- 干活的不是一个会话，是**八条线**（花名册与文件边界：[`TEAM.md`](TEAM.md)）。
  **会话的自述不是权威，`TEAM.md` 才是**——开工先去那里认领自己的线。

## 二、现在到哪了（跨线状态）

| 线 | 在做什么 | 状态 | 权威落点 |
|---|---|---|---|
| **DATA ALEX** | 字段口径整改（108 个字段的产地 + 谁在读 + 对标行业口径） | 🟢 09-04 整包交接完成，七条工单排好 | [`HANDOFF_DATA_field_audit_2026-09-04.md`](data/reference/HANDOFF_DATA_field_audit_2026-09-04.md) |
| **OPS** | 夜间数据可靠性 | 🟢 四条优化 + 分诊器已落地，请求量 ≈15,000→≈8,400 | [事故档 09-04](data/reference/incidents/2026-09-04_we_refetched_data_we_already_had.md) |
| **UI Claire** | 前端 | — | §七 |
| **Marketing Steve / Writer Mia / Studio Q** | 内容线 | 课程 09-20 是当前最大截止日 | [`NOW.md`](NOW.md) |
| **Nighty Zac / Plumber Joe** | 夜间自学 + 数据晨检 | 定时跑，产出进晨报 | [`night_reports/INBOX.md`](data/research/night_reports/INBOX.md) |
| **Growth Gary** | 会员增长台账 | 周记账 | `data/growth/` |

**Andy 的优先级牌在 [`NOW.md`](NOW.md)**——「现在该干嘛」的答案从那里出，不从这一页出。
这一页管**状态**，`NOW.md` 管**他的时间**，两者不重复。

## 三、下一步（有主的事，按线分）

- **DATA ALEX** — `adr_pct` 改算 Qullamaggie 式（我们在算 ATR% 挂 ADR% 的名，过闸集 6.0% 是靠读数偏高混进来的）。工单第 ① 条。
- **OPS** — 明早看 08:15Z 之后哪一班真的调用了 `failure_class`，确认它在云端跑得起来。
- **前端线** — `frontend/src/lib/screenerFilter.js` 整个文件是死代码（唯一调用者 `WatchlistTab.jsx` 全仓无人挂载），删不删待定。
- **Andy 本人** — 见 `NOW.md`；这一页不替他排事。

**待合分支**（产出者没落地权、有权的人不知道有东西等着，是这个项目栽过四次的形状）：
`git branch -r --sort=-committerdate | grep -v main` 现场查，别抄这里的快照。

## 四、交接信息住在哪（这是这一页的主体）

**没有第九个信箱。** 下面八个都是既有的，各管一段，别混：

| 落点 | 装什么 | 什么时候去那里 |
|---|---|---|
| [`CLAUDE.md`](CLAUDE.md) | **规矩本身**（收工三问、直推 main、主树保护六条、通讯录） | 开工前；不确定「能不能这么干」时 |
| [`TEAM.md`](TEAM.md) | 花名册 + 文件边界 + 谁写哪个目录 | 认领身份、判断归属 |
| [`NOW.md`](NOW.md) | **Andy 的**优先级 / 停做清单 / 关卡 | 他问「现在该干嘛」 |
| [`KNOWLEDGE.md`](KNOWLEDGE.md) | 数字权威表 + **SOP 登记处**（三次律①的家） | 引用业务数字前；找已固化的方法 |
| [`DATA_CONTRACTS.md`](data/reference/DATA_CONTRACTS.md) §七/§八 | **跨线投递的唯一权威** | 要给别的线东西时——**写契约行才算送到，消息只是门铃** |
| [`night_reports/INBOX.md`](data/research/night_reports/INBOX.md) | 挂单 · 裁决 · 🔴 哨兵告警 · 收藏夹 | Andy 查「办没办」只看这一处 |
| `night_reports/YYYY-MM-DD.md` | 夜班晨报（首节固定是回执） | 看昨晚发生了什么 |
| [`incidents/`](data/reference/incidents/) | 事故档（根因 + 机制 + 验证） | 同形状的坑第二次出现时 |

⚠️ **`NOW.md` 不是交接文件**——全文 0 次提到「交接」。它只约束 Andy 的时间，AI 的定时任务不受它限制。

## 五、新会话开工的四步

1. 读 [`TEAM.md`](TEAM.md) 认领自己的线，只在自己线的文件边界内写。
2. 读本页第二、三节，知道跨线现在是什么局面。
3. 读 [`CLAUDE.md`](CLAUDE.md)——尤其**直推 main 标准动作**和**主树保护六条**（`git add -A` 在共享主树上会把别人的活卷进你的 commit，这个坑踩过）。
4. 跨线要东西：先写 §七 契约行，再指名发门铃。**永不群发**（同一形状的事故出过四次）。

## 六、这一页不装什么

- 不装 Andy 的待办（那是 `NOW.md`）
- 不装跨线请求（那是 §七）
- 不装夜班结论（那是晨报）
- 不装规矩（那是 `CLAUDE.md`）

**它只回答一个问题：一个刚打开这个仓库的人，需要知道的最少的事是什么。**
写进这里的东西如果在上面任何一个落点里已经有了，**就在这里放链接，不放副本**——
这个项目栽过「同一件事在四个地方各有一份、互相不知道对方改了」的坑。
