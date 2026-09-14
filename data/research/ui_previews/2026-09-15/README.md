# UI 预览稿 · 2026-09-15

**页面**：Library › Model Books · **一处**：Browse 视图的左表 + 右侧详情卡
（`frontend/src/components/modelbooks/BrowseView.jsx:98-161` 卡，`:437-501` 表）。
**⚠️ 不动 dashboard 与 groups 两页；`frontend/` 一个字节没改。** 预览由 [`build.py`](build.py) 读页面自己读的
`frontend/public/data/modelbooks/index.json` + `suspect.json` 生成，说明文字里的数都是脚本算的。

---

## 一、为什么是这一处

**先排除了一个假目标**：headless 量了 14 个页面的「字号×字重×颜色」字数占比（线上站，1440×900，09-15 04:4x JST），
Model Books **99% 的字是 11px**。但 Andy 09-02 定的五档（`a1c39af5`）明写「11 = 标签 / 表格 / 说明」，
那 99% 全是表格单元格——**合规，不是病**。Rotation 的 12px 是 SVG 绘图单位，同一条裁决明文排除。

**真正的病在数据形状**（`index.json` 现读）：

| 读数 | 值 |
|---|---|
| 条目 / 剔除 30 条 suspect 后 | 1,514 / 1,484 |
| 有 pattern 和 key lessons 的（真正的「model book」） | **50** |
| `outcome` 只是把 Gain + Duration 再印一遍的 | **1,464 / 1,514**（全是 Big Movers 源） |
| 默认按 Gain 降序，第一条有标注的排在 | **第 61 行**（首屏约 18 行，0 条有标注） |
| 30 条 suspect 里有标注的 | 0（全是纯价格行） |

所以打开这页，读者首屏看到的是 18 行 3,351%–22,633% 的纯价格行、一列全空的 PATTERN、
卡上「No annotations yet」（纯价格行永远不会有），和卡底一行把上面的数原样再印一遍。
**标题叫 Model Books 的 50 本书，藏在第 61 行以下。**

### ⛳ 迭代时量出来的第二件事：卡上两句话量的不是同一个窗口

有标注的条目，卡上同时有 `Gain / Duration`（按我们发的 K 线算）和 `outcome`（书里写的）。
**50 条里 38 条两边都读得出，其中 32 条相差超过 25%**（倍数或时长任一；25% 是我自造的披露线，不是标准）。
例：TSLA 2020 书上 `10x in 11 months`，K 线窗口 `+1,544.2% in 483 days`；CSCO 1990 书上 `75x in 10 years`，K 线窗口 ×2.0 / 300 天。
另有 10 条没有 K 线涨幅（Chrysler 1962 等），2 条 outcome 不是数（`Multi-bagger`）。
页面现在把两句话都印出来、不说谁是谁，读者只能认为其中一句错了。

---

## 二、四稿 + 两轮迭代

| 稿 | 文件 | 一句话 |
|---|---|---|
| v0 | [`v0_current.html`](v0_current.html) | 现状（对照组） |
| v1 | [`v1_trim.html`](v1_trim.html) | 只删重复与恒空：卡底复述行、「No annotations yet」、空 PATTERN 列；涨幅加千分位 |
| v2 | [`v2_two_books.html`](v2_two_books.html) | 承认是两本书：分段切换 Annotated 50 / Price-only 1,434，默认开前者 |
| v3 | [`v3_annotated_first.html`](v3_annotated_first.html) | 一张表，有标注的置顶，中间一行分隔说明其余是什么 |
| **v2a** | [`v2a_book_vs_chart.html`](v2a_book_vs_chart.html) | 迭代①：卡上两句话各自署名——`This chart +1,544.2% in 483 days` / `The book 10x in 11 months`，并排 |
| **v2b** | [`v2b_price_only_tab.html`](v2b_price_only_tab.html) | 迭代②：胜者的另一个标签页——无 PATTERN 列、一行统计、suspect 开关跟着它藏的那些行走 |

### 评分（Andy 六条，各 0–2；触「新增颜色 / 鸡汤 / 动效」直接判负）

| | 简洁整齐 | 反多巴胺 | 只留交易内容 | 不新增颜色 | 让推理被看懂 | 决策优先 | 合计 |
|---|---|---|---|---|---|---|---|
| v0 现状 | **1** | **1** | 2 | 2 | **0** | **0** | **6** |
| v1 | 2 | **1** | 2 | 2 | **0** | **0** | **7** |
| v2 | 2 | 2 | 2 | 2 | **1** | 2 | **11** |
| v3 | **1** | 2 | 2 | 2 | **1** | **1** | **9** |
| **v2a** | **2** | **2** | **2** | **2** | **2** | **2** | **12** ✅ |
| v2b（v2a 的另一页） | 2 | **1** | 2 | 2 | 2 | **1** | 10 |

**扣分理由**（写具体那一处）：
- v0「简洁」1：一整列恒空 + 卡上同一个数印两遍 + 永远不会兑现的「yet」。「反多巴胺」1：首屏是 18 行千倍股，零条教训——幸存者墙。「推理」0 / 「决策」0：页面叫 Model Books，首屏没有一本书。
- v1「反多巴胺」1、「推理」0、「决策」0：删干净了，但首屏还是那面墙——**删重复不改变读者先看到什么**。
- v2「推理」1：TSLA 卡上 `1544.2% / 483d` 与 `10x in 11 months` 并列不署名，读者会以为有一句是错的。
- v3「简洁」1 与「决策」1：表头写 `GAIN ↓`，可 581% 排在 22,633% 上面——**表头在说谎**；分隔行也破了表格节奏。「推理」1：同 v2 的两句话问题。
- v2b「反多巴胺」1 / 「决策」1：它就是那面墙，只是改成了读者主动点进去才看见。作为 v2a 的第二个状态可以接受，不作为默认。

**颜色**：没有新 token。分段控件用现有 `--color-text` / `--color-surface` / `--color-text-secondary`；落地时应改用站内已有的
`--color-active-tab-bg` / `--color-active-tab-text`（与其他页的选中标签一致）。
**对比度（成对量过，WCAG）**：选中段 surface-on-text **15.34** · 未选段 secondary-on-surface **8.30** · 标签 muted-on-surface **5.61** ·
涨幅 profit-on-surface **8.84** / 偶数行 **8.06**。⚠️ 未选段的底色对页面底色只有 **1.16**——药丸边界几乎看不见，靠文字对比承担，落地时若要边界需加 hairline（现有 `--color-border-light`）。

### 胜者 v2a · 读者比 v0 多知道三件事

1. 这页有**两种东西**：50 本带形态和教训的书，1,434 条只有价格的大涨幅记录——而且先看到的是书；
2. 卡上两个涨幅**量的是不同窗口**，一个是书里写的整段行情，一个是这张图的 K 线区间；
3. 纯价格行**不会有**标注（不再写「yet」），它的数只印一次。

---

## 三、顺带看到的（不在本预览范围，只记事实，归 UI Claire）

- 线上 GNUS 2020 图（`OhlcvChart.jsx`）：价格轴顶端 `12.00` 被裁掉半行；底部一个轴标签被成交量标签 `56.45M` 压住；价格轴画到 0.00 以下。截图在本会话 scratchpad，未入库。
- 页头时间戳显示 `Sep 12, 11:19 AM GMT+9`——用的是 JST 标注；它代表什么（数据更新时刻？）我**没核实**，只记显示形态。

## 四、复现

```bash
python3 data/research/ui_previews/2026-09-15/build.py
# entries 1514 · live 1484 · annotated 50 · price-only 1434 · restate 1464 · first annotated rank 61
```
