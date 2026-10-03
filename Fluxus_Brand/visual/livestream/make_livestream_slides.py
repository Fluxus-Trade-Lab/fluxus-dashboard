#!/usr/bin/env python3
"""会员直播 · 幻灯片（Keynote 式）：段落卡后面接细节页，每页都有一句总结和「这一页的结论」。

Andy 2026-10-03：「每一张卡片会是类似于KEYnoteSlide……KeYTakeaway要有summary也要有。每张卡片的要点有哪些。
这些内容写上去，就是会员可以跟着去做的事情」「可能需要更多……每一张后面还有更多的细节……案例A里面的KYTakeaway在哪里」

⚠️ 幻灯片内容是付费课程材料：内容 JSON、引用的图和渲染出的 PNG/PDF 一律放课程私有仓
（SwingMasterclass `_live/liveNN/slides/`），永不进 AI-Trading-System（PUBLIC）。本脚本只有版式，可以放公开仓。

视觉照 make_livestream_cards.py（同字体、同配色、同渲染）。

页面类型（JSON `slides` 数组，按顺序）：
  title    : summary + agenda
  section  : 段落卡 = idx + summary + points + do（跟着做）
  questions: 问题清单 = title + rows[{q,look,answer}] + takeaway
  image    : 细节页 = title + img（左）+ points（右）+ takeaway（底部结论条）
  closing  : summary + points + do
用法：python3 make_livestream_slides.py --content <ep.json> --outdir <dir> [--pdf <deck.pdf>]
图片路径相对 content JSON 所在目录。
"""
import argparse, html, json, os, sys
from pathlib import Path

# 版式常量与渲染函数来自同目录的 make_livestream_cards.py；脚本被拷到别处时用 FLUXUS_CARDS_DIR 指回去
CARDS_DIR = Path(os.environ.get('FLUXUS_CARDS_DIR', Path(__file__).resolve().parent))
sys.path.insert(0, str(CARDS_DIR))
import make_livestream_cards as C  # noqa: E402

E = html.escape

CSS = """
  {fontface}
  *{{box-sizing:border-box;margin:0;padding:0}}
  html,body{{width:{w}px;height:{h}px;overflow:hidden}}
  body{{background:{bg};color:{fg};font-family:{sans}}}
  .frame{{width:100%;height:100%;padding:64px 96px 48px;display:flex;flex-direction:column}}
  .kicker{{font-family:{mono};font-size:22px;letter-spacing:.14em;text-transform:uppercase;color:{measure}}}
  .head{{display:flex;align-items:baseline;gap:26px;margin-top:24px}}
  .circled{{font-size:76px;line-height:1}}
  .ep{{font-family:{cond};font-weight:700;font-size:92px;line-height:.9}}
  .h1{{font-size:68px;font-weight:600;letter-spacing:-.01em}}
  .h2{{font-size:56px;font-weight:600;letter-spacing:-.01em}}
  .prog{{font-family:{cond};font-weight:700;font-size:34px;color:{measure};margin-left:auto}}
  .sum{{font-size:38px;font-weight:600;margin-top:22px;padding:18px 26px;background:#FFFFFF;border-left:8px solid {fg}}}
  .cols{{display:grid;grid-template-columns:1.25fr 1fr;gap:56px;margin-top:34px;flex:1;min-height:0}}
  .lab{{font-family:{mono};font-size:21px;letter-spacing:.14em;color:{measure};text-transform:uppercase;margin-bottom:12px}}
  ul,ol{{list-style:none}}
  .pts li{{font-size:31px;line-height:1.38;padding:9px 0 9px 28px;position:relative;border-top:1px solid {rule}}}
  .pts li:first-child{{border-top:0}}
  .pts li::before{{content:"";position:absolute;left:0;top:24px;width:11px;height:11px;background:{fg}}}
  .do{{counter-reset:n}}
  .do li{{font-size:31px;line-height:1.38;padding:11px 0 11px 60px;position:relative;counter-increment:n}}
  .do li::before{{content:counter(n);position:absolute;left:0;top:9px;width:42px;height:42px;border-radius:50%;background:{fg};
       color:{bg};font-family:{cond};font-weight:700;font-size:26px;display:flex;align-items:center;justify-content:center}}
  .box{{background:#FFFFFF;padding:22px 28px;border:1px solid {rule}}}
  .agenda li{{font-size:34px;line-height:1.5;border-top:1px solid {rule};padding:8px 0}}
  .agenda li:first-child{{border-top:0}}
  .img{{display:grid;grid-template-columns:1.62fr 1fr;gap:40px;margin-top:22px;flex:1;min-height:0}}
  .img .pic{{height:585px}}
  .img img{{width:100%;height:100%;object-fit:contain;object-position:left top}}
  .img .pts li{{font-size:27px;padding:7px 0 7px 26px}}
  .img .pts li::before{{top:20px}}
  .qs{{display:grid;grid-template-columns:260px 1fr 1fr;margin-top:26px;border-top:2px solid {fg}}}
  .qs div{{padding:13px 18px 13px 0;border-bottom:1px solid {rule};font-size:28px;line-height:1.35}}
  .qs .qh{{font-family:{mono};font-size:20px;letter-spacing:.14em;color:{measure};text-transform:uppercase}}
  .qs .qn{{font-weight:700;font-size:34px}}
  .take{{margin-top:20px;padding:16px 24px;background:{fg};color:{bg};font-size:31px;font-weight:600;line-height:1.4}}
  .take b{{font-family:{mono};font-size:20px;letter-spacing:.14em;font-weight:400;opacity:.75;display:block;margin-bottom:4px}}
  .foot{{display:flex;justify-content:space-between;align-items:baseline;padding-top:18px;border-top:1px solid {rule};margin-top:18px}}
  .meta{{font-family:{mono};font-size:20px;letter-spacing:.06em;color:{measure}}}
  .mark{{font-family:{cond};font-weight:700;letter-spacing:.3em;font-size:26px}}
"""


def page(body, meta=""):
    css = CSS.format(fontface=C._font_css(), w=C.W, h=C.H, bg=C.STONE, fg=C.INK, sans=C.SANS_STACK,
                     cond=C.COND_STACK, mono=C.MONO_STACK, measure=C.MEASURE, rule=C.RULE)
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body><div class="frame">'
            f'{body}<div class="foot"><span class="meta">{E(meta)}</span><span class="mark">FLUXUS</span></div>'
            '</div></body></html>')


def ul(items, cls='pts'):
    return f'<ul class="{cls}">' + ''.join(f'<li>{E(i)}</li>' for i in items) + '</ul>'


def ol(items):
    return '<ol class="do">' + ''.join(f'<li>{E(i)}</li>' for i in items) + '</ol>'


def render(D, base, outdir):
    ep = int(D['episode']); kick = f'FLUXUS 会员直播 · EP {ep:02d}'
    files = []
    sec = 0
    for n, s in enumerate(D['slides']):
        t = s['type']
        if t == 'title':
            body = (f'<div class="kicker">{E(kick)} · {E(D.get("date",""))}</div>'
                    f'<div class="head"><span class="ep">{ep:02d}</span><span class="h1">{E(D["title"])}</span></div>'
                    f'<div class="sum">{E(s["summary"])}</div>'
                    f'<div class="cols"><div><div class="lab">今晚六段</div>{ul(s["agenda"], "agenda")}</div><div></div></div>')
            meta = f'EP {ep:02d} · Discord 舞台'
        elif t == 'section':
            sec = int(s['idx']); name = C.SEGMENTS[sec - 1][1]
            body = (f'<div class="kicker">{E(kick)}</div>'
                    f'<div class="head"><span class="circled">{C.CIRCLED[sec-1]}</span><span class="h1">{E(name)}</span>'
                    f'<span class="prog">{sec:02d} / 06</span></div>'
                    f'<div class="sum">{E(s["summary"])}</div>'
                    f'<div class="cols"><div><div class="lab">要点</div>{ul(s["points"])}</div>'
                    f'<div class="box"><div class="lab">跟着做</div>{ol(s["do"])}</div></div>')
            meta = ''
        elif t == 'image':
            img = (base / s['img']).resolve()
            body = (f'<div class="kicker">{E(kick)} · {C.CIRCLED[sec-1]} {E(C.SEGMENTS[sec-1][1])}</div>'
                    f'<div class="head"><span class="h2">{E(s["title"])}</span></div>'
                    f'<div class="img"><div class="pic"><img src="file://{E(str(img))}"></div>'
                    f'<div><div class="lab">{E(s.get("label","看什么"))}</div>{ul(s["points"])}</div></div>'
                    f'<div class="take"><b>这一页的结论</b>{E(s["takeaway"])}</div>')
            meta = s.get('source', '')
        elif t == 'questions':
            rows = ''.join(f'<div class="qn">{E(q["q"])}</div><div>{E(q["look"])}</div><div>{E(q["answer"])}</div>'
                           for q in s['rows'])
            body = (f'<div class="kicker">{E(kick)} · {C.CIRCLED[sec-1]} {E(C.SEGMENTS[sec-1][1])}</div>'
                    f'<div class="head"><span class="h2">{E(s["title"])}</span></div>'
                    f'<div class="qs"><div class="qh">问什么</div><div class="qh">看图上哪里</div><div class="qh">答案长什么样</div>{rows}</div>'
                    f'<div class="take"><b>这一页的结论</b>{E(s["takeaway"])}</div>')
            meta = s.get('source', '')
        elif t == 'closing':
            body = (f'<div class="kicker">本场到此结束 · EP {ep:02d}</div>'
                    f'<div class="head"><span class="ep">{ep:02d}</span><span class="h1">{E(D["title"])}</span></div>'
                    f'<div class="sum">{E(s["summary"])}</div>'
                    f'<div class="cols"><div><div class="lab">记住</div>{ul(s["points"])}</div>'
                    f'<div class="box"><div class="lab">这一周</div>{ol(s["do"])}</div></div>')
            meta = '回放在会员区 · 下一场见'
        else:
            raise SystemExit(f'unknown slide type {t}')
        name = f'{n+1:02d}_{t}.png'
        C._render(page(body, meta), outdir / name, C.W, C.H)
        files.append(outdir / name)
        print(name)
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--content', required=True)
    ap.add_argument('--outdir', required=True)
    ap.add_argument('--pdf')
    a = ap.parse_args()
    cp = Path(a.content).resolve()
    D = json.load(open(cp, encoding='utf-8'))
    out = Path(a.outdir); out.mkdir(parents=True, exist_ok=True)
    files = render(D, cp.parent, out)
    if a.pdf:
        from PIL import Image
        ims = [Image.open(f).convert('RGB') for f in files]
        ims[0].save(a.pdf, save_all=True, append_images=ims[1:], resolution=144)
        print('pdf', a.pdf, len(ims), 'pages')


if __name__ == '__main__':
    main()
