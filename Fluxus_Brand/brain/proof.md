# proof.md — 证据对象清单（campaign 要用的「票根」都登记在此）

> 谁读：查证站（给主张配证据）· 旗舰站（证据先于观点）。谁写：各线糖改道流入，Steve 整理。
> 铁律：**证据对象 = 数字/事实 + 日期 + 出处指针**。本页登记指针不抄数——数字引用前现场读权威源。

## 在册证据对象

| 对象 | 是什么 | 权威源 | 用法 |
|---|---|---|---|
| H1 2026 绩效 | +90.5% · 39.9% WR · 3.40× payoff | `data/portfolio/` performance_review 产物（本地 gitignored，只能本机读） | 大数字只在有完整口径时用；平时用单笔票根更可信 |
| Track record 页 | fluxus-capital.com 公开页（2026-07-26 上线） | 站点本身 | 外链证据，长文可引 |
| MRNA 案例链 | 08-19 入场当天公开帖（post 2090044356，时间戳锚）→ 08-24 四千字复盘长文 | `data/content/posts.csv` + `Fluxus_Substack/drafts/mrna_2026-08/` | **判断→兑现的完整样本**：先公开说，后兑现，链条可查 |
| NULL 结果帖 | 2026-08-09 「测了没用」公开帖 | `Fluxus_Brand/record/2026-08-09_null_result_post.md` | 「不动是主证据」的示范；诚实=差异化 |
| 盘面读数 | regime / 宽度 / atr_ext 分布 | `data/output/` git 历史（按日期 `git show`） | 查证站按日取快照，不引「记忆中的读数」 |
| 研究结论 | 各研究 NULL/阳性 | `data/research/claims/claims.jsonl`（带 evidence_grade） | 引用带日期与等级 |

### 待补的在册对象（08-31 盘点：四问 #2「能用 proof.md 在册对象支撑吗」现在撑不住多数选题）

| 缺什么 | 谁能补 | 补了之后能撑什么选题 |
|---|---|---|
| **单笔交易票根库** | `data/output/trades/<TICKER>_*.json` 已有每笔的 `trade_id`/`realized_R`/`setup_type`/`path_analytics.mfe_R`——**只是没人去取** | 一切「我这样做过、结果如此」的判据帖（入口 3/4） |
| **NULL 结果清单** | `data/research/claims/claims.jsonl` 里 direction=null 的行 | 「测了没用」体裁——别人不敢发的差异化 |
| **踩坑故事** | `data/reference/incidents/` 已有一批（Joe/Zac 投的） | BUILD 帖矿脉（入口 6 反馈环） |
| **判断→兑现链** | `Fluxus_Receipts/receipts.md` 的 ⏳ 到期项 | 最高级证据：先说后验，无法事后编造 |

**这四类都已经在仓库里了**，缺的不是数据是**登记动作**——谁用到就在上表登一行，别每次重新去找。

## 收录规则

- 新证据对象=一行入表（对象/是什么/权威源/用法），谁产出谁登记。
- **时间戳锚帖是最高级证据**（先说后验，无法事后编造）——每笔值得写的交易，入场当天发锚帖，哪怕 38 views（MRNA 加仓追帖实测）也要发：它买的是三个月后的可信度。
