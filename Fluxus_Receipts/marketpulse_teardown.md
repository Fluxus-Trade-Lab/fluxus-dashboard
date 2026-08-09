# Market Pulse (Ariel) 拆解 + 主题层设计方案

*marketpulsetrader.org · 调研 2026-08-03 · 未登录,基于公开落地页 + 技术指纹*

---

## 一、他是什么

**定位:** 「A faster way to read the tape」—— **工具**,不是刊物。
**定价:** **$19/月 · $189/年**,一个 plan 无分层,7 天试用。

> 对照:TSF $49(信+平台)· JB $99(数据+信)· **Ariel $19(纯工具)**
> **这是三种不同的生意。$19 是 SaaS 定价,靠量;$99 是 alpha 定价,靠人。**

**技术栈:** React + Vite · **自建后端**(`/api/auth/me`)· 无 Supabase/Firebase/Clerk/Stripe 外露 · 唯一外部依赖是 Google Fonts

---

## 二、六个功能模块 + 数据需求

| # | 模块 | 数据 | 更新 |
|---|---|---|---|
| **01** | **Theme Tracker** —— **140+ sub-industry 排名**,五个 tab:`Themes / Groups / S&P / EqWt / Country`,列 = Today/1W/1M/3M/6M/YTD,**一键下钻到成分股** | Finviz industry 分类 + 全市场行情 | 实时 |
| **02** | **Market Breadth** —— **Stockbee 全套 + 完整历史**:4%+ 涨/跌、5日/10日比率、25%+ 季/月、13%+ 月、25%+ 34 日、T2108、>50sma。可下钻到具体股票 | 全市场日线 | 收盘后 |
| **03** | **Stock Deep-Dive** —— 点任意 ticker:图 + 基本面(利润表/净利/现金流/毛利&opex/EPS/资产负债)+ 新闻 + 所属组 | 基本面 + 新闻 API | 实时 |
| **04** | **Earnings + AI 摘要** —— 周历 + **完整电话会纪要** + **AI 生成 10 点摘要** | 财报日历 + transcripts + LLM | 财报季 |
| **05** | **Gap Scanner** —— 全美股实时跳空,盘前 + 盘后,无需刷新 | 实时行情流 | 实时 |
| **06** | **其余** —— **COT 数据**(ES 期货持仓:小投机/大投机/商业/未平仓)· 美国经济日历 · **5 分钟快照**(S&P 板块 / 等权 ETF / 主题 / 国家基金) | CFTC + 日历 + 行情 | 5 分钟 |
| — | **Spotlight** —— 实时新高新低逐秒打印,哪个 sub-industry 在领涨 | 实时行情流 | 实时 |

---

## 三、和 Fluxus Dashboard 的重叠 / 缺口

### 🔴 直接重叠(你已经有,别重复造)

| 他的 | 你的 |
|---|---|
| **02 Market Breadth**(Stockbee 全套 + 历史) | **`breadth.json` · `stockbee_ratio.json` · `breadth_replay.json` · breadth v2 + Time Machine** —— **你的更强**(有回放) |
| 个股图表 | `data/output/tickers/*.json`(OHLC 2y)+ lightweight-charts |
| 筛选 | `universe.json` 3,000 只 × 54 字段 —— **你的因子比他多** |

### 🟡 他有你没有,但**数据已在手,只差代码**

| 他的 | 你的现状 |
|---|---|
| **140+ sub-industry 排名表** | ✅ **`universe.json` 已有 `industry` 字段 —— 145 个 industry,97 个成分股 ≥8** |
| 多周期列(1W/1M/3M/6M/YTD) | ✅ **已有 `perf_1w/1m/3m/6m/1y/ytd`** |
| 组 → 成分股下钻 | ✅ 数据齐,缺 UI |
| S&P / EqWt / Country 分组 | ✅ `etf_data.json` 138 个 ETF 里已含 RSP/QQQE/各国 ETF |

> **这是本次调研最有价值的一条:他的招牌产品(Theme Tracker),你的原料 100% 齐备。**
> **145 个 industry 的聚合排名 = 一个脚本,不是一个项目。**

### 🟢 他有你没有,且需要新数据源

| 他的 | 成本 | 建议 |
|---|---|---|
| 基本面面板(三大报表) | 中(需基本面 API) | ⚠️ 和你的定位无关,**跳过** |
| 财报 transcripts + AI 摘要 | 高 | ⚠️ **跳过** —— 这是他的差异化,不是你的 |
| 实时 gap scanner | 高(实时流) | ⚠️ 跳过(你不做日内) |
| **COT 数据** | **低(CFTC 免费)** | ✅ **值得** —— 期货持仓,和你 ES 交易直接相关 |
| 经济日历 | 低 | ⚠️ 可选 |
| 实时新高新低 | 高 | 跳过 |

### ⚪ 你有他完全没有

**GEX 引擎 · 期权结构引擎 · 组合与业绩复盘 · sequence mining · ticker events 信号史 · AI Coach · 仓位系统**

> **他是"读盘工具",你是"决策系统"。** 他不碰仓位、不碰业绩、不碰期权。**两个产品其实不在同一条赛道上。**

---

## 四、三种分类法对照 —— 这是主题层的核心决策

| | **TSF** | **Market Pulse** | **你现在** |
|---|---|---|---|
| 粒度 | **53 个策展主题** | **145 个 Finviz industry** | **145 个 industry(已有,未用)** |
| 方式 | 人工,叙事驱动 | 机械,完整 | — |
| 含因子? | ✅ Growth/High Beta/Value Factor | ❌ | ❌ |
| 含名单? | ✅ IBD 50 / IPOs / Microcaps / High Octane | ❌ | ❌ |
| 跨行业主题? | ✅ AI-Datacenters 横跨半导体+公用+工业+REIT | ❌ **表达不了** | ❌ |
| 维护成本 | **高** | **零** | 零 |

### 结论:两层,不是二选一

```
第 1 层  行业层(机械)   145 个 Finviz industry     零维护,完整,客观
第 2 层  主题层(策展)   ~28 个跨行业主题           抓真实的交易,需维护
```

**TSF 只有第 2 层。Market Pulse 只有第 1 层。两层都有是真差异化,而且第 1 层免费。**

**为什么第 2 层不可省:** 「AI 数据中心」这笔交易横跨半导体、公用事业、工业、REIT。**行业分类永远表达不了它 —— 而那正是过去两年最大的一笔交易。**

---

## 五、主题层方案:28 个主题 + 成分股怎么定

### 选题原则

只收**行业分类表达不了的**。行业已经覆盖的(Biotechnology、Banks - Regional、Restaurants…)不重复。

### 建议清单

**A · 跨行业叙事(11)** —— 行业层完全无法表达
```
AI - 数据中心 · AI - 电力与基础设施 · AI - 广义
机器人与自动化 · 太空 · 无人机 · 量子计算
电网与电气化 · 再工业化/回流 · 减肥药 GLP-1 · 加密股权
```

**B · 资源与能源(6)**
```
铀与核能 · 锂与电池 · 稀土与关键矿产 · 铜 · 黄金矿 · 白银矿
```

**C · 地理(4)** —— `etf_data.json` 已有对应 ETF
```
中国科技(KWEB/FXI)· 印度(INDA)· 日本(EWJ)· 拉美(EWZ/ECH)
```

**D · 因子与名单(7)** —— **行业分类完全没有这一类,但交易上最有用**
```
High Octane(高 ADR + 高动能)· 成长因子 · 价值因子 · 高 Beta
微盘 · 近期 IPO · 52 周新高龙头
```

### 成分股怎么定 —— 用 ETF 持仓做种子

**别手工维护 53 张名单(TSF 的做法,一年多的活)。**

```
主题成分股 = (代表 ETF 的持仓 ∩ 你的 3,000 只宇宙) + 手工增补 − 手工剔除
```

你的 `pipeline/constants/tickers.py` **已经有 138 个 ETF**,大部分主题现成有代理:

| 主题 | 代理 ETF(已在你的列表里) |
|---|---|
| 半导体 | `SMH` |
| 网络安全 | `CIBR` |
| 软件 | `IGV` `WCLD` |
| 国防 | `ITA` |
| 太空/无人机 | `ARKX`(需加) |
| 机器人 | `ROBO` `DRIV` |
| 铀核能 | `URA` |
| 锂电池 | `LIT` |
| 稀土 | `REMX` |
| 太阳能 | `TAN` · 清洁能源 `ICLN` |
| 铜 | `CPER` |
| 金矿/银矿 | `GDX` `SILJ` |
| 中国科技 | `KWEB` `FXI` `GXC` `MCHI` |
| 加密股权 | `BLOK` `WGMI` |
| 投机科技 | `ARKK` `ARKF` `ARKG` |
| 基建 | `PAVE` |
| 电网/公用 | `UTES` `XLU` |
| AI | `AIQ` |

**只有「AI-数据中心」「AI-电力」「减肥药」「High Octane」「再工业化」这几个需要手工建表 —— 5 张表,不是 53 张。**

因子类(High Octane / 微盘 / 52 周新高)**完全由 `universe.json` 的字段规则生成,零维护**:
```
High Octane  = adr_pct >= 5 且 rs_ibd >= 90 且 market_cap >= 3e8
微盘         = market_cap < 1e9
52 周新高龙头 = high_52w_dist >= -0.05 且 rs_ibd >= 85
```

---

## 六、RS 加速度 —— 最便宜的补丁

### 问题

`rs_21d / rs_63d / rs_126d` 是**累计窗口**,不是不相交窗口。TSF 用的是不相交的(`RS 0-2w` / `2-4w ago` / `4-6w ago`),这样才能算加速度。

### 解法:从累计反推不相交,不需要新数据

```python
# 不相交区间收益(用已有的 perf_* 字段)
r_0_1w   = perf_1w
r_1w_1m  = (1+perf_1m) / (1+perf_1w) - 1
r_1m_3m  = (1+perf_3m) / (1+perf_1m) - 1
r_3m_6m  = (1+perf_6m) / (1+perf_3m) - 1

# 相对强度 = 自己 − SPY(同区间)
rs_bucket = r_bucket - spy_r_bucket

# 加速度 = 近端 RS − 远端 RS
rs_accel = rs_0_1w - rs_1w_1m
```

### 四态分类(照 TSF 的定义)

| 态 | 条件 |
|---|---|
| **Leading** | `rs_1m > 0` 且 `rs_accel > 0` |
| **Weakening** | `rs_1m > 0` 且 `rs_accel <= 0` |
| **Improving** | `rs_1m <= 0` 且 `rs_accel > 0` |
| **Lagging** | `rs_1m <= 0` 且 `rs_accel <= 0` |

**这套公式对个股、industry、主题三层通用** —— 组层面就是成分股等权聚合。

---

## 七、建议顺序

| | 动作 | 工作量 | 说明 |
|---|---|---|---|
| **1** | **RS 加速度 + 四态**(个股层) | **半天** | 纯计算,零新数据 |
| **2** | **145 个 industry 聚合排名**(多周期表) | **1–2 天** | 数据全在,MP 的招牌产品 |
| **3** | industry 四态分类 | 半天 | 依赖 1+2 |
| **4** | **28 个主题 + ETF 持仓做种子** | 3–5 天 | 需要拉 ETF 持仓 |
| **5** | 因子类主题(规则生成) | 半天 | 纯规则 |
| **6** | COT 数据(CFTC 免费) | 1 天 | 和你 ES 交易相关 |
| — | ~~基本面 / transcripts / gap scanner / 实时流~~ | — | **跳过,不是你的赛道** |

**做完 1–3(约 3 天),你就同时有了 Market Pulse 的招牌产品和 TSF 的四态分类,而且 breadth 那块你本来就比他们强。**

**主题层(4–5)才是真正的差异化 —— 因为它是 `04_POSITIONING.md` 那条链的中间环节:**
```
regime  →  主题 RS 与四态  →  单主题风险上限 1.5%  →  仓位数字
```
**没有主题层,「单主题 ≤1.5%」这条风控规则就落不了地。** 这一层你迟早要建,和竞品无关。
