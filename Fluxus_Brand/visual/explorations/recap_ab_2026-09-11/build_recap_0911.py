import json, csv, io, re, math, html, subprocess, tarfile
from datetime import datetime, timedelta
from collections import defaultdict
SP="/private/tmp/claude-501/-Users-taolezhu-Documents-AI-Trading-System-Fluxus-Marketing-Visual-Design/ee3710aa-d552-414c-9357-4584bfc6459a/scratchpad"
R="/Users/taolezhu/Documents/AI-Trading-System"; D="2026-09-11"; e=html.escape
def show(p): return subprocess.run(["git","-C",R,"show",f"origin/main:{p}"],capture_output=True,text=True,check=True).stdout

# ---------- data (authoritative origin/main) ----------
b=json.loads(show("data/output/breadth.json"))
spx=[(r["date"],r["spx_close"]) for r in b["history"]["rows"] if r.get("spx_close")]
i=max(j for j,(d,_) in enumerate(spx) if d<=D); seg=spx[i-20:i+1]; assert seg[-1][0]==D and len(seg)==21
p0=seg[0][1]; pts=[(float(k),-math.log(p/p0)*100.0) for k,(d,p) in enumerate(seg)]
def chaikin(P,it=3):
    for _ in range(it):
        o=[P[0]]
        for a,c in zip(P,P[1:]):
            o.append((a[0]*.75+c[0]*.25,a[1]*.75+c[1]*.25)); o.append((a[0]*.25+c[0]*.75,a[1]*.25+c[1]*.75))
        o.append(P[-1]); P=o
    return P
S=chaikin(pts); L=sum(math.dist(a,c) for a,c in zip(S,S[1:])); S=[(x*1000/L,y*1000/L) for x,y in S]
ARC=sum(math.dist(a,c) for a,c in zip(S,S[1:]))/1000
xs=[p[0] for p in S]; ys=[p[1] for p in S]; k=1000/(max(xs)-min(xs))
P=[((x-min(xs))*k,(y-min(ys))*k) for x,y in S]; DROP_H=(max(ys)-min(ys))*k
assert all(-0.01<=y<=DROP_H+0.01 for _,y in P)
DROP="M "+" L ".join(f"{x:.1f},{y:.1f}" for x,y in P); D0=seg[0][0]
cond=[h for h in b["conditions"]["history"] if h["date"]<=D]; assert cond[-1]["date"]==D
verd=json.loads(show("data/output/breadth_replay.json"))["verdicts"][D]
SCORE=(f"{verd['score']:+d}" if verd["score"] else "0")
arch=[x for x in csv.DictReader(io.StringIO(show("data/history/groups_archive.csv"))) if x["date"]==D]
old=open(f"{SP}/build_recap.py").read()
CSS=re.search(r'CSS = """(.*?)"""',old,re.S).group(1); JS=re.search(r'JS = """(.*?)"""',old,re.S).group(1)

def fl(x):
    try: return float(x)
    except: return None
bykind=defaultdict(list)
for r in arch:
    if fl(r["perf_1d"]) is not None and fl(r["perf_1w"]) is not None: bykind[r["kind"]].append(r)
def tb(kind,col,n=3):
    s=sorted(bykind[kind],key=lambda r:fl(r[col]),reverse=True); return s[:n], s[-n:]
def pct(x,dp=2): return f"{x*100:+.{dp}f}%".replace("-","−")
def signed(v,unit):
    if v is None: return "—"
    return (f"{v:+.0f}" if unit in ("names","warnings") else f"{v:+.2f}").replace("-","−")
SIDE={"bull":"for","bear":"against","neutral":"near"}

# ---------- components ----------
# final form (Andy 09-13, priority=speed): bold line + hollow dot at today's close. Stroke solved for a
# constant ~6px on-screen weight regardless of the day's DROP_H (.drop.thin is CSS-capped at 46px tall).
def bold_stroke(px=6,box_px=46,pad=6): return px*(DROP_H+2*pad)/box_px
def drop_svg(stroke,cls="",pad=6,label="Drop line, 21 sessions to Sep 11",dot=False):
    ex,ey=(float(v) for v in DROP.split()[-1].split(","))
    mark=f'<circle class="dropdot" style="stroke-width:{stroke*0.5:.1f}" cx="{ex}" cy="{ey}" r="{stroke*1.7:.1f}"/>' if dot else ""
    return (f'<svg class="drop {cls}" viewBox="{-pad} {-pad} {1000+2*pad} {DROP_H+2*pad:.1f}" role="img" aria-label="{e(label)}">'
            f'<path style="stroke-width:{stroke}" d="{DROP}"/>{mark}</svg>')
REG=f'1m · drop <span class="m">#0911</span> · {D0} → {D} · SPX · ∫ = {ARC:.3f} m'
def cond_chart():
    n=len(cond); W=940; base=190; top=18; bw=W/n
    o=[f'<svg class="chart" viewBox="0 0 1000 222" role="img" aria-label="Market conditions score, last {n} sessions, {cond[-1]["score"]} on Sep 11">']
    for v in (0,50,100):
        y=base-(v/100)*(base-top)
        o.append(f'<line class="grid{" mid" if v==50 else ""}" x1="0" x2="{W}" y1="{y:.1f}" y2="{y:.1f}"/><text class="ax" x="{W+10}" y="{y+4:.1f}">{v}</text>')
    lastm=None; lastx=-999
    for j,h in enumerate(cond):
        x=j*bw; hh=(h["score"]/100)*(base-top); y=base-hh
        o.append(f'<rect class="{"bar now" if j==n-1 else "bar"}" x="{x+bw*0.14:.2f}" y="{y:.2f}" width="{max(bw*0.72,0.6):.2f}" height="{hh:.2f}"/>')
        m=h["date"][:7]
        if m!=lastm:
            mon=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][int(m[5:])-1]
            lab=f'{mon} {m[2:4]}' if (mon=="Jan" or lastm is None) else mon
            if x-lastx>=48: o.append(f'<text class="ax" x="{x:.1f}" y="216">{lab}</text>'); lastx=x
            lastm=m
    lx=(n-1)*bw+bw/2; ly=base-(cond[-1]["score"]/100)*(base-top)
    o.append(f'<text class="nowlab" x="{lx-8:.1f}" y="{ly-8:.1f}" text-anchor="end">{cond[-1]["score"]}</text></svg>')
    return "".join(o)
def vote_strip(big=False):
    c=[]
    for v in verd["vote_detail"]:
        if not v["measurable"]: g,num,note="uncounted","—","not counted"
        else: g,num,note=SIDE[v["side"]],signed(v["margin"],v["unit"]),v["unit"]
        c.append(f'<div class="vote"><span class="g {g}" aria-hidden="true"></span><div class="vnum">{num}</div><div class="vunit">{e(note)}</div><div class="vlab">{e(v["label"])}</div></div>')
    return f'<div class="votes{" big" if big else ""}">{"".join(c)}</div>'
LEGEND=('<div class="legend"><span><span class="g for"></span>counts for</span><span><span class="g against"></span>counts against</span>'
        '<span><span class="g near"></span>inside its line</span><span><span class="g uncounted"></span>not counted</span>'
        '<span class="lg-note">number = distance past each vote’s own line</span></div>')
def board_table(kind,title):
    def rows(lst,col): return "".join(f'<tr><td class="gname">{e(r["group"])}</td><td class="st">{e(r["state"])}</td><td class="n {"up" if fl(r[col])>=0 else "dn"}">{pct(fl(r[col]))}</td></tr>' for r in lst)
    def block(lab,col):
        t,bt=tb(kind,col); return f'<div class="lcol"><div class="lhead">{lab}</div><table class="lt">{rows(t,col)}<tr class="gap"><td colspan="3"></td></tr>{rows(bt,col)}</table></div>'
    return f'<div class="lpanel"><h4>{e(title)}</h4><div class="lgrid">{block("1 day","perf_1d")}{block("1 week","perf_1w")}</div></div>'
def bars_panel(kind,title,col,lab):
    top,bot=tb(kind,col,4); items=top+bot; mx=max(abs(fl(r[col])) for r in items)
    o=[f'<div class="bpanel"><h4>{e(title)} <span>{lab}</span></h4>']
    for j,r in enumerate(items):
        v=fl(r[col]); w=abs(v)/mx*50
        if j==len(top): o.append('<div class="bsep"></div>')
        pos="left:50%" if v>=0 else "right:50%"
        o.append(f'<div class="brow"><div class="bname">{e(r["group"])}</div><div class="btrack"><span class="zero"></span><span class="bfill {"pos" if v>=0 else "neg"}" style="{pos};width:{w:.2f}%"></span></div><div class="bval {"up" if v>=0 else "dn"}">{pct(v,1)}</div></div>')
    o.append('</div>'); return "".join(o)
def ledger2(rows): return '<div class="scroll"><table class="led">'+"".join(f'<tr><td class="t">{e(a)}</td><td>{e(c)}</td></tr>' for a,c in rows)+'</table></div>'
def olist(items,cls): return f'<ol class="{cls}">'+"".join(f'<li>{e(x)}</li>' for x in items)+'</ol>'

TELL=('<svg class="tell" viewBox="0 0 1000 380" role="img" aria-label="Schematic: a downtrend meets bad news; if price rises it is a news failure, if it keeps falling the news worked">'
 '<line class="evt" x1="620" y1="36" x2="620" y2="352"/>'
 '<text x="632" y="54">BAD NEWS · hot CPI, hike odds up</text>'
 '<path class="trend" d="M 40,90 L 120,132 L 200,116 L 280,170 L 360,160 L 440,214 L 520,204 L 620,256"/>'
 '<path class="upb" d="M 620,256 L 690,226 L 750,246 L 810,196 L 870,214 L 930,160"/>'
 '<path class="dnb" d="M 620,256 L 690,286 L 750,270 L 810,306 L 870,300 L 930,326"/>'
 '<circle cx="620" cy="256" r="6"/>'
 '<text class="lab-up" x="990" y="104" text-anchor="end">NEWS FAILS · selling exhausted → bounce</text>'
 '<text class="small" x="990" y="124" text-anchor="end">still just a bounce until price</text>'
 '<text class="small" x="990" y="142" text-anchor="end">confirms (reclaim + FTD)</text>'
 '<text class="lab-dn" x="990" y="356" text-anchor="end">news “works” · keeps falling</text>'
 '<text x="604" y="300" text-anchor="end">already deeply oversold here</text>'
 '<text x="40" y="370">it’s not the news — it’s the reaction</text></svg>')

# ---------- content (as published 9/11) ----------
TITLE="Rebound Snaps the 4-Day Slide — a News Failure Despite Firm CPI"
BYLINE="Stocks Rise as Bad News Is Priced In · Rally Attempt Day 1 Into the Fed · September 11, 2026"
BIG=("The rebound arrived. Indexes snapped a four-day losing streak despite a firm CPI print — a textbook news failure. Headline CPI came in at 3.4% YoY "
 "(core 0.3% MoM, a touch hot, but core eased to 2.4% YoY), which cemented rate-HIKE odds above ~85% into next Wednesday’s Fed — yet stocks rose anyway "
 "because the bad news was already priced in after four down days and deeply oversold conditions. Oil retreated (Brent −3% off ~$100), the 10-year eased to 4.94%, "
 "and buyers returned to tech. <b>S&amp;P +0.86% to 7,657</b>, reclaiming its 50-day and the 7,580 breakout and closing right at the 21-day; the Dow +0.98% (+509 pts) "
 "and Nasdaq +0.96%. Still weekly LOSSES across the board (worst Dow week since March). <b>This is day 1 of a potential rally attempt — leaders standing out while breadth stays thin.</b>")
IDX=[("SPX","+0.86%","Reclaimed 50-day + 7,580","Closed right on the 21-day"),("QQQ","+0.87%","Best relative structure","Back on the 21-day, above 707"),
     ("RSP","+0.80%","Value lagging, below 50-day","Relief bounce, not a fix"),("DOW","+0.98%","+509 pts, upside break","Snapped 4-day slide"),
     ("MID","+0.83%","Still in the hurt locker","Below key MAs"),("IWM","+0.45%","Weakest, didn’t reach 8-day","2,900 the level, below 100-day"),
     ("VIX","−11.2%","Died out to a sweet range","Oil −3%, 10Y 4.94%, gold/crypto weak")]
def chgcls(t,c): return "" if t=="VIX" else ("up" if c.startswith("+") else "dn")
STATEBAR=[("Short-term","Pullback · Protect"),("Medium-term","Neutral"),("Long-term","Grow · all above 200-day"),("Rally attempt","Day 1")]
WEEK=[("S&P 500","−0.8%"),("Dow","−1.6%"),("Nasdaq","−0.7%"),("Russell 2000","−2.4%")]
STRENGTH=[("AI hardware","DELL +10%, HPE +9% — THE leaders (servers / data-center / cooling). RS new highs before price 3 weeks running; NTAP in the group"),
          ("Semis","The baton passed from NVDA (failed its pivot) to younger semis — AMD reclaimed 50-day, SMTC / TSM / MRVL / INTC building right sides"),
          ("Mega-cap","AAPL (foldable iPhone Duo = fresh catalyst) · GOOGL reclaimed 200-day · META (Muse AI agent, near weekly breakout) · MSFT basing at 500"),
          ("Energy","Oil exploration / refiners firing (VLO, refining group strong)")]
WEAK=[("Software","The tell — OKTA & PLTR failed breakout attempts, sold; SNOW faded a good-earnings gap; broad software still lagging badly"),
      ("Breadth","Only 37% of S&P (30% Nasdaq) above the 5-day — still thin"),("Crypto","BTC / ETH faded hard on volume (rotation into “best of tech”)"),
      ("Rate-sens","Russell, midcaps in the “hurt locker”; utilities / uranium weak"),("Bonds","Yields broke out this week (bonds broke down) — the overhang"),
      ("Bifurcation","Only a handful of top leaders working — not in them = missing the move")]
FOMC=("The Fed decision is the deciding event (hike odds ~85–90%). Watch the S&amp;P vs the 21-day (closed right on it) and 50-day / 7,580; QQQ vs the 21-day and 707; "
      "Russell vs 2,880 / 100-day. <b>The rally attempt needs a follow-through day (day 4–7) to confirm</b> — otherwise it’s an oversold bounce inside a pullback.")
RULES=["Day 1 of a rally attempt — a news failure snapped the slide, but it needs a follow-through day to confirm; until then it’s a bounce, not a trend",
 "Trade the leaders: AI hardware (DELL, HPE), the younger semis (AMD, SMTC, TSM), select mega-cap — that’s where relative strength is",
 "Avoid software (OKTA / PLTR / SNOW failing) and rate-sensitive groups until they firm",
 "Breadth is thin (37% above 5-day) and it’s a bifurcated tape — only the top handful of leaders are working; size and stops matter",
 "FOMC Wednesday is the swing factor — a ~90% hike is largely priced, so watch the REACTION, not the decision",
 "Bonds / yields are the overhang — stocks won’t sustainably rally until the 10-year stops breaking out",
 "Never serious trouble until S&P breaks the 200-day — well above; 7,580 is the near-term line"]
EDU_T="News Failure — and Why It Isn’t a Green Light Yet"
EDU=("Today was a textbook “news failure”: a genuinely bad headline — a firm CPI that pushed rate-hike odds above 85% — hit the tape, and instead of falling, stocks rallied "
 "and snapped a four-day slide. Here’s what that does and doesn’t tell you. <b>What it DOES mean:</b> when a known bad news item can’t push price lower, the selling is exhausted — "
 "the bad news is already priced in, the people who wanted to sell it have sold, and one reason to keep falling has been removed. It often coincides with a sentiment shift, "
 "from “sell every scare” to “even bad news can’t dent us,” and that shift is real fuel. <b>But — and this is the crucial part — a news failure only marks that selling has PAUSED; "
 "it does NOT by itself start a new uptrend.</b> It’s the first piece of the puzzle, not the whole picture. A genuine trend change still has to be CONFIRMED by price: reclaiming key "
 "levels (today the S&amp;P retook its 50-day and 7,580, and closed right on the 21-day — constructive, but not yet a full reclaim) and, above all, a follow-through day — a decisive, "
 "higher-volume up day arriving on day 4–7 of the attempt that signals institutions committing. Until that confirmation comes, what you have is a tradeable oversold BOUNCE, not a new "
 "trend — and in a bifurcated tape with a rate hike two days away, a bounce can still just be a rally within a downtrend that fails at overhead resistance. The discipline: treat today "
 "as day 1, respect that the news failure removed the downside pressure and opened the door, but wait for the follow-through day and the 21-day reclaim before calling a turn. "
 "<b>Trigger over indicator: the news failure is the indicator that fuel is present; the follow-through day is the trigger that lights it.</b>")
R_BOOK=R

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
assert (len(BK_ROWS),BK_NAMES,BK_CLOSED)==(6,5,378),(len(BK_ROWS),BK_NAMES,BK_CLOSED)
BK_M,BK_T,BK_N=book_html(BK_ROWS,BK_NAMES,BK_CLOSED,'+123.45%','70.99%')
PORT=("Snapshot as of the 9/11 close. Return holds +123.5% with cash ~71% — still defensive into the FOMC, carrying a small inverse / short hedge (TZA) against the weak tape "
      "alongside the relative-strength longs. Leaning cautious while the rally attempt waits on a follow-through day.")
DISC="Weekly Market Recap — Friday, September 11, 2026 · Index data verified against session close (exchange / FRED) · Educational content only, not investment advice."

EXTRA_CSS = """
.bigidx.seven{grid-template-columns:repeat(4,minmax(0,1fr)) !important}
.bigidx.seven>.bi:first-child{grid-column:span 2}
@media(max-width:520px){.bigidx.seven{grid-template-columns:repeat(2,minmax(0,1fr)) !important}}
.statebar{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule)}
@media(max-width:620px){.statebar{grid-template-columns:repeat(2,minmax(0,1fr))}}
.statebar>div{background:var(--sheet);padding:11px 13px;display:grid;gap:3px}
.statebar span{font-family:var(--mono);font-size:10px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.statebar b{font-size:13.5px;font-weight:600;color:var(--ink);line-height:1.3}
.statebar.big b{font-family:var(--cond);font-weight:700;font-size:22px;letter-spacing:-.005em}
table.led td.t{min-width:104px}
.tell{display:block;width:100%;height:auto;margin-top:8px}
.tell path{fill:none;stroke-width:3;stroke-linecap:round;stroke-linejoin:round}
.tell .trend{stroke:var(--ink)} .tell .upb{stroke:var(--up)} .tell .dnb{stroke:var(--dn)}
.tell .evt{stroke:var(--muted);stroke-width:1.5;stroke-dasharray:6 6}
.tell circle{fill:var(--ink)}
.tell text{font-family:var(--mono);font-size:13px;fill:var(--muted)}
.tell .lab-up{fill:var(--up);font-weight:600} .tell .lab-dn{fill:var(--dn);font-weight:600}
.tell .small{font-size:12px}
.schem{font-family:var(--mono);font-size:10.5px;letter-spacing:.06em;color:var(--muted);margin:8px 0 0}
.disc{font-family:var(--mono);font-size:10.5px;line-height:1.7;color:var(--muted);border-top:1px solid var(--rule);padding-top:10px;margin:26px 0 0}
.edu .prose{max-width:74ch}
"""

def mast_a(): return '<div class="mast"><span class="brand">FLUXUS CAPITAL</span><span>Weekly Market Recap · No. 0911</span></div><hr class="r ink">'
def folio_a(n): return f'<div class="folio"><span>Fluxus Capital · Weekly Market Recap</span><span>{n} / 4</span></div>'
def folio_b(n): return f'<div class="folio b"><span class="fl">{drop_svg(2,"fmark",4,"Drop mark")}</span><span>Fluxus Capital · Weekly Market Recap</span><span>{n} / 4</span></div>'
def statebar(big=False): return f'<div class="statebar{" big" if big else ""}">'+"".join(f'<div><span>{e(a)}</span><b>{e(c)}</b></div>' for a,c in STATEBAR)+'</div>'
idx_rows="".join(f'<tr><td class="t">{t}</td><td class="n {chgcls(t,c)}">{c}</td><td>{e(x)}</td><td>{e(y)}</td></tr>' for t,c,x,y in IDX)
IDX_TABLE=f'<div class="scroll"><table class="idx"><thead><tr><th>Index</th><th class="rn">Chg</th><th>Technical</th><th>Context</th></tr></thead><tbody>{idx_rows}</tbody></table></div>'
WEEK_M='<div class="metrics">'+"".join(f'<div><span>{e(a)}</span><b class="dn">{c}</b></div>' for a,c in WEEK)+'</div>'

A=f'''
<article class="sheet a">{mast_a()}{drop_svg(bold_stroke(),"thin",dot=True)}<p class="reg">{REG}</p>
  <h2 class="hl-a">{e(TITLE)}</h2>
  <section class="sec"><h3>The Big Picture</h3><p class="prose">{BIG}</p></section>
  <section class="sec"><h3>Index Action · Friday</h3>{IDX_TABLE}</section>
  <section class="sec"><h3>Market State</h3>{statebar()}</section>{folio_a(1)}</article>
<article class="sheet a">{mast_a()}
  <section class="sec first"><h3>Breadth Votes</h3><div class="state-row"><span class="env">{e(verd["env"])}</span><span class="score">{SCORE}<small> / {len(verd["vote_detail"])} votes</small></span></div>{vote_strip()}{LEGEND}</section>
  <section class="sec"><h3>Market Conditions <span class="h3n">{cond[-1]["score"]} / 100 · Caution</span></h3>{cond_chart()}</section>
  <section class="sec"><h3>Weekly Scorecard</h3>{WEEK_M}<p class="prose">Dow’s worst week since March. Friday snapped the 4-day slide, but the week still closed lower.</p></section>
  <section class="sec"><h3>Leaders and Laggards <span class="h3n">top 3 · bottom 3</span></h3><div class="lwrap">{board_table("industry","Industries")}{board_table("theme","Themes")}</div></section>{folio_a(2)}</article>
<article class="sheet a">{mast_a()}
  <section class="sec first"><h3>Where the Strength Is</h3>{ledger2(STRENGTH)}</section>
  <section class="sec"><h3>Weak / Under the Surface</h3>{ledger2(WEAK)}</section>
  <section class="sec"><h3>Next Week · FOMC <span class="h3n">Wed, Sep 16</span></h3><p class="prose">{FOMC}</p></section>
  <section class="sec"><h3>The Rules</h3>{olist(RULES,"ol-a")}</section>{folio_a(3)}</article>
<article class="sheet a">{mast_a()}
  <section class="sec first edu"><h3>Education <span class="h3n">{e(EDU_T)}</span></h3><p class="prose">{EDU}</p></section>
  <section class="sec"><h3>The Tell <span class="h3n">when bad news can’t push price down</span></h3>{TELL}<p class="schem">Schematic — illustrates the pattern, not price data.</p></section>
  <section class="sec"><h3>Portfolio Update</h3>{BK_M}{BK_T}<p class="prose">{PORT}</p>{BK_N}</section>
  <p class="disc">{e(DISC)}</p>{folio_a(4)}</article>'''

tiles="".join(f'<div class="bi"><div class="bi-t">{t}</div><div class="bi-c {chgcls(t,c)}">{c}</div><div class="bi-d">{e(x)}</div><div class="bi-l">{e(y)}</div></div>' for t,c,x,y in IDX)
B=f'''
<article class="sheet b cover">
  <div class="mast"><span class="brand">FLUXUS CAPITAL</span><span>Friday · September 11 · 2026</span></div>
  <div class="hero">{drop_svg(7,"hero",dot=True)}</div><p class="reg">{REG} — same length, different shapes</p><hr class="r ink">
  <h2 class="hl-b">Rebound Snaps the 4-Day Slide.<br>A News Failure Despite Firm CPI.</h2>
  <div class="cover-grid"><p class="prose lead">{BIG}</p>
    <aside class="board"><div class="brd-h">The Board</div>
      <div class="brd-row"><span>Breadth votes</span><b>{e(verd["env"])} {SCORE}</b></div>
      <div class="brd-row"><span>Conditions</span><b>{cond[-1]["score"]} / 100</b></div>
      <div class="brd-row"><span>S&amp;P</span><b class="up">+0.86%</b></div>
      <div class="brd-row"><span>QQQ</span><b class="up">+0.87%</b></div>
      <div class="brd-row"><span>VIX</span><b>−11.2%</b></div>
      <div class="brd-row"><span>S&amp;P week</span><b class="dn">−0.8%</b></div>
      <div class="brd-row"><span>Rally attempt</span><b>Day 1</b></div></aside></div>{folio_b(1)}</article>
<article class="sheet b">
  <div class="kicker">The Tape · Friday</div><h3 class="hb">Index Action</h3><div class="bigidx seven">{tiles}</div>
  <div class="kicker sp">Market State</div>{statebar(big=True)}
  <div class="kicker sp">Breadth Votes</div><div class="state-b"><span class="env-b">{e(verd["env"])}</span><span class="score-b">{SCORE}<small>/ {len(verd["vote_detail"])}</small></span></div>{vote_strip(big=True)}{LEGEND}
  <div class="kicker sp">Market Conditions · <b>{cond[-1]["score"]} / 100 · Caution</b></div>{cond_chart()}{folio_b(2)}</article>
<article class="sheet b">
  <div class="kicker">Weekly Scorecard</div>{WEEK_M}
  <div class="split-b" style="margin-top:34px"><div><div class="kicker">Where the Strength Is</div>{ledger2(STRENGTH)}</div><div><div class="kicker">Weak / Under the Surface</div>{ledger2(WEAK)}</div></div>
  <div class="kicker sp">Rotation · Friday</div><div class="bars2">{bars_panel("industry","Industries","perf_1d","1 day")}{bars_panel("theme","Themes","perf_1d","1 day")}</div>
  <div class="kicker sp">Rotation · The Week</div><div class="bars2">{bars_panel("industry","Industries","perf_1w","1 week")}{bars_panel("theme","Themes","perf_1w","1 week")}</div>{folio_b(3)}</article>
<article class="sheet b">
  <div class="pull edu"><div class="kicker">Education</div><h3 class="hb big">{e(EDU_T)}</h3><p class="prose lead">{EDU}</p></div>
  <div class="kicker sp">The Tell · when bad news can’t push price down</div>{TELL}<p class="schem">Schematic — illustrates the pattern, not price data.</p>
  <div class="split-b" style="margin-top:34px"><div><div class="kicker">Next Week · FOMC · Wed Sep 16</div><p class="prose">{FOMC}</p>
      <div class="kicker sp">Book</div>{BK_M}{BK_T}<p class="prose">{PORT}</p>{BK_N}</div>
    <div><div class="kicker">The Rules</div>{olist(RULES,"ol-b rules")}</div></div>
  <p class="disc">{e(DISC)}</p>{folio_b(4)}</article>'''

FONTS='<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Sans+Condensed:wght@600;700&display=swap">'
TOP=f'''<header class="top">
  <p class="eyebrow">Fluxus Capital · Weekly Market Recap · 9/11 期 · A / B</p>
  <h1>9/11 周刊 · A 登记体 · B 掉落体</h1>
  <p class="lede">同一期、同一份数据，两种外观，各四页全文。周刊比日刊多出市场状态条、周成绩单、强弱清单、FOMC 预告和教学长文，全部重排；所有表格、票面和图由数据生成。</p>
  <p class="prov">数据 · 全部读 <b>origin/main</b>（本地树停在 9/10）· <b>breadth.json</b> Conditions 9/11 = {cond[-1]["score"]}，与发布一致 · <b>breadth_replay.json</b> 12 票 9/11，与发布的 PDF 逐项一致 · <b>groups_archive.csv</b> 行业 {len(bykind["industry"])} / 主题 {len(bykind["theme"])}（9/11）· SPX 收盘（掉落线 {D0} → {D}）。
  持仓 · <b>data/output/trades</b>（剔除 5 个旧导出残留文件）算出开仓 6 行 / 5 个名字 / 已平 378，与发布一致；收益率和现金仓位仍来自 tracker。
  ⚠ 发布版的领涨领跌截图其实是 <b>9/10</b> 的数据（逐项核对吻合），本页用的是 9/11 归档。</p>
  <div class="switch" role="group" aria-label="切换版本"><button type="button" data-ver="A" aria-pressed="true">A · 登记体</button><button type="button" data-ver="B" aria-pressed="false">B · 掉落体</button></div>
</header>'''
JS2=JS.replace("'recapVer'","'recapVer0911'")
page=(f'<title>Fluxus Weekly Recap 9/11</title>\n{FONTS}\n<style>{CSS}{EXTRA_CSS}</style>\n{TOP}\n'
      f'<div id="verA">{A}</div>\n<div id="verB" hidden>{B}</div>\n<script>{JS2}</script>\n')
open(f"{SP}/recap_0911.html","w").write(page)
bs=B.split('<article')[1:]; as_=A.split('<article')[1:]
check=f'<!doctype html><meta charset="utf-8">{FONTS}<style>{CSS}{EXTRA_CSS}</style><body><div><article{bs[1]}</div><div><article{bs[2]}</div><div><article{as_[3]}</div></body>'
open(f"{SP}/recap_0911_check.html","w").write(check)
print(f"book rows {len(BK_ROWS)} names {BK_NAMES} closed {BK_CLOSED} stale-dropped {BK_STALE}: {BK_ROWS}")
print(f"ok {len(page)} bytes · drop {D0}->{D} arc {ARC:.3f} H {DROP_H:.1f} · cond bars {len(cond)} last {cond[-1]['score']} · votes {verd['env']} {verd['score']:+d} · archive ind {len(bykind['industry'])} theme {len(bykind['theme'])}")
