# 证据包 · 「延伸到 9.7 个 ATR 之后,同样的止损给出多大仓位」

**口径声明(必须写进任何成稿的注脚):本包所有盘面数字截至 2026-08-27 ET 收盘。**
出处:`data/output/quality.json` → `"date": "2026-08-27"`、`"status": "ok"`、`missing_blocks` 为空;`data/output/universe.json` 与 `data/output/episodic_pivot.json` 共用 `"timestamp": "2026-08-28T03:25:47.716461+00:00"`(= 2026-08-27 23:25 EDT,08-27 收盘后跑的)。
⚠️ 现在是 **2026-08-29 06:xx ET(周六)**。**2026-08-28(周五)整个交易日的数据我们没有** —— 不是「陈旧一场」,是**陈旧两场**(08-28 已收盘 + 周末)。CRM 的 9.68 是 08-27 收盘的读数,08-28 之后可能已经不是这个数。

---

## 已核实主张(每条带出处)

### 1. 四只 EP 的 atr_ext 与 R=0.25% 下的仓位,现场从 `universe.json` 原始字段复算,与信号站给的表**逐位一致**

```bash
python3 -c "
import json
u=json.load(open('data/output/universe.json'))
rows={r['ticker']:r for r in u['rows']}
R=0.25
print('universe timestamp:', u['timestamp'])
for t in ['CRM','VEEV','OKTA','OOMA']:
    r=rows[t]
    atrp=r['atr']/r['close']
    ext=r['sma50_dist']/atrp
    stop=r['sma50_dist']/(1+r['sma50_dist'])
    print(t, round(r['close'],2), round(atrp*100,3), round(r['sma50_dist']*100,2),
          round(ext,2), r['atr_from_sma50'], round(stop*100,2), round(R/stop,2))
"
```

| | close | ATR% | 距50日线 | atr_ext(复算) | `atr_from_sma50`(文件存储) | 止损距离(收盘→50日线,占收盘) | 仓位@R0.25% |
|---|---|---|---|---|---|---|---|
| CRM | 252.05 | 4.225% | 40.91% | **9.68** | 9.68 ✅ | 29.03% | **0.86%** |
| VEEV | 282.13 | 3.988% | 37.51% | **9.41** | 9.41 ✅ | 27.28% | **0.92%** |
| OKTA | 172.91 | 5.381% | 23.68% | **4.40** | 4.40 ✅ | 19.15% | **1.31%** |
| OOMA | 23.04 | 5.600% | 13.47% | **2.41** | 2.41 ✅ | 11.87% | **2.11%** |

复算值与文件里独立存储的 `atr_from_sma50` 列 100% 吻合,不是自证。

### 2. 反事实「退回入场带上沿 ext=4.00」的比值:CRM **49.8%**、VEEV **50.4%** —— 可复现,且「一半」是真结论不是修辞

```bash
python3 - <<'PY'
import json
u=json.load(open('data/output/universe.json'))
rows={r['ticker']:r for r in u['rows']}
R=0.25
stop=lambda d: d/(1+d)
for t in ['CRM','VEEV','OKTA','OOMA']:
    r=rows[t]; a=r['atr']/r['close']; d=r['sma50_dist']
    szn=R/stop(d); sz4=R/stop(4.00*a)
    print(t, round(szn,3), round(sz4,3), round(szn/sz4*100,1))
PY
```

| | 现在仓位 | ext=4.00 时仓位 | 比值 |
|---|---|---|---|
| CRM | 0.861% | 1.729% | **49.8%** |
| VEEV | 0.917% | 1.817% | **50.4%** |
| OKTA | 1.306% | 1.411% | 92.5% |
| OOMA | 2.105% | 1.366% | 154.1%(它比入场带**还近**) |

⚠️ **口径提醒**:天真算法(直接 4.00 / 9.68)给的是 **41.3%**,不是 49.8%。差别来自 `(1+dist)` 那一项(把「距 SMA50 的百分比」换算成「占收盘价的百分比」)。**成稿里若出现 41% 就是算错了。**

### 3. atr_ext 的定义与实现出处已核实,且带一段「本项目自己踩过的坑」的可引用历史

`pipeline/screeners/atr_enrichment.py:48` `atr_multiple_from_sma50()`,docstring 明写来源:Jeff Sun 自己的指标页(2026-08-24 抓取),`A = ATR% = $ATR / last price`、`B = % gain from 50-MA`、`B / A = ATR% multiple from 50-MA`。
同一 docstring 记录:2026-08-24 之前这个函数算的是 `(close - SMA50) / ATR`,是误移植;**MRNA 在 08-21 用旧口径读 5.2(持有区),Deepvue/Jeff Sun 显示 11.2(深度减仓)—— Andy 本人抓到的**;当天 5,327 只里有 110 只在两种口径下落在 ≥7 减仓线的两侧。这是一条**属于我们自己的、可公开的收据**。

### 4. Andy 自己写过的 sizing 原话 —— 逐字,出处为**实际发出去的那一版**

⚠️ 任务书给的两个 brief 文件里**没有**这三句英文原话(详见「反面事实 §8」)。权威源是 `Fluxus_Substack/drafts/mrna_2026-08/PUBLISHED_X_2026-08-24_en.md`,文件头注明:「2026-08-24 21:33 JST 实际发出去的版本(X 长文)https://x.com/Fluxus_Z/status/2091866509748687051 …逐段从线上正文比对回写」。

- **`PUBLISHED_X_2026-08-24_en.md:111-113`**
  > "**Position size is not risk. Stop distance is risk.**
  > **Size = risk budget ÷ stop distance**"
- **`PUBLISHED_X_2026-08-24_en.md:115`**
  > "0.25% ÷ 4.34% ≈ 5%. **I didn't decide on 5%, I arrived at it.** The stop sits **0.73 ATR** from entry — close because the structure is tight, not because I'm brave. I am not brave. And it runs in reverse too: **a sloppy chart with nowhere to put a stop gets a tiny position automatically. I never need discipline to pass on garbage. The arithmetic passes for me.**"
- **`PUBLISHED_X_2026-08-24_en.md:104`**(同一笔的实际账户风险,与 0.25% 的**规则值**不是同一个数)
  > "**Trade 1, the structure:** in 62.72, stop 60, $2.72 a share, account risk **0.217%**."
- **`PUBLISHED_X_2026-08-24_en.md:19`**(副标,0.25% 的公开出处)
  > "*Three filters, five rules, and exactly how much: 0.25% for 23R*"

> **这四条是旗舰站唯一被允许使用的立场来源。** 措辞上要注意:**0.25% 是「1R 的规则值」,0.217% 是「MRNA 那笔的实际账户风险」** —— 变体 B 写 "the same 0.25% of risk" 成立,因为它引的是规则不是那笔。

### 5. 「本篇算术与 Andy 自己的算术同型」可被验证

他公开的除法:`0.25% ÷ 4.34% ≈ 5%`(他自己的四舍五入;精确值 5.76%)。
本篇的除法:`0.25% ÷ 29.03% = 0.86%`。**同一个分子、同一个算符,只换了分母。** 这是本条内容唯一的论证结构 —— 不引入任何新方法。

### 6. 「没人写这个角度」的依据只有 n=5、单日快照 —— 依据本身已核实,但**它很小**

出处:`Fluxus_Brand/ops/briefs/2026-08-28_today_x_options.md:21-30`,五个账号(@firesidealpha 68,980 曝光 / @traderstewie 32,275 / @TedHZhang 14,887 / @RichardMoglen 12,460 / @cfromhertz 11,030),归纳出四个已被占的角度。
**核实结论:仓库里没有任何数据文件保存这次扫描**(`grep -rn "firesidealpha" --include="*.md" --include="*.json" .` 只命中 brief 自身)。
👉 **成稿或内部记录里必须写「n=5 账号,2026-08-28 单日快照,无留存原始数据」,不许写成「全网/普查」。**

### 7. OKTA 的 EP 是唯一一只同时「在 52 周新高上」且「还在入场带附近」的

`universe.json`:OKTA `days_since_52wh = 0`、`high_52w_dist = −0.0111`、`atr_ext = 4.40`、`tradeable = true`。
它是四只里唯一「热点 + 结构还没被吃掉」的一只 —— 如果成稿需要一个「不是全都追不得」的平衡点,这是有数据支撑的那个。

---

## 未证实 / 反面事实

> 以下每一条都**削弱**本论点或本论点的周边表述。全部实测,不是顾虑。

### 1. ⚠️⚠️ 最硬的一条:「以 50 日线为结构止损」是本包**自己引入的假设**,Andy 从没这样做过

他公开的那笔:止损 **0.73 ATR / 4.34%** 距入场。
本包的 CRM:止损 **29.03%**,是他那笔的 **6.7 倍宽**。
把参照换成 21 日 EMA,同一条 R 规则给出完全不同的答案:

```bash
python3 -c "
import json
u=json.load(open('data/output/universe.json'))
rows={r['ticker']:r for r in u['rows']}
for t in ['CRM','VEEV','OKTA','OOMA']:
    r=rows[t]; c=r['close']; s50=c/(1+r['sma50_dist'])
    print(t, round((c-s50)/c*100,2), round(0.25/((c-s50)/c*100)*100,2),
             round((c-r['ema21'])/c*100,2), round(0.25/((c-r['ema21'])/c*100)*100,2))
"
```

| | 止损@50日线 | 仓位 | 止损@21EMA | 仓位 | 差 |
|---|---|---|---|---|---|
| CRM | 29.03% | 0.86% | 20.31% | **1.23%** | +43% |
| VEEV | 27.28% | 0.92% | 15.92% | **1.57%** | +71% |
| OKTA | 19.15% | 1.31% | 17.34% | 1.44% | +10% |

👉 **`0.86%` 这个绝对数字完全由「止损放哪」决定,不由市场决定。** 成稿如果把 0.86% 当成一个客观读数,是不诚实的。**方向性结论(延伸后仓位变小)在两种参照下都成立;绝对数字只在声明了参照之后才成立。**
👉 同理,**49.8% / 50.4% 这两个「一半」也是 50 日线口径下的比值**,换参照会变。

### 2. CRM / VEEV **都不在 52 周新高附近**,「追龙头」这个隐含画面与数据不符

`universe.json`:CRM `days_since_52wh = 166`、`high_52w_dist = −0.0586`;VEEV `days_since_52wh = 223`、`high_52w_dist = −0.0914`。
即:一根跳空把 CRM 拉到**离一个 166 天前设下的高点还差 5.86%** 的位置。
👉 这里的「extended」是**离均线远**,不是**创新高**。任何写成「新高延伸」「龙头突破」的措辞都会被这两个字段直接证伪。

### 3. OOMA 被我们自己的库标为**不可交易**

`tradeable = false`、`avg_volume = 399,880`、`market_cap = $634M`。它出现在 EP 名单里,但不该出现在任何讲仓位的成稿里(而且它的 154.1% 比值会让读者以为「延伸小的票能开更大」是普遍规律 —— 那只是它离均线近)。

### 4. 「四只里三只是软件」与我们自己的 sector 字段不符

`universe.json` 的 `sector` / `industry`:
- CRM = Technology / Software - Application
- OKTA = Technology / Software - Infrastructure
- **VEEV = Healthcare / Health Information Services**
- OOMA = Technology / Software - Application(但 tradeable=false)

Technology 确实是 3/4,但那三只是 **CRM / OKTA / OOMA**,不是 brief 里写的 CRM / OKTA / VEEV。VEEV 在口语上叫 SaaS 没错,但**我们的数据不这样分类** —— 若成稿要说「软件」,得用外部定义,不能宣称是自家数据。

### 5. 「Article 曝光极低(222)」这个载体论据**已过期,且方向被削弱**

`data/content/posts.csv:10`:MRNA 长文 views = **271**(不是两份 brief 反复引用的 222),bookmarks = 1、likes = 5(全库单帖最高赞)。
按 views 排序全库 14 条:**421 / 299 / 272 / 271**。
👉 那篇 Article 现在排 **第 4,只比第 3 名短帖低 1 次曝光**。「三条最高曝光帖全是短帖 vs Article 222」这个对比在当前数据下几乎不成立 —— 真正的落差只有第 1 名(421)那一条。
👉 顺带:brief 写的「421 / 297 / 272」中 **297 应为 299**(`posts.csv` 2026-08-19 那条)。

### 6. 变体 B 的「Four days ago」在今天(2026-08-29)是**五天**

长文发布 2026-08-24;今天 2026-08-29 ET。`(date(2026,8,29)-date(2026,8,24)).days = 5`。这句是唯一一个会被读者一秒查出来的错。

### 7. 色带阈值与被引用的 Jeff Sun 分档**不是同一套数**

`atr_enrichment.py:12-14` 的颜色:green ≤4 / amber ≤6 / **red >6**。
任务书与 docstring:48 引用的 Jeff Sun 分档:0-4 入场 / 5-7 持有 / **≥7 减仓**。
CRM 9.68、VEEV 9.41 在两套下都 ≥7,**这两条安全**;但 OKTA 4.40 落在两套定义之间的空档(代码判 amber,Jeff Sun 的 0-4/5-7 分档没定义 4-5)。若成稿要写「OKTA 还在入场带」,那是**代码色带说的**,不是 Jeff Sun 分档说的。

### 8. 任务书指定的两个 brief 文件里**没有**那三句 sizing 英文原话;而其中一处「Andy 原话」实为 **Steve 起草待核**

- `2026-08-24_mrna_howto_brief.md:41-50` 是 Steve 的 T3 模板,带 `[…]` 占位符,写的是 **portfolio risk <0.2%**(取自 8/19 那条公开帖),不是 0.25%,且全是模板不是成稿。
- `2026-08-23_mrna_longform_structure.md:650` 上方明确标注:**「⚠️ Andy 08-23 要求在这里插一段 R 的概念介绍。以下是 Steve 起的草,请核对。」** —— 其下 652-658 行那段中文「1R = 账户的 0.25% / 仓位 = 风险预算 ÷ 止损距离 / 乱七八糟没地方放止损的图会被算术自动拒绝掉」**是 Steve 写的,不是 Andy 写的,且没有找到 Andy 核准记录**。
👉 **不要引用这两个文件当立场来源。** 唯一经线上正文逐段比对的是 `PUBLISHED_X_2026-08-24_en.md`(见已核实 §4)。

### 9. 「46 账号普查」不是这次红海的证据

`Fluxus_Brand/research/Fluxus_Fintwit_100_Census.md:3-4`:数据抓于 **2026-07-31**,内容是账号档案 / 付费漏斗 / bio,**不是「谁在写今天这个角度」的扫描**。`2026-08-28_1B_fill_in.md:13` 用它论证「宽度描述是红海」,属于跨用途引用。

### 10. 未证实(无法核实,列出以免被当成事实)

- 「热度就今明两天」「9 月是波动大的月份被更正为胜率最低」等 —— 前者无出处;后者出处 `data/reference/seasonality_SPX.json` **本包未复算**(Andy 已定 1B 去掉季节性,不在本轮范围)。
- brief 里五个账号的曝光/收藏比数字 —— 无留存原始数据,只能标「引自 08-28 brief,单日目测」。
- 08-28(周五)CRM/VEEV/OKTA 的实际走势 —— **我们没有**。若成稿在周一发,**必须在 cron 跑完后用同一段脚本重算 atr_ext,再决定 9.68 这个数字还能不能写。**