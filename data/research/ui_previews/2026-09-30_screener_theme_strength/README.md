# T-0930-50 · Screener 主题相对强弱渲染截图

验收第③条的证据（ops 裁决 T-0930-53：改截图，不再要求 Andy 现场拍板）。

## 截图

- `screener_cybersecurity.png` —— `#/screener` 选中 Cybersecurity 一个主题，按 Top Quartile
  列排序后的表头 10 行。可见新的四态徽标（Leading / Lagging / Improving）与顶栏读句
  「31 names under All ∩ Cybersecurity. States: 7 Leading · 1 Improving · 3 Lagging.」——
  State/Top Quartile 两列都已切到 `themeStrengthMath.js` 算出的对代理 ETF 超额读数，
  不再是股票主场 group 的状态机。OKTA/NET/DT 三只排前三、Top Quartile 列打勾，
  与复核员（T-0930-53 判词）手算的 NET 最强一致。

## 生成方式（供复现）

```
# 分支 agent/claire/T-0930-50（commit 7c06d76c4），detached worktree
cd frontend && npm ci
npx playwright install chromium   # 一次性
npm run dev -- --port 5183

# frontend/public/data/output/ 是 gitignored 的本机镜像，正常开发靠符号链接／手动同步到
# data/output/ 才能起 dev server；本机把用得到的几个 json（含 theme_board.json、
# universe.json、groups.json）从 data/output/ 拷进 frontend/public/data/output/。

node - <<'EOF'   # playwright 脚本，要点：
# 1. page.goto('http://localhost:5183/#/screener')
# 2. localStorage.setItem('screener-query', JSON.stringify({scan:'all', states:[],
#    themes:['Cybersecurity'], gates:[]}))；reload 让 ScreenerPage 的 loadQuery() 读到
# 3. 等 'Cybersecurity' 文案出现，点 Top Quartile 表头排序，screenshot fullPage
EOF
```

两个测试根 + `themeStrengthMath.test.js`（9/9）已在同一 worktree 跑绿（见验收第一条）。
