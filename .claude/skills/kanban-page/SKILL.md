---
name: kanban-page
description: 给 Andy 的页面默认长成 Trello 式看板——Andy 2026-10-01 原话「完美，这个以后是默认标准了」。凡要给 Andy 出/改/重做任何「看状态、看进度、看今天有什么」的 Artifact 页面都先读本 skill：Fluxus 每日（daily-page）、课程上线进度页、X 日调研日报、任何项目进度页/牌面/早报/周报/台账首页/待办清单；他说「做成看板」「像 trello」「改成卡片」「这页太乱」「出个进度页」「刷新那个链接」、或只丢一个 artifact 链接让你更新，也算。模板在 template.html，照抄骨架只换数据块，不另起炉灶。
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
- **不做假交互**：拖卡片不回写任务板就不做拖动。每个可点的东西都要真的有结果。
- **回话**：发布时声明 `capabilities: {"comments": {"composer_only": true}}`；「回话」按钮调 `openComposer({element: 卡片})`，`claude.use("comments")` 拿到 null 就藏按钮。定时班读评论（`ArtifactComments read`）当 Andy 的回执——评论与状态冲突时评论赢。
- **固定链接**：已有页面一律 `Artifact action:"read"` 那个 url 后**带 `url` 参数 republish**；`<title>` 保持原名不变。新页面第一次发布才不带 url，发完把链接写进该流程的 skill/README。
- 中文先过 `fable-voice` 七病自查；数字现场读权威源，读不到写「读不到」，不拿昨天顶替。
- 本机预览：模板没有 charset 声明（发布时平台加），本地看要先在前面加 `<!doctype html><meta charset="utf-8">` 另存一份再开，不然是乱码。

## 四、已用本标准的页面

| 页面 | 固定链接 | 谁刷新 | 数据块怎么来 |
|---|---|---|---|
| Fluxus 每日 | https://claude.ai/artifact/LCb5gkgt4Bv8asdrtVjYH6 | 守护进程 daily_page 班（skill `daily-page`） | `~/Documents/fluxus-ops/state/dailypage.json` + 现场核 |
| 课程上线 09-25 | https://claude.ai/artifact/RPSokvUnub38CCttkFkvbk | 定时任务 course-page-refresh-6h | 任务板 + 页面评论 + 现场核 |
| X 日调研 | 见 `data/content/x_watch/README.md` | steve-x-daily-watch（skill `x-watch`） | 当天日报 `daily/<ET 日>.md` |

## 五、gotcha（同一工作流的坑追加在这里）

- 2026-10-01：本地 http.server 预览出现乱码＝缺 charset，不是模板坏了（见上）。
