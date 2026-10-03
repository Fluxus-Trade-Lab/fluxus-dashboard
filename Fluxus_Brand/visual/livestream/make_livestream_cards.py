#!/usr/bin/env python3
"""会员直播画面卡生成器（T-1002-78）—— 片头 / 6 段落卡 / 片尾 / 下三分之一名牌条，OBS 用。

版式继承海报系统（`Fluxus_Poster_System.md`）与课程发布视觉母版（`visual/course_launch/`）：
暖石底 #F2F1ED、墨色 #1c1917、IBM Plex 三族同源、无渐变无阴影无辉光。
场次号与标题是参数，每场直播改两个 flag 就能重出全套；中英各一套文字参数，默认先出中文。

    python3 Fluxus_Brand/visual/livestream/make_livestream_cards.py \\
        --episode 1 --title "先看环境" --title-en "Read the Environment First" \\
        --date "2026-10-03"

只出某一类卡（比如改完名牌条文字只想重出那一张）：
    python3 .../make_livestream_cards.py --episode 1 --title "先看环境" --only lowerthird
"""

from __future__ import annotations

import argparse
import base64
import html
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUTROOT = ROOT / "Fluxus_Brand" / "visual" / "livestream" / "out"

FONTDIR = ROOT / "Fluxus_Brand" / "visual" / "explorations" / "2026-08-08" / "fonts"
FACES = [  # (CSS family, weight, 文件名) —— 同 make_data_card.py / make_poster.py
    ("Plex", 400, "IBMPlexSans-Regular.woff2"),
    ("Plex", 600, "IBMPlexSans-SemiBold.woff2"),
    ("PlexCond", 700, "IBMPlexSansCondensed-Bold.woff2"),
    ("PlexMono", 400, "IBMPlexMono-Regular.woff2"),
]
SANS_STACK = 'Plex,"PingFang SC",-apple-system,"Helvetica Neue",sans-serif'
COND_STACK = 'PlexCond,Plex,"PingFang SC",-apple-system,sans-serif'
MONO_STACK = 'PlexMono,ui-monospace,"SF Mono",Menlo,monospace'

STONE = "#F2F1ED"
INK = "#1c1917"
INK2 = "#57534E"
MEASURE = "#948F86"
RULE = "#e7e5e4"

W, H = 1920, 1080  # OBS 画布标准 16:9

# 固定六段（Andy 10-02 定，策划页 UCsft7bm…）；中英文案各一份，--lang 切换卡上展示哪一套
SEGMENTS = [
    (1, "读盘", "Reading the Tape"),
    (2, "本章一张图", "This Chapter, One Chart"),
    (3, "三个案例", "Three Cases"),
    (4, "Dashboard 实操", "Dashboard Walkthrough"),
    (5, "会员问答", "Member Q&A"),
    (6, "作业与下一场", "Homework & Next Session"),
]
CIRCLED = ["①", "②", "③", "④", "⑤", "⑥"]


def _font_css() -> str:
    out = []
    for family, weight, fname in FACES:
        path = FONTDIR / fname
        if not path.exists():
            raise SystemExit(
                f"缺字体：{path}\n"
                "直播画面卡不许回退到替代字体（同海报系统规矩）。补齐 IBM Plex woff2 再跑。")
        b64 = base64.b64encode(path.read_bytes()).decode("ascii")
        out.append(
            f"@font-face{{font-family:{family};font-weight:{weight};"
            f"font-display:block;src:url(data:font/woff2;base64,{b64}) "
            'format("woff2")}')
    return "\n  ".join(out)


def _render(page_html: str, out: Path, w: int, h: int, transparent: bool = False) -> None:
    if not Path(CHROME).exists():
        raise SystemExit(f"找不到 Chrome：{CHROME}")
    out.parent.mkdir(parents=True, exist_ok=True)
    tmpdir = ROOT / "visuals"
    tmpdir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", suffix=".html", dir=str(tmpdir), encoding="utf-8", delete=False
    ) as fh:
        fh.write(page_html)
        tmp = Path(fh.name)
    try:
        cmd = [
            CHROME, "--headless", "--disable-gpu", "--hide-scrollbars",
            "--allow-file-access-from-files", "--force-device-scale-factor=1",
        ]
        if transparent:
            cmd.append("--default-background-color=00000000")
        cmd += [f"--screenshot={out}", f"--window-size={w},{h}", str(tmp)]
        subprocess.run(cmd, check=True, capture_output=True, timeout=90)
    finally:
        tmp.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# 片头卡 / 片尾卡：共用一个骨架（大标题 + 场次号 + 测量行 + FLUXUS 标记）
# ---------------------------------------------------------------------------

TITLE_TEMPLATE = """<!doctype html><html><head><meta charset="utf-8"><style>
  {fontface}
  *{{box-sizing:border-box;margin:0}}
  html,body{{width:{w}px;height:{h}px;overflow:hidden}}
  body{{background:{bg};color:{fg};font-family:{sans};padding:0}}
  .frame{{position:relative;width:100%;height:100%;padding:88px 110px;display:flex;
          flex-direction:column}}
  .kicker{{font-family:{mono};font-size:28px;letter-spacing:.14em;text-transform:uppercase;
           color:{measure}}}
  .episode{{font-family:{cond};font-weight:700;font-size:220px;line-height:.86;
            letter-spacing:-.02em;color:{fg};margin-top:40px}}
  .title-zh{{font-size:72px;font-weight:600;letter-spacing:-.01em;margin-top:28px;max-width:1500px}}
  .title-en{{font-size:34px;font-weight:400;color:{fg2};margin-top:18px;max-width:1500px}}
  .rule{{height:1px;background:{rule};margin-top:auto}}
  .foot{{display:flex;justify-content:space-between;align-items:baseline;padding-top:34px}}
  .meta{{font-family:{mono};font-size:26px;letter-spacing:.06em;text-transform:uppercase;
         color:{measure}}}
  .mark{{font-family:{cond};font-weight:700;letter-spacing:.3em;font-size:30px}}
</style></head><body><div class="frame">
  <div class="kicker">{kicker}</div>
  <div class="episode">{episode}</div>
  <div class="title-zh">{title_zh}</div>
  {title_en_html}
  <div class="rule"></div>
  <div class="foot"><span class="meta">{meta}</span><span class="mark">FLUXUS</span></div>
</div></body></html>"""


def build_title_or_closing(
    kind: str, episode: int, title_zh: str, title_en: str, date_str: str, next_date_str: str
) -> str:
    if kind == "title":
        kicker = "FLUXUS 会员直播"
        meta = f"EP {episode:02d} · {date_str} · Discord 舞台" if date_str else f"EP {episode:02d} · Discord 舞台"
    else:  # closing
        kicker = "本场到此结束"
        meta = (f"回放在会员区 · 下一场 {next_date_str}"
                if next_date_str else "回放在会员区 · 下一场见")
    episode_str = f"{episode:02d}"
    title_en_html = (
        f'<div class="title-en">{html.escape(title_en)}</div>' if title_en else ""
    )
    return TITLE_TEMPLATE.format(
        w=W, h=H, fontface=_font_css(), sans=SANS_STACK, cond=COND_STACK, mono=MONO_STACK,
        bg=STONE, fg=INK, fg2=INK2, measure=MEASURE, rule=RULE,
        kicker=html.escape(kicker), episode=html.escape(episode_str),
        title_zh=html.escape(title_zh), title_en_html=title_en_html,
        meta=html.escape(meta),
    )


# ---------------------------------------------------------------------------
# 段落卡：大序号 + 中英段名 + 进度（也是剪辑切点，文件名按顺序编号）
# ---------------------------------------------------------------------------

SEGMENT_TEMPLATE = """<!doctype html><html><head><meta charset="utf-8"><style>
  {fontface}
  *{{box-sizing:border-box;margin:0}}
  html,body{{width:{w}px;height:{h}px;overflow:hidden}}
  body{{background:{bg};color:{fg};font-family:{sans}}}
  .frame{{position:relative;width:100%;height:100%;padding:88px 110px;display:flex;
          flex-direction:column}}
  .kicker{{font-family:{mono};font-size:26px;letter-spacing:.14em;text-transform:uppercase;
           color:{measure}}}
  .row{{display:flex;align-items:baseline;gap:40px;margin-top:64px}}
  .circled{{font-size:130px;line-height:1}}
  .progress{{font-family:{cond};font-weight:700;font-size:56px;color:{measure}}}
  .name-zh{{font-size:108px;font-weight:600;letter-spacing:-.01em;margin-top:44px}}
  .name-en{{font-size:40px;font-weight:400;color:{fg2};margin-top:20px}}
  .rule{{height:1px;background:{rule};margin-top:auto}}
  .foot{{display:flex;justify-content:space-between;align-items:baseline;padding-top:34px}}
  .meta{{font-family:{mono};font-size:26px;letter-spacing:.06em;text-transform:uppercase;
         color:{measure}}}
  .mark{{font-family:{cond};font-weight:700;letter-spacing:.3em;font-size:30px}}
</style></head><body><div class="frame">
  <div class="kicker">{kicker}</div>
  <div class="row"><span class="circled">{circled}</span><span class="progress">{idx:02d} / 06</span></div>
  <div class="name-zh">{name_zh}</div>
  <div class="name-en">{name_en}</div>
  <div class="rule"></div>
  <div class="foot"><span class="meta">{meta}</span><span class="mark">FLUXUS</span></div>
</div></body></html>"""


def build_segment(episode: int, idx: int, name_zh: str, name_en: str) -> str:
    return SEGMENT_TEMPLATE.format(
        w=W, h=H, fontface=_font_css(), sans=SANS_STACK, cond=COND_STACK, mono=MONO_STACK,
        bg=STONE, fg=INK, fg2=INK2, measure=MEASURE, rule=RULE,
        kicker=html.escape(f"FLUXUS 会员直播 · EP {episode:02d}"),
        circled=CIRCLED[idx - 1], idx=idx,
        name_zh=html.escape(name_zh), name_en=html.escape(name_en),
        meta="",  # 观众看得见的卡上不印内部说明（OPS 10-03 复核）
    )


# ---------------------------------------------------------------------------
# 下三分之一名牌条：透明底，OBS 叠加在画面下方；只占画布底部一条，不是整屏
# ---------------------------------------------------------------------------

BAR_H = 180
BAR_W = 820  # 名牌条实际宽度；画布仍出 1920 全宽，右侧留透明，OBS 里按需裁剪/缩放

LOWERTHIRD_TEMPLATE = """<!doctype html><html><head><meta charset="utf-8"><style>
  {fontface}
  *{{box-sizing:border-box;margin:0}}
  html,body{{width:{w}px;height:{h}px;overflow:hidden;background:transparent}}
  .bar{{position:absolute;left:0;bottom:0;width:{barw}px;height:112px;
        background:rgba(28,25,23,.92);display:flex;align-items:center;
        padding:0 44px;font-family:{sans}}}
  .rule{{width:6px;height:56px;background:{stone};margin-right:24px}}
  .name{{color:{stone};font-size:38px;font-weight:600;letter-spacing:-.01em}}
  .sub{{color:#b9b3ab;font-size:22px;font-weight:400;margin-left:18px;
        font-family:{mono};letter-spacing:.04em;text-transform:uppercase}}
</style></head><body>
  <div class="bar">
    <div class="rule"></div>
    <div class="name">{name}</div>
    <div class="sub">{sub}</div>
  </div>
</body></html>"""


def build_lowerthird(name: str, sub: str) -> str:
    return LOWERTHIRD_TEMPLATE.format(
        w=W, h=BAR_H, barw=BAR_W, fontface=_font_css(), sans=SANS_STACK, mono=MONO_STACK,
        stone=STONE, name=html.escape(name), sub=html.escape(sub),
    )


# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", type=int, required=True, help="场次号，如 1")
    ap.add_argument("--title", required=True, help="本场标题（中文），如 “先看环境”")
    ap.add_argument("--title-en", default="", help="本场标题（英文），可省")
    ap.add_argument("--date", default="", help="本场展示日期，如 2026-10-03，可省")
    ap.add_argument("--next-date", default="", help="片尾卡的下一场日期，可省（省则写“下一场见”）")
    ap.add_argument("--name", default="Andy", help="名牌条主名字")
    ap.add_argument("--name-sub", default="FLUXUS CAPITAL", help="名牌条副标（等宽大写）")
    ap.add_argument(
        "--only", choices=["title", "segments", "closing", "lowerthird"],
        help="只出某一类卡，省略＝全出",
    )
    ap.add_argument("--outdir", help="输出目录，默认 out/ep<NN>/")
    args = ap.parse_args()

    outdir = Path(args.outdir) if args.outdir else OUTROOT / f"ep{args.episode:02d}"
    outdir.mkdir(parents=True, exist_ok=True)
    made: list[Path] = []

    if args.only in (None, "title"):
        page = build_title_or_closing(
            "title", args.episode, args.title, args.title_en, args.date, args.next_date)
        out = outdir / "00_title.png"
        _render(page, out, W, H)
        made.append(out)

    if args.only in (None, "segments"):
        for idx, name_zh, name_en in SEGMENTS:
            page = build_segment(args.episode, idx, name_zh, name_en)
            out = outdir / f"{idx:02d}_segment_{idx}.png"
            _render(page, out, W, H)
            made.append(out)

    if args.only in (None, "closing"):
        page = build_title_or_closing(
            "closing", args.episode, args.title, args.title_en, args.date, args.next_date)
        out = outdir / "99_closing.png"
        _render(page, out, W, H)
        made.append(out)

    if args.only in (None, "lowerthird"):
        page = build_lowerthird(args.name, args.name_sub)
        out = outdir / "lowerthird.png"
        _render(page, out, W, BAR_H, transparent=True)
        made.append(out)

    for p in made:
        print(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p)


if __name__ == "__main__":
    main()
