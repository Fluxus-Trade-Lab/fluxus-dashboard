import json, csv, html, io, tarfile, subprocess
from datetime import datetime, timedelta
from collections import defaultdict
SP="/private/tmp/claude-501/-Users-taolezhu-Documents-AI-Trading-System-Fluxus-Marketing-Visual-Design/ee3710aa-d552-414c-9357-4584bfc6459a/scratchpad"
ROOT="/Users/taolezhu/Documents/AI-Trading-System"
D="2026-09-04"
e=html.escape

# ---------- data ----------
lines=open(f"{SP}/drop0904.txt").read().strip().split("\n")
DROP_H=float(lines[0]); DROP=lines[1]
cond=[h for h in json.load(open(f"{ROOT}/data/output/breadth.json"))["conditions"]["history"] if h["date"]<=D]
verd=json.load(open(f"{ROOT}/data/output/breadth_replay.json"))["verdicts"][D]
arch=[r for r in csv.DictReader(open(f"{ROOT}/data/history/groups_archive.csv")) if r["date"]==D]
def fl(x):
    try: return float(x)
    except: return None
bykind=defaultdict(list)
for r in arch:
    if fl(r["perf_1d"]) is not None and fl(r["perf_1w"]) is not None: bykind[r["kind"]].append(r)
def tb(kind,col,n=3):
    s=sorted(bykind[kind],key=lambda r:fl(r[col]),reverse=True)
    return s[:n], s[-n:]

# ---------- formatting ----------
def pct(x,dp=2):
    v=x*100; s=f"{v:+.{dp}f}%"; return s.replace("-","−")
def signed(v,unit):
    if v is None: return "—"
    if unit in ("names","warnings"): s=f"{v:+.0f}"
    else: s=f"{v:+.2f}"
    return s.replace("-","−")
SIDE={"bull":("for","Counts for"),"bear":("against","Counts against"),"neutral":("near","Inside its line")}

# ---------- components ----------
def drop_svg(stroke,cls="",pad=6,label="Drop line, 21 sessions to Sep 4"):
    return (f'<svg class="drop {cls}" viewBox="{-pad} {-pad} {1000+2*pad} {DROP_H+2*pad}" role="img" aria-label="{e(label)}">'
            f'<path style="stroke-width:{stroke}" d="{DROP}"/></svg>')
REG=f'1m · drop <span class="m">#0904</span> · 2026-08-07 → 2026-09-04 · SPX · ∫ = 1.000 m'

def cond_chart():
    n=len(cond); W=940; H=200; base=190; top=18
    bw=W/n
    out=[f'<svg class="chart" viewBox="0 0 1000 222" role="img" aria-label="Market conditions score, last {n} sessions, 51 on Sep 4">']
    for v in (0,50,100):
        y=base-(v/100)*(base-top)
        dash=' class="grid mid"' if v==50 else ' class="grid"'
        out.append(f'<line{dash} x1="0" x2="{W}" y1="{y:.1f}" y2="{y:.1f}"/>')
        out.append(f'<text class="ax" x="{W+10}" y="{y+4:.1f}">{v}</text>')
    lastm=None; lastx=-999
    for i,h in enumerate(cond):
        x=i*bw; hh=(h["score"]/100)*(base-top); y=base-hh
        last=(i==n-1)
        out.append(f'<rect class="{"bar now" if last else "bar"}" x="{x+bw*0.14:.2f}" y="{y:.2f}" width="{max(bw*0.72,0.6):.2f}" height="{hh:.2f}"/>')
        m=h["date"][:7]
        if m!=lastm:
            mon=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][int(m[5:])-1]
            lab=f'{mon} {m[2:4]}' if mon=="Jan" or lastm is None else mon
            if x-lastx>=48:
                out.append(f'<text class="ax" x="{x:.1f}" y="216">{lab}</text>')
                lastx=x
            lastm=m
    lx=(n-1)*bw+bw/2; ly=base-(cond[-1]["score"]/100)*(base-top)
    out.append(f'<text class="nowlab" x="{lx-8:.1f}" y="{ly-8:.1f}" text-anchor="end">{cond[-1]["score"]}</text>')
    out.append('</svg>')
    return "".join(out)

def vote_strip(big=False):
    cells=[]
    for v in verd["vote_detail"]:
        if not v["measurable"]:
            glyph='<span class="g uncounted" aria-hidden="true"></span>'; num="—"; note="not counted"
        else:
            k=SIDE[v["side"]][0]
            glyph=f'<span class="g {k}" aria-hidden="true"></span>'; num=signed(v["margin"],v["unit"]); note=v["unit"]
        cells.append(f'<div class="vote">{glyph}<div class="vnum">{num}</div><div class="vunit">{e(note)}</div><div class="vlab">{e(v["label"])}</div></div>')
    return f'<div class="votes{" big" if big else ""}">{"".join(cells)}</div>'

LEGEND=('<div class="legend"><span><span class="g for"></span>counts for</span><span><span class="g against"></span>counts against</span>'
        '<span><span class="g near"></span>inside its line</span><span><span class="g uncounted"></span>not counted</span>'
        '<span class="lg-note">number = distance past each vote’s own line</span></div>')

def board_table(kind,title):
    t1,b1=tb(kind,"perf_1d"); t2,b2=tb(kind,"perf_1w")
    def rows(lst):
        return "".join(f'<tr><td class="gname">{e(r["group"])}</td><td class="st">{e(r["state"])}</td><td class="n {"up" if fl(r[col])>=0 else "dn"}">{pct(fl(r[col]))}</td></tr>' for r in lst)
    def block(lab,top,bot,col_):
        global col; col=col_
        return (f'<div class="lcol"><div class="lhead">{lab}</div><table class="lt">{rows(top)}'
                f'<tr class="gap"><td colspan="3"></td></tr>{rows(bot)}</table></div>')
    return (f'<div class="lpanel"><h4>{e(title)}</h4><div class="lgrid">'
            f'{block("1 day",t1,b1,"perf_1d")}{block("1 week",t2,b2,"perf_1w")}</div></div>')

def bars_panel(kind,title,col,lab):
    top,bot=tb(kind,col,4)
    items=top+bot
    mx=max(abs(fl(r[col])) for r in items)
    out=[f'<div class="bpanel"><h4>{e(title)} <span>{lab}</span></h4>']
    for i,r in enumerate(items):
        v=fl(r[col]); w=abs(v)/mx*50
        if i==len(top): out.append('<div class="bsep"></div>')
        side="pos" if v>=0 else "neg"
        out.append(f'<div class="brow"><div class="bname">{e(r["group"])}</div><div class="btrack"><span class="zero"></span>'
                   f'<span class="bfill {side}" style="{"left:50%" if v>=0 else f"right:50%"};width:{w:.2f}%"></span></div>'
                   f'<div class="bval {"up" if v>=0 else "dn"}">{pct(v,1)}</div></div>')
    out.append('</div>'); return "".join(out)

def weekly_lines():
    th=sorted(bykind["theme"],key=lambda r:fl(r["perf_1w"]),reverse=True)
    win=" · ".join(f'{e(r["group"])} {pct(fl(r["perf_1w"]),1)}' for r in th[:4])
    los=" · ".join(f'{e(r["group"])} {pct(fl(r["perf_1w"]),1)}' for r in reversed(th[-3:]))
    return win,los

IDX=[("QQQ","718.96","+0.18%","only major green two days running","weekly close above its DTL"),
     ("IWM","296.01","+0.28%","still below the 50-day (−0.34%)","needs a volume breakout"),
     ("SPY","770.19","−0.39%","gave back 1/3 of Thursday, 0.76× vol","7,800 = upside pivot"),
     ("RSP","219.00","−0.48%","average stock absent — 0.58× vol","below 21-day, at the 50"),
     ("DIA","534.08","−0.53%","held its 50-day retest this week","—"),
     ("MDY","—","+0.14%","low-volume rally into declining MAs","—")]
def idx_table():
    r="".join(f'<tr><td class="t">{a}</td><td class="n">{b}</td><td class="n {"up" if c.startswith("+") else "dn"}">{c}</td><td>{e(d)}</td><td>{e(x)}</td></tr>' for a,b,c,d,x in IDX)
    return f'<div class="scroll"><table class="idx"><thead><tr><th>Index</th><th class="rn">Last</th><th class="rn">Chg</th><th>Technical</th><th>Context</th></tr></thead><tbody>{r}</tbody></table></div>'

LED=[("Memory & Storage","+6.2%","deep dive below"),("Semis Large","+3.5%","INTC +4.5% RS97 · ARM +3.9% · ALAB +9.8% on 1.9× volume"),
     ("DELL","+15% wk","earnings stage-two breakout, 200% weekly volume"),("HPE","+15% wk","earnings + guide, 150% volume, cup-with-low-handle"),
     ("BE","+7.4%","+22.6% wk · RS97 · 1.34× vol"),("CRCL","","breakout, above 100"),("HOOD","+16.5% wk","breakout, reclaimed the 120 pivot"),
     ("IOT","+3.7%","3.9× volume, highest on the board — strong ER, watch next week"),("META","+1.0%","reclaimed the 50-day on volume + new AI model clears benchmarks")]
LAG=[("Cloud Software","−3.0%","wk −3.7% — SNOW −5.4% on 1.6× vol: the seller’s poster child"),("Cybersecurity","−0.9%","wk −5.1%"),
     ("Mag 7","−1.4%","QQQ’s green is the semis, not mags"),("TSLA","−5.9%","1.7× vol, RS16 — event-priced, buyers never stepped in"),
     ("Failures","","FROG failed breakout · NET non-confirmation reversal · SNOW gap-and-crap"),("Gold / Crypto","","GLD −0.8% · IBIT −2.4%, BTC held an inside day")]
def ledger(rows,cls):
    return '<div class="scroll"><table class="led">'+"".join(
        f'<tr><td class="t">{e(a)}</td><td class="n {cls}">{e(b)}</td><td>{e(c)}</td></tr>' for a,b,c in rows)+'</table></div>'

WATCH=["Memory’s first real-volume follow-through (SNDK / MU above their 50-day)","Does software keep getting sold — SNOW is the tell of that group",
       "Five-day ratio 0.90 → clears 1.0 or it’s still just repair (thrust needs 636; Friday 415)","Dips on AI leaders — the buy list",
       "TWLO through 250 on volume","Hike odds 60%+ — selling after Labor Day is the base case"]
RULES=["Uptrend intact — weekly close above the 21 EMA — but bifurcated: big-cap AI leads, breadth lags",
       "Good news is bad news: strong data = higher hike odds = pressure; CPI/PPI decide next week",
       "7,800 is the S&P upside pivot; the declining-tops line is the near-term cap",
       "Trade leaders with buyable closes (DELL, CRCL, HOOD) — volume + a strong close",
       "Memory + the semi snapback is the constructive AI tell; NVDA holding its 8/21 is the key",
       "Software is two-tone — buy the reclaims, avoid the fails",
       "Never serious trouble until the S&P breaks the 200-day — mid/small caps are the weak link"]
def olist(items,cls):
    return f'<ol class="{cls}">'+"".join(f'<li>{e(x)}</li>' for x in items)+'</ol>'

TITLE="No Follow-Through — Semis Take What Software Gives Up"
BYLINE="Semis & Memory Lead · September 4, 2026 (Friday)"
BIG=("After Thursday’s +1% across the board, no follow-through — still a sideways market, and Friday made it a split one: "
     "<b>SPY −0.39%, Dow −0.53%, equal-weight −0.48%</b> (0.58× volume, 21-day RS 5th percentile), while QQQ +0.18% and IWM +0.28% "
     "held green — because semis and mega-cap AI are stronger. Semis Large +3.5%, Broad +3.9%, <b>Memory &amp; Storage +6.2%</b> led everything; "
     "Cloud Software −3.0% paid for it (SNOW −5.4% on 1.6× volume). NFP +162K vs 55K expected — BLS official, July revised −23K → +21K — "
     "unemployment unchanged at 4.1%; rate-hike odds snapped back above 60%. Light volume everywhere, long weekend ahead: "
     "<b>trim some of Thursday’s longs, let the weekly closes do the talking.</b>")
FOUNDERS="AI trade rallies. MU/SNDK leads. Broad market not participating. Split tape environment. <b>Trade the strong theme, not the index market itself.</b>"
ONEBIG=("Nine of thirteen members carry RS ≥ 91 — a running theme, not a one-day trade. Volume showed up in only two: "
        "SNDK (+11.9%, 1.24×) and MU (+6.1%, 1.27×, pre-market gap bought at the open, small). Both reclaimed their 50-day this week; "
        "MU is coiling into a tight range with rising lows. <b>Two leaders, one sedan chair.</b>")
PORTNOTE=("Snapshot as of the 9/4 close. Return holds +123.4% with cash near 77% — defensive into the bifurcated tape, hot-jobs pressure, "
          "and the CPI/PPI week ahead. A tight book sits in the relative-strength names while breadth stays soft.")
WIN,LOS=weekly_lines()

def folio_a(n): return f'<div class="folio"><span>Fluxus Capital · Daily Market Recap</span><span>{n} / 4</span></div>'
def mast_a(): return '<div class="mast"><span class="brand">FLUXUS CAPITAL</span><span>Daily Market Recap · No. 0904</span></div><hr class="r ink">'

R_BOOK=ROOT

def load_book(D):
    """Open book as of D, computed from data/output/trades on origin/main.
    Drops files the latest export run did not rewrite: trade_postmortem.py names files by trade_id
    (which embeds entry_date) and never deletes, so an entry-date correction leaves the old file behind."""
    raw=subprocess.run(["git","-C",R_BOOK,"archive","origin/main","data/output/trades"],capture_output=True,check=True).stdout
    recs=[]
    with tarfile.open(fileobj=io.BytesIO(raw)) as tf:
        for m in tf.getmembers():
            if m.isfile() and m.name.endswith(".json"):
                j=json.loads(tf.extractfile(m).read())
                if isinstance(j,dict) and isinstance(j.get("trade"),dict): recs.append(j)
    ts=lambda j: datetime.fromisoformat(j["generated_at"])
    latest=max(ts(j) for j in recs)
    live=[j for j in recs if latest-ts(j)<=timedelta(minutes=10)]
    op=[j for j in live if j["trade"]["entry_date"]<=D and (not j["trade"]["closed"] or (j["trade"]["exit_date"] or "9999")>D)]
    cl=[j for j in live if j["trade"]["closed"] and (j["trade"]["exit_date"] or "9999")<=D]
    rows=[]
    for j in sorted(op,key=lambda j:(j["trade"]["entry_date"],j["trade"]["ticker"])):
        t=j["trade"]; px=[b for b in j["ohlc_window"] if b["date"]<=D]
        sign=1 if t["direction"]=="long" else -1
        rows.append((t["ticker"],t["entry_date"],sign*(px[-1]["close"]-t["entry_price"])/(t["r_dollars"]/t["original_qty"])))
    return rows,len({r[0] for r in rows}),len(cl),len(recs)-len(live)

def book_html(rows,names,closed,ret,cash):
    m=(f'<div class="metrics"><div><span>Return</span><b>{ret}</b><i class="src">tracker</i></div>'
       f'<div><span>Cash</span><b>{cash}</b><i class="src">tracker</i></div>'
       f'<div><span>Open names</span><b>{names}</b><i class="src">computed</i></div>'
       f'<div><span>Closed</span><b>{closed}</b><i class="src">computed</i></div></div>')
    tr="".join(f'<tr><td class="t">{tk}</td><td>{ed}</td><td class="n {"up" if r>=0 else "dn"}">{(f"{r:+.2f}R").replace("-","−")}</td></tr>' for tk,ed,r in rows)
    t=f'<div class="scroll"><table class="book"><thead><tr><th>Open position</th><th>Entry</th><th class="rn">Open R · close</th></tr></thead><tbody>{tr}</tbody></table></div>'
    n='<p class="schem">Open names, closed count and open R are computed from the trade records at the session close. Return and cash come from the tracker and are not in the data layer yet.</p>'
    return m,t,n

BK_ROWS,BK_NAMES,BK_CLOSED,BK_STALE=load_book(D)
assert (len(BK_ROWS),BK_NAMES,BK_CLOSED)==(4,3,373),(len(BK_ROWS),BK_NAMES,BK_CLOSED)
BK_M,BK_T,BK_N=book_html(BK_ROWS,BK_NAMES,BK_CLOSED,'+123.35%','76.86%')
# ---------------- VERSION A ----------------
A=f'''
<article class="sheet a">{mast_a()}
  {drop_svg(2.5,"thin")}
  <p class="reg">{REG}</p>
  <h2 class="hl-a">{e(TITLE)}</h2>
  <p class="byline">{e(BYLINE)}</p>
  <section class="sec"><h3>The Big Picture</h3><p class="prose">{BIG}</p></section>
  <section class="sec"><h3>Index Action · Friday</h3>{idx_table()}</section>
  {folio_a(1)}
</article>

<article class="sheet a">{mast_a()}
  <section class="sec first"><h3>Market State</h3>
    <div class="state-row"><span class="env">{e(verd["env"])}</span><span class="score">+{verd["score"]}<small> / {len(verd["vote_detail"])} votes</small></span></div>
    {vote_strip()}{LEGEND}
  </section>
  <section class="sec"><h3>Market Conditions <span class="h3n">51 / 100 · Neutral</span></h3>{cond_chart()}</section>
  <section class="sec note-blk"><h3>Founders Note</h3><p class="prose">{FOUNDERS}</p></section>
  <section class="sec"><h3>What Led</h3>{ledger(LED,"up")}</section>
  {folio_a(2)}
</article>

<article class="sheet a">{mast_a()}
  <section class="sec first"><h3>What Lagged / Failed</h3>{ledger(LAG,"dn")}</section>
  <section class="sec"><h3>Leaders and Laggards <span class="h3n">top 3 · bottom 3</span></h3>
    <div class="lwrap">{board_table("industry","Industries")}{board_table("theme","Themes")}</div></section>
  <section class="sec"><h3>The One Big Thing <span class="h3n">Memory &amp; Storage +6.2%</span></h3><p class="prose">{ONEBIG}</p></section>
  <section class="sec"><h3>Weekly · What This Week Locked In</h3>
    <dl class="kvl"><dt>Winners</dt><dd>{WIN}</dd><dt>Losers</dt><dd>{LOS}</dd>
    <dt>Assets</dt><dd>USO +9.4% wk (+19.4% mo, 90th RS pctl) · IBIT +3.0% wk (+24% mo)</dd><dt>Book</dt><dd>ETHA stays on; stops on the rest; evaluate next week</dd></dl></section>
  {folio_a(3)}
</article>

<article class="sheet a">{mast_a()}
  <section class="sec first"><h3>Tuesday Watch <span class="h3n">Monday closed — Labor Day</span></h3>{olist(WATCH,"ol-a")}</section>
  <section class="sec"><h3>The Rules</h3>{olist(RULES,"ol-a")}</section>
  <section class="sec"><h3>Portfolio Update</h3>
    {BK_M}{BK_T}
    <p class="prose">{PORTNOTE}</p>{BK_N}</section>
  {folio_a(4)}
</article>'''

# ---------------- VERSION B ----------------
def folio_b(n):
    return f'<div class="folio b"><span class="fl">{drop_svg(2,"fmark",4,"Drop mark")}</span><span>Fluxus Capital · Daily Market Recap</span><span>{n} / 4</span></div>'
B=f'''
<article class="sheet b cover">
  <div class="mast"><span class="brand">FLUXUS CAPITAL</span><span>Friday · September 4 · 2026</span></div>
  <div class="hero">{drop_svg(7,"hero")}</div>
  <p class="reg">{REG} — same length, different shapes</p>
  <hr class="r ink">
  <h2 class="hl-b">No Follow-Through.<br>Semis Take What Software Gives Up.</h2>
  <div class="cover-grid">
    <p class="prose lead">{BIG}</p>
    <aside class="board">
      <div class="brd-h">The Board</div>
      <div class="brd-row"><span>State</span><b>{e(verd["env"])} +{verd["score"]}</b></div>
      <div class="brd-row"><span>Conditions</span><b>51 / 100</b></div>
      <div class="brd-row"><span>QQQ</span><b class="up">+0.18%</b></div>
      <div class="brd-row"><span>SPY</span><b class="dn">−0.39%</b></div>
      <div class="brd-row"><span>RSP</span><b class="dn">−0.48%</b></div>
      <div class="brd-row"><span>Led</span><b>Memory &amp; Storage +6.2%</b></div>
      <div class="brd-row"><span>Paid</span><b>Cloud Software −3.0%</b></div>
    </aside>
  </div>
  {folio_b(1)}
</article>

<article class="sheet b">
  <div class="kicker">The Tape</div>
  <h3 class="hb">Index Action</h3>
  <div class="bigidx">{"".join(f'<div class="bi"><div class="bi-t">{a}</div><div class="bi-c {"up" if c.startswith("+") else "dn"}">{c}</div><div class="bi-l">{b}</div><div class="bi-d">{e(d)}</div></div>' for a,b,c,d,x in IDX)}</div>
  <div class="kicker sp">Market State</div>
  <div class="state-b"><span class="env-b">{e(verd["env"])}</span><span class="score-b">+{verd["score"]}<small>/ {len(verd["vote_detail"])}</small></span></div>
  {vote_strip(big=True)}{LEGEND}
  <div class="kicker sp">Market Conditions · <b>51 / 100 · Neutral</b></div>
  {cond_chart()}
  {folio_b(2)}
</article>

<article class="sheet b">
  <div class="split-b">
    <div><div class="kicker">What Led</div>{ledger(LED,"up")}</div>
    <div><div class="kicker">What Lagged / Failed</div>{ledger(LAG,"dn")}</div>
  </div>
  <div class="kicker sp">Rotation · Friday</div>
  <div class="bars2">{bars_panel("industry","Industries","perf_1d","1 day")}{bars_panel("theme","Themes","perf_1d","1 day")}</div>
  <div class="kicker sp">Rotation · The Week</div>
  <div class="bars2">{bars_panel("industry","Industries","perf_1w","1 week")}{bars_panel("theme","Themes","perf_1w","1 week")}</div>
  {folio_b(3)}
</article>

<article class="sheet b">
  <div class="pull"><div class="kicker">The One Big Thing</div>
    <h3 class="hb big">Memory &amp; Storage +6.2%</h3><p class="prose lead">{ONEBIG}</p></div>
  <div class="split-b">
    <div><div class="kicker">Founders Note</div><p class="prose">{FOUNDERS}</p>
      <div class="kicker sp">Tuesday Watch · Monday closed</div>{olist(WATCH,"ol-b")}</div>
    <div><div class="kicker">The Rules</div>{olist(RULES,"ol-b rules")}</div>
  </div>
  <div class="kicker sp">Book</div>
  {BK_M}{BK_T}
  <p class="prose">{PORTNOTE}</p>{BK_N}
  {folio_b(4)}
</article>'''

CSS=open(f"{SP}/recap_css.css").read() if False else None

CSS = """
:root{
  --paper:#F2F1ED; --sheet:#FBFAF7; --ink:#1A1917; --ink2:#4A463F; --rule:#D9D6CD; --soft:#E8E5DD;
  --muted:#8A857A; --accent:#D1600F; --up:#3F6B4A; --dn:#A8402F; --bar:#BDB8AC;
  --up-bar:#8FAE97; --dn-bar:#C98A7E;
  --sans:"IBM Plex Sans",-apple-system,"PingFang SC",sans-serif;
  --cond:"IBM Plex Sans Condensed","IBM Plex Sans",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
}
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
  --paper:#12110F; --sheet:#1A1917; --ink:#E9E7E2; --ink2:#B7B4AC; --rule:#35312B; --soft:#28251F;
  --muted:#8E8A80; --accent:#E8843C; --up:#7FB48C; --dn:#E0705C; --bar:#5A564D; --up-bar:#4F7A5B; --dn-bar:#8E4A3F;
}}
:root[data-theme="dark"]{
  --paper:#12110F; --sheet:#1A1917; --ink:#E9E7E2; --ink2:#B7B4AC; --rule:#35312B; --soft:#28251F;
  --muted:#8E8A80; --accent:#E8843C; --up:#7FB48C; --dn:#E0705C; --bar:#5A564D; --up-bar:#4F7A5B; --dn-bar:#8E4A3F;
}
*{box-sizing:border-box}
body{background:var(--paper);color:var(--ink);font-family:var(--sans);margin:0;padding:44px 20px 100px;line-height:1.6;-webkit-font-smoothing:antialiased}
.top{max-width:1060px;margin:0 auto 26px}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);margin:0}
.top h1{font-family:var(--cond);font-weight:700;font-size:clamp(30px,4.4vw,46px);line-height:1.04;margin:8px 0 10px;text-wrap:balance}
.top .lede{font-size:15.5px;color:var(--ink2);max-width:64ch;margin:0 0 10px}
.prov{font-family:var(--mono);font-size:11px;line-height:1.7;color:var(--muted);max-width:92ch;margin:0}
.prov b{color:var(--ink);font-weight:500}
.switch{display:flex;gap:0;margin:22px 0 0;border:1.5px solid var(--ink);width:max-content;max-width:100%}
.switch button{font:500 12px/1 var(--mono);letter-spacing:.14em;text-transform:uppercase;padding:11px 18px;border:0;background:transparent;color:var(--ink);cursor:pointer}
.switch button+button{border-left:1.5px solid var(--ink)}
.switch button[aria-pressed="true"]{background:var(--ink);color:var(--sheet)}
.switch button:focus-visible{outline:2px solid var(--accent);outline-offset:3px}

.sheet{background:var(--sheet);border:1px solid var(--rule);margin:0 auto 28px;position:relative}
.sheet.a{max-width:860px;padding:46px 52px 30px}
.sheet.b{max-width:1060px;padding:50px 60px 30px}
.mast{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;font-family:var(--mono);font-size:10.5px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted)}
.mast .brand{color:var(--ink);font-weight:600;letter-spacing:.26em}
hr.r{border:0;border-top:1px solid var(--rule);margin:12px 0 0}
hr.r.ink{border-top:1.5px solid var(--ink)}

.drop{display:block;width:100%;height:auto;overflow:visible}
.drop path{fill:none;stroke:var(--accent);stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}
.drop.thin{margin-top:18px;height:46px}
.drop.fmark{width:64px;height:14px}
.drop.fmark path{stroke:var(--muted)}
.reg{font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:9px 0 0}
.reg .m{color:var(--ink);font-weight:600}

.hl-a{font-family:var(--cond);font-weight:700;font-size:clamp(26px,3.6vw,36px);line-height:1.06;letter-spacing:-.01em;margin:22px 0 6px;text-wrap:balance}
.byline{font-family:var(--mono);font-size:11px;letter-spacing:.08em;color:var(--muted);margin:0}
.sec{margin-top:30px}
.sec.first{margin-top:24px}
.sec h3{font-family:var(--mono);font-size:11px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:var(--ink);border-top:1.5px solid var(--ink);padding-top:10px;margin:0 0 12px}
.h3n{color:var(--muted);font-weight:400;letter-spacing:.06em;text-transform:none;margin-left:8px}
.prose{font-size:14px;line-height:1.72;color:var(--ink2);max-width:70ch;margin:0}
.prose b{color:var(--ink);font-weight:600}
.scroll{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-family:var(--mono);font-variant-numeric:tabular-nums}
table.idx{font-size:12px}
table.idx th{text-align:left;font-weight:500;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);padding:0 14px 7px 0;border-bottom:1px solid var(--rule);white-space:nowrap}
table.idx th.rn{text-align:right}
table.idx td{padding:7px 14px 7px 0;border-bottom:1px solid var(--soft);color:var(--ink2);vertical-align:top}
td.t{color:var(--ink);font-weight:500;letter-spacing:.05em;white-space:nowrap}
td.n{text-align:right;white-space:nowrap;color:var(--ink)}
.up{color:var(--up)} .dn{color:var(--dn)}
td.n.up{color:var(--up)} td.n.dn{color:var(--dn)}
table.led{font-size:12px}
table.led td{padding:6px 14px 6px 0;border-bottom:1px solid var(--soft);color:var(--ink2);vertical-align:top}
table.led td.n{min-width:78px}

.state-row{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap;margin-bottom:14px}
.env{font-family:var(--cond);font-weight:700;font-size:40px;line-height:1;letter-spacing:-.01em}
.score{font-family:var(--cond);font-weight:700;font-size:26px}
.score small{font-family:var(--mono);font-weight:400;font-size:12px;color:var(--muted);letter-spacing:.06em;margin-left:4px}
.votes{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule)}
@media(max-width:760px){.votes{grid-template-columns:repeat(4,minmax(0,1fr))}}
@media(max-width:520px){.votes{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:380px){.votes{grid-template-columns:repeat(2,minmax(0,1fr))}}
.vote{background:var(--sheet);padding:10px 10px 11px;display:grid;gap:2px;align-content:start}
.g{display:inline-block;width:11px;height:11px;vertical-align:middle}
.g.for{background:var(--up)} .g.against{background:var(--dn)}
.g.near{border:1.5px solid var(--muted)} .g.uncounted{border:1.5px dashed var(--muted)}
.vnum{font-family:var(--mono);font-size:15px;color:var(--ink);font-variant-numeric:tabular-nums;margin-top:5px}
.vunit{font-family:var(--mono);font-size:9.5px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.vlab{font-size:11.5px;line-height:1.35;color:var(--ink2);margin-top:3px}
.votes.big .vnum{font-size:20px}
.legend{display:flex;flex-wrap:wrap;gap:8px 18px;font-family:var(--mono);font-size:10px;color:var(--muted);margin-top:10px;align-items:center}
.legend > span{display:inline-flex;align-items:center;gap:6px}
.lg-note{letter-spacing:.04em}

.chart{display:block;width:100%;height:auto;margin-top:4px}
.chart .bar{fill:var(--bar)} .chart .bar.now{fill:var(--ink)}
.chart .grid{stroke:var(--rule);stroke-width:1} .chart .grid.mid{stroke-dasharray:3 3}
.chart .ax{font-family:var(--mono);font-size:10px;fill:var(--muted)}
.chart .nowlab{font-family:var(--mono);font-size:13px;font-weight:600;fill:var(--ink)}

.lwrap{display:grid;grid-template-columns:1fr;gap:26px}
@media(min-width:720px){.lwrap{grid-template-columns:1fr 1fr}}
.lpanel h4{font-size:13px;font-weight:600;margin:0 0 8px}
.lgrid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.lhead{font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);padding-bottom:5px;border-bottom:1px solid var(--rule)}
table.lt{font-size:11.5px}
table.lt td{padding:5px 6px 5px 0;border-bottom:1px solid var(--soft);vertical-align:top}
table.lt td.gname{color:var(--ink);font-family:var(--sans);font-size:12px;line-height:1.3}
table.lt td.st{color:var(--muted);font-size:9.5px;letter-spacing:.04em;white-space:nowrap}
table.lt tr.gap td{border-bottom:1px dashed var(--rule);padding:3px 0}
dl.kvl{display:grid;grid-template-columns:auto 1fr;gap:6px 18px;margin:0}
dl.kvl dt{font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);padding-top:2px}
dl.kvl dd{margin:0;font-size:13.5px;color:var(--ink2)}

ol{margin:0;padding:0;list-style:none;counter-reset:n}
ol li{counter-increment:n;display:grid;grid-template-columns:30px 1fr;gap:6px;padding:8px 0;border-bottom:1px solid var(--soft);font-size:13.5px;color:var(--ink2)}
ol li::before{content:counter(n);font-family:var(--mono);font-size:11px;color:var(--muted);padding-top:2px}
ol.rules li{font-size:14.5px;color:var(--ink)}
.metrics{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule);margin-bottom:12px}
.metrics>div{background:var(--sheet);padding:12px 14px;display:grid;gap:2px}
.metrics span{font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.metrics b{font-family:var(--cond);font-weight:700;font-size:28px;line-height:1.05;font-variant-numeric:tabular-nums}
.tick{font-family:var(--mono);font-size:12px;letter-spacing:.06em;color:var(--ink2);margin:0 0 10px}
.folio{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;font-family:var(--mono);font-size:10px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);border-top:1px solid var(--rule);margin-top:34px;padding-top:10px}
.folio .fl{display:inline-flex}

/* ---- B ---- */
.hero{margin:30px 0 6px}
.hl-b{font-family:var(--cond);font-weight:700;font-size:clamp(36px,5.4vw,62px);line-height:1.0;letter-spacing:-.018em;margin:24px 0 22px;text-wrap:balance}
.cover-grid{display:grid;grid-template-columns:1fr;gap:30px}
@media(min-width:840px){.cover-grid{grid-template-columns:1.4fr .6fr;gap:44px}}
.prose.lead{font-size:15px;line-height:1.75}
.board{border-top:1.5px solid var(--ink);padding-top:8px}
.brd-h{font-family:var(--mono);font-size:10.5px;letter-spacing:.2em;text-transform:uppercase;font-weight:600;margin-bottom:4px}
.brd-row{display:flex;justify-content:space-between;gap:12px;border-bottom:1px solid var(--soft);padding:8px 0;font-family:var(--mono);font-size:12px;color:var(--muted)}
.brd-row b{color:var(--ink);font-weight:500;text-align:right}
.brd-row b.up{color:var(--up)} .brd-row b.dn{color:var(--dn)}
.kicker{font-family:var(--mono);font-size:11px;letter-spacing:.22em;text-transform:uppercase;color:var(--muted);margin-bottom:10px}
.kicker b{color:var(--ink);font-weight:500}
.kicker.sp{margin-top:42px;border-top:1.5px solid var(--ink);padding-top:12px}
.hb{font-family:var(--cond);font-weight:700;font-size:38px;line-height:1.02;letter-spacing:-.012em;margin:0 0 16px}
.hb.big{font-size:clamp(38px,5vw,54px)}
@media(max-width:900px){.bigidx{grid-template-columns:repeat(3,minmax(0,1fr)) !important}}
@media(max-width:520px){.bigidx{grid-template-columns:repeat(2,minmax(0,1fr)) !important}}
.bigidx{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule)}
.bi{background:var(--sheet);padding:14px 14px 15px;display:grid;gap:3px;align-content:start}
.bi-t{font-family:var(--mono);font-size:12px;letter-spacing:.12em;font-weight:500}
.bi-c{font-family:var(--cond);font-weight:700;font-size:34px;line-height:1;font-variant-numeric:tabular-nums}
.bi-l{font-family:var(--mono);font-size:11px;color:var(--muted);font-variant-numeric:tabular-nums}
.bi-d{font-size:12px;line-height:1.35;color:var(--ink2);margin-top:4px}
.state-b{display:flex;align-items:baseline;gap:16px;flex-wrap:wrap;margin-bottom:14px}
.env-b{font-family:var(--cond);font-weight:700;font-size:clamp(46px,7vw,72px);line-height:.95;letter-spacing:-.02em}
.score-b{font-family:var(--cond);font-weight:700;font-size:40px}
.score-b small{font-family:var(--mono);font-weight:400;font-size:15px;color:var(--muted);margin-left:4px}
.split-b{display:grid;grid-template-columns:1fr;gap:34px}
@media(min-width:840px){.split-b{grid-template-columns:1fr 1fr;gap:48px}}
.bars2{display:grid;grid-template-columns:1fr;gap:30px}
@media(min-width:760px){.bars2{grid-template-columns:1fr 1fr;gap:44px}}
.bpanel h4{font-size:13px;font-weight:600;margin:0 0 8px;display:flex;justify-content:space-between;gap:10px}
.bpanel h4 span{font-family:var(--mono);font-weight:400;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.brow{display:grid;grid-template-columns:minmax(0,1.25fr) minmax(0,1fr) 58px;gap:10px;align-items:center;padding:5px 0;border-bottom:1px solid var(--soft)}
.bname{font-size:12.5px;line-height:1.3;color:var(--ink2)}
.btrack{position:relative;height:10px}
.btrack .zero{position:absolute;left:50%;top:-4px;width:1px;height:18px;background:var(--rule)}
.bfill{position:absolute;top:0;height:10px}
.bfill.pos{background:var(--up-bar)} .bfill.neg{background:var(--dn-bar)}
.bval{font-family:var(--mono);font-size:12px;text-align:right;font-variant-numeric:tabular-nums}
.bsep{border-top:1px dashed var(--rule);margin:4px 0}
.pull{border-bottom:1.5px solid var(--ink);padding-bottom:26px;margin-bottom:6px}
@media(max-width:560px){.sheet.a,.sheet.b{padding:30px 22px 22px}.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}}
.metrics i.src{font-style:normal;font-family:var(--mono);font-size:9px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
table.book{font-size:12px;margin:4px 0 12px;max-width:480px}
table.book th{text-align:left;font-weight:500;font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);padding:0 16px 6px 0;border-bottom:1px solid var(--rule)}
table.book th.rn,table.book td.n{text-align:right}
table.book td{padding:6px 16px 6px 0;border-bottom:1px solid var(--soft);color:var(--ink2)}
"""

JS = """
(function(){
  var btns=document.querySelectorAll('[data-ver]');
  function show(v){
    document.getElementById('verA').hidden = v!=='A';
    document.getElementById('verB').hidden = v!=='B';
    btns.forEach(function(x){ x.setAttribute('aria-pressed', x.getAttribute('data-ver')===v ? 'true':'false'); });
    try{ localStorage.setItem('recapVer', v); }catch(e){}
  }
  btns.forEach(function(x){ x.addEventListener('click', function(){ show(x.getAttribute('data-ver')); }); });
  var s='A'; try{ s = localStorage.getItem('recapVer') || 'A'; }catch(e){}
  show(s==='B'?'B':'A');
})();
"""

FONTS='<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Sans+Condensed:wght@600;700&display=swap">'

TOP=f'''<header class="top">
  <p class="eyebrow">Fluxus Capital · Daily Market Recap · 9/4 期 · A / B 细节</p>
  <h1>A 登记体 · B 掉落体</h1>
  <p class="lede">同一期、同一份数据，两种外观，各四页全文。所有表格、票面和图都由数据文件生成，不再贴截图。</p>
  <p class="prov">数据 · <b>groups_archive.csv</b> 行业 120 / 主题 56（9/4）· <b>breadth.json</b> Conditions 序列（9/4 = 51，与已发布一致）· <b>breadth_replay.json</b> 12 票明细（09-10 重算）· SPX 收盘（掉落线，弧长 1.000 m）。
  持仓 · <b>data/output/trades</b>（剔除 5 个旧导出残留文件）算出开仓 4 行 / 3 个名字 / 已平 373，与发布一致；收益率和现金仓位仍来自 tracker。
  ⚠ 12 票中有 4 票的边距与已发布 PDF 不一致，是重算造成的。</p>
  <div class="switch" role="group" aria-label="切换版本">
    <button type="button" data-ver="A" aria-pressed="true">A · 登记体</button>
    <button type="button" data-ver="B" aria-pressed="false">B · 掉落体</button>
  </div>
</header>'''

page=(f'<title>Fluxus Recap Covers</title>\n{FONTS}\n<style>{CSS}</style>\n{TOP}\n'
      f'<div id="verA">{A}</div>\n<div id="verB" hidden>{B}</div>\n<script>{JS}</script>\n')
open(f"{SP}/recap_covers.html","w").write(page)

a_sheets=A.split('<article')[1:]; b_sheets=B.split('<article')[1:]
check=(f'<!doctype html><meta charset="utf-8">{FONTS}<style>{CSS}</style><body>'
       f'<div><article{a_sheets[1]}</div><div><article{b_sheets[2]}</div></body>')
open(f"{SP}/recap_check.html","w").write(check)
print("ok", len(page), "bytes; cond bars", len(cond), "; A sheets", len(a_sheets), "B sheets", len(b_sheets))
