---
name: focus-notes
description: 给 Screener 漏斗的每只 Focus 候选写一句只说个股的话（中英各一，B1：组的方向页面另印一栏，句子不许重复组）——回踩深浅、组内排名、离高点、业绩、同组相对位置；外加全页共用的一句大盘。每个数都必须出自该票的事实卡，写完过核对闸。凡任务 type=focus_notes、守护进程每日「候选一句话」班、或有人说「给候选配一句话 / focus notes / 重写 XX 那句 / 今天的候选说了什么 / 一句话怎么又错了」都用本 skill；Andy 2026-10-01 定了 B1，29 只样本在 reference/approved_b1_2026-09-29.json，照那个写，不另起炉灶。
---

# focus-notes：每只候选一句话

Andy 2026-10-01 先批了整句写法（「那 27 句候选，写法ok」），同日改定 **B1**（「B1」）：页面一行一只，组的方向另印一栏，句子只说个股。样本是 `reference/approved_b1_2026-09-29.json` 那 29 只。**照它写，别重新发明。**

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

## 三、写句子（中英各一）——只说个股（B1）

Andy 2026-10-01 定的排法是 **B1**（「B1」；前一句原话「B一只一行的方式，可以但是组方向和一行句子的内容重复性极高，有改。不合适的话，就不用句子，而是直接走数据」）：页面一行一只，**组的名字、状态、加速度由页面自己从事实卡印在一栏里**，句子只说这只票自己。所以：

- **不写组**：组名、Leading / Improving / Weakening / Lagging、组的 accel / ex1m / 三档——一律不进句子（闸会拦组名和四个状态词）。可以说「跟着组一起回落」「同组四只里最深」这种**相对位置**，那是个股的信息。
- **写它自己**：选最能说明它位置的两三个数——离 21EMA 几个 ATR（回踩深浅）、组内百分位、离 52 周高、一个月涨跌、离 50SMA、EPS / 营收。一句，逗号分隔，可以一个分号。越短越好（样本中位约 20 个汉字）。
- **同组比较**：「四只炼油里回踩最深」这类闸查不了，**写之前把同组几只的数列出来核一遍，写进 gate.hand_checked**。⚠️ 09-29 的整句样本里 INTC「回得最浅」就是错的（PANW 0.99 > INTC 0.98），当时没核。
- **大盘一句**（`_market`）：全页共用，只写一次：交通灯 SPY/QQQ 与结论、广度 env 与 score、Regime、系统口径 exposure、主题四态的计数。这一句可以有状态词。
- **读数互相矛盾就直说**：例如 `rs` 1 却 `grp_pctile` 100 →「⚠️ RS 评级 1，组内却是第 100 百分位，两个读数互相矛盾。先当数据问题查，别当候选。」并开单给 alex。

样本：`reference/approved_b1_2026-09-29.json`（29 只，中英）。旧的整句样本 `approved_zh_2026-09-29.json` 留作写法沿革，**不再照抄**。

**不许**：买 / 卖 / 建议 / 应该 / 止损 / 仓位（闸会拦）；卡上没有的数；财报（`next_earnings` 目前全空，见 T-1001-04）；「这是……的信号」这类判断——判断是 Andy 的，句子只做读数和指向。

**英文**：同一套规则，不是逐字翻译。英文写法 Andy 还没单独审过，第一次上页前在交付说明里标「EN 未审」。

## 四、过闸

```bash
python3 .claude/skills/focus-notes/scripts/check_notes.py <当日产出文件>
```

`flagged` 非空就改句子重跑，直到空。闸查不到的同组比较，在 runs 日志里列出你核过的数。

## 五、产出与落地

存量 `data/research/screener_redesign/focus/latest.json`（旧口径留下的文件）自 2026-10-01 起停更，不再有班次写它；删它按 `gate.py` 判 `status=="D"` + `data/` 前缀 = andy 档，不要顺手删，要删另开单问 Andy。

逐日存档文件：`data/research/screener_redesign/focus/<asof>.json`（`data/` 前缀，gate=none，可自合；此子目录归本线，2026-10-01 ops 裁 T-1001-16）。形状：

```json
{"asof": "2026-09-29", "generated_at": "<UTC ISO>", "counts": {}, "rule": {}, "market": {},
 "setups": {"pullback": {"label": "", "label_en": "", "rows": [<card>]}},
 "notes": {"_market": {"zh": "", "en": ""}, "STX": {"zh": "", "en": ""}},
 "gate": {"flagged": [], "hand_checked": ["MPC: 四只炼油 21EMA 0.41/0.50/0.15/0.76"]},
 "en_reviewed_by_andy": false}
```

= `build_cards.py` 的整份输出 + `notes` + `gate`。**同一份内容再写一份 `frontend/public/data/focus.json`**——DATA ALEX T-1001-06 定的落地路径（不进 `data/output/`），Screener 页只读这一个（T-1001-08），它拿 `asof` 和站点最新交易日比，过期会在页上标出来。这个精确路径 gate.py 已判 none（2026-10-01 ops 裁 T-1001-16），不走 reviewer——**换来的是没有复核员再替你查这份文件**，push 前自己跑一遍 `python3 -m pytest -q pipeline/tests/test_public_output_privacy.py`（二十秒级，`frontend/public` 是它的扫描根之一，已有的白名单豁免见该测试 `PUBLIC_ROOTS`），红了就是句子/字段里混进了像美元、股数、会员名这类不该公开的东西，不许带红推送。按宪法「直推 main 标准动作」在临时树提交**只这两个文件**，push 带重试，最后 `git log origin/main -1` 核到自己的 commit。

## 坑（同工作流的坑追加在这里，不另开 memory）

- **组选哪个**：挂多个主题时，`build_cards.py` 取三个月超额最高的那个放进 `theme`（ESTC 挂 Cloud Software 与 Cybersecurity，取后者），页面的组栏就印它。B1 之后句子**不提主题名**（闸会拦），这条规则只管页面组栏印哪个组。
- **RS 评级 1**：09-25 SUNB、09-29 ANDG 都是 1，组内却靠前。成因在查（T-1001-04），在查清前一律按上面的 ⚠️ 句处理。
- **忘写 `frontend/public/data/focus.json` 页面就停在旧日子**：页上会标「句子还停在 X」，但那是症状；两份同时写、同一个 commit。
- **临时目录会被清**：`/private/tmp` 下的草稿隔夜可能就没了（09-26 的模板丢过一次），当天写完当天落仓库。
