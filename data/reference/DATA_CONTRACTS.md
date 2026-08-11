# 数据契约 —— 给 UI session 的交接

*2026-08-09 建,2026-08-10 更新。字段全部从活文件抽取,不是凭记忆写的。*
*生产者是 `pipeline/`,消费者是 `frontend/`。这份文档是两边之间唯一的约定。*

---

## 零、三条必须先读的规矩

**① 有些字段不是装饰,是许可证。**
下面标了 ⚠️ **必须渲染** 的字段,决定了页面有没有资格说那句话。
省掉它们,页面就会说出数据没说过的话。这不是设计偏好,是正确性。

**② 不可测 ≠ 零。**
`null` 一律表示「这一维我们算不出来」,永远不是「这一维是 0」。
UI 要把它画成空框、画在刻度之外,不能画成最低档。

**③ 契约变更走这份文档。**
数据端加字段不会通知你;这份文档更新了才算数。反过来,UI 需要新字段也写在这里再来找我。

---

## 一、`data/output/rotation.json` —— 风格轮动

**产出**:`pipeline/rotation/build_rotation.py`,每日 cron 最后一步
**当前消费方**:`frontend/src/components/breadth/RotationPanel.jsx`

### 顶层

| 字段 | 类型 | 含义 |
|---|---|---|
| `date` | str | 最后一根 K 线的日期。**不是运行日** —— 周末跑会是上周五 |
| `benchmark` | str | `"SPY"`。所有超额都是对它算的 |
| `step_sessions` | int | `10`,一格 = 10 个交易日 |
| `bucket_dates` | str[5] | 每格结束那天,由旧到新 |
| `bucket_labels` | str[5] | `["10–8w ago", …, "Last 2w"]` |
| `baskets` | obj[] | 见下 |
| `cuts` | obj[3] | 见下 |
| `verdict` | obj | 见下 |
| `state_windows` | obj | ⚠️ **必须渲染** |
| `coverage` | obj | `{baskets, of, missing[]}` |

### `verdict` —— 这是产品本身

| 字段 | 含义 |
|---|---|
| `sentence` | ⚠️ **整句直接显示,不要自己拼** 。文案逻辑在引擎里,UI 重拼必然走样 |
| `call` | `"risk_on"` / `"risk_off"` / `null`(切法互相矛盾时) |
| `agree` / `of` | 两周尺度上几票同意 / 共几票 |
| `month_call` / `month_agree` / `month_of` | 一个月尺度同上 |
| `phase` | `"established"`(两尺度一致 = 格局)· `"turning"`(两周翻了、月没翻)· `"split"` · `null` |

> **`phase` 是这个对象最贵的一位。** `turning` 和 `established` 在两周图上长得一模一样,
> 只有这一位能分开。**不显示 `phase` 等于把「刚翻」当成「已成格局」发出去。**

### `cuts[]` —— 三个切法,让那句话可被核对

`key` `label` `question` `long[]` `short[]` `spread`(两周) `month_spread`(一个月) `delta`(速度) `vote` `month_vote`

- 数值单位是**小数**(`0.0667` = +6.67pp),UI 自己乘 100
- `spread = 多头侧超额 − 空头侧超额`,同一窗口
- `delta` = 本两周 spread − 上两周 spread,**这是 RRG 给不出的「速度量级」**
- ⚠️ **`month_spread` 必须和 `spread` 并排显示。** 单独发两周读数,就是发我们自己测出会变号的那个窗口

### `baskets[]` —— 11 个风格篮子

`ticker` `name` `side`(`risk_on`/`risk_off`/`null`) `line`(float|null ×5) `ribbon`(obj ×5) 以及当日的 `state` `level` `accel`

- `line[k]` = 第 k 格那两周的对 SPY 超额,**不相交,不累计**
- `ribbon[k]` = `{state, level, accel}`,`state` ∈ Leading / Weakening / Improving / Lagging / `null`
- 四态配色必须和 `groups/StateBadge` 一致 —— 同样四个词在一个产品里不能有两套色板

### ⚠️ `state_windows` —— 必须渲染

```json
{"level_sessions": 63, "near_sessions": 21}
```

**色带的格子是两周宽,但格子里的态是 63/21 个交易日算出来的。**
两周宽的方块会诱导读者按两周去读,而两周窗口正是我们实测**半样本会变号**的那个
(`pipeline/themes/FOUR_STATE_DESIGN.md` 第六节)。

现在的做法是每格 hover 打出这句话。换个形式可以,**去掉不行**。

---

## 二、`data/output/breadth.json` → `regime` —— 环境分数

**产出**:`pipeline/screeners/regime.py`,由 `state_board.rows` 推出
**当前消费方**:无(UI 待接)

| 字段 | 含义 |
|---|---|
| `score` | 0–100,九维等权。`null` 表示整块不可测 |
| `band` / `band_label` | `damaged` / `mixed` / `healthy` / `extended` |
| `describes` | 该档描述的盘面 |
| `bands[]` | `{key,label,min,max,describes}` ×4,给 UI 画刻度 |
| `measured` / `of` | ⚠️ **必须显示**。8/9 和 6/9 不是同一个声明 |
| `strong[]` / `weak[]` | 满格 / 弱或缺的维度名 |
| `evidence` | 一句话说明这个分是怎么来的 |
| `predicts_return` | 恒为 `false` |
| `separates_tail` | 恒为 `true` |
| `caveat` | ⚠️ **必须显示** |

**档位边界 47 / 63 / 75 是 558 个交易日的经验四分位**,不是拍的整数。
所以「顶档」的意思是「我们真见过的最强那四分之一」。

### ⚠️ 为什么 caveat 是强制的

这个分数**对下个月均值收益无信息**(甚至轻微反向),**但对左尾单调**:
−5% 回撤频率从 Damaged 的 27.2% 单调降到 Extended 的 5.8%,两个半样本各自也单调。

两件事同时为真,方向相反,所以一个布尔值必然误报其中一个 —— 这就是拆成
`predicts_return` / `separates_tail` 两位的原因。

**它是仓位预算的输入,不是方向的输入。**
UI 若把它画成红绿灯,就是在替它做一个它明确做不到的声明。
另外:整个结论底下只有 **10 段独立回撤事件**,读作排序,别读作概率。

---

## 三、`data/output/groups.json` —— 主题与行业

**产出**:`pipeline/themes/build_groups.py`
**当前消费方**:`useGroups.js` → `GroupsPage.jsx`

顶层:`date` `benchmark` `universe_size` `industries[]` `themes[]` `themes_skipped` `audit` `stocks` `summary`

行字段:`group` `members` `tickers[]` `excess_3m` `rs_accel` `state` `persistence` `persistence_of` `perf_1w/1m/3m/6m/1y`
主题另有:`method` `source` `publish` `measurable` `needs_manual` `validation` `validation_excess`

### 三条陷阱

**`publish=false` 不能静默丢掉。** 它表示「这个主题没通过共动性验证」。
悄悄过滤会让「未验证」和「不存在」变成同一件事 —— `useGroups` 现在把它们分开返回,保持这个行为。

**`persistence` 必须连 `persistence_of` 一起显示。** 分母会变(组按同侪 5 个窗口,个股对基准 3 个)。
只印一个整数,等于把两把不同的尺子放进同一列。这个 bug 出过一次。

**`rs_accel` 是描述,不是信号。** 叠在 h_score 之上实测 −0.18pp,半样本一致。
`StateBadge` 的 hover 文案已经写了这句,别去掉。

---

## 四、`data/history/groups_archive.csv` —— 每日快照

**产出**:`build_groups.save()`,与 `groups.json` 同一次写入,不可分离
**消费方**:暂无。**这是为 10 周后的主题色带准备的**

每日 195 行(121 行业 + 74 主题,随分类学变动),按日期幂等替换。
列:`date` `kind`(`industry`/`theme`)`group` `members` `excess_3m` `rs_accel` `state` `persistence` `persistence_of` `perf_1w/1m/3m/6m`

**存的是当天发布的 `state`,不是原始 perf。** 事后重算会把今天的窗口常数套到昨天的数据上,
等于偷改我们说过的话。UI 要画历史色带,直接读这一列。

**起算日 2026-08-09。** 满 5 格需要 50 个交易日 —— 扣掉劳工节(2026-09-07),
落在 **2026-10-19(周一)**。

### ⚠️ 但主题色带不是「全有或全无」

`groups.json` 的主题行现在带 `ribbon` 字段,值是 5 个 `{state, level, accel}`,
**和 `rotation.json` 里 baskets[].ribbon 完全同一种对象、同一套窗口**,可以共用组件。

| 主题类型 | 数量 | `ribbon` | 为什么 |
|---|---|---|---|
| `method="proxy"` | **16** | ✅ **现在就有** | 成员是一只 ETF,历史是基金自己的价格序列,任意过去窗口今天就能算 |
| `etf` / `industry` / `rule` | 58 | `null` 到 2026-10-19 | 读数是「某一刻对一组股票取中位数」,不写下来就没有;归档从 2026-08-09 才开始 |

**前端不需要为此写分支。** `null` 段照 `StateRibbon` 既有行为画虚线空框,
到 10 月归档满了,那 58 行自己就有值了 —— 契约不变,不用改代码。

**倒推补不了。** 就算把 3000 只成分股的日线全抓来也不行:成分名单本身在变,
而我们没存过它的历史(今天就删了 7 个主题、给 Quantum Computing 加了 IBM、
把市值地板从 3 亿抬到 10 亿)。拿今天的名单去套 6 月的价格,
算的是「今天这批票当时的表现」,不是「当时这个主题的状态」——
带后见之明的数,比没有数更糟。

---

## 五、当前未接入的东西

| 文件 | 状态 |
|---|---|
| `data/output/sentiment.json` | 5 项价格序列已自动化;AAII / NAAIM 走手工录入,**从未录过**。前端无消费方 |
| `data/output/baskets/*.json` | 共享日线仓库(27 只 ETF:轮动 12 ∪ proxy 主题 16),中间产物,UI 不该直接读 |

---

## 六、已知的失败形态

| 现象 | 原因 | 谁负责 |
|---|---|---|
| `rotation.json` 日期不动 | cron 的 rotation 步骤挂了 —— **会让整个构建失败并发 Discord 告警** | 数据端 |
| `groups.json` 里主题变少 | 共动性验证没过,`publish=false` | 数据端(预期行为) |
| 色带某格是虚线空框 | 那一格算不出态(历史不够或数据缺) | UI 照常画空框,**不要填色** |
| `regime.score` 为 `null` | 九维全不可测 | UI 显示「不可测」,**不要显示 0** |
