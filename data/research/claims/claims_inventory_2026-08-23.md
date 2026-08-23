# 正向结论盘点（2026-08-23，盘点 agent 产出，台账回填依据）

36 条正向结论,按「是否进代码」×「证据类型」分类。C 类(仅样本内)约 20/36,几乎全部来自
同两个样本源:event_bars.pkl(亮过信号的票,幸存偏差)+ 2026-03→08 单一格局窗口。

## 证据类型分布(关键行摘录)

- **A 外部真值(5 条,最硬)**:Structure Pivot 5/5 黄金 · VCS 4位小数 · RS 1M 190/190 ·
  Momentum 97=rs63(70/70 recall,精度仅 28%=必要非充分) · 21SMA 周期计数与三家公开统计一致
- **B 半样本/预注册(6 条,风险线为主)**:VIX-TS(115 ep)· NHNL(146 ep)· regime BANDS 左尾
  (15/16 格一致)· r2_nas2(档差不及 VIX,未进灯——**自限的好例子**)
- **⚠ 三条「主规格失败、变体通过」被显式记录且前两条已进灯**:GEX 全样本 NULL/滚动 PASS ·
  HY OAS 主规格 NULL/滚动变体 PASS · R3 complacency 预注册口径 p=0.44/事后口径 p=2e-21
- **C 仅样本内且已进代码(风险最高)**:3WT/COIL 蓄势席链 · EP entry 席 · 回踩仅领头股闸 ·
  第一波配方 · LL-HL 三格 edge 声明 · heat 共振加分 · PP trend_base 闸(10日/30日窗不一致)
- **D 说不清(2 条)**:MRNA 单例驱动的共振加分幅度 · complacency 度量未定

## 好的自限先例(值得写进协议案例)

- `top_3m` 与 `rs63_97`:代码里明确「只探不筛」/shadow-only
- `regime.py`:`predicts_return: False` + `separates_tail: True` 双字段把正负结论并排存
- r2_nas2:通过了半样本但档差不及 VIX,主动不进灯

完整 36 行表见盘点 agent 原始输出(本文件为节选);全部已按行回填 claims.jsonl(2026-08-23)。
