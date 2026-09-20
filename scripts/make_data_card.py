#!/usr/bin/env python3
"""出数据卡：大字体数字 + 一句话结论 + 测量行 → PNG。

课程发售预热期的「数据卡片」母版（`Fluxus_Brand/ops/briefs/2026-09-19_course_launch_build_in_public_brief.md`
末节）：不做课程截图、不做倒计时，只用一个可验证的数字 + 一句话方法论结论。
版式继承海报系统（`Fluxus_Poster_System.md`）：暖石底、IBM Plex、无渐变无阴影，
字体链路与 make_poster.py 同源（自托管 woff2，缺字体直接报错，不回退系统字体）。

    python3 scripts/make_data_card.py \\
        --number "86%" \\
        --en "14 past buyers. 86% later became paying members." \\
        --zh "过去 14 个课程买家，86% 后来成为付费会员。" \\
        --meta "SOURCE: 2026-08-29 business model note"

输出默认 visuals/out/<日期>_card_<slug>.png，1080×1350（4:5，X 信息流）。
--ratio 16x9 出 1600×900。--dark 出深色版。渲染用系统里的 Chrome headless。
"""

from __future__ import annotations

import argparse
import base64
import html
import re
import subprocess
import tempfile
from datetime import date
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VISUALS = ROOT / "visuals"
OUTDIR = VISUALS / "out"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

FONTDIR = ROOT / "Fluxus_Brand" / "visual" / "explorations" / "2026-08-08" / "fonts"
FACES = [                       # (CSS family, weight, 文件名) —— 同 make_poster.py
    ("Plex",     400, "IBMPlexSans-Regular.woff2"),
    ("Plex",     600, "IBMPlexSans-SemiBold.woff2"),
    ("PlexCond", 700, "IBMPlexSansCondensed-Bold.woff2"),
    ("PlexMono", 400, "IBMPlexMono-Regular.woff2"),
]
SANS_STACK = 'Plex,"PingFang SC",-apple-system,"Helvetica Neue",sans-serif'
COND_STACK = 'PlexCond,Plex,"PingFang SC",-apple-system,sans-serif'
MONO_STACK = 'PlexMono,ui-monospace,"SF Mono",Menlo,monospace'

SIZES = {"4x5": (1080, 1350), "16x9": (1600, 900), "1x1": (1080, 1080)}


@lru_cache(maxsize=1)
def fontface_css() -> str:
    out = []
    for family, weight, fname in FACES:
        path = FONTDIR / fname
        if not path.exists():
            raise SystemExit(
                f"缺字体：{path}\n"
                "数据卡不许回退到替代字体（同海报系统规矩）。补齐 IBM Plex woff2 再跑。")
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        out.append(f"@font-face{{font-family:{family};font-weight:{weight};"
                   f"font-display:block;src:url(data:font/woff2;base64,{b64}) "
                   'format("woff2")}')
    return "\n  ".join(out)


TEMPLATE = """<!doctype html><html><head><meta charset="utf-8"><style>
  {fontface}
  *{{box-sizing:border-box;margin:0}}
  html,body{{width:{w}px;height:{h}px;overflow:hidden}}
  body{{background:{bg};color:{fg};
        font-family:{sans};
        font-size:{base}px;padding:{pad}em}}
  .stack{{display:flex;flex-direction:column;height:100%}}
  .number{{font-family:{cond};font-weight:700;font-size:{numsize}em;
           line-height:.86;letter-spacing:-.02em;color:{fg};margin-top:2.2em}}
  .label{{margin-top:1.15em;display:flex;flex-direction:column}}
  .en{{font-size:1.55em;font-weight:600;letter-spacing:-.01em;line-height:1.32}}
  .zh{{font-size:1.05em;font-weight:400;color:{fg2};line-height:1.65;margin-top:.65em}}
  .foot{{display:flex;justify-content:space-between;align-items:baseline;
         margin-top:auto;padding-top:1.1em;border-top:1px solid {rule}}}
  .meta{{font-family:{mono};font-size:.92em;letter-spacing:.06em;
         text-transform:uppercase;color:{fg3}}}
  .mark{{font-family:{cond};font-weight:700;letter-spacing:.3em;font-size:.85em}}
</style></head><body><div class="stack">
  <div class="number">{number}</div>
  <div class="label">
    <div class="en">{en}</div>
    {zh}
  </div>
  <div class="foot"><span class="meta">{meta}</span><span class="mark">FLUXUS</span></div>
</div></body></html>"""

LIGHT = dict(bg="#F2F1ED", fg="#1c1917", fg2="#57534E", fg3="#948F86", rule="#e7e5e4")
DARK = dict(bg="#12110f", fg="#f5f4f2", fg2="#8a8480", fg3="#6b6560", rule="#332e29")


def build_html(number: str, en: str, zh: str, meta: str, ratio: str, dark: bool) -> str:
    w, h = SIZES[ratio]
    theme = DARK if dark else LIGHT
    base = round(w / 42)          # 同 make_poster.py：1080 → 26px 基准
    pad = 2.6
    numsize = 4.6 if ratio != "16x9" else 3.6   # 数字是这张卡唯一的视觉锚点
    return TEMPLATE.format(
        w=w, h=h, base=base, pad=pad, numsize=numsize,
        fontface=fontface_css(), sans=SANS_STACK, cond=COND_STACK, mono=MONO_STACK,
        number=html.escape(number),
        en=html.escape(en),
        zh=f'<div class="zh">{html.escape(zh)}</div>' if zh else "",
        meta=html.escape(meta), **theme)


def render(page: str, out: Path, ratio: str) -> None:
    w, h = SIZES[ratio]
    if not Path(CHROME).exists():
        raise SystemExit(f"找不到 Chrome：{CHROME}")
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".html", dir=str(VISUALS),
                                     encoding="utf-8", delete=False) as fh:
        fh.write(page)
        tmp = Path(fh.name)
    try:
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
             "--allow-file-access-from-files", "--force-device-scale-factor=2",
             f"--screenshot={out}", f"--window-size={w},{h}", str(tmp)],
            check=True, capture_output=True, timeout=90)
    finally:
        tmp.unlink(missing_ok=True)


def slugify(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return s[:40] or "card"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--number", required=True, help="大字体那个数字/短语，如 86%% 或 66.5%%")
    ap.add_argument("--en", required=True, help="一句话结论（英文）")
    ap.add_argument("--zh", default="", help="一句话结论（中文，可省）")
    ap.add_argument("--meta", default="", help="测量行 —— 数字的出处，不许留空造假源")
    ap.add_argument("--ratio", default="4x5", choices=list(SIZES))
    ap.add_argument("--dark", action="store_true")
    ap.add_argument("--out", help="输出路径")
    args = ap.parse_args()

    if not args.meta.strip():
        raise SystemExit("--meta 不能为空：数据卡的出处必须写实，不许发无源数字。")

    slug = slugify(args.number + "-" + args.en)
    name = args.out or (OUTDIR / f"{date.today():%Y%m%d}_card_{slug}"  # localtime-ok: 输出文件名
                        f"{'_dark' if args.dark else ''}.png")
    out = Path(name)
    if not out.is_absolute():
        out = ROOT / out

    render(build_html(args.number, args.en, args.zh, args.meta, args.ratio, args.dark), out, args.ratio)
    w, h = SIZES[args.ratio]
    print(f"{(out.relative_to(ROOT) if out.is_relative_to(ROOT) else out)}  ({w}×{h} @2x)")


if __name__ == "__main__":
    main()
