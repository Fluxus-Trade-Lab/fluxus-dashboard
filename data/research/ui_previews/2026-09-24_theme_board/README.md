# T-0924-97 · Theme Board 首次真实渲染预览

给 Andy 看 Rotation 页 Proxy Board 卡片（T-0924-90 后置项）。

## 状态（2026-09-24 15:50 JST / 06:50 UTC）

- **`data/output/theme_board.json` 尚未由夜间管线在 main 上落地**——merge（`39de84ae`，15:15:48 JST）发生在最近一次夜间数据管线跑之后（上一次 market data commit `93bb5b4a` 是 2026-09-24 08:23 JST），下一次排程 20:20 UTC（≈次日 05:20 JST）才会真跑到这块新增的 emit 代码。任务验收第一条暂不能打勾，等下一班夜间管线落地后由后续会话核实补勾。
- 本预览用的是 `pipeline/themes/proxy_board.py::build()` **同一份生产函数**，喂的是真实行情（yfinance 实时抓取 51 只代理 ETF + 2,746 只成员票，`data/output/groups.json` 的真实主题名单），不是手造 fixture——只是没有走夜间 cron 那次落地流程，本机现跑一次。
- 范围说明：成员分布常驻计数条只对按 rs 预排前 16 个主题抓了真实成员行情（2,746 只票），覆盖了默认展开的前 12 行（`HEAD=12`，按 rs 降序排列，与预抓的 top16 重合）；`All 50 themes` 展开后，靠后的主题会显示灰色 n/a 计数条——那些主题的成员行情本预览没抓（4,885 只全量成员票太贵，等夜间管线的真实产出自然会补全）。这一点只影响预览范围，不影响截图里能看到的 12 行的真实性。

## 截图

- `proxy_board_card.png` —— Proxy Board 卡片单独裁切：图例（Leading 11 / Improving 14 / Weakening 1 / Lagging 24）、并排期 `was` 标记、成员分布计数条、rs 数值。
- `rotation_page_full.png` —— 整个 Rotation 页全屏，Proxy Board 接在原有三卡（Terrain / Flux / Momentum & Acceleration）下面，页面版式没有变化（Andy 09-24 原话「dashboard 版面一个像素不动，三卡也不动」在这条预览里成立）。

## 生成方式（供复现）

```
python3 /tmp/gen_theme_board.py   # 见任务日志 agents/claire/runs/，复现要点：
# 1. pipeline.constants.theme_proxies.THEME_PROXIES + data/output/groups.json 的真实成员名单
# 2. pipeline.themes.proxy_board.fetch_bars(51 只代理 ETF) 真实抓取
# 3. 按 bucket-0 rs 预排，取前 16 个主题的真实成员做 pipeline.themes.short_window.fetch_bars（2,746 只票）
# 4. pipeline.themes.proxy_board.build(...) 生产同款函数产出 theme_board.json
# 5. 写入 frontend/public/data/output/theme_board.json（gitignored，仅本机预览），`npm run dev` 起本地服务
# 6. playwright-core 无头截图 http://localhost:5183/#/rotation
```

frontend 侧无改动（T-0924-90/94 已合并的组件原样渲染）；两个测试根 + `ThemeBoardCard.test.jsx`（4/4）已跑绿。
