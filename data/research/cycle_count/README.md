# 21SMA 周期计数复算（L6B 数据底座）

`cycle_SPY.csv` / `cycle_QQQ.csv` — 2009-2026 日线：date, close, sma21, count
（count = 连续收于 21 日 SMA 上方/下方的带符号天数，+N/−N）。

- 生成：yfinance 日线 → 21 日 SMA → 连续计数；2026-08-12 由 Claude 复算，
  与 Ameet Rai / Deepvue / TraderLion 公开统计核对，近乎一致。
- 一处修正：2020 以来最长下行 = **32 天（起 2022-04-11，SPY）**，非 COVID 的 30 天；
  QQQ 2022-08-22 起有 43 天水下纪录。
- 消费方：`SwingMasterclass/M2_L06B_MAs_Cycles_Tops.md`（统计表 + 342 笔交易分桶）。

重跑：
```python
import yfinance as yf, pandas as pd
df = yf.download('SPY', start='2009-01-01', auto_adjust=True)
c = df['Close'].squeeze(); sma = c.rolling(21).mean()
above = (c > sma).astype(int)
grp = (above != above.shift()).cumsum()
cnt = above.groupby(grp).cumcount() + 1
signed = cnt.where(above == 1, -cnt)
pd.DataFrame({'close': c, 'sma21': sma, 'count': signed}).dropna().to_csv('cycle_SPY.csv')
```
