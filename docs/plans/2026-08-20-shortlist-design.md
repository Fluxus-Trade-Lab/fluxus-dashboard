# Short List 对照页 · 设计方案（2026-08-20，等 Andy/前端过目）

*Andy："把它做成标准化的产品，每次我问你你都可以这样回答我。然后我想在 Today's List 页面加一个 tab，是我们的 short list comparison page。上面有我们主动添加的名单，加上每天你生成这样的 6 个名字卡片。目标是进行比对，不合适的我会打岔，你可以自我学习我的选择。"*

## 一、一句话架构

**一个卡片引擎，三个出口**：①每晚 cron 产 `shortlist.json`（手动名单 + 6 席自动候选，含图数据）→ 前端 Short List tab 渲染；②Andy 在页面上 ✗/★ → GAS Sheet → 次晚 cron 拉回落档 = 学习语料；③聊天里"核实这几个名字" → 同一引擎出 HTML artifact（今天八股那种）。

## 二、数据端

### 1. 卡片引擎 `pipeline/screeners/name_cards.py`（新，纯函数）
输入 ticker 列表 → 每只一个 card 对象。**页面不算任何东西**（老原则）：
```
card = { ticker, label(主题+四态), verdict(一句话判词，引擎按规则生成),
  readings: { close, chg_pct, rel_volume, rs_1m, rs_3m, rs_line_pctl_21/63,
              atr_from_sma50, high_52w_dist, vcs, trend_base, tml, heat_rank, heat_score, confluence_days },
  series: { d[130], c[130], e21[130], s50[130], v[130] },          // ~3KB/只
  marks:  [ {d, kinds:[EP|4%|NH+RS|x21|x50], chg, rv} ],           // K 线信号日
  panels: [ {date, panel, chg_pct, atr} ],                          // watchlist_hits 摘录
  events: [ {date, screeners[]} ],                                  // ticker_events 近 3 月
  flags:  { chase, near_gate(贴着$20M门), healthcare, in_manual_list } }
```
判词规则 = 八股报告里那套读法（水域→资格→位置→入场刀→名册警示），写成确定性模板，不是自由发挥——同输入必同输出，可测试。

### 2. 六席自动候选（每晚，"六个座位六个问题"）
| 席 | 问题 | 选法（确定性，同分按 h_score） |
|---|---|---|
| ① 在烧 | 今天谁在堆叠信号 | heat 榜第 1 名（排除已在手动名单/昨日六席连任 >2 天的） |
| ② 领跑 | 谁刚成为 TML | true_market_leaders 里 **新进**（昨日不在）h_score 最高者 |
| ③ 入场 | 今天最好的入场刀 | EP 格有则 EP 里 rv 最高；无则「第一波」(4%×ATR≤4×hi20×RS新高) 首名 |
| ④ V 反 | 谁在深回撤后翻身 | ma_reclaim 里离 52 周高 ≤−25% 且 rs_3m 最高者 |
| ⑤ 蓄势 | 谁压得最紧 | vcs 格里 vcs 最高者 |
| ⑥ 资产层 | 资产里谁在领跑 | asset_signals 里 RS 线 21 日=100 且 hi20 的首名（GLD/IBIT 这种） |
空席就空着（比如没有 EP 的日子），空着本身是读数。

### 3. 手动名单 + 打岔回路（复用 GAS 管道，零新基建）
- Google Sheet 加一个 tab `Shortlist`：`ticker, added_date, status(active/vetoed/starred), note, acted_date`。
- 前端加名/✗/★ → 现有 sheetsSync 推 GAS；夜里 cron 用 FLUXUS_GAS_URL 拉回 → 卡片引擎把 manual 名单渲进 shortlist.json，veto/star 落 `data/history/shortlist_feedback.csv`（audit 在册）。
- **学习 = 先记账后建模**（老规矩）：feedback.csv 每行带当时的全套 readings + 来自哪一席。攒 ≥30 个打岔后每周日出一份「你否了什么」分析（哪个席被否率高、被否的和被留的在哪个字段上分得开）；在数字出来之前**不做任何自动调席**。

### 4. 聊天出口
`pipeline/tools/name_cards_html.py`：ticker 列表 → 今天八股这种 HTML。以后你在聊天里报名字，我跑它 + artifact，格式恒定。

## 三、前端（建议，前端定稿）
1. Today's List 顶部加 tab：`晨报 | Short List`。
2. Short List tab = 两段：**我的名单**（手动，可加可删）+ **今日六席**（每席标它回答的问题）。卡片布局照 artifact：图（我们发 series+marks，自绘 SVG/lightweight-charts，信号标记必须叠在图上——TV widget 叠不了我们的标记，不用）+ 读数表 + 判词。
3. 每卡两个钮：**✗ 不合适**（打岔）/ **★ 关注**（进手动名单）→ 走 sheetsSync。✗ 之后卡片灰显不消失（当天还能反悔）。
4. 手动加名：输入框 + 校验（在 universe 或 asset_signals 里才收）。

## 四、边界与老实话
- 六席选法 v1 是拍的（席位问题对、选法内的排序依据是便利选择）——所以先只记账，拿 Andy 的打岔当标注来验，不预设它对。
- series 130 根 × 20 只 ≈ 60KB，可接受；手动名单设上限 20 只。
- 图表口径 = yfinance auto_adjust，与管线一致；拆股日会重绘历史（已知特性）。

## 五、顺序
1. 数据端：name_cards 引擎 + shortlist.json + 六席（1 晚）→ 2. 前端 tab 渲染（shortlist.json 就位后）→ 3. GAS Shortlist tab + 回路（前后端各半）→ 4. 30 个打岔后第一份学习报告。
