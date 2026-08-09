#!/usr/bin/env python3
"""为 Fluxus_Visual_Library.md 的每条视觉代码抓候选图，供人工筛选。

用法：
    python3 scripts/fetch_visuals.py                 # 抓全部（跳过已抓够的）
    python3 scripts/fetch_visuals.py --only V01,V05  # 只抓指定代码
    python3 scripts/fetch_visuals.py --count 12      # 每条抓 12 张
    python3 scripts/fetch_visuals.py --refetch V44   # 强制重抓（换了搜索词之后）

产出：
    visuals/candidates/<CODE>/<n>.jpg   候选图（gitignore）
    visuals/manifest.json               每张图的来源页 / 直链 / 尺寸

筛选用 scripts/build_visual_gallery.py 生成的本地网页。
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import re
import time
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
LIBRARY = ROOT / "Fluxus_Brand/visual/Fluxus_Visual_Library.md"
OUT = ROOT / "visuals"
CANDIDATES = OUT / "candidates"
MANIFEST = OUT / "manifest.json"

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
MIN_WIDTH = 500
MIN_BYTES = 15_000
BAD_EXT = (".svg", ".gif", ".webm", ".mp4")


@dataclass
class Entry:
    code: str
    title: str                      # V01 后面那句情绪标签
    desc: str = ""                  # 中文描述
    query: str = ""                 # 英文搜索词
    section: str = ""               # 一、体育运动 / …
    alias_of: str | None = None     # 「同 V20」这类复用条目
    images: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------- 解析 md

def parse_library(path: Path = LIBRARY) -> list[Entry]:
    text = path.read_text(encoding="utf-8")
    entries: list[Entry] = []
    section = ""

    # 按 **Vxx** 切块，同时记住块之前最近的一级标题
    for chunk in re.split(r"(?=^\*\*V\d+\*\*)", text, flags=re.M):
        heads = re.findall(r"^## +(.+)$", chunk, flags=re.M)
        m = re.match(r"\*\*(V\d+)\*\*\s*·?\s*(.*)", chunk)
        if not m:
            if heads:
                section = heads[-1].strip()
            continue

        code, title = m.group(1), m.group(2).strip()
        body = chunk[m.end():]
        # 块尾可能带下一节的标题，归给下一条
        next_head = re.search(r"^## +(.+)$", body, flags=re.M)

        quoted = [ln.lstrip("> ").strip() for ln in body.splitlines() if ln.startswith(">")]
        query = ""
        desc_lines = []
        for ln in quoted:
            q = re.search(r"搜索词[：:]\s*`?([^`]+)`?", ln)
            if q:
                query = q.group(1).strip()
            else:
                desc_lines.append(ln)
        desc = " ".join(desc_lines).strip()

        alias = None
        if not query:
            a = re.search(r"同\s*(V\d+)", desc)
            alias = a.group(1) if a else None

        entries.append(Entry(code=code, title=title, desc=desc, query=query,
                             section=section, alias_of=alias))
        if next_head:
            section = next_head.group(1).strip()

    # 别名条目继承源条目的搜索词
    by_code = {e.code: e for e in entries}
    for e in entries:
        if not e.query and e.alias_of and e.alias_of in by_code:
            e.query = by_code[e.alias_of].query
    return entries


# ---------------------------------------------------------------- 图片搜索

class ImageSearch:
    """DuckDuckGo 图片搜索（无需 API key）。"""

    def __init__(self) -> None:
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": UA})

    def _vqd(self, query: str) -> str | None:
        r = self.s.post("https://duckduckgo.com/", data={"q": query}, timeout=25)
        m = re.search(r'vqd=["\']?([\d-]+)["\']?', r.text)
        return m.group(1) if m else None

    def search(self, query: str, limit: int = 40) -> list[dict]:
        vqd = self._vqd(query)
        if not vqd:
            return []
        url = "https://duckduckgo.com/i.js?" + urllib.parse.urlencode(
            {"l": "us-en", "o": "json", "q": query, "vqd": vqd, "f": ",,,", "p": "1"}
        )
        r = self.s.get(url, headers={"Referer": "https://duckduckgo.com/"}, timeout=25)
        if r.status_code != 200:
            return []
        try:
            results = r.json().get("results", [])
        except ValueError:
            return []

        out, seen_hosts = [], {}
        for it in results:
            src = it.get("image", "")
            if not src or src.lower().endswith(BAD_EXT):
                continue
            if int(it.get("width") or 0) < MIN_WIDTH:
                continue
            host = urllib.parse.urlparse(src).netloc
            # 同一站点最多 3 张，避免一整页都来自同一个图库
            if seen_hosts.get(host, 0) >= 3:
                continue
            seen_hosts[host] = seen_hosts.get(host, 0) + 1
            out.append({
                "src": src,
                "page": it.get("url", ""),
                "title": (it.get("title") or "")[:160],
                "width": it.get("width"),
                "height": it.get("height"),
                "host": host,
            })
            if len(out) >= limit:
                break
        return out


def download(session: requests.Session, item: dict, dest: Path) -> dict | None:
    try:
        r = session.get(item["src"], timeout=25, stream=True,
                        headers={"Referer": item.get("page") or item["src"]})
        if r.status_code != 200:
            return None
        ctype = r.headers.get("Content-Type", "")
        if not ctype.startswith("image/"):
            return None
        data = r.content
        if len(data) < MIN_BYTES:
            return None
        ext = {"image/png": ".png", "image/webp": ".webp"}.get(ctype.split(";")[0], ".jpg")
        path = dest.with_suffix(ext)
        path.write_bytes(data)
        return {**item, "file": str(path.relative_to(OUT)), "bytes": len(data)}
    except Exception:
        return None


# ---------------------------------------------------------------- 主流程

def fetch_entry(entry: Entry, searcher: ImageSearch, count: int) -> Entry:
    folder = CANDIDATES / entry.code
    folder.mkdir(parents=True, exist_ok=True)

    hits = searcher.search(entry.query, limit=count * 3)
    if not hits:
        print(f"  {entry.code}  搜索无结果：{entry.query!r}")
        return entry

    session = requests.Session()
    session.headers.update({"User-Agent": UA})
    saved: list[dict] = []
    idx = 0
    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {}
        for hit in hits:
            idx += 1
            futures[pool.submit(download, session, hit, folder / f"{idx:02d}")] = hit
        for fut in cf.as_completed(futures):
            got = fut.result()
            if got:
                saved.append(got)
    saved.sort(key=lambda d: d["file"])
    entry.images = saved[:count]
    # 清掉超出数量的下载
    for extra in saved[count:]:
        (OUT / extra["file"]).unlink(missing_ok=True)
    print(f"  {entry.code}  {len(entry.images):2d} 张  ← {entry.query}")
    return entry


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=8, help="每条视觉代码保留几张候选")
    ap.add_argument("--only", default="", help="只抓这些代码，逗号分隔，如 V01,V05")
    ap.add_argument("--refetch", default="", help="强制重抓这些代码（已有的先删）")
    ap.add_argument("--delay", type=float, default=1.5, help="每条之间的等待秒数")
    args = ap.parse_args()

    entries = parse_library()
    print(f"解析到 {len(entries)} 条视觉代码")

    only = {c.strip().upper() for c in args.only.split(",") if c.strip()}
    refetch = {c.strip().upper() for c in args.refetch.split(",") if c.strip()}

    CANDIDATES.mkdir(parents=True, exist_ok=True)
    old = {}
    if MANIFEST.exists():
        old = {e["code"]: e for e in json.loads(MANIFEST.read_text())["entries"]}

    searcher = ImageSearch()
    for entry in entries:
        if only and entry.code not in only:
            if entry.code in old:
                entry.images = old[entry.code].get("images", [])
            continue
        if entry.code in refetch:
            for f in (CANDIDATES / entry.code).glob("*"):
                f.unlink()
        elif old.get(entry.code, {}).get("images"):
            have = [i for i in old[entry.code]["images"] if (OUT / i["file"]).exists()]
            if len(have) >= args.count:
                entry.images = have
                continue
        if not entry.query:
            print(f"  {entry.code}  缺搜索词，跳过")
            continue
        fetch_entry(entry, searcher, args.count)
        time.sleep(args.delay)

    MANIFEST.write_text(json.dumps({
        "source": LIBRARY.name,
        "count_per_code": args.count,
        "entries": [
            {"code": e.code, "title": e.title, "desc": e.desc, "query": e.query,
             "section": e.section, "alias_of": e.alias_of, "images": e.images}
            for e in entries
        ],
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    total = sum(len(e.images) for e in entries)
    empty = [e.code for e in entries if not e.images]
    print(f"\n完成：{total} 张候选图，{MANIFEST.relative_to(ROOT)}")
    if empty:
        print(f"没抓到图的代码（可能要改搜索词）：{' '.join(empty)}")


if __name__ == "__main__":
    main()
