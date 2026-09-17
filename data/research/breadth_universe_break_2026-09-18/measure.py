"""宇宙规模断点对「家数类」读数的影响 —— 两处，一处已修一处没修。

背景：`data/history/breadth_archive.csv` 的 `universe_size` 有两个断点。
2026-08-10 那个是 `2f782b53` 把 Finviz 翻页上限从 150 页抬到 600 页
（此前整个 M–Z 被截掉），当日读数从约 3,000 跳到约 5,620。

家数类读数（up_4pct / down_4pct / 新高新低 / 季度价差）跨这条线不可比：
同一个市场，宇宙翻倍，家数也翻倍，而阈值和历史分位都还停在老宇宙上。

后端 `breadth_signals.thrust_count()` 2026-08-09（`16db6a88b`）已经按宇宙缩放，
前端 `MarketStateSummary.jsx` 和 `percentile_context()` 没有。本脚本量这两处。

    python3 data/research/breadth_universe_break_2026-09-18/measure.py
"""
from __future__ import annotations

import sys

import pandas as pd

sys.path.insert(0, '.')
from pipeline.screeners.breadth_signals import thrust_count   # noqa: E402

ARCHIVE = 'data/history/breadth_archive.csv'
BREAK = '2026-08-10'          # 翻页上限抬高后的第一场
TILE_CONST = 300.0            # frontend/src/components/breadth/MarketStateSummary.jsx:15


def load() -> pd.DataFrame:
    df = pd.read_csv(ARCHIVE).sort_values('date').reset_index(drop=True)
    df['date'] = df['date'].astype(str)
    return df


def label(up: float, down: float, need: float) -> str:
    """牌面上那四个词，前端与后端共用的判定形状。"""
    if up >= need and down >= need:
        return 'churn / volatile'
    if up >= need:
        return 'bullish thrust'
    if down >= need:
        return 'bearish thrust'
    return 'no thrust'


def thrust_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in df.iterrows():
        up, down = float(r['up_4pct']), float(r['down_4pct'])
        need = thrust_count(r)
        rows.append((r['date'], up, down, need,
                     label(up, down, TILE_CONST), label(up, down, need)))
    return pd.DataFrame(rows, columns=['date', 'up4', 'dn4', 'need',
                                       'tile_300', 'engine_scaled'])


def pctile(series: pd.Series, i: int):
    """percentile_context 的算法：当日值在「到当日为止」的全历史里的分位。"""
    upto = series.iloc[:i + 1].dropna()
    today = series.iloc[i]
    if pd.isna(today) or len(upto) == 0:
        return None
    return int(round(float((upto <= today).mean()) * 100))


def percentile_table(df: pd.DataFrame) -> pd.DataFrame:
    u = pd.to_numeric(df['universe_size'], errors='coerce')
    num = lambda c: pd.to_numeric(df[c], errors='coerce')   # noqa: E731
    series = {
        'up_4pct': num('up_4pct'),
        'down_4pct': num('down_4pct'),
        'nh_nl_net': num('new_highs') - num('new_lows'),
        'qtr_spread': num('up_25pct_qtr') - num('down_25pct_qtr'),
    }
    rows = []
    for i in range(len(df)):
        if df['date'][i] < BREAK:
            continue
        row = {'date': df['date'][i]}
        for key, s in series.items():
            row[f'{key}_count'] = pctile(s, i)        # 现行做法
            row[f'{key}_ratio'] = pctile(s / u, i)    # 同口径的比率版
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    df = load()
    u = pd.to_numeric(df['universe_size'], errors='coerce')
    pre, post = df['date'] < BREAK, df['date'] >= BREAK

    print('== 归档与断点 ==')
    print(f'{len(df)} 场 {df["date"].iloc[0]}..{df["date"].iloc[-1]}'
          f' | {BREAK} 及以后 {post.sum()} 场（{100 * post.mean():.1f}%）')
    print(f'universe_size 中位：断点前 {u[pre].median():.0f} → 断点后 {u[post].median():.0f}')
    for col in ('up_4pct', 'down_4pct'):
        s = pd.to_numeric(df[col], errors='coerce')
        print(f'{col} 中位：{s[pre].median():.0f} → {s[post].median():.0f}'
              f'（×{s[post].median() / s[pre].median():.2f}）')

    print('\n== 一、牌面那个词：前端 300 常量 vs 后端按宇宙缩放 ==')
    t = thrust_table(df)
    tp, tq = t[t.date >= BREAK], t[t.date < BREAK]
    print(f'断点后不一致 {(tp.tile_300 != tp.engine_scaled).sum()}/{len(tp)} 场'
          f' · 断点前 {(tq.tile_300 != tq.engine_scaled).sum()}/{len(tq)} 场')
    for name, frame in (('断点前', tq), ('断点后', tp)):
        share = lambda col: 100 * (frame[col] == 'churn / volatile').mean()   # noqa: E731
        print(f'  {name} churn/volatile 出现率：前端 {share("tile_300"):.1f}%'
              f' · 后端 {share("engine_scaled"):.1f}%')
    print(tp.to_string(index=False))

    print('\n== 二、percentile_context：家数分位 vs 比率分位（断点后每一场）==')
    p = percentile_table(df)
    for key in ('up_4pct', 'down_4pct', 'nh_nl_net', 'qtr_spread'):
        d = (p[f'{key}_count'] - p[f'{key}_ratio']).dropna()
        print(f'  {key}: 家数口径比比率口径高 中位 {d.median():+.0f} 分位点'
              f' · 最大 {d.abs().max():.0f} · n={len(d)}')
    print(p.to_string(index=False))


if __name__ == '__main__':
    main()
