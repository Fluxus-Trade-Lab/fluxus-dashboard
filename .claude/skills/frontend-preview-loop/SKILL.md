---
name: frontend-preview-loop
description: Dashboard 前端改动的标准工序——Andy 对 Market State / Screener / Tearsheet 等页面提改动方向时（常常只是一句「整理一下」「复刻 XX 网站」「这张表太乱」），先用真实数据出一份 Artifact 预览让他挑一个方向，拍板了再落进 frontend/ 组件；自造参数必须印在页面上，态词/vs昨只在引擎真有票、真有历史档案时出现；收工前跑两个测试根 + vitest + build + 无头渲染核对。凡任务 owner=claire、type=frontend，或有人说「这段前端整理一下」「加个切换/开关」「照 XX 网站的样子改」「这张卡/表太乱」「接进那一段」「给 dashboard 加个字段」，都先读本 skill 再动手，别在没出预览、没确认真实数据来源的情况下直接改组件。
owner: claire
---

# frontend-preview-loop — Dashboard 前端改动的标准工序

> 抽自 2026-09-23 三次真实来回（T-0923-80/85/92，Market State ②广度两窗图 → 清「问/读」两栏 → 复刻 TradersLab 表格），第 3 次触发 CLAUDE.md「三次律」。方法是「预览先行、真实数据、自造参数留痕、态词有出处」，照抄能省掉大半轮次，不是重新发明。

## 何时用

Andy 在对话里给一个页面改动方向，而不是完整规格——「整理一下」「复刻 XX」「这张表太乱」「加个切换」。这类活的产出从来不是一次写对，是**预览 → 他挑一个 token → 实装**的循环（同 CLAUDE.md「交付面」§③一屏决策台）。如果任务书里已经写着「Andy 看完预览后：『……』」这类逐字引语，说明预览这一步已经有人做过，直接进第 3 步实装即可。

## 工序

### 1. 开工前读两处

- 同一块地皮有没有已经挂过号（同 `chart-for-andy` 的「先读已有规划」）——`data/reference/proposals/` 与相邻 memory 先扫一遍，避免推翻别人这周正在写的东西。
- Andy 点名对标网站（finviz / TradersLab 等）时，先问一句「谁的 reads 里已经有它」——`data/research/` 下搜关键词、问一下有没有会话已经建过对照页；没有就先抓真实截图建一份，别凭印象画布局。

### 2. 出预览，用真实数据

不改 `frontend/` 正式组件之前，先出一个 Artifact 预览稿：

- **数据必须是真的**——`data/output/` 当前值或 `data/history/` 真实历史，不编数字凑效果。CLAUDE.md「先找口径，别自己造」这条铁律在前端一样成立：预览给不存在的态词/vs昨编数据，会被直接判错（09-23 判例见下）。
- 给 2–3 个方向/token 供他挑（「A 版 / B 版」「①②用 B，③–⑥用 A」），别只出一版让他只能对或不对。
- 拿到选择后，把原话记进任务书 `andy:` 字段或 §七契约行，再动组件代码——这是后续复核判 PASS/FAIL 时唯一的授权依据。

### 3. 实装时的两条纪律（09-23 定案，别倒退）

- **自造的参数印在页面上**：窗口长度、阈值、并段规则这类没有官方口径的自造数，图/表下方明写数值和一句为什么（同「数字只有一个家」「先找口径别自己造」两条宪法）。
- **态词（bull/bear/neutral pill）只来自引擎真投过票的字段**（如 `verdict.votes`），没票的读数不给态词——09-23 判例：预览稿给「站上20日线/净涨跌」编了态词，Andy 判错，不许带进实现。**vs 昨**同理，只在真有前一日档案的读数上出现，没历史就不写、不编。
- 计算逻辑抽成纯函数放单独文件（如 `fooMath.js`），配同名 `.test.js`；JSX 组件只管渲染不夹计算——下次改口径时不用碰渲染代码，`breadthPanesMath.js`/`morningReadMath.js` 是现成范例。

### 4. 收工前三件事，缺一不算完

1. **两个测试根全绿**（worker 流程第 4 步已经跑 `pipeline/tests tests`）+ `frontend/` 下 `npm run test`（vitest）。
2. **无头渲染核对**：截一次目标段落的渲染（playwright-core headless 或本地 dev/preview），确认无页面报错、无中英混排、无文字截断——同 `chart-for-andy`「交给他看之前自己先截一张挑毛病」。
3. **build 过**：`npm run build`；产物体积异常暴涨要先查是不是又把 `data/output` 整份拷进了 `frontend/public`（`vercel-ops` skill 09-20 记录过同形状事故，现在走的是同源代理不是拷贝）。

### 5. Gate 别假设

`frontend/` 默认走 reviewer（TEAM.md 08-22），但具体这条 diff 判 none / reviewer / andy 由 `taskboard.py gate <id> --worktree <树>` 现算——09-23 三个真实样例三档都出现过。跑 gate 命令，照它的判定走，别凭经验直接假设某一档。

### 6. 分支习惯

`feat/*` 短分支，合并即删（TEAM.md 08-22）；已经过 Andy 预览拍板的小改，gate=none 就直接推 main，不用每次都留分支等复核。

## 参照

- 视觉细节（轴/色/字体/标注/突变不标记）另有专门的 `chart-for-andy` skill——图表类改动两个一起读，本 skill 管工序，那个管画法。
- 对标网站的原图与页面清单，一旦建过就该是一份可复用的对照页（放 `data/research/` 一类目录）——抄尺子（σ 尺子/切池子/领先主题）不抄全水位，见工序第 1 步。
