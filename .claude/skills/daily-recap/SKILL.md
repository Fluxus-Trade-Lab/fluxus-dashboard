---
name: daily-recap
description: 用我们自己的数据 + Andy 自己的话，生成每日市场复盘（Daily Market Recap，中英双语 PDF）。凡 Andy 提到 复盘/recap/briefing/DailyBriefing/市场总结/收盘总结/双语 PDF/Revere/YouTube transcript 对比/给会员的日报——即使他没说「做复盘」三个字、即使只是给了一个 YouTube 链接或让改 PDF 里的一处——都必须先读本 skill 再动手：里面有他亲定的三条法、四问、均线规则、截图规则与裁决记录，跳过任何一条都会重演已付过学费的错误。产出是给 Andy 审的底稿，判断句留白，机器永不代他下判断。
when_to_use: 复盘、recap、briefing、market recap、每日市场、生成 PDF 底稿。不触发：盘中提醒、个股 tearsheet（有专门 skill）、Substack 周刊（另一条流程）。
owner: ops
---

# daily-recap — 你的数据认形态，Andy 的话下判断

> 2026-09-05/06 一天六轮实测纠正换来的。每条判据都带他的原话出处，改这份文件前先读裁决记录。
> 口径引用 `data/reference/METRIC_SOURCES.md`，**本文件不重复定义任何指标**。

## 三条法（Andy 2026-09-06 亲定，凌驾一切）

- **A · 无标准（或标准不指这件事）——不得当标准读数上页。** 自造的量必须自报家门。
- **B · 有标准但本仓库算不出——那就不用。** 不许用近似量顶替（例：FTD / distribution day 需要指数日成交量，`data/output/` 没有 → 这两个词不出现，直到数据源补上）。
- **C · 判断力是 Andy 的。** 判断句只从他的 Discord #live-commentary 与 Founders Note 取，润色限于补主语、接句、加标点——**不加他没说过的判断**。命名权（谁是 the tell、关键位在哪、教学选题）一律留白，标 `⟨Andy⟩`。

## 一行值不值得印（四问，全过才印）

1. **它昨天是什么？** 一样就删——没变的状态没有信息量（他原话：「他今天站上 50 均线，他昨天也站上 50 均线了，所以你在说这个传达什么信息呢」）。「没变」本身是新闻时报连续次数，不报状态。
2. **数字核过原始字段吗？** 位置字段（`*_dist` / `atr_from_*`）≠ 事件字段（`cross_*`）。09-05 一天读反两次，方向全错。他的话：「数据一定要准确，这个是无法原谅的错误。」
3. **评论有指向性吗？** 评论要有，但一句；「读数 + 感想」（That's the whole spread 之类）等于没写。
4. **说法有出处吗？** 查 METRIC_SOURCES.md。没登记的说法不用（09-05 把财报大跌错叫 intermediate climax top——O'Neil 的口径根本不指那个）。

## 均线规则

- **只以事件出现**：reclaimed / lost / rejected / 贴着。永不写「在 X 均上方」。
- **分尺度**：5/8 日＝动能呼吸（丢了常是噪音）· 21EMA＝强势股生命线 · 50 日＝中期/机构成本 · 200 日＝牛熊界（他的规则七：「跌破 200 日之前谈不上真正的麻烦」）。同一个 lost，尺度差三个量级，不许平铺。
- **震荡闸（先过闸再报事件）**：排列（8>21>50 或全反）+ 斜率同向 + 缠绕度（三线最大间距/ATR，暂用 1.5 阈值，待标定）。三项不全成立＝震荡盘，**一个均线事件都不报**，改报结构位与相对强度——他 09-02 期原文：「in a flat market the moving average is noise; the level that holds or fails is the signal」（trigger over indicator）。
- **均线交叉**（20/50、50/200）是换季信号，频率低含义重，单独一行，不与日内事件混排。

## 结构（对齐他的 PDF 规格 `Daily_Recap_Workflow_Spec.md`，每节一句话职责）

1. **标题**：paraphrase 当天性格 + 谁领涨 + 谁是问题；基调色 涨绿/跌红/震荡蓝
2. **The Big Picture**：一段，两拍（见裁决记录 [2026-09-19]），写法约束见 [2026-09-22] 与 [2026-09-23]（判据前置 / 反事实 / 判断带风险条款）。骨架用他当天 Discord 的句子（例：「QQQ starts acting strong while SPY weaker now. since semi and mags are stronger」），每句挂上量化它的读数
3. **Index Action**：三列等宽表 `% | 技术变化（事件！）| 关键位/备注`；关键位是判断 → `⟨Andy⟩`
4. **Founders Note**：他手写的，Sheet 里取；取不到留白，永不代笔
5. **What Led**：按板块分组，个股一行＝名字+%+RS+事件；**他点过名的票必须在**（Top watch / 论点股 / doing good 的全算）；**领涨落后每行必须写出驱动的 ticker**（Andy 2026-09-15），只有真正无单票可指的整组状态变化才允许没有 ticker
6. **What Lagged / Blew Up**：不 working 的是画面的一半；财报失望（数据源补齐前只写他提到的）
7. **主线深挖**：当天唯一最大的事（09-04＝Memory & Storage），成分展开、放量与站位分开说
8. **（仅周五）Weekly**：周收盘视角——`perf_1w`、`wk_ema10/20`、`three_weeks_tight`、`rs_0_1w`；他的话：「weekly close very important」。30 周线补上前不引 Weinstein stage
9. **Session Commentary（盘中评论，2026-09-15 立）**：Discord 里当天盘中说的话——被拒的反弹、守住的位置、"卖方控盘"这类实时判断、点名某只票——放这里，不进 Tomorrow。`content_*.json` 字段 `session_commentary`（数组，可省略），中性口吻不署名，同三条法 C
10. **Tomorrow**：加速度排名在这儿用——他的口径是**为明天做准备**，不是描述昨天，只写下一交易日的关键位/事件/待验证问题；写成「看什么」清单。**盘中已经发生的观察不放这里**（见第 9 条）
11. **The Rules**：他的七条，固定文本照抄
12. **Portfolio Update**：指标条+截图+一句中性点评；依赖他先更新 tracker（人肉前置，堵了就留占位）；**cost / stop / TRIM / CLOSE 改成 R 阶梯，见裁决记录 [2026-09-23]**

## 工作流

⚠️ **title 带「试跑」**：先看「试跑铁律」一节（本文件靠后），`export FLUXUS_RECAP_ROOT=…` 再往下走——日刊没有例外。

1. 读当天 `data/output/`：breadth（state_board/mm/verdict）· groups（themes/industries 的 state+accel+perf_1d）· rotation（cuts+verdict）· asset_signals（`*_dist`+`rs_line_pctl_21`+`rel_volume`）· universe（个股 RS/量比/`atr_from_sma50`）· shortlist · market_health（算排列/斜率/缠绕）
2. **对昨日做差**（breadth_archive / groups_history / asset_signals.csv）——只留变了的格子
3. 收 Andy 当天的话：Discord #live-commentary（截图或导出）+ Founders Note；一句都不许丢
4. 过四问 + 均线规则 + 三条法，拼结构
5. 交给 Andy：留白处标 `⟨Andy⟩`，数字全部可溯源（每个数标来源字段）
6. **他给 Revere transcript 之后**才做 diff：「他们有而我们没有的」记进本文件裁决记录，逐条决定融不融

## 裁决记录

### [2026-09-05] 建账日六轮纠正（全部他原话，出处 `Fluxus_Brand/ops/briefs/2026-09-05_andy_review_process.md`）
- 「你有很多很多的废话」→ 一行一件事；「就是一句话 Index is not market」但那句也「没有指向性」
- 「我没有让你直接去数字就够了……评论是要加的但只需要加一句话」
- 「memory 和 storage 这点是对的……应该继续深入进去」→ 主线深挖节
- 「其他的板块呢？比方说软件比方说大科技 mag7……在变差的板块是什么」→ What Lagged 必有
- 「今天站上 50 均线，他昨天也站上 50 均线了，你在说这个传达什么信息呢」→ 四问第 1 条
- 「数据一定要准确，这个是无法原谅的错误」（21 均方向全反）→ 四问第 2 条
### [2026-09-06] 三条法 + 口语裁定
- 「候选行批了……"hot potato" / "the tell" / "lone standout" 都是口语，忽略」——口语可出现在他自己的句子里，机器不主动用
- A/B 两条法原话见顶部；「最后是没有判断力」→ C 条
### [2026-09-06] 周五规格
- 「周五的复盘通常可以加上一些周线级别的复盘信息。只针对周五」

### [2026-09-06] 首次对卷（eval #1 · 09-04 vs Revere transcript vs 旧工具 PDF）
- **偷来的框架一件：三档 gauge（短/中/长）+ 升降级事件**。短=周收 vs 21EMA，中=中小盘 vs 50 日，长=200 日。
  形态天然满足「只报变化」，且全部可算——加进结构第 0 节，Bottom line 一句跟在后面。
- **周五的财报动作用周框架**：DELL 我写成周五 +1.5%，真故事是周 +15%/周量 200%。周五版里
  财报驱动的名字一律标 W、给周读数。
- **报自家清单的当日成绩**（shortlist 六席 / zones）——对标方每天报 21over21/Turbo12/Mag7，我们有清单没报过。
- **外部补入一律标 ◇**：新闻、缺失指数（MDY/VIX/DXY）、读图结论（DTL/launchpad/pivot 位）。
  ◇ 是引用不是背书；图形结构语言仍属 A 法（要么 Andy 读图，要么不写）。
- **我们的数字当裁判**：transcript 自打架（小盘均线在头顶 vs Russell 在 50/100 上方），
  我方 IWM 50 日下方 −0.34% 裁定前者对。对卷时凡数字冲突，以可溯源字段为准并标注。
- HOOD/META 论点股：无新事件仍可入——挂在「行情对论点的回应」下（HOOD 周 +16.5% 收复 120◇）。
### [2026-09-06] 五档放行
Andy 原话「可以放行 这个五档是可以用的」——自家五档（Defence / Caution / Neutral / Constructive / Euphoria）
连同其中的 Neutral 一词照用；它是我们的方案，不算借词。复盘与页面继续用它，三套档位词的收敛不再立项。
### [2026-09-06] 展现形态第一轮（PDF v1 → v2，全部他指示）
- **未验证的判定框架不上页**：「三个时间尺度 我们还没有验证三个时间级别的判定条件，先不放。short term 为什么用一个 weekly 21ema 来验证？？？」——短/中/长期的判定条件先立标准、再验证、才能印；A 法适用于框架不只适用于指标
- **截图用亮主题底色**，不用暗底（playwright `colorScheme:'light'`）
- **Portfolio 以他最后发布的版本为权威**：生成前对照他最新交付物（老工具 PDF/tracker），不是本地最近一张截图——09-04 他的 tracker 已从 7 仓并成 3 名（ZETA、HOOD ×2、ETHA），我用了旧图
- 正文里的方法论注脚（均线缠绕闸说明）与页脚数据出处段：**内部规则不上成品页**——留在工作稿 md，PDF 只给读者要读的
### [2026-09-06] 截图规则（他原话「这几张截图都是有问题，原因之一是通过浏览器数据可能并不及时」）
- **截图前先核数据新鲜度**，按页面的数据源分两类：
  - **静态 JSON 页**（Dashboard / Themes，读 `data/output/*.json`）：headless 可截，但先确认当天收盘数据已落 main（页面顶部日期栏 = 天然核验水印，截出来必须是目标交易日）
  - **浏览器状态页**（Portfolio，数据走 Google Sheets sync + localStorage）：**headless 干净 profile 里永远是空/旧的，禁止用无状态浏览器截**——只能用 Andy 自己浏览器的截图，或他最后交付物（上一份 PDF）里抽出的图。09-06 实测栽过：本地最近一张截图是 7 仓旧版，他的 tracker 已并成 3 名
- **Founders Note 不截图**：最新内容在 Sheet 里，pipeline 能直接拿到文本——取文字进正文，不走图。（待接：pipeline 读 Founders Note 的取数路径）
- 三尺度框架：他 09-06 裁「不急」——进停车场，立标准+验证之前不重提
### [2026-09-06] Founders Note 取数已接（他指示「把 founders note 的 pipeline 取数接上」）
- 工具：`pipeline/tools/founders_note.py --date YYYY-MM-DD`（GAS Meta tab，key `writing:founders-daily:YYYY-MM`）；凭证 `.env` 的 GAS_URL / GAS_SYNC_TOKEN（token 他一次性填，浏览器扩展保护读不出）
- **日期对位是判断，留给 Andy**：他的复盘写在次日早晨——9/4 场的 note 实测是 **09-06 那条**（「AI trade rallies. MU/SNDK leads. Split tape」），而 09-04 那条是 NFP 前对周四的看法。取数取 T 与 T 后第一条，两条都给他挑，机器不定
### [2026-09-06] 收口（他原话「嗯收口」）——skill 实验第一轮完整闭环
- **Founders Note 日期对位首例**：9/4 场用的是 09-06 那条（次日早晨写的才是对上一场的复盘）；「取 T 与 T 后第一条给他挑」的规则经实战确认
- **中文成品走 fable-voice 文风账**：ZH 版不是 EN 的翻译层，是按文风账重写的一版——能逐字倒译回英文的句子就重写。他裁「中文不行，改改中文」后全篇过账，v3 获批
- 完整产线定型：数据读取 → 四问过滤 → Andy 原话收集 → founders_note.py 取 note → 亮主题截图（静态页）/ 他交付物抽图（Portfolio）→ 双语 HTML → weasyprint → pdftotext 禁词 grep → 交付。工具与脚本：`pipeline/tools/founders_note.py` + 会话存档的 build_recap.py（待固化位置，下轮迁入 pipeline/content/）
- 补：他说的「中文表达训练」= `biaoda` skill（~/Desktop/中文表达训练/ 的说明书与风格卡，他自己训练的）。**下轮起 ZH 版过两本账：fable-voice（治翻译腔）+ biaoda（他的风格卡）**，本轮只过了前者

### [2026-09-06] 全系统裁决落地 + gotcha 收编第一批（Andy 原话「同意啊 我们就应该用workflow和create skill机制。全系统范围内的。而且确认要能用上，description变pushy」）
- 本 skill 的 description 已按裁决 pushy 化（触发场景全列进 description——官方治 undertrigger 的标准修法）
- **PDF/截图产线 gotcha 收编**（原散在 memory/会话，官方姿势是长在 skill 里）：
  1. **CJK 字体**：weasyprint 走 fontconfig，**不认 PingFang**（.ttc 未被索引）——中文栈用 `"Hiragino Sans GB","Heiti SC"`，等宽块用 `Menlo,"Hiragino Sans GB",monospace`（Menlo 无 CJK，漏兜底=豆腐块）；渲染后必 rasterize 页 1 视觉核对
  2. **macOS 截图文件名**含 U+202F（PM 前的窄不换行空格）——路径永不手打，用 glob 取真实路径、`Path.as_uri()` 编码
  3. **weasyprint 环境**：PEP 668 挡 pip --user，装在 venv（当前 /tmp/pdfenv，重启即失；固化位置待迁 pipeline/content/）
  4. **成品终检三件套**：pdftotext 禁词 grep（Spec §4 名单 + 领导力）必须 0 命中 · 每页 rasterize 过目 · 图片渲染进来了没有（weasyprint 图片路径错是静默跳过，不报错）

### [2026-09-13] 自动化立项：四条裁决 + 持仓口径（设计全文 `docs/superpowers/specs/2026-09-13-daily-recap-automation-design.md`，Andy「Spec同意」）
- **Big Picture 以字幕叙事为主**（他选「照原 spec，字幕叙事为主」）：对 Big Picture 取代三条法 C 的「判断句只取他原话」；其余节的数据规则不变，教学选题的命名权仍归他
- **教育选题**（他选「早上递 A/B，挑完出成品」）：机器出两个、他挑一个，不回就等，永不替他选；调试样张默认 A 并在交付说明写明
- **送达**「10:30 JST 前」· **首跑**「09-15 周二」· 首跑前先交过去一周样张（他原话「先做过去这一周的每天复盘和每周复盘，作为调试的样本」）
- **持仓只用 R 与 %**（他原话「管线只做R 和%, 不写股数和美元」）：Portfolio Update 从 GAS 直取、只算 R/%——**取代 09-06「以他最后交付物/截图为权威」那条**
- **仓库是公开的**：字幕、材料包、PDF、持仓数据一律不进 git，只存本机
- weasyprint 环境固化位置定为 `~/.venvs/fluxus-recap`（取代上文 gotcha 3 的 /tmp/pdfenv）

### [2026-09-13] 口吻与 Founders Note（Andy 原话）
- **正文不出现「Andy 说」，也不用第一人称**（「正文里不出现Andy 说这样的字眼，也不用第一人称」）：他 Discord 里的判断改写成中性陈述句融进正文，忠实转述、不加判断、不加强语气；英文原句可加引号但不署名、不挂时间戳；表格备注栏不写「Andy:」。成品闸加一道：pdftotext 文本「Andy」= 0。三条法 C 仍然有效——判断的**来源**只能是他的话，变的只是**不署名**
- **Founders Note 取不到或没写：整节不出现，页面不提示**（「Founders note如果连接不上，可以空着，有时候我没有写，写的时候可以加上」）；GAS 失败只进交付说明，不挡出片。取代上文「取不到留白」的写法——留白是「不出现」，不是印一个空框

### [2026-09-13] 更正：The Rules 不是「固定七条照抄」（结构第 10 条那句写错了）
- 证据：Andy 自动化前手工出的 `Market_Recap_2026-09-01/02/03_EN.pdf`，第 1–6 条**每天按当天行情重写**（09-01「Failed breakout + swing failure is the pattern」、09-02「7,620 must hold」、09-03「Trade the leaders: crypto, software…」），**只有第 7 条固定**：「Never serious trouble until S&P breaks the 200-day」+ 当天一句读法。他的 spec §3 第 10 条原文就是「最后一条**通常**是……」
- 执行口径：第 1–6 条当天写（来源守数据规则与口吻规则：不署名、不用第一人称）；第 7 条固定开头
- 教训：写 skill 条款时我没去对他真实出过的成品，凭一句概括定成了「固定文本」；差点让样张 agent 把对的改成错的。**立规则前先拿他发布过的成品对一遍**
- 补记（同日）：上一条教训里的「差点」不准确——样张 agent 已经照错误指令把 9/4 的七条抄成常量，印到 09-08..09-11 四份和周复盘上（出现「7,800 pivot」「只做 DELL、CRCL、HOOD」等过期话），并已发给 Andy；是 agent 自己在交付说明里指出的。成品闸新增：第 1–6 条与 9/4 文本相同或近似即报红

### [2026-09-13] 成品样式与选题（Andy 原话「A登记体可以，默认教育选题是A, 保证每周内容不会太重复」；前一句「我喜欢这种视觉和排版的哎」）
- **成品视觉 = Visual 线复盘视觉系统（9/11 周刊那版 CSS 照抄），排版定 A 登记体**：生产只出 A；版式归 Visual Vera，产线只供内容文件
- **教育默认 A、不等人**：内容照出 A/B 两题（B 也写好正文与示意图参数），正文按 A 出片；取代同日上午「早上递 A/B，挑完出成品」的等待关卡。B 只进给他的交付说明，他说换就 `--edu B` 重出
- **会员版 PDF 不放选题卡**（「A · 默认 / B · 备选」是内部挑选信息，同「内部规则不上成品页」）；给他看的预览页保留
- **每周不太重复**：教育选题台账（本机 `_ledger/edu_topics.jsonl`，含他 spec §5 已用题材）——新 A/B 与近 20 个交易日 concept 相同或题目相似 ≥0.6 即换题，周刊 A 不与本周日刊撞 concept；同周内纪律 1–6、明天看什么、Big Picture 首句逐条与本周已出各期比，≥0.75 即重写（周刊对本周日刊放宽到 0.85；第 7 条固定开头不计）

### [2026-09-13] X 帖、字号、专名（Andy 原话）
- **X 帖 = 结构句 + Big Picture 全文 + cashtag**（「X短文结构先行，不过太短了，我是会员，可以写更多。直接用the big picture的文字可以吗？」→ 对规则「Big Picture 第一句已在讲结构就直接用，否则前面加一句结构句」回「是好主意」）：正文逐字取 Big Picture（去 `<b>` 与 ◇），不再二次创作；结构句与 Big Picture 首句相似 ≥0.4 视为重复、省略；总长 ≤1,500 字符（会员长帖上限 25,000）。取代同日下午 v1/v2 两个 ≤280 短帖变体
- **PDF 内容栏字号放大到 12–13pt**（「PDF文字小了点…可否用12-13？同时保证还是只用4页，第5页是portfolio update」）：实测原来正文约 10pt、表格约 9.5pt；在守住「4 页内容 + 第 5 页组合更新」前提下取可行最大值，放不下时拿取舍方案问他，不删内容
- **「Grow」屏蔽**（「"Grow"也是专有词，也屏蔽」）：视频趋势仪表盘状态名，区分大小写
- **「theme week」类缩写禁用**（他读成「theme weak」的错字）：一周涨跌写成 over the week / 1-week / 本周；自动字幕 week/weak 易混，交付说明列出来自字幕叙事的相关句供人工扫

- 字号补定（Andy「对，我倾向用正文12, 其他以此类推。」）：**打印正文 12pt**，表格/标签/标题按「12 ÷ 原正文实测磅值」同比放大（原正文约 9.9pt → 约 1.2 倍）；4 页内容 + 第 5 页组合更新的约束不变，放不下拿取舍方案问他，不降字号、不删内容
- **PDF 字号 gotcha（09-13，OPS 自己量错过一次）**：①`pdftotext -bbox` 的行框高度不是字号——9.9pt 行框对应的正文实为 8.67pt，量字号要拿已知字号的同段文字单独打印对照；②Chrome 打印时只要有元素比 A4 版心宽（当时四张 nowrap 表并排到 1,051px），整页会被静默缩印（倍数 0.924），CSS 写多大都白写——打印样式里宽块改上下排，并用「新旧行框之比 = 目标字号 ÷ 原实测字号」复核（12 ÷ 8.67 = 1.38，实测 1.38）
- X 帖 cashtag 与链接（Andy「X挑选不用禁止cash出现当前持仓，就挑当天复盘里出现的个股，Substack帖子末尾就不用出现。」）：cashtag **只取当天复盘正文里出现过的个股**，不避开持仓（闸 P3）；X 帖末尾**不放 Substack 链接或引导语**
- 字号定稿（Andy「表格用9.5， 正文用10.5，这样距离更加舒适。」）：**正文 10.5pt、表格 9.5pt**，行距比维持 1.4–1.5（12pt 那版行距比只有 1.31，他判定「设计上退步」）；页边距 12mm
- 教育段允许跨页（Andy「教育段可以跨页」）：撤销「必须整段在一页」，改成唯一底线是**不许在句子/段落中间断页**
- 日刊页数新标准（Andy「接受日刊变成5+1的组合，只要除了教育和portfolio update之外的内容能够全部进入这前4页就算通过。」）：教育、组合更新之外的内容必须在前 4 页放完；组合更新独占最后一页；教育段可在第 4 页收尾也可溢到第 5 页——日刊因此是 5 页或 6 页，不再强求死磕 4+1
- 这轮只重出 09-11 与 W37（Andy「不需要重出5期，只需要出W37和9/11这两个。」）；09-08/09/10 维持原样不动
- 周刊封面掉落线标签更正（Andy「首页的"1M · DROP #W37 · 2026-08-13 → 2026-09-11 · SPX · ∫ = 1.000 M" 这周的开始弄错了。」）：日期本身没错（SPX 过去 21 个交易日的技术窗口，本来就往前推约一个月），错在标签写成周号 `#W37`，和一串非本周日期挤在一行会读成「第 37 周从 8/13 开始」——**改成按该期最后交易日的日期式标签（如 `#0911`），日刊周刊统一**；`No. W37` 刊号留在报头不动，不接日期
- ↳ **更正（Andy 09-14，原话「那个周的困惑没有去除」，引用原文 `1M · DROP #0911 · 2026-08-13 → 2026-09-11`）：**「日期式标签」这条判断没错，但实现把日期的横杠删掉了（`String(is.D).slice(5).replace("-", "")`），周刊的 `#0911` 和当天日刊自己的刊号 `#0911`（`is.no`，同样无横杠）长得一模一样，换汤没换药——读者分不清这是「本周窗口截止日」还是「误标了某天的日刊」。**修法：保留横杠**（`String(is.D).slice(5)` 不再 `.replace`），周刊渲染成 `#09-11`，日刊仍是 `#0911`，两者在字形上就能分开。`recap_page.js` `regLine()` 一处，`9b5a9bbc`。
- 最后一页加免责声明 + 账号（Andy「最后一页，加入disclaimer和twitter handle/官网」）：文案取自仓库现成的 `Fluxus_Substack/templates/post_footer.html`，去掉第一人称改成复盘的客观口吻——EN「Nothing here is advice or a recommendation to buy or sell anything. Measure your own water.」/ ZH「这里不给建议，也不劝人买卖。量好自己的水。」（过 fable-voice，保留他原话「量好自己的水」）；接 `@Fluxus_Z · fluxus-capital.com`；挂在组合更新节末尾，永远落在最后一页页脚，日刊周刊、中英文都有；不算组合更新正文，不影响 L1/X1 两道闸

### [2026-09-13] 掉落线定稿（Andy 原话依次：「太粗了！！方案取消，换成原来的。」→「落点 / 删副标题是要的。」→「让线尽量在宽度和高度上占领视觉空间的中心大部分。」）
- **线**：粗细保持 2.5px。`stroke-width` 是非缩放描边，单位就是屏幕像素；当晚有一版把它当 viewBox 单位反解，渲染出 14–18px，被判「太粗」
- **位置**：sheet-1 的 `.drop.thin` 由固定 46px 高改为**水平居中、占版心宽 84%、高度随曲线自适应**；不撑满整栏（此前「宽度方面不要太撑住全部空间」）
- **落点**：当天收盘处一个空心圆，fill `var(--sheet)`、stroke `var(--accent)` 2.5px，半径 4.5px（按打印版心 704px × 84% 换算成 viewBox 单位）。不编码任何行情数字：大小/环/刻度/收尾变粗四个情绪编码方案已否（「落点这些方案不行」），裂纹落点暂停（「大改动也暂停」）
- **副标题**：sheet-1 标题下的 `byline` 删除
- 预览 artifact 058faf91；源头 Visual 线 design/marketing-visual；产线落地步骤见 DATA_CONTRACTS §七 同日 Visual Vera → OPS Fable 行。版式归 Visual Vera，改线的粗细、位置、落点或副标题前先读这条
- ↳ ✅ 已落地代码（09-14，`f0e4d760`）：三处改完，09-11 daily + W37 weekly 重渲染闸全绿，收据见 DATA_CONTRACTS §七 同条 OPS 回执行。

### [2026-09-13] 主标题折行定稿（Andy 看完三栏对照原话「采用推荐的」）
- 原因：`.hl-a{text-wrap:balance}` 把两行排成等长，第一行在版心一半多就折（Andy「到了中间就另起了一行」）；中文字少多数一行放得下，但 9/11 中文同样中折且拆开「硬｜件」
- **定稿**：一行放不下时在标题自己的破折号处折——英文 `—` 用不断行空格粘在前一个词后，中文 `——` 整体留在行尾；前半句自己超过一行时退回 `text-wrap:pretty`（排满、末行不留一两个词）；`word-break:keep-all`，中文不拆词
- 对照页 artifact ec9a593b（10 个真实 EN/ZH 标题）；产线落地步骤见 DATA_CONTRACTS §七 同日 Visual Vera → OPS Fable「主标题折行」行。版式归 Visual Vera
- ↳ ✅ 已落地代码（09-14，`d62c313a`，首次回执 `f0e4d760`/`5fccd259` 有误，Vera 核验后按她两点修正重做）：四张核验图核对通过，收据见 DATA_CONTRACTS §七 同条 OPS 回执行。

### [2026-09-14] 掉落线改 5 个交易日；日报灰尾、周报全橙；周报标签写周（Andy 原话「视觉上，线的展示变成用最近5个交易日的数据。SPX 日报呈现：最近一个交易日用橙色，其他用渐变灰（像尾巴）。下方文字 1M DROP #09-11 周报呈现：最近5个交易日全部用橙色，无渐变。下方文字1M DROP Week37 2026-09-08 向右箭头 2026-09-11」）
- **困惑的真因**（此前两轮都诊断错）：不是标签 `#W37`/`#0911`，是周刊封面下那段 21 日数据窗口 `2026-08-13 → 2026-09-11`——印在「WEEKLY · W37」报头下，读成「这一周」。09-13 那条「周刊封面掉落线标签更正」只改了标签，没动日期区间
- **数据**：SPX 最近 5 个收盘（`visual.DROP_SESSIONS = 5`，原 21）；x 轴总跨度仍按 20 单位，线高与 21 日版同一比例
- **日报**：最后一个交易日那段用 accent 橙，之前几段用 muted 灰、越早越淡（渐变）；标签 `1M · DROP #09-11 · SPX · ∫ = 1.000 M`，不再印日期区间
- **周报**：整条 accent 橙、无渐变；标签 `1M · DROP WEEK37 · 2026-09-08 → 2026-09-11 · SPX · ∫ = 1.000 M`，区间是**当周交易日**，不是数据窗口
- 落点空心圆、线宽 2.5px、84% 居中不变；`SPX · ∫ = 1.000 M` 尾巴 Andy 未提，暂保留
- ↳ **更正（Andy 09-14「删除啊！」）**：`SPX · ∫ = 1.000 M` 尾巴删除，标签到日期/区间为止（`95a5a859`）
- ↳ **分页（Visual Vera 09-14 核出）**：线加高后 09-11 EN 的大字状态行被切成两页；`.state-row` 进打印不断开名单，闸 L3 查「/ N votes」与状态词同一行（`1de3e32e`）
- 代码 `93803e32`；版式归 Visual Vera，源头设计稿请同步（§七 同日 OPS → Visual Vera 行）
- ↳ **Visual Vera 判（09-14）已落地 `9ac2faa2`**：一天一段——日报 6 个收盘（橙段即最后一个交易日）；周报=上周最后收盘+本周每个交易日（劳动节周 5 点）；`dropLine` x 跨度 10；`.drop.thin` `max-height:160px`（线高中位约 99px）
- ↳ **Visual Vera 判（09-14，OPS 交来的两处）**：①**一天 = 一段**——日报画 6 个收盘（5 段涨跌，橙色即最后一天那段），周报画「上周最后一个收盘 + 本周每个交易日」（劳动节周 5 点），线与标签日期一致；②**加高**——`dropLine()` 横向跨度 20 → 10，`.drop.thin` 加 `max-height:160px`，比例每期固定。依据与落地步骤见 DATA_CONTRACTS §七 同日 OPS → Visual Vera 行下的 Visual Vera 判。

### [2026-09-14] 掉落线改用 SPX 60 分钟 K、平滑半天（Andy 原话「我选择了SPX 60分钟 平滑度半天」；此前「肯定是锯齿状不用想的，我们追求美感，不追求准确度。大致像当日的走势就行」）
- **数据**：`^GSPC` 60 分钟收盘，fetch 步骤写进 `pack/spx_60m.json`（本机，不进 git）；render 只读缓存。Yahoo 60 分钟 K 留 730 天、30/15/5 分钟只留 60 天（09-14 实测）——选 60 分钟就是为了随时可补，**暂不另建长期存档**；已出过的期数靠各自 pack 里的缓存可重出
- **窗口**：日报 = 前一交易日最后一根 + 最近 5 个交易日每一根；周报 = 上周最后一根 + 本周每一根；`spx_cut` 标出最后一个交易日的起点，橙段正好是这一天
- **平滑**：高斯，窗口 195 分钟（3.25 根，σ = 半窗），首尾两点保持真实收盘；几何沿用 `dropLine()`（x 跨度 10、Chaikin 三轮、160px 封顶）
- 灰尾、周报全橙、标签、落点、线宽不变。对照页 artifact 7605aade（K 线周期 × 平滑 21 格）。代码 `b87eb7c0`

### [2026-09-15] Session Commentary 独立成节 + 领涨落后必须带 ticker（Andy 原话：「1. DISCORD内容应该是变成"盘中评论"，而不是"下个交易日看什么"。2. 主题和行业的领涨落后 要写上ticker名字。3. 这些改动下次生效。不需要改动已经生成的pdf」）
- **09-14 v2 出片时的错法**：把 Discord 盘中观察（"开盘一小时抄底全落空""PLTR 第一次被 20EMA 挡回""原油顶到趋势线压力位"）塞进了 Tomorrow——那些是**已经发生**的盘中读数，不是「为明天做准备」的看什么清单，两者被 09-06 定的 Tomorrow 口径（「为明天做准备，不是描述昨天」）互斥
- **修法**：新增字段 `session_commentary`（数组，可省略），独立渲染一节「Session Commentary / 盘中评论」，位置在 Sentiment 之后、Tomorrow 之前；Tomorrow 收紧为只装下一交易日的关键位/事件/待验证问题。落地在 `pipeline/content/recap/visual.py`（`keep` 元组）、`run.py`（`headings()`）、`visual_assets/recap_page.js`（layout A/B 都加了，生产只出 A）、`dedupe.py`（R2 同周查重覆盖新字段）、`xpost.py`（P3 cashtag 来源字段覆盖新字段）、`CONTENT_SCHEMA.md`
- **领涨落后（What Led/Lagged）**：note 里必须写出驱动的 ticker，不能只写板块名和百分比；只有真正无单票可指的整组状态变化行才允许没有 ticker
- **只对下次生效**：09-14 已出的两版 PDF 不重出，此次改动是产线机制，不是内容勘误
- 未做：没有加硬闸拦截「note 里零 ticker」——09-11 的合法样本里就有整组无 ticker 的行（如「元器件 / 通信设备」一行），硬闸会误杀；先靠这条记录和 schema 文档的书面要求执行，真出现第二次漏写再考虑机制化（三次律）

### [2026-09-19] Big Picture 两拍 + 对照组 + 他点的教育题 + PDF 递进会话（Andy 当日原话逐条）
- **诊断**（他：「我现在总是觉得现有复盘版本是大量的数据堆砌，少了insight，big picture得总结质量不高」；对卷后「你的对照是准确的」）：09-18 首版 Big Picture 约 30 个数、先报数后无判断；字幕版约 8 个数，先定性、把事件串成有名字的线（回踩 7,580 → 守 100 日 → 反包 → 跟进＝洗盘）。09-13「以字幕叙事为主」那条我没执行到位。
- **Big Picture 两拍**（「目前的改法，我批了：Big Picture 固定成三拍，全段不超过 8 个数，其余数字都放到下面的表格里。① 一句定性：市场现在处在什么阶段、变化在哪里。② 故事线：一周或一天是怎么走过来的，外部结论标 ◇。第三个分歧和验证不需要。」）：①一句定性，不含数字；②故事线，外部结论标 ◇；全段 ≤8 个数（价格/百分比/家数/周数；均线周期名不计），其余数进表格。**不写「Discord vs 视频」的分歧**——「我在discord的发言本来就是单独成为一个环节的…并不一定和视频冲突」，Discord 只进盘中评论节。
- **对照组**（「我需要你整理一版（对照组），纯粹是来自字幕的每日复盘…目的是学习写作」「这个对照组只需要英文，内容都来自字幕。这样你每天交付3个文件」）：每日多出一份 EN 纯字幕版 PDF（不掺我方数据/Discord，字幕数字照写，去专名，无持仓动作），模板在本机 `_templates/control_transcript_recap_template.html`；外加写作学习建议（「然后出一个每天的写作学习建议。我们下周测试」）。都只存本机。
- **PDF 递进会话**（「PDF需要能够让我直接在这个会话当中 看到并且打开而不是给我 文件的地址」）：SendUserFile display=render，只给路径＝没交付。
- **Discord 只读 live-commentary + 互帮互助**（「Discord 不需要全频道必读」）；导出标签 trading-floor/互帮互助 对调，已交 DATA ALEX（§七 09-19 行）。
- **他点的教育题压过台账闸**（「新的教育选题 用 neWS FailIure」→「改」）：选项写 `picked_by_andy: <原话>`，R1 放行；新增 `news_failure` 示意图（`6de15be7`）。
- **标题也是定性 + 故事，不用数字解释**（「9/18的标题是否也不要用数字去解释。比如这次写qqq 过720，但2/3还没上车 这个就还是需要定性+故事。看看字幕对照组」）：标题、副标题不出现价位/百分比/家数，写成「发生了什么 —— 意味着什么」。09-18 改为「The Shakeout Is Over for the Indexes — Crypto Ignites, the Average Stock Waits」/「指数洗完了盘——加密点火，普通股票还在等」。日刊周刊都适用。
- **周复盘同样两拍**（「周复盘也一起改成两拍」）：① 这一周处在什么阶段、变化在哪里 ② 这一周怎么一天天走过来的；≤8 个数。


### [2026-09-22] 对照组漏出 + 中文教材语气 + ◇ 要有出处（Andy 当日原话逐条）
- **漏出**（「你没有按照我之前要求的来。我需要一份纯粹是从字幕里产生的版本英文pdf，作为比较参照。还有一个要求我已经不记得了」）：09-19 的对照组裁决只写进了本节，没写进守护进程的出片任务模板（fluxus-ops `schedule.json` 的 `ops-recap-daily`），worker 照模板跑，09-21 只出了两份。「不记得的那个」＝每日写作学习建议。已补进模板第 4.5 步；递送单也改为三份 PDF + writing_note。**裁决要同时落 skill 和任务模板，只落一处＝下一班照旧。**
- **中文用教材语气**（「中文版可能太口语了，需要点写教材的语气」）：ZH 是重写，但语域是交易教材讲案例——陈述句、术语准确、少口头语和俚语式比喻（09-21 例：「捅开」「扛着」「接走」「压着」）。
- **◇ 要能指到出处**：09-21 Big Picture 把「AMD–Meta 扩大合作 ◇」写成跳空的原因，字幕里没有，材料包里也只有 Discord 一句「OPEN AI and META are big customers」。指不到出处的事件不进 Big Picture。
- **Big Picture 学对照组的写法**（「没讲清楚我的要求，中文版也按教材语气改，big picture学习字幕参照组。1999的案例今天不用写进去」；前一轮他的读法：「文风字幕好很多。传达的大方向信息和我们一样」）：短句，一句只讲一件事；领涨按组写，每组挂 1–2 只代表个股和涨幅（v3 全删个股被他打回：「个股你去掉了，我觉得去掉的太多」），其余进表格；分化写完立即给「因为」（09-21：美元）；最后一句换尺度（周线 / 季节性 / 历史），但不是每个字幕素材都要用——09-21 的 1929/1999 罕见统计他裁定不写。09-21 v3 样本：定性句 → 趋势线与底部 → 窄领涨（大市值、CPU、AI 存储）→ 分化 + 美元原因 → 新低 16:1 → 季节性收尾，全段 4 个数。ZH 全文（含教育、纪律、盘中评论、表格备注）都按教材语气改，改长了就删例子，不降字号。**语域取中**（「在之前口语化的版本和现在的教材版本之间找到一个平衡，语言简洁的平衡，和突出重点信息。另外标题也是要改的内容之一。口语化不行」）：不用俚语动词（捅开/扛着/接走），也不堆「位于…之上」「由…降至…」这类公文腔；短句、主谓直给，标题同样适用（EN 也不用 never showed up 这类口语）。v4 样本：「指数突破上周的整理区间，重回上升趋势；但推动突破的是大市值股票，不是整个市场。」
- **教育题术语用标准中文译名，并附英文原名**（「凹槽支点 英文也给出」「也确认中文专业术语是不是凹槽支点」）：写之前先查原书中文版或主流中文社区的译法，标题和正文第一次出现时写成「中文（English）」。09-21 例：pocket pivot 的标准译名是「口袋支点」（Kacher & Morales《像欧奈尔信徒一样交易》中文版），我们原先写的「凹槽支点」是自造的；示意图标注在 `visual_figs.py` 里同步改（已合 main `ef9707a6`）。

### [2026-09-23] 对照组三条差距入规（Andy 原话「把这三条差距写进复盘的写作规则里，你改进学习」；来源 09-22 对照组 `writing_note_2026-09-22.md`）

三条都是**写法约束，不是造判断**——素材（字幕叙事 / 他的话）里有就写出来，没有就整句不写，三条法 C 不变。适用于 Big Picture 两拍与纪律 1–6，日刊周刊通用。

1. **判据前置，结论后置。** 先写「这种局面接下来要求什么」，再写它发生了没有；不许把判词甩在最前面，让读者只能接受、无法自己复核。
   - ✗ 09-22 我们：「Monday's breakout passed its first test: the gap was not given back.」
   - ✓ 对照组：「What a strong Monday asks for on Tuesday is that nothing be given back, and nothing was.」
   - 人工自检：Big Picture 第一拍出现 passed / failed / confirmed / held 这类判词时，它前面必须已经有一把尺子。

2. **至少一句反事实**——写出「本来不想看到什么，而它没发生」。信号常常是某样东西的缺席；不写出来，发生了的事就没有重量。
   - ✓ 对照组：「What was wanted after that was the absence of a hard reversal of the kind the tape kept producing between August 4th and last Wednesday.」
   - 素材里找不到「没发生的那件事」就不写，不许编一个出来凑。

3. **进攻性判断自带风险条款。** 凡是指向「该站在哪边、该拿什么」的句子，同一句或下一句必须交代错了怎么办（止损方式或失效条件），出处同判断本身。
   - ✗ 09-22 我们：「the position belongs where relative strength already is.」后面没有下文，判断是悬空的。
   - ✓ 对照组讲小盘超卖：「the discipline is a tight stop rather than a moving-average confirmation… If it fails, it fails.」

↳ **当天就踩的坑（Andy 贴回改写的开头，原话「写的很 ai 就是废话多。没有了以前的简练」）**：
**判据前置 ≠ 加一句解释。** 尺子可以只有半句，不要把它讲清楚。
- ✗ 我第一版：「A gap that closes at the top of its range asks one thing of the next session: give nothing back. Tuesday gave nothing back — and the choppy tape that produced a hard reversal every few days from early August through last Wednesday did not come back with it ◇.」——定语、从句、同位语全堆上，比它要替掉的那句还长
- ✓ 改完：「Monday's gap asked one thing of Tuesday: give nothing back. Nothing was. The hard reversals that ran through August did not come ◇.」——三句短句，三条约束全在，比原版还短
- 风险条款同理：`carried on tight stops and abandoned quickly if the tape stops cooperating` → `on tight stops, out quickly if it stops working`。
**三条约束都不应该让段落变长**——加了尺子、反事实、止损之后，字数还应该持平或变少；变长了就是写成了解释。

**不让的部分**（对照组没有、我们保留）：广度读数是量出来的、能追到字段（09-22 的 324/170、McClellan −22.3 → −10.8、T2108 31.6 → 33.4）；What Led/Lagged 每行点名驱动的 ticker。**两边数字冲突以我方字段为准，并写清是哪一种口径**——对照组说的多是指数/ETF，我方常是成分组内均值（09-22 半导体 +0.8% vs Semiconductors Broad +2.25%、Mag 7 −0.55% vs Tech Mega Caps 9 只 −0.63% 都是这个差，不是错）。


### [2026-09-23] Portfolio Update 改成 R 阶梯：cost / stop / TRIM / CLOSE 全上页（Andy 原话两句）

> 「下个版本把 portfolio的cost和stop写进去，TRIM和CLOSE position也写进入。」
> 「以多少R的形式，不出现美元数值。」

第二句是口径：**页上不出现任何每股价格、美元金额、股数**，全部用 R 与 %。
entry 就是 R 的零点，所以一个仓位在页上是一条三点阶梯：
`cost = 0R` · `stop = (stop_price − entry_price) / R_dollars`（初始止损定义上就是 −1.0R，trail 过的会是正数）· `now = open_R`。
- **印的是当前 stop**（他 trail 止损，2026-08-17 裁决，`sheets_source.py:31-33`）；`initial_stop` 只当 R 的分母，不单独上页。
  `initial_stop` 缺失时 `unknown_r=True`，该仓位 stop 栏留空，不猜。
- **TRIM / CLOSE** 走 `trims[]`（`type` 能分两者）：每条腿印「日期 · TRIM 掉 <占原仓位 %> · 该腿 +X.XXR」或「日期 · CLOSE · 全笔合计 +X.XXR」；
  每腿 R 沿用 `build_pack.py` 里已有的那行，**不另算一套**；占比用 `qty / original_qty`（百分比，不是股数）；窗口是 `period_start`→D。
- 这条**不推翻** 2026-09-13 的「只用 R 与 %」，是它的展开：cost 与 stop 化成 R 之后不含账户规模信息，也推不出股数。
- 落地单 `T-0923-51`（fluxus-ops，P1），含要改的五处与验收；**money 闸要跟着收紧**，并按两个失效方向各造一个阳性对照（漏改 / 改了但接错），两边都判红才算闸有效。
↳ ✅ **已落地（同日）**：Andy 确认「明天的复盘直接按新的R阶梯出。印的是当前的stop。initialStop 缺失的仓位 stop 栏留空不猜。」
  字段与渲染规格看 `CONTENT_SCHEMA.md` 〈Portfolio: the R ladder〉；标签要补 `pos_stop` 与 `legs_title`（缺了会按语言兑底，不会在中文页印英文）。
  实测：09-22 真书干跑，8 个仓位的 stop_R 从 −1.00R（PLTR 新仓）到 +1.96R（HOOD 锁利），TRIM/CLOSE 三行合计 +2.17R，与 `realized_R_period` 逐字对上；ZH 全闸绿，L1 不受影响。


### [2026-09-24] 标题定式：两个对仗短句，事件一句、含义一句，不加情绪（Andy 批「这个ok」）

09-23 我出的 `The Leaders Went Last — and Mostly Did Not Go` 他判「标题模糊…你训练地相对消极，看空。
leaders went last感觉是盘面要完蛋了。参照文写的是"A RED DAY THE LEADERS SAT OUT，three macro headwinds"
不一样的」。两个毛病：**「went last」是谜语，没说今天发生了什么**；而且把一个中性偏好的事实
（领涨股没参与下跌）写成了坏消息。**副标题里本来就有 three macro headwinds，标题自己把它扔了。**

第二版 `The Selling Skipped the Leaders` 也被打回：「不通顺，它的中文更不会通顺」——
**动词要在两种语言里都是本行话**，`skipped` 英文别扭、中文根本翻不出来。

**获批的那一版**：
> `The Market Sold Off, the Leaders Didn't — Dollar, Yields and Crude Did the Damage`
> 「大盘杀跌，龙头没跟——压力来自美元、利率和原油」

定式（日刊周刊通用，接 [2026-09-19]「标题不用数字解释」那条）：
1. **前半句 = 事件，后半句 = 含义或成因**，破折号分开，两半都短
2. **两个短句对仗、主谓直给**：`sold off / didn't` 与「杀跌 / 没跟」都是交易里本来就在说的话——
   **动词先在中英两边各念一遍**，有一边别扭就换掉，不要先写英文再翻
3. **不加情绪词**。同一个事实的两种写法里选中性那个：「龙头没参与下跌」是陈述，
   「龙头也撑不住了」是评价。**默认不往看空那边倒**——09-23 那次的偏向是训出来的，不是数据里的
4. **成因要核出处**：我第一稿写 `Dollar, Yields and Metals`，而 big picture 里的三重逆风是
   **美元、十年期利率、原油**——金属是被打的那个。**把受害者写成元凶**，出片前对着 big_picture 核一遍
### [2026-09-24] Index Action 的两列怎么填：对照文优先，我方数据补充（Andy 原话）

> 「还是应该参考下对照文在写什么，优先写对照文里提到的，再是你的数据」

09-23 出的那版，Index Action 的技术变化列**五行全是 `no new average event`**。
根因是把均线规则（「只以事件出现，永不写在均线上方」）执行成了「没有事件就写一句没有事件」——
一列五行说同一句话，正是四问第 1 条要删的东西。**但空着也不对**：那是把问题删掉，不是填对。

**填列顺序（这一条把 09-13「以字幕叙事为主」从 Big Picture 扩到 Index Action）**：
1. **先看对照文对这个指数说了什么**——结构位、被拒的位置、在等什么、哪根均线在争夺，标 ◇
2. 字幕没提到的，才用我方数据的均线事件（reclaimed / lost / rejected / 贴着）
3. 两边都没有，才留空——**永不写「无事件」这类占位句**

09-23 那五行，照字幕本来该是（逐条有出处）：
| | 字幕里现成的 |
|---|---|
| SPY | 仍在 7816 那个高点下方 ◇；21 日与 50 日能不能守住还不确定 ◇ |
| QQQ | 仍在均线上方、离历史高点很近 ◇；734 是整理中枢，等它回踩确认 ◇ |
| RSP | 广度持续恶化 ◇；211 成了要看的位置，等它做支撑 ◇ |
| DIA | 指数与卖压都在继续走低 ◇；盯上周三那个放量低点 ◇ |
| IWM | **勉强守住 150 日；昨天在 8/21 日线被拒后已在 100 日下方** ◇；有可能去试 200 日与左侧前低 ◇ |

**LEVEL/NOTE 列不许复述同表已有的列**（同日同一版的第二个毛病）：
表里已经有收盘价、涨跌幅、量比三列，note 却写成 `767.81, −0.72% on 1.24× · 7,695 held twice ◇`——
前半截是三列的抄写。**note 只装列里没有的东西**：结构位、在等什么、谁在驱动。

两条都可机器判，闸待补（OPS）：①事件列出现 `no new`/`无事件`/`—` 这类占位＝红；
②note 的前 20 个字符里出现本行 close / change% / volume 中任意两个的数值＝红。


### [2026-09-24] 09-23 复盘验收五条（Andy 逐条原话；09-23 那期改完一次性重出）

> 1. 教育选题 给我看A/B的另一个，还有参照文的选题不错。
> 2. LEADERS and laggards 我们按照dashboard的写法 出industries, SECTORS, 和themes 这三类。然后写ticker，全名用小字。和dashboard上一样。所以就是ticker，名字，涨跌幅。不写四态。
> 3. index action notes学习参照文的read
> 4. cross assets这次要写，按照它的搬过来就行。
> 5. 你看看别人的sentiment写的更加简洁。

**① 教育段**：每期交付说明里要**把 B 的标题与 why 一起给他看**，不是只报 A。

**⭐ 选题判据（Andy 2026-09-24 定，原话「教育今天选参照文的，以后碰到类似问题，要选偏当天的，而非教科书的」）**：
**A/B 里选偏当天的那个，不选教科书的那个。** 判别问一句——
> **把今天的日期换成上个月的某一天，这段话还成立吗？** 成立＝教科书，换掉。

- 教科书式（09-23 我出的两个都是）：「回调停在上一个低点之上」「假跌破先洗你再给钱」——
  形态讲得对，但任何一天都能印，读者学不到**今天**该看什么。
- 偏当天式（对照组 09-23 的 `LESSON`，Andy 点名要的那个）：「广度在恶化时你想看到什么——
  如果龙头这时也在崩，那比实际发生的事可怕得多；实际是一批龙头守住窄幅、拖着指数走。
  **指数的数字告诉你跌了多少，龙头告诉你性质**」。同一个形态知识，挂在今天的盘面上。
- 做法：A/B 至少有一个必须是当天式的；两个都是教科书式就重出题。
  选了字幕/对照组的题，按 09-19 的 `picked_by_andy` 口径写进选项、R1 台账闸放行，
  **台账里登记的 concept 要跟着改**（`_ledger/edu_topics.jsonl`，09-23 那行原登记
  `higher_low_higher_high`，重出时改成对照组那题的 concept）。

对照组的 `LESSON` 另有一种写法值得学：它不讲通用形态，而是**讲今天这个局面下该做的区分**
（09-23：「广度在恶化时你想看到什么——如果龙头同时在崩，那才可怕；实际是龙头守住窄幅、
指数在跌。指数的数字告诉你跌了多少，龙头告诉你性质」）。它还有一节 `LESSONS FROM THE TAPE`，
六条当天提炼的要点。**我们的教育段偏教科书，它的偏当天**——两者可以并存，别把当天那层丢了。

**② Leaders / Laggards 改成 dashboard 的三分栏**（取代原来 themes+industries 混排的一张表）：
| 栏 | 数据源 | 行内容 |
|---|---|---|
| Industries | `data/output/etf_data.json` 的 `change_pct`（**ETF 代码**） | ticker · 全名（小字）· 涨跌幅 |
| Sectors | 同上，11 只 SPDR（XLB/XLE/XLP/XLK/XLI/XLV/XLU/XLC/XLRE/XLF/XLY） | 同上 |
| Themes | `data/output/groups.json` 的 `themes` 的 `perf_1d` | 名字 · 涨跌幅（主题没有 ticker） |
- **全名取 `frontend/src/lib/etfNames.json`**——那正是 dashboard 用的那份（09-24 逐字核过截图：
  MSOS「Pure US Cannabis」· BOAT「Global Shipping」· XLB「Materials」）。**不要另建一份名字表。**
- **不写四态**（Leading / Weakening / Improving / Lagging 全部去掉）。
- 每栏各取前三后三，**按 perf 排序取，不按「哪个有故事」挑**——09-23 的 lagged 漏了
  Genomics −4.03% 与 Rare Earth Metals −4.45%，两个都比印上去的 Tech Mega Caps −1.47%、
  Memory & Storage −1.43% 更差，就是靠编辑判断挑行挑出来的。
- 这条同时解释了 09-24 Andy 说的「和前端不一样」：从前复盘读的是 `groups.json` 的 **139 个 Finviz 行业**
  （成分股均值），dashboard 的 Industries 栏读的是 **ETF**，两个池子，数字当然对不上。

**③ Index Action 的 note 学对照文的 read**：接 同日「Index Action 两列填法」那条。
对照文给的是**读法**不是读数——「跌破后回到下降趋势线、再次突破」「这个位置成了要看的支撑」。
我方的 note 从前一半在复述同表已有的 close/change%/volume（见上条）。

**④ Cross Assets 独立成节**（09-23 没写，Andy「这次要写，按照它的搬过来就行」）：
对照组的 `ACROSS ASSETS` 一资产一段，覆盖**美元 · 债券与十年期 · 黄金白银 · 原油 · 比特币**，
每段是读法不是报价（例：「十年期比长债更要紧，因为它定的是实体经济的借贷成本」）。
我方的这些资产此前散在 `extra_index_rows`（TLT/UUP/GDX/USO 四行），要收成一节。

**⑤ Sentiment 要短**（Andy「你看看别人的sentiment写的更加简洁」）：
对照组 4 句约 70 词：5 日线上方占比（SPX/NDX）· VIX 读数与涨幅 · Fear & Greed · 当天 PMI · 明天的日程。
我方 09-23 那段 401 字符，全是广度内部数（涨跌家数、4% 家数、T2108、McClellan、Record High Percent）。
**两个毛病**：太长；而且**广度已经有整块 Market State 的 12 格投票在讲**，Sentiment 再报一遍是复述——
与 note 列复述同表列同一个病。Sentiment 该装的是**情绪计量与催化剂**（VIX、F&G、日程），不是广度。


---

## 试跑铁律（ops 自修，源于 T-0919-24 事故：试跑吃掉了 W38 正班；不是口径/判断改动，不需要 Andy 点头）

**任何 title 带「试跑」的出片班（日刊或周刊）**，动手第一件事、在任何 `recap.run` 调用之前，先执行：
```bash
export FLUXUS_RECAP_ROOT="$HOME/Documents/Trading/01_Market_Reports_Daily/_dryrun_$(date +%m%d)"
```
`RECAP_ROOT` 由 `pipeline/content/recap/__init__.py` 在启动时从这个环境变量读取；设了它，`fetch`/`check`/`render`/`ledger-add` 的全部产出（pack/pdf/img/delivery.md/教育台账）都改落 `_dryrun_<MMDD>/`，不碰生产期号目录。**下面各模式「幂等」那句手工判断也必须用同一个变量**（写法见下），否则判断本身仍会读到生产目录、给出假结论。⚠️ 教育选题台账（`_ledger/edu_topics.jsonl`）会跟着指向一个空文件，本班的 R1 去重闸这一轮形同虚设——试跑看到「选题不重复」不代表选题真的不重复，正班仍要用真台账核一遍。收工前自检：`echo $FLUXUS_RECAP_ROOT` 含 `_dryrun`；`ls "$FLUXUS_RECAP_ROOT"` 看到的是当天试跑输出，不是历史正式期号。

**忘记这一步 = 试跑变成正班**：T-0919-24（09-18 22:49 ET 的试跑，周五夜）没设这个变量，直接写进了生产目录 `2026-09/2026-W38/`；那时周六美东的周末回顾视频还没发布（`render_state.json` 的 `transcript_present:false`），出的是「无字幕版」，却被当成幂等锁死的正式成品——09-20 10:00 JST 的正班（T-0920-25）撞上幂等闸整班空转（详见 T-0920-30）。同一父目录下现成的 `_dryrun/`、`_dryrun_0913_oldrules/` 就是这个约定的先例，只是没被写进这份 skill、也没被那次试跑用上。

此规矩只对 recap 这一类出片班生效：`RECAP_ROOT` 是仓库里唯一「产出永不进 git、靠本地文件存在与否做幂等」的路径（`pipeline/content/recap/__init__.py` 顶部注释「never into the repo」），别的班次（增长记账、仓库周检、内容台备稿、Discord→X 草稿）写的都是 `data/` 下 git 追踪、有 gate 审核的文件，撞车会在 git 层被看见，不需要这条铁律。**日刊出片班同理**：它的完整步骤书在 `ops-recap-daily`（守护进程 `schedule.json`，见 `.fluxus-ops-daemon` 仓库）里，第 0 步已经同步带上了这条铁律；这份 skill 的日刊「工作流」一节是老的、更概括的版本，没有编号步骤可挂——**日刊试跑一样先 export 这个变量，不要因为这份 skill 里日刊部分没写出来就跳过**。

## 周模式（recap-weekly 并入，2026-09-18）

周复盘出片班（归 ops 线）。用中文工作与汇报。时间盒 90 分钟。成品发会员（PDF）与 Substack（逐页图 + PDF 附件）。**周刊不发 X**（Andy 原话「周复盘不发X」）。**只出片，不发布。**

### 第 0 步 · 时钟与幂等
**title 带「试跑」先看上面「试跑铁律」，设好 `FLUXUS_RECAP_ROOT` 再往下走——下面这条判断也要用它。**
`date '+%Y-%m-%d %A %H:%M %Z'`；工作树里 `python3 -c "from pipeline.marketcal import last_completed_session as l; print(l())"` 得到最近完成交易日 D，期号 W = D 所在 ISO 周，格式 `YYYY-Www`（如 `2026-W38`）。
若 `${FLUXUS_RECAP_ROOT:-$HOME/Documents/Trading/01_Market_Reports_Daily}/<D 的 YYYY-MM>/<W>/pdf/Market_Recap_<W>_EN.pdf` 已存在 → 汇报「W 已出过」并收工。

### 第 1 步 · 工作树（代码一律用 origin/main）
```bash
export WT="<scratchpad 绝对路径>/wt-recap-weekly"
git -C /Users/taolezhu/Documents/AI-Trading-System fetch origin
git -C /Users/taolezhu/Documents/AI-Trading-System worktree add --detach "$WT" origin/main
test -d "$WT" && echo ok
```
python 命令写成 `(cd "$WT" && …)`；git 一律 `git -C`；永不 stash，永不在共享主树改文件。

### 第 2 步 · 取材
```bash
(cd "$WT" && python3 -m pipeline.content.recap.run fetch --week W)
```
- 叙事来源是周六美东上传的周末回顾视频（标题含 Weekend Review）。代码没挑中就在 Revere 频道 `https://www.youtube.com/channel/UCV27KlSTS2zAidGEbu0HcZA/videos` 里找该周六的周末回顾，用 `--video-id` 指定重跑。仍然没有 → 继续做，叙事由本周各期日刊内容与我方数据撑，汇报写明「无字幕版」。
- GAS 偶发 404 属已知，代码会重试；凭据永不打印。

### 第 3 步 · 必读（每次读）
1. 本 skill 全文，尤其裁决记录（含「周五规格」与 2026-09-13 各条）
2. `~/Downloads/Daily_Recap_Workflow_Spec.md`
3. `$WT/pipeline/content/recap/CONTENT_SCHEMA.md`（周刊字段：`weekly_k_names`、`weekly_k_line`；**不写 `x_posts`**）
4. 中文：`$WT/.claude/skills/fable-voice/SKILL.md` + `~/Desktop/中文表达训练/01-风格卡/风格卡-日用版.md` + `~/Desktop/中文表达训练/00-说明书/教练说明书.md` 第二、三节
5. 本周各期日刊的 `content_EN.json` / `content_ZH.json`（在 `<YYYY-MM>/<YYYY-MM-DD>/pack/`）——周刊是**一周的总结**，不是把日刊拼起来
6. 上一期周刊的内容文件（抄 labels）；教育台账 `~/Documents/Trading/01_Market_Reports_Daily/_ledger/edu_topics.jsonl`

### 第 4 步 · 写 `<W>/pack/content_EN.json` 与 `content_ZH.json`
口径同日刊（Andy 2026-09-13）：叙事以字幕为主、Discord 加强、我方数字为准、外部标 ◇；**不出现「Andy」、不用第一人称**；纪律 1–6 写成**周尺度**，第 7 条固定开头 + 本周读法；教育 A、B 都写全、`chosen: "A"`，**A 的 concept 不得与本周任何一期日刊的 A 相同**，也不得与台账近 20 个交易日或 spec 八个老题材重复；只用 R 与 %；中文是重写不是翻译。周线读数只引用 pack 里有的字段（`perf_1w`、`wk_ema10/20`、`three_weeks_tight`、`rs_0_1w`）。
- **一周涨跌**写 `over the week (theme)` / `1-week` / 「本周」「一周」，**不写 `theme week` / `industry week` / `IBIT week` 这类缩写**（周刊最容易踩，W37 样张一次踩了 11 处）。
- **「Grow」是视频专名，不出现。**
- **Big Picture 两拍 + 标题定性**（2026-09-19，见裁决记录）：① 一句定性 ② 故事线，≤8 个数；标题副标题不用数字。

### 第 5 步 · 过闸与出片
```bash
(cd "$WT" && python3 -m pipeline.content.recap.run check --week W)
```
红就改写，最多 3 轮；仍红 → 停手汇报。**绝不绕过闸。**
```bash
(cd "$WT" && ~/.venvs/fluxus-recap/bin/python -m pipeline.content.recap.run render --week W)
(cd "$WT" && python3 -m pipeline.content.recap.run ledger-add --week W)
```
render 必须用 venv 的 python（真字号闸需要 pdfminer.six）。

**版式定稿（2026-09-13 晚最终版）**：正文 10.5pt、表格 9.5pt，宽松行距（行距比 1.4–1.5）。**教育段允许跨页**，唯一底线是不许在句子/段落中间断页。**页数规则**：教育、组合更新之外的全部内容必须在前几页放完；组合更新独占最后一页；教育段收尾在哪一页由内容多少决定——周刊内容更多，正常会是 6 页，**不要为了凑某个固定页数压字号或删内容**。

闸含：专名（含 Grow）、W1 一周缩写、版心截断、示意图重叠、**L1 页数结构**（教育/组合更新之外内容须在前 4 页、组合更新独占末页、断句底线）、**L2 真字号**（pdfminer 实读：正文 10.5±0.1pt、表格 ≥9.0pt——周刊的「逐日读数」表最容易撑宽页面触发 Chrome 整页缩印，红了不许缩字号，停手汇报是哪个元素超宽）。

### 第 6 步 · 核对产出
`<W>/pdf/` 中英 PDF（页数与教育是否溢出写进 `delivery.md`）· `img/EN`、`img/ZH`（数量 = 页数）· `delivery.md` · `preview.html`；**不应有 `x/`**。

### 第 7 步 · INBOX 留痕（仓库公开：只写状态）
直推 main 标准动作（临时树、只 add INBOX、删除行自检为空、冲突重放最多 3 轮、push 后核实、移除临时树），追一行：
`- [MM-DD] 📰 周复盘 <W>：已出（中英 PDF · Substack 逐页图）· 闸全绿` 或 `…：未出 —— <一句原因>`

### 红线
不发任何消息 · 不发布到任何平台 · 字幕、材料包、PDF、图片、台账永不进 git · 不改 `pipeline/` 代码（工具报错就开一件任务给 ops：`taskboard.py new --owner ops --type skill_fix --title "周复盘工具报错 <一句>"` 并停手）· 不碰 Visual 线工作树 · 不 force、不 stash。

### 最终回复（≤8 行）
`周复盘 <W>：已出 / 未出（原因）` · PDF 路径与页数（教育是否溢出）· 正文实测字号 · 教育 A（B）题目 · `delivery.md` 里 ★ 句数 · 缺什么 · 耗时。
