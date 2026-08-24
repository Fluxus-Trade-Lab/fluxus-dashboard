# 2026-08-25 · 一个零命中的筛子让整场交易日数据没落地

**级别**：事故（一整个交易日的 `data/output/` 从未提交；前端在周二早上显示上周五的收盘）
**发现**：Plumber Joe 早巡，2026-08-25 07:2x JST
**cron**：[run 32782004003](https://github.com/Fluxus-Trade-Lab/fluxus-dashboard/actions/runs/32782004003) · 08-24 21:54 UTC · 21m9s · failure

## 发生了什么

管线全程跑完没崩（universe 5,622 行、watchlist 19 格、shortlist 6 席、delayed_ep 归档 56 行都正常）。
死在倒数第三步 **Schema snapshot check**：

```
2 removal(s): failing the check
  episodic_pivot.json tickers[]: removed ['atr_color','atr_ext','change_pct','market_cap','rel_volume','sector','ticker']
  shortlist.json cards[].panels[]: removed ['atr','chg_pct','date','panel']
```

exit 1 → `Validate outputs`、**`Commit and push`** 双双 skipped。26 个 output 全部留在 runner 上蒸发。

## 根因

`pipeline/tools/schema_snapshot.py:56`

```python
elif isinstance(node, list) and node and isinstance(node[0], dict):
```

`and node` 意味着**空列表不产生任何 key**。于是形状快照里该 section 直接消失，`diff()` 把它读成「所有字段被删」。

同一份日志里写着答案：

```
pipeline.screeners.episodic_pivot: episodic_pivot: 0 / 5622 stocks pass (gap >= 10%, rvol >= 3.0, mcap >= $500M)
```

**没有票通过筛子，被读成了「筛子的字段没了」。**

## 为什么这条闸不能拆

它是 08-19 事故立的：那晚 `breadth.json top: removed [conditions, regime, state_board, verdict]` 原样打印在同一位置，然后**照样提交了**，Breadth 页整天变暗。注释就写在 `schema_snapshot.py:120-126`。闸的判断是对的，它的**证据构造**是错的。

## 教训

**「空」和「不存在」在形状采样里长得一模一样，而只有一个是事故。**
任何从样本推断 schema 的检查都有这个洞：它看见的是 `len(rows) > 0` 那条分支里的世界。零命中是行情的常规输出——EP 要求 gap ≥10% ∧ rvol ≥3 ∧ mcap ≥$500M，安静的一天本来就该是 0——所以这不是极端边界，是**每隔几周必然复发、且每次代价是一整场数据**的假阳性。

推论（可迁移）：把「阈值筛选的结果」当作 schema 来源，等于让**行情**决定你的契约。契约该来自代码（字段定义），不该来自今天有几行数据。

## 处置

- 事实 + 归属 → `DATA_CONTRACTS.md` §十（DATA ALEX：补跑数据 + 修工具）
- 修法建议 + 测试用例 → `night_reports/INBOX.md`（Zac 夜里可做）
- Joe 只报不修（任务书：不修代码、不重跑 cron）
