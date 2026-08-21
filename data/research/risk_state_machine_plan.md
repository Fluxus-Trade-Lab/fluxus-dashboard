# 自有风险状态机方案（Risk-State Machine）

*2026-08-21 立。上游：turin 复刻全系列（[study](turin_trky_study.md) · [replication plan](turin_trky_replication_plan.md)）。*
*Andy 定调（08-21）：「公开体系当风险状态机全部成立，这部分我们确认了。剩下的需要我们自己找数据和测试。」*
*状态：correction_risk 仍 **parked 不接前端**；本方案全部产出为内部记录。*

---

## 〇、命题

不是「预测回调」，是**用长历史校准的阈值状态机**回答一个问题：**当下的尾部环境属于哪一档，仓位预算该开多大。**

继承的六条设计理念（turin 逆向 + 我们验证）：状态不概率 · 顶底不对称 · edge 在错误成本不对称 · 简单部件+超长历史 · 对齐分档不加权 · **timing 层不碰**（E2/E3 的教训：这套东西掐点全部软，调预算全部硬）。

## 一、已确认的底座（全部上线/可上线，不再测）

| 维度 | 历史 | E1 战绩 | 现状 |
|---|---|---|---|
| VIX 五分位 | 1990+ | 原表 | ✅ 在表 |
| 200dma | 1990+ | 原表 | ✅ 在表 |
| **VIX-TS 三态**（0.8/1.0） | 2006+ | 极差 26.2pp 击败 VIX | ✅ **08-21 进表**（第三维；CBOE 补源已解决 Yahoo 停更） |
| **NHNL**（KY 阈值） | 2001+ | 极差 28.0pp 击败 VIX | ✅ 08-21 起旁注 |
| **GEX 252d 滚动分位** | 2011+ | 每 VIX 档内单调 | ✅ 08-21 起旁注 |
| R2 Nas cumAD | 2007+ | PASS（档差不及 VIX） | 候补，暂不进表（三维 893/格已够薄，四维打住） |

## 二、待测新维度（我们自己的数据；按成本升序）

| # | 维度 | 数据 | 深度 | 测法 |
|---|---|---|---|---|
| N1 | **Credit 趋势态**（E1 唯一未竟项） | HYG adj-close 的 HMA 上/下 + 斜率态 | 2007+，现成 | E1 标准，**下一晚直接跑** |
| N2 | **CFTC 持仓（真 COT/TFF 报告）** | CFTC 官网免费周频 CSV，ES/VIX 期货的资管+杠杆基金净持仓 z | 1986+/2006+，**需新建 fetcher** | E1 标准（周频→日频前向填充）；turin 的 KY 套件有 COT 部件，我们还没有 |
| N3 | **我们的链上真 skew** | `data/reference/skew_log.jsonl`（25Δ risk-reversal，自算） | ⚠ 仅数周 | 只进 ledger。注意：SKEW 指数 E1 反向 NULL，但我们记的是链上口径，**不同量不同名**，独立记 |
| N4 | **自选池 breadth 派生** | breadth_archive（adz2 我们池 PASS 但仅 10 episodes） | 2024+ | 只进 ledger，攒 episodes |
| N5 | **我们 GEX 引擎 levels + flow 读数** | gex 引擎、session_reads（7 个 session） | 周级 | 只进 ledger；兼做 SM 聚合的互验（接 todo_gex_coverage_check） |
| N6 | **量能 breadth（UVOL−DVOL）**：ema19−ema39 振荡器（F&G Remake 部件，08-21 从 TV idea 图上的源码逆向） | TV USI/INDEX: UVOL/DVOL，tvdatafeed | 待探深度 | E1 标准；与家数口径 A/D 分开记账（同族不同量） |
| N7 | **Safe Haven Demand**：SPX−长债 20d 收益差（F&G Remake 部件） | ^GSPC + IEF/TLT（yfinance，ZB1! 的现货替身） | 2002+ | E1 标准，零成本 |
| N8 | **Put/Call（USI:PCC 5d SMA）** | TV USI:PCC，tvdatafeed——**可能补上 E1 当时 P/C 缺席的缺口** | 待探深度 | E1 标准 |
| N9 | **价格×vol 7 日滚动相关**（CC(VIX,close,7)、CC(VVIX,close,7)——他 "VIX7d/VVIX7d" 的真身，背离警告器） | ^VIX/^VVIX + ^GSPC（yfinance，零成本） | ^VVIX 2007+ | E1 标准；这是顶部条件族里唯一的「二阶」量（相关性不是水平），单独记 |

*N6–N9 来源：08-21 收 TV ideas 时在 `This-time-different` 图上发现的 F&G Remake 完整 Pine 源码（`turin_fixtures/tv_ideas/`）。发现晚于 E1 首轮，尚未进任何回测。七部件中 VIX/动量/NHNL 三个与已测同族，Junk Bond 并入 N1 一起测（趋势化 + 利差水平两种用法）。*

**方法闸（预注册，沿用）**：≥60 episodes 的维度走 E1 全套（半样本单调 + 极差对 VIX + VIX 档内增量 + 变换必须滚动分位）；<60 episodes 的**不判定**，进 ledger 攒够再说。盘点纠偏记录：`data/profile/tff_tables.json` 是 market-profile TFF（Jones 1988）不是 CFTC 持仓——名字撞了，别再混（[[pitfall-same-quantity-three-names]]）。

## 三、状态机组装（对齐分档，无权重）

- **主读数** = 表内三维（VIX × 200dma × TS）的格子概率 + n_cell——已在 correction_risk.json
- **Confluence 灯数** = 旁注维度亮灯计数（NHNL oversold / GEX Q1 / credit 趋势下 / …各自过自己的阈值算一盏），0–N 盏，**不加权不平均**——绿/橙/红三档照 turin 的分级语义
- 输出语言 = **仓位预算档**（对接 RegimeBand 的 position language，[[reference-regime-two-band-schemes]]），永不出方向
- 出口只有两个：correction_risk.json（已在，parked）+ regime ledger（下）

### 三·五、P3 灯定义定稿（2026-08-21；实现即规格：`pipeline/risk/regime_ledger.py`）

| 灯 | 点亮条件（= E1 该切的危险极） | E1 历史频率 |
|---|---|---|
| lamp_ts | VIX/VIX3M 3EMA **> 1.0**（backwardation） | 32.1% |
| lamp_nhnl | NYSE NHNL 比率 10d EMA **< 0.30**（washout 区） | 37.2% |
| lamp_credit | HY OAS 滚动 252d 分位 **≥ 0.8**（Q5 走阔） | 34.8% |
| lamp_gex | GEX/px² 滚动 252d 分位 **< 0.2**（Q1 低 gamma） | 21.2% |

规则：灯只计数（0–4）不加权；任一维 staleness > 7 天 → 该灯记缺勤（不点亮也不计入 available）；主读数永远是三维格子概率 + n_cell，灯是语境。R2 Nas cumAD 与后续 PASS 维度一律入灯不入表。

## 四、Forward ledger（信号化讨论的唯一入场券）

- nightly 追加 `data/history/regime_ledger.csv`：date · 各维状态 · 灯数 · spx_close · 各维数据 staleness
- 节律：4–6 周首验（leaders_log 模式）；**6–12 个月 ledger = 将来任何「成为信号/产品」讨论的最低门槛**（接 08-20 大局讨论的结论）
- 实现挂进 run_all 的 correction_risk 步骤旁（同 failure domain 原则：ledger 崩不能连累主输出）

## 四·五、P1 结果（2026-08-21 跑毕；`scripts/research/turin_e1_cuts.py` 追加，明细同 `turin_e1_results.json`）

**N1a HYG 趋势态（turin 定版 filter 的核心部件）：❌ NULL。** 主规格 HMA(100) 半样本翻向（前半 +1.0 / 后半 −1.0），三个周期（50/100/200）极差全部 ≤7.4pp（VIX 同样本 21.7pp）。旁注不删规则：他把它用在**策略内部的 regime filter**，不是表切——两种用法，我们只否证了后者。

**N1b HY OAS 利差水平：主规格 NULL / 滚动变体 ✅ PASS 且第三个击败 VIX。**
- 主规格（全样本五分位，1996+）：极差 23.5pp 但后半样本 ρ 崩到 0.1——25 年的利差长期压缩把绝对档位打穿了
- **滚动 252d 分位五档（robustness 变体）：9.1% / 19.2% / 16.2% / 20.6% / 34.8%**，ρ 0.9/0.9/0.6，极差 **25.7pp > VIX 23.0pp**，每个 VIX 档内方向一致（t3 档内 spread 32.0pp）
- 数据：FRED 免 key 口已收（匿名只给 3 年）；**走 TV 镜像 `FRED:BAMLH0A0HYM2` 拿到 1996-12 起全历史**，已入 `breadth_tv/` 与 fetch 脚本

**⭐ 方法教训第二次应验，升格为屋规**：GEX（08-21 上午）和 OAS（08-21 晚）都是「全样本分位 NULL / 滚动 252d 分位 PASS」——**任何有长期趋势/世代漂移的序列，表切一律默认滚动分位；全样本分位只当 robustness 报**。预注册主规格从此照此写。

**击败 VIX 的维度现在有三个**：vixts3 26.2pp · nhnl3 28.0pp · **credit_oas5_roll 25.7pp**——正好凑齐「vol 期限结构 × 内部宽度 × 信用压力」三个正交家族，P3 组装的灯数骨架就用它们仨 + GEX。

### 四·六、P2 结果（2026-08-21 跑毕；fetcher `scripts/research/fetch_cftc_tff.py`，数据 `data/reference/cftc/`，候选在 turin_e1_cuts.py 11-13）

**N2 CFTC TFF 持仓：三个候选全部 ❌ NULL**（预注册规格：net %OI → 滚动 3 年报告分位 → 五档；日频接合滞后 report+3BD 防前视）：

| 候选 | 表 | 半样本 ρ | 判定 |
|---|---|---|---|
| ES 资管净持仓 | **U 形**：Q1 24.3% / Q3 9.1% / Q5 14.9% | −0.6 / −0.4 / −0.7 | NULL（极差 15.1pp 平 VIX 但不单调） |
| ES 杠杆基金净持仓 | 平：19.0→13.7%，无形状 | −0.4 / −0.6 / **+0.4 翻向** | NULL |
| VIX 杠杆基金净持仓 | 非单调（Q4 25.0% 峰后回落） | 0.8 / 0.5 / 0.4 | NULL |

**两条旁注（不改判定）：**
1. ES 资管的 U 形本身有信息——**两端都危险**（挤空=压力已在场，挤多=自满），单调五档天生量不出这种形状。若将来重访，须预注册「极端度」折叠量（\|rank−0.5\|）为**新实验**，不许在本轮数据上事后换形状。
2. VIX 杠杆持仓的信息集中在高 VIX 档内（档内 spread 37.2pp、方向一致）——又一个「与 VIX 交互」的维度，但独立不过线。
3. 数据资产保留：fetcher 可复跑（Socrata 公开 API 无 key；ES 13874A 连续 1,053 周报 2006+，VIX 1170E1 1,012 周报），将来 turin 的 KY-COT 部件复刻直接用。

**E1 总计分更新：16 个候选（含变体）→ 6 PASS / 10 NULL。** 击败 VIX 的仍是三维：vixts3 · nhnl3 · credit_oas5_roll。COT 不进表也不进灯。

### 四·七、N6–N9 结果（2026-08-21 深夜跑毕；F&G Remake 四部件，候选 14–18）

数据全部到位（`USI:UVOL` 1996+ / `USI:DVOL` 1992+ / `USI:PCC` 2006+ 已入 breadth_tv 与 fetch 脚本；TLT/VVIX 走 yfinance）。预注册：N6/7/8 滚动 252d 分位五档（屋规），N9 相关系数本身有界无漂移用全样本五档。

**五个候选全部 ❌ NULL：**

| 候选 | 表 | 死因 |
|---|---|---|
| n6 量能振荡器（他的原式 ema19−ema39 of UVOL−DVOL） | 21.0→18.4%，平 | 极差仅 3.2pp |
| n7 Safe Haven（SPX−TLT 20d 收益差） | 20.3→15.3% | 后半 ρ −0.3 不稳 |
| n8 put/call（sma5 PCC） | Q5 24.1% 最高（put 堆积=压力已在场，非反向指标） | 半样本 0.4 弱 |
| **n9 价格×VIX 7d 相关** | **完美单调但反向**：Q5（价涨 vol 也涨）11.6% **最低**，Q1 20.2% 最高；ρ −1.0/−0.9/−1.0，36 年 199 episodes，VIX 档内方向全一致 | 极差 8.7pp < 门槛 12.1pp |
| n9 价格×VVIX 版 | 前半正后半负，翻向 | 3.5pp |

**⭐ 第二次出现的反向家族（旁注）**：n9-VIX 与 skew5 同型——**「看得见的对冲需求在场 = 前瞻尾部更安全」**：SKEW 高（尾部保护买盘）更安全、价涨 vol 也涨（涨势带对冲）更安全；真正危险的涨势是把 vol 打趴下的那种。turin 的「价涨 VIX 涨 = 背离警告」在 21d/5%dd 口径上是**反的**（他的用法可能在别的 horizon/语义上成立，照规矩不删他的方法，此为旁注）。这个反向本身单调 36 年、每个 VIX 档内成立——**若将来要用，进灯的方向应是 Q1（vol 被压着的涨势）亮警告，不是 Q5**——但极差不过线，本轮不进任何出口。

**E1 终版记分：21 个候选（含变体）→ 6 PASS / 15 NULL。** 表内三维 + 四盏灯的骨架自 P1 起未被任何新候选撼动——F&G Remake 的七个部件（单测口径）无一进表，与「他的价值在 confluence 不在单件」的判断一致。N 系列测试至此全部收口；下一个节点 = P5 首复盘（4–6 周后）。

## 五、排期与判据

| Phase | 内容 | 量 | 完成判据 |
|---|---|---|---|
| P1 | N1 credit 趋势态过 E1 | 1 晚 | PASS/NULL 落 turin_e1_results.json 同格式 |
| P2 | N2 CFTC fetcher + COT 维度过 E1 | 1–2 晚 | 同上；fetcher 进 scripts/research/ |
| P3 | 组装规格定稿（灯数定义逐维写死） | ✅ **08-21 完成**（§三·五） | 本文档 §三补齐每盏灯的确切阈值 |
| P4 | regime_ledger 上线 nightly | ✅ **08-21 实现并首行落账**：`pipeline/risk/regime_ledger.py`，挂进 run_all（独立 failure domain），幂等，TV/SM 刷新内置降级。首行 2026-08-20：灯 0/4 全灭（ts 0.822 中性 / NHNL 0.767 mid / OAS rank 0.21 / GEX rank 0.24），prob_3d 13.8%。**⚠ 开放项（Andy 拍板）**：GH cron 里生效需 commit `data/reference/breadth_tv/`+`SqueezeMetrics/DIX.csv`（现在均未跟踪，CI 上灯会全缺勤但主读数照记）；tvdatafeed 若要进 CI 另需 workflow 加依赖 | 连续 5 晚成功追加 + staleness 旗工作 |
| P5 | 4–6 周后首次复盘 | — | 复盘报告追加本文档 |

**风险**：外源依赖（TV/SqueezeMetrics/CFTC——fetch 全部可复跑、有 staleness 旗，断供降级为缺勤不误报）；细胞变薄（三维打住，新 PASS 维度一律走灯数不走表）；短历史维度的诱惑（ledger 层永远不判定，别提前毕业）。
