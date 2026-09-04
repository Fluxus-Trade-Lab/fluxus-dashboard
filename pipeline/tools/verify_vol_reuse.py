"""vol_5d_50d 复用验证：从 1y 面板切出来的值，等不等于 3mo 专门拉的值。

砍掉 volume_enrichment 的整轮下载，前提是这两条路径给出同一个数。
两条路径的下载参数不同——adapter 用 yfinance 默认（auto_adjust 未指定），
volume_enrichment 显式 auto_adjust=False——所以这是要量的，不是要想的。

用法: python3 verify_vol_reuse.py [样本数]
"""
import sys
import random
import json
import pandas as pd
import yfinance as yf

sys.path.insert(0, sys.argv[2] if len(sys.argv) > 2 else ".")
from pipeline.screeners.volume_enrichment import ratio_from_volumes  # noqa: E402

N = int(sys.argv[1]) if len(sys.argv) > 1 else 200

uni = json.load(open("data/output/universe.json"))
rows = uni["rows"] if isinstance(uni, dict) and "rows" in uni else uni
tickers = [r["ticker"] for r in rows if r.get("ticker")]
random.seed(20260904)
sample = random.sample(tickers, min(N, len(tickers)))
print(f"样本 {len(sample)} 只，来自 universe {len(tickers)} 只")

# A 路：adapter 的参数（1y，group_by='ticker'，auto_adjust 用默认）
a = yf.download(sample, period="1y", group_by="ticker",
                progress=False, threads=True)
# B 路：volume_enrichment 的参数（3mo，group_by='column'，auto_adjust=False）
b = yf.download(sample, period="3mo", interval="1d", group_by="column",
                threads=True, progress=False, auto_adjust=False)

bvol = b["Volume"]
if isinstance(bvol, pd.Series):
    bvol = bvol.to_frame(sample[0])

same = diff = only_a = only_b = neither = 0
diffs = []
for t in sample:
    try:
        va = ratio_from_volumes(a[t]["Volume"].dropna())
    except Exception:
        va = None
    vb = ratio_from_volumes(bvol[t]) if t in bvol.columns else None
    if va is None and vb is None:
        neither += 1
    elif va is None:
        only_b += 1
    elif vb is None:
        only_a += 1
    elif abs(va - vb) < 1e-4:
        same += 1
    else:
        diff += 1
        diffs.append((t, va, vb, round(abs(va - vb) / vb * 100, 2)))

print(f"\n两路都有值且相同 : {same}")
print(f"两路都有值但不同 : {diff}")
print(f"只有 1y 面板有值 : {only_a}   (复用后多测到的)")
print(f"只有 3mo 有值    : {only_b}   (复用后会丢的 ← 关键)")
print(f"两路都测不出     : {neither}")
if diffs:
    print("\n不同的前 15 个 (ticker, 1y切, 3mo拉, 相对差%):")
    for d in sorted(diffs, key=lambda x: -x[3])[:15]:
        print("  ", d)
