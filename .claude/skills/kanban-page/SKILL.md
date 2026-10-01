---
name: kanban-page
description: 给 Andy 的页面默认长成 Trello 式看板——Andy 2026-10-01 原话「完美，这个以后是默认标准了」。凡要给 Andy 出/改/重做任何「看状态、看进度、看今天有什么」的 Artifact 页面都先读本 skill：Fluxus 每日（daily-page）、课程上线进度页、X 日调研日报、任何项目进度页/牌面/早报/周报/台账首页/待办清单；他说「做成看板」「像 trello」「改成卡片」「这页太乱」「出个进度页」「刷新那个链接」、或只丢一个 artifact 链接让你更新，也算。两种默认设计：A 静态看板（template.html）· B 可拖拽看板（template_drag.html，列＝状态时用，拖动存进页面数据库）。照抄骨架只换数据块，不另起炉灶。
owner: ops
---

# kanban-page — 给 Andy 的页面＝看板

**来源**：Andy 2026-10-01 看了「Fluxus 每日」看板预览（https://claude.ai/artifact/QtovBKu5rDdUZvWZ4Sahd2）后原话：
「完美，这个以后是默认标准了。把课程上线进度页和steve的X日调研也这样改。」
样板＝同目录 `template.html`（就是那一版，逐字节）。

## 一、骨架（照抄 template.html，不另造）

1. **顶部**：eyebrow（日期 + JST/ET 双标时刻）· 一句话结论 h1（≤2 行，先说最要紧的坏事）· 右上一个 tag。
2. **状态条**：3–5 个 chip，`tone` 只有 `ok` / `hot` / 空三种。数字放 `<b>`。
3. **看板**：3–5 列（`.list`），每列标题带 lucide 图标 + 计数。卡片（`.card`）：
   - 顶部 labels（`hot` 红＝过期/要注意/P0-P1，`amb` 琥珀＝等待/P2，`ok` 绿＝正常/剩余充足，`blu` 蓝＝信息）
   - 标题（一句业务话）· 一行说明 · 可选：要他回的那句（`.ask`）、进度条、关键数字（`.metric`）
   - foot：单号/计数 + 可选链接 + 可选「回话」
4. **卡背**：点卡片开 `<dialog>`，放全文、现场核的依据、单号、链接。**结论在卡面，明细在卡背。**
5. **数字出处**：底部折叠 `details.src`。

## 二、数据和样式分开

- 页面所有内容来自顶部那块 `<script type="application/json" id="data">`。**定时班每天只替换这块 JSON**，样式、脚本、结构一个字不动。
- JSON 里只放纯业务语言；渲染全用 `textContent`，不拼 HTML（防注入，也防格式坏）。
- 新页面要新的列：在 JSON 里加数组，脚本里照现有一列的写法加一段渲染，不改 CSS 类名。

## 三、硬规矩

- **深色为底**（bare `:root` 是深色，浅色在 `prefers-color-scheme: light` 与 `[data-theme="light"]` 里）。token 只在 `:root` 定义，组件只用 token。
- **手机**：列横向滑动（`.board` 自己 `overflow-x:auto`），页面本身不许横向滚动。发布前在 375 宽核 `scrollWidth <= innerWidth`。
- **第三方库**：Andy 允许。现用 lucide（jsdelivr 固定版本 `lucide@0.460.0`）。加新库必须固定版本、走允许的 CDN、加载失败时页面照样能读（图标缺了不影响文字）。
- **不做假交互**：每个可点、可拖的东西都要真的有结果。拖动只在变体 B 里做（见第六节）——拖了要存、刷新班要读，否则就不开。
- **回话**：发布时声明 `capabilities: {"comments": {"composer_only": true}}`；「回话」按钮调 `openComposer({element: 卡片})`，`claude.use("comments")` 拿到 null 就藏按钮。定时班读评论（`ArtifactComments read`）当 Andy 的回执——评论与状态冲突时评论赢。
- **固定链接**：已有页面一律 `Artifact action:"read"` 那个 url 后**带 `url` 参数 republish**；`<title>` 保持原名不变。新页面第一次发布才不带 url，发完把链接写进该流程的 skill/README。
- 中文先过 `fable-voice` 七病自查；数字现场读权威源，读不到写「读不到」，不拿昨天顶替。
- 本机预览：模板没有 charset 声明（发布时平台加），本地看要先在前面加 `<!doctype html><meta charset="utf-8">` 另存一份再开，不然是乱码。

## 四、已用本标准的页面

| 页面 | 固定链接 | 谁刷新 | 数据块怎么来 |
|---|---|---|---|
| Fluxus 每日 | https://claude.ai/artifact/LCb5gkgt4Bv8asdrtVjYH6 | 守护进程 daily_page 班（skill `daily-page`） | `~/Documents/fluxus-ops/state/dailypage.json` + 现场核 |
| 课程上线 09-25 | https://claude.ai/artifact/RPSokvUnub38CCttkFkvbk | 定时任务 course-page-refresh-6h | 任务板 + 页面评论 + 现场核 |
| X 日调研 | https://claude.ai/artifact/5zrcFsdMM4b3sGr8wEp8fJ | steve-x-daily-watch（skill `x-watch` 四点五节） | `tools/build_daily_board.py` 读当天 `daily/<ET 日>.md` |
| X 名单 Ticker 台账 | https://claude.ai/artifact/QDZD6bT5ngjfbgpF34gGt8 | steve-x-daily-watch（skill `x-watch` 第五节） | `tools/build_board.py`（展示层照本标准，热度分列；搜索/日期/筛选保留） |


## 六、变体 B：可拖拽看板（Andy 2026-10-01 原话：「加一个设计并成为默认设计之一，看板的卡片可以拖拽。比如从进行中拖拽到已完成。」）

**什么时候用**：列是**状态**（卡在你手上 / 进行中 / 已完成 / 排期……），一张卡从一列到另一列有业务含义。
列是**分类**（Fluxus 每日的「项目 / 今天的系统 / 各线昨天」）就用变体 A——拖了没有意义。

**模板**：`template_drag.html`（＝课程上线进度页那一版）。比 A 多三样：
1. SortableJS（cdnjs `Sortable/1.15.2`，固定版本）。`sort:false`——只许跨列，不许列内排序（列内顺序没人读，排了是假交互）。手机上长按 180ms 才拖，免得挡住左右滑列。
2. **每张卡必须有稳定的 `id`**（JSON 里的 `id` 字段，没有就用标题 sha1 前 8 位）。刷新班改卡片内容时 id 不许变。`D.drag:true` 才开拖。
3. 页面数据库：发布时 `capabilities: {"comments": {"composer_only": true}, "db": {}}`。拖一下写一条 `moves/<卡片 id>`：`{to, to_title, from, from_title, home, title, at}`；拖回原列＝删这条。8 秒内可「撤销」，撤销后卡片回原位置。数据库不可用（`claude.use("db")` 为 null）就不开拖，页面照样能读。

**刷新班怎么接**（这条不接，拖动就是假的）：
- 开工先 `ArtifactData list collection:"moves"`（url＝该页）。每一条都是 Andy 的回执，**和页面评论同级、与任务板冲突时它赢**。
- 拖到「已完成」＝Andy 说这件做完了：卡片移进已完成列，`ref` 写「Andy <MM-DD HH:MM> 拖到已完成」；对应任务单在最终回复里列「任务板待关」。拖到别的列照样照办，卡背写清是他拖的。
- 并进 JSON 并发布之后，**删掉已处理的那几条 moves**（`ArtifactData batch` delete，带 `if_version`）——不删，下次打开页面它会把卡片再挪一次。
- 拖到「已完成」但现场核发现没做完：不替他改回去，卡片留在已完成，标签加「待核：<现场看到的>」，最终回复里拉响。

## 五、gotcha（同一工作流的坑追加在这里）

- 2026-10-01：本地 http.server 预览出现乱码＝缺 charset，不是模板坏了（见上）；同理要补 `<meta name="viewport" content="width=device-width,initial-scale=1">` 才能测手机宽度（发布时平台会注入，本地不会）。
- 2026-10-01：本地测拖拽没有真数据库——在页面前面塞一个 `window.claude.use('db')` 的内存替身（collection/doc/set/delete/onSnapshot），桌面拖动能用 CDP 鼠标拖测到。
