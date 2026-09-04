# 盘前数据窗探针 — 2026-09-04（约 05:02 ET，交易日）

**任务**：实测裁「Finviz/Yahoo 在 04:00–09:30 ET 端的是不是昨收」，判 Andy（盘前拉数据合法）和代码闸
`pipeline/screeners/run_all.py:454-464`（拒跑 04:00–16:15 ET）谁对。

## 结论：**无法裁定——本探针会话的出网被组织策略整体拦截，三个目标源一个都没连上，不是"实测支持谁"，是"这轮没测成"。**

不做推断，只报实测：

| 目标 | 方式 | 结果 |
|---|---|---|
| `finviz.com/quote.ashx?t=AAPL` | `curl` 直连 | `CONNECT tunnel failed, response 403`（agent-proxy: `connect_rejected`，`finviz.com:443`） |
| `finviz.com/quote.ashx?t=AAPL/NVDA/SPY` | `WebFetch` 工具 | 三只全部 `EGRESS_BLOCKED`："Access to finviz.com is blocked by the network egress proxy." |
| `query1.finance.yahoo.com`（yfinance 底层） | Python `yfinance.Ticker(...).history()` | `curl_cffi.requests.exceptions.ConnectionError: CONNECT tunnel failed, response 403`（AAPL/NVDA/SPY 全部同样报错，第一只失败即中止） |
| 对照：`pypi.org` | `curl` 直连 | `200`（出网本身工作，只是金融数据源不在白名单） |

`agent-proxy` 状态（`/__agentproxy/status`）里的 `noProxy` 白名单只列了 `api.anthropic.com` / npm / pypi / crates / go proxy 等开发基础设施域名，不含任何行情数据源——这次拦截是**这个 Claude Code Remote 探针容器的组织级出网策略**挡的，与 Finviz/Yahoo 当天服务端行为无关，**也不能反推生产环境（GitHub Actions runner）是否同样被挡**——生产管道显然平时能拉到数据（`data/output/` 有每日更新），说明 GH runner 的出网策略与本探针容器不同，两者不能互相替代验证。

## 唯二能引用的实测证据（均为历史二手，非本轮实测）

- `run_all.py:451-456` 代码注释记录的历史事故（2026-08-19）：`workflow_dispatch` 于 05:18 ET 拉到 Finviz **PREMARKET** 报价 P 115.33，对照当天官方收盘 117.06——两者不等，说明**至少那一次**，Finviz 在盘前端的确不是收盘价而是实时盘前价。这是当初写这道闸的直接依据，但发生在别的执行环境（GH runner），且是别的交易日，不能替代今天的实测。
- 本机 `pipeline.marketcal.market_now()` 确认现在是 `2026-09-04 05:02:18-04:00`、`is_trading_day=True`，落在闸拦截区间 `(4,0)–(16,15)` 内——探针触发时机本身没问题，是网络层面测不了。

## 未完成项

- 未能取得 AAPL/NVDA/SPY 今日 09-04 盘前 Finviz 显示价与涨跌幅。
- 未能取得 yfinance `AAPL` 含今日的 1d 日线（无法判断是否已存在未完成的今日 bar）。
- 未能与 09-03 官方收盘做逐只比对。

**建议**：这道题只能在有出网权限连 Finviz/Yahoo 的环境里测（例如生产用的 GH Actions runner，用
`FORCE_INTRADAY_RUN=1` 手动 dispatch 一次盘前跑，比对输出的 `close` 字段与前一交易日收盘、并肉眼看 Finviz 页面是否带
"Premarket" 标签），不是这个探针容器能做的事。

→ DATA ALEX：**本轮未产出结论，不满足"若结论支持 Andy"的前提**——`run_all.py:460` 的闸先不要动。
若要继续裁这道题，需要在有出网权限的环境（如 GH Actions）重跑本探针；本文件到此为止，不代为建议改动。
