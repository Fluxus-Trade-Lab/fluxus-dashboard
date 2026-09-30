---
name: focus-notes
description: 给 Screener 漏斗的每只 Focus 候选写一句话（中英各一）——它的组（主题，没有主题就看行业）在变强还是变弱，它自己站在哪；外加全页共用的一句大盘。每个数都必须出自该票的事实卡，写完过核对闸。凡任务 type=focus_notes、守护进程每日「候选一句话」班、或有人说「给候选配一句话 / focus notes / 重写 XX 那句 / 今天的候选说了什么 / 一句话怎么又错了」都用本 skill；Andy 2026-10-01 批过写法（「写法ok」），29 句样本在 reference/，照那个写，不另起炉灶。
---

# focus-notes：每只候选一句话

Andy 2026-10-01 批的写法：「那 27 句候选，写法ok」。批的是 `reference/approved_zh_2026-09-29.json` 那 29 句（27 只回踩 + IOVA + ABSI）。**照它写，别重新发明。**

## 一、开工：数据是不是今天的

```bash
python3 -c "from pipeline.marketcal import last_completed_session as l; print(l())"
```

在基于 `origin/main` 的临时树里跑（主树常落后 main）。`data/output/market_light.json` 的 `date` ≠ 上面那个交易日 → 数据没落地，**不写**，`block` 本单并写明等的是哪天的数据。当天的产出文件已存在 → 已经写过，`done`，不重写。

## 二、出事实卡

```bash
python3 .claude/skills/focus-notes/scripts/build_cards.py --data data/output --out /tmp/cards.json
```

只写 `focus: true` 的票（①宇宙闸 + §11.1 四条全过）。卡里有什么数，句子才能用什么数。

## 三、写句子（中英各一）

**结构**：先说组，再说它自己。一句话，可以用分号。

- **组**：`theme` 有就用主题，没有就写「没有主题归属，看行业」再用 `ind`。状态词照抄英文（Leading / Improving / Weakening / Lagging）。`accel` 带正负号、不带 %（它是 rs_accel×100）：「在加速（+39.5）」「减速 −26.5」。`ex1m` 是一个月相对 SPY 的超额：「一个月跑赢 SPY 13.3%」「落后 SPY 9.4%」。`prev` 是三档，从旧到新，最后一档就是当前状态：「三档 Leading → Improving → Weakening」。
- **它自己**：选最能说明它位置的一两个数——离 21EMA 几个 ATR（回踩深浅）、组内百分位、离 52 周高、一个月涨跌、EPS/营收。
- **同组比较**：「四只炼油里回踩最深」这类句子闸查不了，**写之前自己把同组几只的数列出来核一遍**。
- **大盘一句**（`_market`）：全页共用，只写一次：交通灯 SPY/QQQ 与结论、广度 env 与 score、Regime、系统口径 exposure、主题四态的计数。
- **读数互相矛盾就直说**：例如 `rs` 1 却 `grp_pctile` 100 →「⚠️ RS 评级 1，组内却是第 100 百分位，两个读数互相矛盾。先当数据问题查，别当候选。」并开单给 alex。

**不许**：买 / 卖 / 建议 / 应该 / 止损 / 仓位（闸会拦）；卡上没有的数；财报（`next_earnings` 目前全空，见 T-1001-04）；「这是……的信号」这类判断——判断是 Andy 的，句子只做读数和指向。

**英文**：同一套规则，不是逐字翻译。英文写法 Andy 还没单独审过，第一次上页前在交付说明里标「EN 未审」。

## 四、过闸

```bash
python3 .claude/skills/focus-notes/scripts/check_notes.py <当日产出文件>
```

`flagged` 非空就改句子重跑，直到空。闸查不到的同组比较，在 runs 日志里列出你核过的数。

## 五、产出与落地

文件：`data/research/screener_redesign/focus/<asof>.json`（白名单，可自合）。ALEX 确认 `data/output/focus.json` 之前一律写这里（T-1001-06）。形状：

```json
{"asof": "2026-09-29", "generated_at": "<UTC ISO>", "counts": {}, "rule": {}, "market": {},
 "setups": {"pullback": {"label": "", "label_en": "", "rows": [<card>]}},
 "notes": {"_market": {"zh": "", "en": ""}, "STX": {"zh": "", "en": ""}},
 "gate": {"flagged": [], "hand_checked": ["MPC: 四只炼油 21EMA 0.41/0.50/0.15/0.76"]},
 "en_reviewed_by_andy": false}
```

= `build_cards.py` 的整份输出 + `notes` + `gate`。**同一份内容再写一份 `latest.json`**（同目录）——Screener 页只读这一个（T-1001-08），它拿 `asof` 和站点最新交易日比，过期会在页上标出来。按宪法「直推 main 标准动作」在临时树提交**只这两个文件**，push 带重试，最后 `git log origin/main -1` 核到自己的 commit。

## 坑（同工作流的坑追加在这里，不另开 memory）

- **组选哪个**：挂多个主题时取三个月超额最高的那个（ESTC 挂 Cloud Software 与 Cybersecurity，取后者）。句子里要说「挂两个主题，按三个月超额取 X」。
- **RS 评级 1**：09-25 SUNB、09-29 ANDG 都是 1，组内却靠前。成因在查（T-1001-04），在查清前一律按上面的 ⚠️ 句处理。
- **忘写 `latest.json` 页面就停在旧日子**：页上会标「句子还停在 X」，但那是症状；两份同时写、同一个 commit。
- **临时目录会被清**：`/private/tmp` 下的草稿隔夜可能就没了（09-26 的模板丢过一次），当天写完当天落仓库。
