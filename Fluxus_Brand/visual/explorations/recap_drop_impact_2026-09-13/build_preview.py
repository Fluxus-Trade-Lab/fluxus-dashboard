#!/usr/bin/env python3
"""Preview of the drop-line landing mark (drop_impact.js) on real SPX closes from origin/main.

    python3 build_preview.py [out.html]

The line is drawn exactly as pipeline/content/recap/visual_assets/recap_page.js dropLine() draws it;
only the crack at its end is new.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECAP = HERE.parents[1] / "recap"
REPO = "/Users/taolezhu/Documents/AI-Trading-System"

raw = subprocess.run(["git", "-C", REPO, "show", "origin/main:data/output/breadth.json"],
                     capture_output=True, check=True).stdout
rows = [(r["date"], r["spx_close"]) for r in json.loads(raw)["history"]["rows"] if r.get("spx_close")]
closes = [r for r in rows if r[0] <= "2026-09-11"][-26:]
assert closes[-1][0] == "2026-09-11" and len(closes) == 26, closes[-1]

TEMPLATE = r"""<title>落点裂纹</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@600;700&display=swap">
<style>
:root{
  --paper:#F2F1ED; --sheet:#FBFAF7; --ink:#1A1917; --ink2:#4A463F; --rule:#D9D6CD; --soft:#E8E5DD;
  --muted:#8A857A; --accent:#D1600F;
  --sans:"IBM Plex Sans",-apple-system,"PingFang SC",sans-serif;
  --cond:"IBM Plex Sans Condensed","IBM Plex Sans",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,Menlo,monospace;
}
@media (prefers-color-scheme:dark){ :root:not([data-theme="light"]){
  --paper:#12110F; --sheet:#1A1917; --ink:#E9E7E2; --ink2:#B7B4AC; --rule:#35312B; --soft:#28251F;
  --muted:#8E8A80; --accent:#E8843C;
}}
:root[data-theme="dark"]{
  --paper:#12110F; --sheet:#1A1917; --ink:#E9E7E2; --ink2:#B7B4AC; --rule:#35312B; --soft:#28251F;
  --muted:#8E8A80; --accent:#E8843C;
}
*{box-sizing:border-box}
body{background:var(--paper);color:var(--ink);font-family:var(--sans);margin:0;padding:40px 20px 90px;line-height:1.6;-webkit-font-smoothing:antialiased}
.wrap{max-width:1120px;margin:0 auto}
.eyebrow{font-family:var(--mono);font-size:11px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);margin:0 0 10px}
h1{font-family:var(--cond);font-weight:700;font-size:clamp(28px,4vw,40px);line-height:1.08;margin:0 0 12px;text-wrap:balance}
.lede{font-size:15px;color:var(--ink2);max-width:66ch;margin:0}
.lede b{color:var(--ink);font-weight:600}
h2{font-family:var(--cond);font-weight:700;font-size:21px;margin:52px 0 4px}
.note{font-size:13.5px;color:var(--ink2);max-width:66ch;margin:0 0 16px}

.controls{display:flex;flex-wrap:wrap;gap:12px 22px;align-items:center;margin:26px 0 0;position:sticky;top:0;z-index:2;background:var(--paper);padding:10px 0;border-bottom:1px solid var(--rule)}
.seg{display:flex;align-items:center;gap:8px;font-family:var(--mono);font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}
.seg .btns{display:flex;border:1.5px solid var(--ink)}
.seg button,.replay{font:600 12px/1 var(--mono);letter-spacing:.06em;background:var(--sheet);color:var(--ink);border:0;padding:8px 13px;cursor:pointer}
.seg button+button{border-left:1.5px solid var(--ink)}
.seg button[aria-pressed="true"]{background:var(--ink);color:var(--sheet)}
.replay{border:1.5px solid var(--ink)}
button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}

/* the recap sheet, at print scale: A4 = 794 css px, 45px margins */
.pg{width:794px;background:var(--sheet);border:1px solid var(--rule);padding:40px 45px 34px}
.mast{display:flex;justify-content:space-between;font-family:var(--mono);font-size:11.7px;letter-spacing:.2em;text-transform:uppercase;color:var(--muted);padding-bottom:12px;border-bottom:1.5px solid var(--ink)}
.mast .brand{color:var(--ink);font-weight:600;letter-spacing:.26em}
.drop{display:block;width:100%;height:auto;overflow:visible}
.drop path{fill:none;stroke:var(--accent);stroke-linecap:round;stroke-linejoin:round;vector-effect:non-scaling-stroke}
.drop.thin{margin-top:14px;height:46px}
.reg{font-family:var(--mono);font-size:11.2px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:9px 0 0}
.reg .m{color:var(--ink);font-weight:600}
.hl-a{font-family:var(--cond);font-weight:700;font-size:29px;line-height:1.14;margin:22px 0 6px;max-width:30ch}
.byline{font-family:var(--mono);font-size:12.3px;letter-spacing:.04em;color:var(--muted);margin:0}
.sec{border-top:1.5px solid var(--ink);margin-top:18px;padding-top:12px}
.sec h3{font-family:var(--mono);font-size:12.3px;letter-spacing:.22em;text-transform:uppercase;margin:0 0 8px}
.sec p{font-size:14px;line-height:1.45;margin:0;color:var(--ink2)}
.sec p b{color:var(--ink)}
__IMPACT_CSS__

.duo{display:grid;grid-template-columns:1fr;gap:22px;margin-top:22px}
@media(min-width:1100px){.duo{grid-template-columns:1fr 1fr}}
figure{margin:0}
figcaption{font-family:var(--mono);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:0 0 8px}
figcaption b{color:var(--ink);font-weight:600}
.scale{overflow:hidden;max-width:100%}
.duo .pg{zoom:.68}
@media(max-width:1099px){.duo .pg{zoom:.8}}
@media(max-width:700px){.duo .pg{zoom:.43}}

.feed{display:flex;flex-wrap:wrap;gap:22px;margin-top:14px}
.phone{width:380px;max-width:100%;background:var(--sheet);border:1px solid var(--rule);padding:12px 10px 10px}
.phone .who{font:600 12.5px/1.3 var(--sans);margin:0 0 2px}
.phone .who span{color:var(--muted);font-weight:400}
.phone .txt{font-size:12.5px;color:var(--ink2);margin:0 0 8px;line-height:1.4}
.phone .shot{height:300px;overflow:hidden;border:1px solid var(--rule);border-radius:12px}
.phone .pg{zoom:.453;border:0}

.levels{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px;margin-top:14px}
.card{background:var(--sheet);border:1px solid var(--rule);padding:16px 18px 14px}
.card .tag{font-family:var(--mono);font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted);margin:0 0 2px}
.card .tag b{color:var(--ink)}
.card.pick{border-color:var(--ink)}
.card p.d{font-size:13px;color:var(--ink2);margin:10px 0 0}

.days{margin-top:14px;border-top:1.5px solid var(--ink)}
.day{display:grid;grid-template-columns:minmax(0,420px) 1fr;gap:10px 28px;align-items:center;padding:16px 0 14px;border-bottom:1px solid var(--rule)}
.day .reg{margin:0;line-height:1.7}
@media(max-width:700px){.day{grid-template-columns:1fr}}

.lineage{margin-top:14px;border-top:1.5px solid var(--ink)}
.lineage .row{display:grid;grid-template-columns:minmax(0,300px) 1fr;gap:6px 32px;padding:14px 0 13px;border-bottom:1px solid var(--rule)}
.lineage p{margin:0}
.lineage .w{font-family:var(--mono);font-size:11px;letter-spacing:.08em;color:var(--muted);line-height:1.5}
.lineage .w b{display:block;font-family:var(--cond);font-size:19px;letter-spacing:0;color:var(--ink);margin:2px 0 1px}
.lineage .w span{display:block}
.lineage .u{font-size:14px;color:var(--ink2);max-width:62ch}
.lineage .u b{color:var(--ink);font-weight:600}
@media(max-width:700px){.lineage .row{grid-template-columns:1fr}}
.score{width:340px;max-width:100%;margin-top:30px;background:var(--sheet);border:1px solid var(--ink);padding:22px 24px 18px;font-family:var(--mono);font-size:13px;line-height:1.75;color:var(--ink);box-shadow:4px 4px 0 var(--soft)}
.score p{margin:0}
.score .t{font-weight:600;letter-spacing:.22em;margin-bottom:10px}
.score .by{color:var(--muted);font-size:11px;margin-top:12px}
.foot{margin-top:56px;padding-top:14px;border-top:1px solid var(--rule);font-family:var(--mono);font-size:11px;line-height:1.85;color:var(--muted)}
.foot b{color:var(--ink);font-weight:500}
</style>

<main class="wrap">
  <p class="eyebrow">Fluxus Capital · 复盘视觉 · 掉落线的落点</p>
  <h1>线不动，落地的地方裂一下</h1>
  <p class="lede">橙线照旧：SPX 21 个交易日，弧长 1.000 m，粗细不变、位置不变。只在它落下的那一点，纸面裂开一次：几道放射裂纹、一段断环、中心一撮碎玻璃。裂法用刊号当种子随机生成，<b>每期裂得不一样，同一期永远裂得一样；不编码任何行情数字。</b></p>

  <div class="controls" role="group" aria-label="裂纹设置">
    <div class="seg">力度<span class="btns" data-k="level"><button data-v="light">轻</button><button data-v="mid">中</button><button data-v="heavy">重</button></span></div>
    <div class="seg">裂纹颜色<span class="btns" data-k="tone"><button data-v="ink">墨</button><button data-v="accent">橙</button></span></div>
    <button class="replay" type="button">重播撞击</button>
  </div>

  <section class="duo">
    <figure><figcaption>现在 · 9/11 日刊第 1 页</figcaption><div class="scale"><div class="pg" id="now"></div></div></figure>
    <figure><figcaption><b>落点裂纹</b> · 同一页，只多一处</figcaption><div class="scale"><div class="pg live" id="new"></div></div></figure>
  </section>

  <h2>X 信息流里的实际大小</h2>
  <p class="note">产线发 X 的是 p1.png（1460 px 宽），手机上约 380 px 宽显示。两张按这个比例缩的。</p>
  <div class="feed">
    <figure><figcaption>现在</figcaption><div class="phone"><p class="who">Fluxus Capital <span>@Fluxus_Z</span></p><p class="txt">Four down days ended with a gap up that stuck…</p><div class="shot"><div class="pg" id="feedNow"></div></div></div></figure>
    <figure><figcaption><b>落点裂纹</b></figcaption><div class="phone"><p class="who">Fluxus Capital <span>@Fluxus_Z</span></p><p class="txt">Four down days ended with a gap up that stuck…</p><div class="shot"><div class="pg live" id="feedNew"></div></div></div></figure>
  </div>

  <h2>三档力度</h2>
  <p class="note">打印原大，9/11 同一个种子。颜色跟上面的开关走。</p>
  <div class="levels" id="levels"></div>

  <h2>五期，五种裂法</h2>
  <p class="note">当前力度与颜色，真实 SPX 窗口。线的形状来自行情，裂的形状来自偶然。</p>
  <div class="days live" id="days"></div>

  <h2>谱系：这一笔从哪里来</h2>
  <p class="note">公司的名字就是 Fluxus。下面每一行都是一件真实作品，右边一栏写的是我们拿它做什么，不只是引用。</p>
  <div class="lineage">
    <div class="row"><p class="w">Marcel Duchamp<b>三个标准终止器</b><span>3 Standard Stoppages · 1913–14</span></p><p class="u">一米长的线从一米高落下，落成什么形状就把它做成尺子。<b>→ 掉落线本身</b>：每期同样 1.000 m，形状交给市场。</p></div>
    <div class="row"><p class="w">Marcel Duchamp<b>大玻璃</b><span>The Large Glass · 1915–23</span></p><p class="u">1926 年展出后运输途中裂开；1936 年他亲手把碎片夹回玻璃，裂纹留下，算作作品的完成。<b>→ 落点裂纹</b>：落下的那一刻留下的，不修掉。</p></div>
    <div class="row"><p class="w">Duchamp × Man Ray<b>灰尘培育</b><span>Dust Breeding · 1920</span></p><p class="u">大玻璃平放积了几个月的灰，被拍成照片，时间变成一层可以看见的东西。<b>→ 周刊候选</b>：把本周五道裂叠在同一块玻璃上，一周的时间一眼看完。</p></div>
    <div class="row"><p class="w">Nam June Paik<b>禅之电影</b><span>Zen for Film · 1964</span></p><p class="u">一卷空白胶片，每放映一次就多一层灰和划痕，每一场都不一样。<b>→ 种子规则</b>：每期裂法各不相同，同一期重印永远是同一道。</p></div>
    <div class="row"><p class="w">Nam June Paik<b>小提琴独奏之一</b><span>One for Violin Solo · 1962</span></p><p class="u">把小提琴慢慢举高，一下砸在桌上，就结束了。<b>→ 特效的分寸</b>：只撞一次、零点几秒、不循环；印刷品上只留下结果。</p></div>
    <div class="row"><p class="w">George Brecht<b>水山药</b><span>Water Yam · 1963</span></p><p class="u">一盒印着几行字的小卡片，每张是一件「事件」的乐谱，谁都能照着演。<b>→ 下面这张卡</b>：把每天的掉落写成一张乐谱，演出者是市场。</p></div>
    <div class="row"><p class="w">Yoko Ono<b>修补作品</b><span>Mend Piece · 1966</span></p><p class="u">一只摔碎的杯子、胶水和胶带，留给观众去补。<b>→ 每期一块新玻璃</b>：裂纹不累积到下一期，昨天的碎留在昨天。</p></div>
    <div class="row"><p class="w">George Maciunas<b>Fluxus 宣言 · Flux Year Box</b><span>1963 · 1966–68</span></p><p class="u">flux 是流动；便宜、短暂、谁都能参与，作品装进一只盒子寄出去。<b>→ 实物线</b>：Fluxus Capital 的 invitation 和特刊用盒子、卡片和日常物件做。</p></div>
  </div>

  <div class="score" aria-label="事件乐谱卡">
    <p class="t">DROP PIECE</p>
    <p>take twenty-one closes.</p>
    <p>let one metre of them fall.</p>
    <p>where it lands, let it crack once.</p>
    <p>tomorrow, a new pane.</p>
    <p class="by">Fluxus Capital · daily, after the close</p>
  </div>
  <p class="note" style="margin-top:8px">仿 Brecht 事件卡的体例写的原创文字：小卡片、全小写、没有标点以外的修饰。可以印在周刊封底、invitation 或者 X 置顶。</p>

  <div class="foot">
    源头 · <b>Fluxus_Brand/visual/recap/drop_impact.js</b>（几何）+ <b>drop_impact.css</b>（颜色、非缩放描边、撞击动画）· 分支 design/marketing-visual<br>
    接线 · dropSvg() 画完线的 &lt;path&gt; 之后追加 dropImpact(dl, {seed: 刊号, pxPerUnit: 46 / (dl.h + 12)})；PDF 与 X 图是静态的，动画只在网页预览里
  </div>
</main>

<script>
__IMPACT_JS__
</script>
<script>
(function () {
  "use strict";
  var CLOSES = __DATA__;
  var PAD = 6, BOXH = 46;
  var LABEL = {light: "轻", mid: "中", heavy: "重"};
  var DESC = {
    light: "五道细纹，没有环。缩到信息流几乎只剩一个毛边的收笔。",
    mid: "七道纹加一段断环，中心有碎屑。缩小后读得出「撞过」，不抢线。",
    heavy: "九道纹、两圈环、分叉更多。原大好看，缩小后开始像一朵花。"
  };
  var state = {level: "mid", tone: "ink"};

  /* identical to recap_page.js dropLine() */
  function dropLine(closes) {
    var p0 = closes[0];
    var P = closes.map(function (p, k) { return [k, -Math.log(p / p0) * 100]; });
    var i;
    for (var it = 0; it < 3; it++) {
      var o = [P[0]];
      for (i = 0; i < P.length - 1; i++) {
        var a = P[i], c = P[i + 1];
        o.push([a[0] * 0.75 + c[0] * 0.25, a[1] * 0.75 + c[1] * 0.25]);
        o.push([a[0] * 0.25 + c[0] * 0.75, a[1] * 0.25 + c[1] * 0.75]);
      }
      o.push(P[P.length - 1]);
      P = o;
    }
    var len = 0;
    for (i = 1; i < P.length; i++) { len += Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]); }
    P = P.map(function (q) { return [q[0] * 1000 / len, q[1] * 1000 / len]; });
    var arc = 0;
    for (i = 1; i < P.length; i++) { arc += Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]); }
    var xs = P.map(function (q) { return q[0]; }), ys = P.map(function (q) { return q[1]; });
    var minx = Math.min.apply(null, xs), maxx = Math.max.apply(null, xs);
    var miny = Math.min.apply(null, ys), maxy = Math.max.apply(null, ys);
    var k = 1000 / (maxx - minx);
    var d = "M " + P.map(function (q) {
      return ((q[0] - minx) * k).toFixed(1) + "," + ((q[1] - miny) * k).toFixed(1);
    }).join(" L ");
    return {d: d, h: (maxy - miny) * k, arc: arc / 1000};
  }

  function win(D) {
    var i = CLOSES.findIndex(function (r) { return r[0] === D; });
    var w = CLOSES.slice(i - 20, i + 1);
    return {D0: w[0][0], D: D, tag: D.slice(5).replace("-", ""), dl: dropLine(w.map(function (r) { return r[1]; }))};
  }

  function svg(w, level, tone) {
    var dl = w.dl;
    var g = level ? dropImpact(dl, {seed: w.tag, level: level, tone: tone, pxPerUnit: BOXH / (dl.h + 2 * PAD), pad: PAD}) : "";
    return '<svg class="drop thin" viewBox="' + (-PAD) + " " + (-PAD) + " " + (1000 + 2 * PAD) + " " +
      (dl.h + 2 * PAD).toFixed(1) + '" role="img" aria-label="SPX drop line, 21 sessions to ' + w.D + '">' +
      '<path style="stroke-width:2.5" d="' + dl.d + '"/>' + g + "</svg>";
  }

  function reg(w) {
    return '<p class="reg">1m · drop <span class="m">#' + w.tag + "</span> · " + w.D0 + " → " + w.D +
      " · SPX · ∫ = " + w.dl.arc.toFixed(3) + " m</p>";
  }

  var W = win("2026-09-11");
  function page(level, tone) {
    return '<div class="mast"><span class="brand">Fluxus Capital</span><span>Daily Market Recap · No. 0911</span></div>' +
      svg(W, level, tone) + reg(W) +
      '<h2 class="hl-a">A Hot Core Print Gets Bought — AI Hardware Runs, the Average Stock Doesn\'t</h2>' +
      '<p class="byline">Four-day slide ends · HPE/DELL +12% · RSP and IWM still under the 50-day · Friday, September 11, 2026</p>' +
      '<div class="sec"><h3>The Big Picture</h3><p>Four down days ended with a gap up that stuck: <b>SPY +0.85%, QQQ +0.87%, both back above the 50-day</b> — on a CPI print that ran hot, core +0.3% m/m against 0.2% expected. Bad data, higher prices: next week\'s hike was already priced near 90%, and once December odds slipped under 49% the uncertainty was gone.</p></div>';
  }

  function render() {
    document.getElementById("now").innerHTML = page(null);
    document.getElementById("feedNow").innerHTML = page(null);
    document.getElementById("new").innerHTML = page(state.level, state.tone);
    document.getElementById("feedNew").innerHTML = page(state.level, state.tone);
    document.getElementById("levels").innerHTML = ["light", "mid", "heavy"].map(function (lv) {
      return '<div class="card' + (lv === state.level ? " pick" : "") + '"><p class="tag">力度 · <b>' + LABEL[lv] + "</b>" +
        (lv === "mid" ? " · 默认" : "") + "</p>" + svg(W, lv, state.tone) + reg(W) + '<p class="d">' + DESC[lv] + "</p></div>";
    }).join("");
    document.getElementById("days").innerHTML = ["2026-09-04", "2026-09-08", "2026-09-09", "2026-09-10", "2026-09-11"].map(function (D) {
      var w = win(D);
      return '<div class="day"><div>' + svg(w, state.level, state.tone) + "</div>" + reg(w) + "</div>";
    }).join("");
    document.querySelectorAll(".btns").forEach(function (g) {
      g.querySelectorAll("button").forEach(function (b) {
        b.setAttribute("aria-pressed", String(state[g.dataset.k] === b.dataset.v));
      });
    });
  }

  function play() {
    document.querySelectorAll(".live .impact, .levels .impact").forEach(function (g) {
      g.classList.remove("play");
      void g.getBoundingClientRect();
      g.classList.add("play");
    });
  }

  document.querySelectorAll(".btns").forEach(function (g) {
    g.addEventListener("click", function (ev) {
      var b = ev.target.closest("button");
      if (!b) { return; }
      state[g.dataset.k] = b.dataset.v;
      render();
      play();
    });
  });
  document.querySelector(".replay").addEventListener("click", play);
  render();
})();
</script>
"""

html = (TEMPLATE
        .replace("__IMPACT_CSS__", (RECAP / "drop_impact.css").read_text())
        .replace("__IMPACT_JS__", (RECAP / "drop_impact.js").read_text())
        .replace("__DATA__", json.dumps(closes)))
out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "drop_impact_preview.html"
out.write_text(html)
print(out, len(html))
