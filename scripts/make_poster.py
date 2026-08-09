#!/usr/bin/env python3
"""出海报：一张图 + 一句话 + 一行测量 → PNG。

    python3 scripts/make_poster.py \\
        --image visuals/candidates/V01/01.jpg \\
        --en "It's a blind spot. That's exactly why cash is the right position." \\
        --zh "正因为这是盲区，现金才是最合适的仓位。" \\
        --meta "SPX 6412 · 20EMA 6455 · CASH 60%"

不给 --image 时用 --code V01 从 visuals/selected/ 里取已筛好的图。
输出默认 visuals/out/<日期>_<code>.png,1080×1350(4:5,X 信息流)。
--ratio 16x9 出 1600×900(信的封面 / 横版)。
--dark 出深色版(暗调照片用)。

框的定义见 Fluxus_Poster_System.md。渲染用系统里的 Chrome headless。
"""

from __future__ import annotations

import argparse
import base64
import html
import subprocess
import tempfile
from datetime import date
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VISUALS = ROOT / "visuals"
OUTDIR = VISUALS / "out"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# v2 字体：IBM Plex,自托管,OFL。见 DESIGN.md 第一节。
# 机器上没装 Plex,所以把 woff2 内联进临时 HTML —— 不留系统字体的回退余地,
# 缺文件就报错,绝不悄悄退回 Helvetica。
FONTDIR = ROOT / "Fluxus_Brand" / "visual" / "explorations" / "2026-08-08" / "fonts"
FACES = [                       # (CSS family, weight, 文件名)
    ("Plex",     400, "IBMPlexSans-Regular.woff2"),
    ("Plex",     600, "IBMPlexSans-SemiBold.woff2"),
    ("PlexCond", 700, "IBMPlexSansCondensed-Bold.woff2"),
    ("PlexMono", 400, "IBMPlexMono-Regular.woff2"),
]
# 中文永不进等宽字(海报系统 2026 年验证:会塌)。Plex 无中文字形,
# 主句/副句都靠这条链落到 PingFang SC;展签行按规格只写测量,不写中文。
SANS_STACK = 'Plex,"PingFang SC",-apple-system,"Helvetica Neue",sans-serif'
COND_STACK = 'PlexCond,Plex,"PingFang SC",-apple-system,sans-serif'
MONO_STACK = 'PlexMono,ui-monospace,"SF Mono",Menlo,monospace'

SIZES = {"4x5": (1080, 1350), "16x9": (1600, 900), "1x1": (1080, 1080)}


@lru_cache(maxsize=1)
def fontface_css() -> str:
    """把 woff2 内联成 data: URI —— file:// 页面加载字体不受 CORS 摆布。"""
    out = []
    for family, weight, fname in FACES:
        path = FONTDIR / fname
        if not path.exists():
            raise SystemExit(
                f"缺字体：{path}\n"
                "海报系统不许回退到替代字体。补齐 IBM Plex woff2 再跑。")
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
        font-size:{base}px;padding:{pad}em {pad}em {padb}em;
        display:flex;flex-direction:column;{flex}}}
  .frame{{{framecss};background:{mat};overflow:hidden;flex-shrink:0}}
  .frame img{{width:100%;height:100%;object-fit:cover;display:block}}
  .label{{{labelcss};display:flex;flex-direction:column}}
  .en{{font-size:2.15em;font-weight:600;letter-spacing:-.01em;line-height:1.28}}
  .zh{{font-size:1.28em;font-weight:400;color:{fg2};line-height:1.6;margin-top:.7em}}
  .foot{{display:flex;justify-content:space-between;align-items:baseline;
         margin-top:auto;padding-top:1.1em;border-top:1px solid {rule}}}
  /* Measurement line — DESIGN.md §5.3. It may never be the smallest type in a
     piece: it is what separates a measurement from a poster, so at 1em (below
     .zh 1.28 and .mark 1.05) it was losing the size contest and reading as a
     caption. Set in ink rather than the palest grey for the same reason. */
  .meta{{font-family:{mono};
         font-size:1.15em;letter-spacing:.06em;text-transform:uppercase;color:{fg}}}
  .mark{{font-family:{cond};font-weight:700;letter-spacing:.3em;font-size:1.05em}}
</style></head><body>
  <div class="frame"><img src="{img}" alt=""></div>
  <div class="label">
    <div class="en">{en}</div>
    {zh}
    <div class="foot"><span class="meta">{meta}</span><span class="mark">FLUXUS</span></div>
  </div>
</body></html>"""

LIGHT = dict(bg="#F2F1ED", fg="#1c1917", fg2="#57534E", fg3="#948F86",
             mat="#EDECE7", rule="#e7e5e4")
DARK = dict(bg="#12110f", fg="#f5f4f2", fg2="#8a8480", fg3="#6b6560",
            mat="#1c1a18", rule="#332e29")


def build_html(img: Path, en: str, zh: str, meta: str, ratio: str, dark: bool) -> str:
    w, h = SIZES[ratio]
    theme = DARK if dark else LIGHT
    base = round(w / 42)                      # 1080 → 26px 基准
    pad = 2.6
    if ratio == "16x9":                        # 横版：图左字右
        flex = "flex-direction:row;gap:2.4em;"
        framecss = "flex:0 0 52%;height:100%"
        labelcss = "flex:1;padding-top:0"
        base = round(w / 62)
        pad, padb = 2.6, 2.6
    else:
        flex = ""
        framecss = f"height:{30 if ratio == '4x5' else 22}em"
        labelcss = "padding-top:2.2em;flex:1"
        padb = 2.2
    return TEMPLATE.format(
        w=w, h=h, base=base, pad=pad, padb=padb, flex=flex,
        framecss=framecss, labelcss=labelcss,
        fontface=fontface_css(), sans=SANS_STACK, cond=COND_STACK, mono=MONO_STACK,
        img=html.escape(img.resolve().as_uri()),
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


def resolve_image(args) -> Path:
    if args.image:
        p = Path(args.image)
        return p if p.is_absolute() else (ROOT / p)
    if not args.code:
        raise SystemExit("要么给 --image,要么给 --code")
    hits = sorted((VISUALS / "selected").glob(f"{args.code.upper()}*"))
    hits = [h for h in hits if h.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
    if not hits:
        raise SystemExit(f"visuals/selected/ 里没有 {args.code} —— 先跑 apply_visual_picks.py")
    return hits[0]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", help="图片路径")
    ap.add_argument("--code", help="视觉代码,从 visuals/selected/ 取图,如 V01")
    ap.add_argument("--en", required=True, help="英文那句(主句)")
    ap.add_argument("--zh", default="", help="中文那句(可省)")
    ap.add_argument("--meta", default="", help="展签那一行 —— 当天的测量")
    ap.add_argument("--ratio", default="4x5", choices=list(SIZES))
    ap.add_argument("--dark", action="store_true", help="深色版")
    ap.add_argument("--out", help="输出路径")
    args = ap.parse_args()

    img = resolve_image(args)
    if not img.exists():
        raise SystemExit(f"图不存在：{img}")

    meta = args.meta or f"{(args.code or img.stem).upper()} · {date.today():%Y.%m.%d}"  # localtime-ok: poster caption
    name = args.out or (OUTDIR / f"{date.today():%Y%m%d}_{(args.code or img.stem).upper()}"  # localtime-ok: output filename
                        f"{'_dark' if args.dark else ''}.png")
    out = Path(name)
    if not out.is_absolute():
        out = ROOT / out

    render(build_html(img, args.en, args.zh, meta, args.ratio, args.dark), out, args.ratio)
    w, h = SIZES[args.ratio]
    print(f"{(out.relative_to(ROOT) if out.is_relative_to(ROOT) else out)}  ({w}×{h} @2x)")


if __name__ == "__main__":
    main()
