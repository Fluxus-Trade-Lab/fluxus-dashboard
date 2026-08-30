"""World Bank Pink Sheet（月度商品价格，1960 起）的最小 xlsx 读取器。

不装 openpyxl —— xlsx 就是一个装着 XML 的 zip，这里只取需要的两列。
数据说明：Pink Sheet 的黄金/白银是**当月均价**（不是月末价），
所以它与月末口径不是同一个量，报告里必须说清（见 results.md §五）。
"""
import re
import zipfile
import pandas as pd

SHEET = "xl/worksheets/sheet2.xml"   # 'Monthly Prices'


def _shared_strings(z):
    try:
        xml = z.read("xl/sharedStrings.xml").decode("utf-8", "ignore")
    except KeyError:
        return []
    return [re.sub(r"<[^>]+>", "", m) for m in re.findall(r"<si>(.*?)</si>", xml, re.S)]


def read_monthly(path="pink.xlsx"):
    z = zipfile.ZipFile(path)
    sst = _shared_strings(z)
    xml = z.read(SHEET).decode("utf-8", "ignore")
    grid = {}
    for row in re.findall(r"<row[^>]*r=\"(\d+)\"[^>]*>(.*?)</row>", xml, re.S):
        rn, body = int(row[0]), row[1]
        for c in re.findall(r"<c r=\"([A-Z]+)\d+\"([^>]*)>(.*?)</c>", body, re.S):
            col, attrs, inner = c
            v = re.search(r"<v>(.*?)</v>", inner, re.S)
            if not v:
                continue
            val = v.group(1)
            if 't="s"' in attrs:
                val = sst[int(val)] if int(val) < len(sst) else val
            grid[(rn, col)] = val
    return grid


def series(grid, header_names):
    """在前 10 行里找列名，返回 {name: pd.Series(index=PeriodIndex('M'))}。"""
    hdr_row, cols = None, {}
    for rn in range(1, 12):
        row = {c: v for (r, c), v in grid.items() if r == rn}
        hit = {v.strip(): c for c, v in row.items() if v.strip() in header_names}
        if len(hit) == len(header_names):
            hdr_row, cols = rn, hit
            break
    if hdr_row is None:
        raise SystemExit(f"找不到表头列 {header_names}")
    date_col = "A"
    out = {n: {} for n in header_names}
    rn = hdr_row + 1
    maxrow = max(r for r, _ in grid)
    while rn <= maxrow:
        d = grid.get((rn, date_col))
        if d and re.match(r"^\d{4}M\d{1,2}$", str(d).strip()):
            y, m = str(d).strip().split("M")
            per = pd.Period(f"{y}-{int(m):02d}", freq="M")
            for n, c in cols.items():
                v = grid.get((rn, c))
                try:
                    out[n][per] = float(v)
                except (TypeError, ValueError):
                    pass
        rn += 1
    return {n: pd.Series(v).sort_index() for n, v in out.items()}


if __name__ == "__main__":
    g = read_monthly()
    s = series(g, {"Gold", "Silver"})
    for k, v in s.items():
        print(f"{k}: n={len(v)}  {v.index[0]} -> {v.index[-1]}  首值={v.iloc[0]}  末值={v.iloc[-1]}")
