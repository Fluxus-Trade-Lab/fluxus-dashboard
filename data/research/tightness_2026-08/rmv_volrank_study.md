# RMV vs Volatility Percentile Rank —— 「紧」原来是两个不同的量（2026-08-23）

Andy 给的两条线索：RMV（TraderLion/Deepvue）与 Volatility Percentile Rank（LuxAlgo）。
两者都解决同一个缺陷：绝对区间%（我们卡上的 `range5_pct`）跨票不可比，必须**对自己归一**。
但归一的窗口完全不同，测出来命运也完全不同。

## 定义（实现口径）

| 指标 | 归一方式 | 窗口 | 我们的实现 |
|---|---|---|---|
| RMV | min-max：`100×(cur−min)/(max−min)`，bar range 按量能降权（`volRatio=min(vol/sma30,1)`） | **前 15 根 bar**（不含当根） | 原版 + SMA3 平滑两个变体 |
| VolRank | 百分位：当前 ATR% 在自身历史中的 rank | **252 日** | `ATR14/close` 的 252d rolling rank |

RMV 低 = 微观紧（bar 级收缩）；VolRank 低 = 年度级波动率压缩。惯例阈值都是 <20。

## 测试

场景 = Selection Lab 同款 fresh-high pullback（52wh≤60d、距高 −3~−20%、50SMA 上、距 21EMA ≤1.5ATR、$20M 流动性）。
计分 = 交易框（R=ATR14，20 日内先 +2R 赢 / 先 −1.5R 输）。
样本 = event_bars 池 28,676 个 setup-day（1,382 票 × 102 天）；稳健性用**去重叠子样本**（每票相邻 setup ≥30 天，n=3,706）。

## 结果（去重叠子样本，全样本方向一致）

| 三分位 | RMV 赢率 | VolRank 赢率 | VolRank fwd20 中位 | VolRank MAE 中位 |
|---|---|---|---|---|
| 最紧 | 35.7% | **45.6%** | **+1.92%** | **−4.73%** |
| 中 | 38.5% | 37.7% | −0.15% | −6.16% |
| 最松 | 41.5% | 32.4% | −2.21% | −7.41% |

- **VolRank：真信号**。rho=−0.127（p<0.0001），赢率差 13 个百分点，三个口径（赢率/收益/回撤）单调。
- **RMV：无优势，且在回踩时点方向反着**（最紧组赢率最低）。SMA3 平滑版彻底躺平（rho=−0.000, p=0.97）。RMV<20 与 ≥20 完全无差。
- `range5_pct`（现卡读数）：收益无信号，但 **MAE 单调**（最紧 −4.0 vs 最松 −9.0，全样本）——它量的是回撤深度，不是胜率。

## 和旧结论的统一

三次测量拼成一张图：**「紧」在扳机时刻有效（3WT 突破 +1.11 edge），在回踩雷达阶段无效（VCS 无优势、RMV 无优势）；真正在雷达阶段有效的是长窗压缩（VolRank）**。
这也解释了百人小结里「不紧」否决 67% 错杀率——Andy 眼睛判的是微观紧，而那个维度在这个场景本来就不判别。

## 边界

- event_bars 池自带幸存偏差（2026 年触发过信号的名字）；组间相对比较不受影响。
- RMV 实现是 TradingView 开源近似（Deepvue 原版未公开精确公式），已用两个变体交叉验证。
- 单一 setup（fresh-high pullback）内的结论；突破场景 3WT 结论另测在案。

## 可动的下一步

1. `volrank` 加进名片 readings（引擎现成，ATR 已算）；「不紧」否决时卡上能看到长窗压缩读数。
2. RMV 别接——两个变体都无优势，先记 NULL；oratnek 对照如需可只做影子列。

逐行样本：`pullback_tightness_sample.csv`（28,676 行，含 rmv/volrank/fwd20/mae20/tf）。
来源：LuxAlgo volatility-percentile-rank 概念页、Deepvue RMV 页、TradingView 开源 RMV 脚本。
