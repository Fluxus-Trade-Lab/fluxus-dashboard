/* Fluxus recap page: renders one issue × language × layout from the embedded JSON.
   Components are ports of the Visual line's build_recap.py / build_recap_0911.py.
   Robustness: rendering never waits for web fonts (CSS stacks fall back); a section whose data
   is missing or malformed renders "—" instead of taking the page down.
   Modes: preview (topic cards visible) · print (#print=1: A layout, light theme, no topic cards —
   member PDFs carry reader content only). DATA.layouts limits the layouts a page offers. */
(function () {
  "use strict";

  var DASH = "—";
  var MINUS = "−";
  var X0 = 40;
  var X1 = 960;
  var YT = 30;
  var YB = 350;
  var printMode = false;

  /* ---------------------------------------------------------------- formatting */
  function txt(v) {
    if (v === null || v === undefined) {
      return "";
    }
    if (typeof v === "object" && Array.isArray(v.j)) {
      return v.j.join("");
    }
    return String(v);
  }

  function esc(v) {
    return txt(v)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function rich(v) {
    return esc(v).replace(/&lt;(\/?)b&gt;/g, "<$1b>");
  }

  function isNum(x) {
    return typeof x === "number" && isFinite(x);
  }

  function minus(s) {
    return s.replace("-", MINUS);
  }

  function plus(x, dp) {
    return isNum(x) ? (x >= 0 ? "+" : "") + minus(x.toFixed(dp)) : DASH;
  }

  function pct(x, dp) {
    return isNum(x) ? plus(x * 100, dp === undefined ? 2 : dp) + "%" : DASH;
  }

  function fixed(x, dp) {
    return isNum(x) ? minus(x.toFixed(dp)) : DASH;
  }

  function grouped(x, dp) {
    if (!isNum(x)) {
      return DASH;
    }
    var parts = Math.abs(x).toFixed(dp).split(".");
    parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    return (x < 0 ? MINUS : "") + parts.join(".");
  }

  function plusGrouped(x) {
    return isNum(x) ? (x >= 0 ? "+" : "") + grouped(x, 0) : DASH;
  }

  function cls(x) {
    return isNum(x) ? (x >= 0 ? "up" : "dn") : "";
  }

  function signCls(s) {
    var c = txt(s).trim().charAt(0);
    return c === "+" ? "up" : (c === MINUS || c === "-") ? "dn" : "";
  }

  function sR(x) {
    return isNum(x) ? plus(x, 2) + "R" : DASH;
  }

  function scoreTxt(s) {
    if (!isNum(s)) {
      return DASH;
    }
    return s === 0 ? "0" : (s > 0 ? "+" : MINUS) + Math.abs(s);
  }

  function fill(tpl, vals) {
    return txt(tpl).replace(/\{(\w+)\}/g, function (m, k) {
      return isNum(vals[k]) ? String(vals[k]) : DASH;
    });
  }

  function safe(fn) {
    try {
      return fn();
    } catch (err) {
      if (window.console) {
        window.console.warn("recap section failed", err);
      }
      return '<p class="schem">' + DASH + "</p>";
    }
  }

  function list(a) {
    return Array.isArray(a) ? a : [];
  }

  /* ---------------------------------------------------------------- drop line (SPX, 21 sessions) */
  function dropLine(closes) {
    if (!Array.isArray(closes) || closes.length < 2 || !closes.every(isNum)) {
      return null;
    }
    var p0 = closes[0];
    var P = closes.map(function (p, k) {
      return [k, -Math.log(p / p0) * 100];
    });
    var i;
    for (var it = 0; it < 3; it++) {
      var o = [P[0]];
      for (i = 0; i < P.length - 1; i++) {
        var a = P[i];
        var c = P[i + 1];
        o.push([a[0] * 0.75 + c[0] * 0.25, a[1] * 0.75 + c[1] * 0.25]);
        o.push([a[0] * 0.25 + c[0] * 0.75, a[1] * 0.25 + c[1] * 0.75]);
      }
      o.push(P[P.length - 1]);
      P = o;
    }
    var len = 0;
    for (i = 1; i < P.length; i++) {
      len += Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]);
    }
    P = P.map(function (q) {
      return [q[0] * 1000 / len, q[1] * 1000 / len];
    });
    var arc = 0;
    for (i = 1; i < P.length; i++) {
      arc += Math.hypot(P[i][0] - P[i - 1][0], P[i][1] - P[i - 1][1]);
    }
    var xs = P.map(function (q) { return q[0]; });
    var ys = P.map(function (q) { return q[1]; });
    var minx = Math.min.apply(null, xs);
    var maxx = Math.max.apply(null, xs);
    var miny = Math.min.apply(null, ys);
    var maxy = Math.max.apply(null, ys);
    var k = 1000 / (maxx - minx);
    var d = "M " + P.map(function (q) {
      return ((q[0] - minx) * k).toFixed(1) + "," + ((q[1] - miny) * k).toFixed(1);
    }).join(" L ");
    return { d: d, h: (maxy - miny) * k, arc: arc / 1000 };
  }

  function dropSvg(dl, stroke, klass, aria, pad) {
    if (!dl) {
      return '<p class="reg">' + DASH + "</p>";
    }
    var p = pad === undefined ? 6 : pad;
    return '<svg class="drop ' + klass + '" viewBox="' + (-p) + " " + (-p) + " " + (1000 + 2 * p) + " " +
      (dl.h + 2 * p).toFixed(1) + '" role="img" aria-label="' + esc(aria) + '">' +
      '<path style="stroke-width:' + stroke + '" d="' + dl.d + '"/></svg>';
  }

  function regLine(is, dl) {
    var arc = dl ? dl.arc.toFixed(3) : DASH;
    /* the tag names the window this line draws (21 SPX sessions), so it is always the date-style tag of the
       last session — never the issue number. On a weekly, "#W37" next to 08-13 → 09-11 read as "week 37
       started on 08-13" (Andy 09-13); the issue number lives in the mast as "No. W37". */
    var tag = is.weekly ? String(is.D || "").slice(5).replace("-", "") : is.no;
    return '<p class="reg">1m · drop <span class="m">#' + esc(tag) + "</span> · " + esc(is.D0) + " → " +
      esc(is.D) + " · SPX · ∫ = " + arc + " m</p>";
  }

  /* ---------------------------------------------------------------- conditions chart */
  function condChart(cond, V) {
    var s = cond && cond.scores;
    if (!Array.isArray(s) || !s.length) {
      return '<p class="schem">' + DASH + "</p>";
    }
    var n = s.length;
    var W = 940;
    var base = 190;
    var top = 18;
    var bw = W / n;
    var o = ['<svg class="chart" viewBox="0 0 1000 222" role="img" aria-label="' + esc(V.cond_aria) + '">'];
    [0, 50, 100].forEach(function (v) {
      var y = (base - v / 100 * (base - top)).toFixed(1);
      o.push('<line class="grid' + (v === 50 ? " mid" : "") + '" x1="0" x2="' + W + '" y1="' + y + '" y2="' + y + '"/>');
      o.push('<text class="ax" x="' + (W + 10) + '" y="' + (Number(y) + 4).toFixed(1) + '">' + v + "</text>");
    });
    s.forEach(function (v, j) {
      if (!isNum(v)) {
        return;
      }
      var hh = v / 100 * (base - top);
      o.push('<rect class="' + (j === n - 1 ? "bar now" : "bar") + '" x="' + (j * bw + bw * 0.14).toFixed(2) +
        '" y="' + (base - hh).toFixed(2) + '" width="' + Math.max(bw * 0.72, 0.6).toFixed(2) +
        '" height="' + hh.toFixed(2) + '"/>');
    });
    var lastx = -999;
    list(cond.months).forEach(function (m, q) {
      var x = m[0] * bw;
      var mm = parseInt(String(m[1]).slice(5), 10);
      var lab = (V.months && V.months[mm - 1]) || String(m[1]);
      if (q === 0 || mm === 1) {
        lab += " " + String(m[1]).slice(2, 4);
      }
      if (x - lastx >= 64) {
        o.push('<text class="ax" x="' + x.toFixed(1) + '" y="216">' + esc(lab) + "</text>");
        lastx = x;
      }
    });
    var last = s[n - 1];
    if (isNum(last)) {
      var lx = (n - 1) * bw + bw / 2;
      var ly = base - last / 100 * (base - top);
      o.push('<text class="nowlab" x="' + (lx - 8).toFixed(1) + '" y="' + (ly - 8).toFixed(1) +
        '" text-anchor="end">' + last + "</text>");
    }
    o.push("</svg>");
    return o.join("");
  }

  /* ---------------------------------------------------------------- votes */
  var SIDE = { bull: "for", bear: "against", neutral: "near" };

  function voteStrip(verd, V, big) {
    var votes = list(verd && verd.votes);
    if (!votes.length) {
      return '<p class="schem">' + DASH + "</p>";
    }
    var cells = votes.map(function (v) {
      var label = v[0];
      var side = v[1];
      var margin = v[2];
      var unit = v[3];
      var measurable = v[4];
      var g = "uncounted";
      var num = DASH;
      var note = V.legend[3];
      if (measurable) {
        g = SIDE[side] || "near";
        num = (unit === "names" || unit === "warnings") ? plus(margin, 0) : plus(margin, 2);
        note = (V.units && V.units[unit] !== undefined) ? V.units[unit] : unit;
      }
      var lab = (V.vlabels && V.vlabels[label]) || label;
      return '<div class="vote"><div><span class="g ' + g + '" aria-hidden="true"></span></div>' +
        '<div class="vnum">' + num + '</div><div class="vunit">' + esc(note) + "</div>" +
        '<div class="vlab">' + esc(lab) + "</div></div>";
    });
    return '<div class="votes' + (big ? " big" : "") + '">' + cells.join("") + "</div>";
  }

  function legend(V) {
    var L = V.legend;
    return '<div class="legend">' +
      '<span><span class="g for"></span>' + esc(L[0]) + "</span>" +
      '<span><span class="g against"></span>' + esc(L[1]) + "</span>" +
      '<span><span class="g near"></span>' + esc(L[2]) + "</span>" +
      '<span><span class="g uncounted"></span>' + esc(L[3]) + "</span>" +
      '<span class="lg-note">' + esc(L[4]) + "</span></div>";
  }

  /* ---------------------------------------------------------------- groups */
  function groupRows(rows) {
    return list(rows).map(function (r) {
      return '<tr><td class="gname">' + esc(r[0]) + '</td><td class="st">' + esc(r[1]) +
        '</td><td class="n ' + cls(r[2]) + '">' + pct(r[2]) + "</td></tr>";
    }).join("");
  }

  function boardTable(g, title, V) {
    function block(lab, rows) {
      var r = list(rows);
      return '<div class="lcol"><div class="lhead">' + esc(lab) + '</div><table class="lt">' +
        groupRows(r.slice(0, 3)) + '<tr class="gap"><td colspan="3"></td></tr>' +
        groupRows(r.slice(Math.max(r.length - 3, 3))) + "</table></div>";
    }
    return '<div class="lpanel"><h4>' + esc(title) + '</h4><div class="lgrid">' +
      block(V.d1, g && g.d1) + block(V.w1, g && g.w1) + "</div></div>";
  }

  function barsPanel(rows, title, lab) {
    var items = list(rows);
    var vals = items.map(function (r) { return isNum(r[2]) ? Math.abs(r[2]) : 0; });
    var mx = Math.max.apply(null, vals.concat([0])) || 1;
    var o = ['<div class="bpanel"><h4>' + esc(title) + " <span>" + esc(lab) + "</span></h4>"];
    items.forEach(function (r, j) {
      if (j === 4) {
        o.push('<div class="bsep"></div>');
      }
      var v = r[2];
      var w = isNum(v) ? Math.abs(v) / mx * 50 : 0;
      var pos = isNum(v) && v < 0 ? "right:50%" : "left:50%";
      o.push('<div class="brow"><div class="bname">' + esc(r[0]) + '</div><div class="btrack">' +
        '<span class="zero"></span><span class="bfill ' + (isNum(v) && v < 0 ? "neg" : "pos") +
        '" style="' + pos + ";width:" + w.toFixed(2) + '%"></span></div><div class="bval ' + cls(v) + '">' +
        pct(v, 1) + "</div></div>");
    });
    o.push("</div>");
    return o.join("");
  }

  /* ---------------------------------------------------------------- generic blocks */
  function ledger(rows) {
    return '<div class="scroll"><table class="led">' + list(rows).map(function (r) {
      return '<tr><td class="t">' + rich(r[0]) + '</td><td class="n ' + signCls(r[1]) + '">' + rich(r[1]) +
        "</td><td>" + rich(r[2]) + "</td></tr>";
    }).join("") + "</table></div>";
  }

  function olist(items, klass) {
    return '<ol class="' + klass + '">' + list(items).map(function (x) {
      return "<li>" + rich(x) + "</li>";
    }).join("") + "</ol>";
  }

  function statebar(cells, big) {
    return '<div class="statebar' + (big ? " big" : "") + '">' + cells.map(function (c) {
      return "<div><span>" + esc(c[0]) + "</span><b>" + esc(c[1]) + "</b></div>";
    }).join("") + "</div>";
  }

  function tableIdx(head, rowsHtml, right, extra) {
    var h = list(head).map(function (x, i) {
      return "<th" + (right.indexOf(i) >= 0 ? ' class="rn"' : "") + ">" + esc(x) + "</th>";
    }).join("");
    return '<div class="scroll"><table class="idx ' + (extra || "") + '"><thead><tr>' + h +
      "</tr></thead><tbody>" + rowsHtml + "</tbody></table></div>";
  }

  /* ---------------------------------------------------------------- schematic */
  function figure(spec) {
    if (!spec || !Array.isArray(spec.items) || !Array.isArray(spec.ylim)) {
      return '<p class="schem">' + DASH + "</p>";
    }
    var y0 = spec.ylim[0];
    var y1 = spec.ylim[1];
    function X(x) {
      return X0 + x / 100 * (X1 - X0);
    }
    function Y(y) {
      return YB - (y - y0) / (y1 - y0) * (YB - YT);
    }
    function klass(c) {
      return c ? ' class="' + c + '"' : "";
    }
    var o = ['<svg class="tell" viewBox="0 0 1000 380" role="img" aria-label="' + esc(spec.aria) + '">'];
    spec.items.forEach(function (it) {
      var kind = it[0];
      var c = it[1];
      if (kind === "path") {
        var pts = [];
        for (var i = 0; i + 1 < it[2].length; i += 2) {
          pts.push(X(it[2][i]).toFixed(1) + "," + Y(it[2][i + 1]).toFixed(1));
        }
        o.push("<path" + klass(c) + ' d="M ' + pts.join(" L ") + '"/>');
      } else if (kind === "hline") {
        var y = Y(it[2]).toFixed(1);
        var a = X(it[3] === null ? 0 : it[3]).toFixed(1);
        var b = X(it[4] === null ? 100 : it[4]).toFixed(1);
        o.push("<line" + klass(c) + ' x1="' + a + '" x2="' + b + '" y1="' + y + '" y2="' + y + '"/>');
      } else if (kind === "vline") {
        var vx = X(it[2]).toFixed(1);
        o.push("<line" + klass(c) + ' x1="' + vx + '" x2="' + vx + '" y1="' + YT + '" y2="' + YB + '"/>');
      } else if (kind === "band") {
        var tp = Y(Math.max(it[2], it[3]));
        var bt = Y(Math.min(it[2], it[3]));
        o.push("<rect" + klass(c) + ' x="' + X0 + '" y="' + tp.toFixed(1) + '" width="' + (X1 - X0) +
          '" height="' + (bt - tp).toFixed(1) + '"/>');
      } else if (kind === "rect") {
        var rx0 = X(Math.min(it[2], it[4]));
        var rx1 = X(Math.max(it[2], it[4]));
        var ry0 = Y(Math.max(it[3], it[5]));
        var ry1 = Y(Math.min(it[3], it[5]));
        o.push("<rect" + klass(c) + ' x="' + rx0.toFixed(1) + '" y="' + ry0.toFixed(1) + '" width="' +
          (rx1 - rx0).toFixed(1) + '" height="' + (ry1 - ry0).toFixed(1) + '"/>');
      } else if (kind === "seg") {
        o.push("<line" + klass(c) + ' x1="' + X(it[2]).toFixed(1) + '" y1="' + Y(it[3]).toFixed(1) +
          '" x2="' + X(it[4]).toFixed(1) + '" y2="' + Y(it[5]).toFixed(1) + '"/>');
      } else if (kind === "text") {
        o.push("<text" + klass(c) + ' x="' + X(it[2]).toFixed(1) + '" y="' + Y(it[3]).toFixed(1) +
          '" text-anchor="' + (it[5] || "start") + '">' + esc(it[4]) + "</text>");
      } else if (kind === "callout") {
        var cx = X(it[2]);
        var cy = Y(it[3]);
        var lx = X(it[4]);
        var ly = Y(it[5]);
        var above = ly < cy;
        o.push('<ellipse class="mark" cx="' + cx.toFixed(1) + '" cy="' + cy.toFixed(1) + '" rx="20" ry="12"/>');
        o.push('<line class="lead" x1="' + cx.toFixed(1) + '" y1="' + (above ? cy - 12 : cy + 12).toFixed(1) +
          '" x2="' + lx.toFixed(1) + '" y2="' + (above ? ly + 5 : ly - 14).toFixed(1) + '"/>');
        o.push("<text" + klass(c) + ' x="' + lx.toFixed(1) + '" y="' + ly.toFixed(1) +
          '" text-anchor="middle">' + esc(it[6]) + "</text>");
      }
    });
    o.push("</svg>");
    return o.join("");
  }

  /* ---------------------------------------------------------------- issue sections */
  function stateCells(is, c) {
    var L = c.labels;
    var s = is.state || {};
    if (is.weekly) {
      var low = s.low || {};
      var fri = s.fri || {};
      return [
        ["SPY · " + txt(list(L.week_index_cols)[2]), pct(s.spy_week)],
        [L.state_votes, txt(low.env) + " " + scoreTxt(low.score) + " → " + txt(fri.env) + " " + scoreTxt(fri.score)],
        [L.state_conditions, (isNum(low.cond) ? low.cond : DASH) + " → " + (isNum(fri.cond) ? fri.cond : DASH)],
        [L.state_4pct, fixed(fri.up4, 0) + " / " + fixed(fri.down4, 0)]
      ];
    }
    return [
      [L.state_votes, txt(s.env) + " " + scoreTxt(s.score)],
      [L.state_conditions, (isNum(s.cond) ? s.cond : DASH) + " / 100"],
      [L.state_4pct, fixed(s.up4, 0) + " / " + fixed(s.down4, 0)],
      [L.state_adv, plusGrouped(s.net)]
    ];
  }

  function indexTable(is, c) {
    var rows = list(is.idx).map(function (a) {
      var n = (c.index_notes || {})[a.t] || ["", ""];
      var mid;
      if (is.weekly) {
        mid = Array.isArray(a.days) ? a.days.map(function (d) {
          return isNum(d) ? plus(d * 100, 1) : DASH;
        }).join(" ") : DASH;
      } else {
        mid = isNum(a.vol) ? a.vol.toFixed(2) + "×" : DASH;
      }
      return '<tr><td class="t">' + esc(a.t) + '</td><td class="n">' + grouped(a.last, 2) +
        '</td><td class="n ' + cls(a.chg) + '">' + pct(a.chg) + '</td><td class="n">' + mid +
        "</td><td>" + rich(n[0]) + "</td><td>" + rich(n[1]) + "</td></tr>";
    });
    list(c.extra_index_rows).forEach(function (r) {
      rows.push('<tr><td class="t">' + rich(r[0]) + '</td><td class="n">' + rich(r[1]) + '</td><td class="n">' +
        rich(r[2]) + '</td><td class="n">' + rich(r[3]) + "</td><td>" + rich(r[4]) + "</td><td>" +
        rich(r[5]) + "</td></tr>");
    });
    var head = is.weekly ? c.labels.week_index_cols : c.labels.index_cols;
    return tableIdx(head, rows.join(""), [1, 2, 3], is.weekly ? "wk" : "");
  }

  function tiles(is, c) {
    var t = list(is.idx).map(function (a) {
      var ev = ((c.index_notes || {})[a.t] || [""])[0];
      return '<div class="bi"><div class="bi-t">' + esc(a.t) + '</div><div class="bi-c ' + cls(a.chg) + '">' +
        pct(a.chg) + '</div><div class="bi-l">' + grouped(a.last, 2) + '</div><div class="bi-d">' + rich(ev) +
        "</div></div>";
    });
    list(c.extra_index_rows).forEach(function (r) {
      t.push('<div class="bi"><div class="bi-t">' + rich(r[0]) + '</div><div class="bi-c">' + rich(r[2]) +
        '</div><div class="bi-l">' + rich(r[1]) + '</div><div class="bi-d">' + rich(r[4]) + "</div></div>");
    });
    return '<div class="bigidx' + (t.length >= 6 ? " seven" : "") + '">' + t.join("") + "</div>";
  }

  function daysTable(is, c) {
    var rows = list(is.days).map(function (r) {
      var lab = txt(r[0]).slice(5) + (r[1] ? txt(c.labels.base_mark) : "");
      return '<tr><td class="t">' + esc(lab) + "</td><td>" + esc(r[2]) + " " + scoreTxt(r[3]) +
        '</td><td class="n">' + (isNum(r[4]) ? r[4] : DASH) + '</td><td class="n">' + fixed(r[5], 0) + " / " +
        fixed(r[6], 0) + '</td><td class="n">' + plusGrouped(r[7]) + '</td><td class="n">' +
        (isNum(r[8]) ? r[8].toFixed(1) + "%" : DASH) + '</td><td class="n">' + plus(r[9], 1) + "</td></tr>";
    });
    return tableIdx(c.labels.days_cols, rows.join(""), [2, 3, 4, 5, 6], "days");
  }

  function scorecard(is) {
    return '<div class="metrics">' + list(is.scorecard).map(function (s) {
      return "<div><span>" + esc(s[0]) + '</span><b class="' + cls(s[1]) + '">' + pct(s[1]) + "</b></div>";
    }).join("") + "</div>";
  }

  function weeklyK(is, c) {
    var k = is.weekly_k;
    if (!k) {
      return "";
    }
    var L = c.labels;
    var rows = list(k.names).map(function (n) {
      return '<tr><td class="t">' + esc(n[0]) + '</td><td class="n ' + cls(n[1]) + '">' + pct(n[1], 1) +
        '</td><td class="n ' + cls(n[2]) + '">' + pct(n[2], 1) + '</td><td class="n ' + cls(n[3]) + '">' +
        pct(n[3], 1) + "</td><td>" + (n[4] ? esc(L.yes) : "") + '</td><td class="n">' +
        (isNum(n[5]) ? n[5] : DASH) + "</td></tr>";
    }).join("");
    function names(xs) {
      return list(xs).map(function (t) { return txt(t[0]) + " " + pct(t[1], 1); }).join(" · ");
    }
    var rs = k.rs01 ? '<p class="prose"><b>' + esc(L.rs01_top) + "</b> " + esc(names(k.rs01.top)) +
      "<br><b>" + esc(L.rs01_bottom) + "</b> " + esc(names(k.rs01.bottom)) + "</p>" : "";
    return tableIdx(L.wk_cols, rows, [1, 2, 3, 5]) + '<p class="schem">' + esc(fill(L.wk_summary, k.summary || {})) +
      "</p>" + rs + '<p class="prose">' + rich(c.weekly_k_line) + "</p>";
  }

  function book(is, c, V) {
    var b = is.book;
    if (!b) {
      return "";
    }
    var L = c.labels;
    var cells = [
      [L.m_return, pct(isNum(b.ret) ? b.ret / 100 : null)],
      [L.m_cash, isNum(b.cash) ? b.cash.toFixed(1) + "%" : DASH],
      [L.m_open, isNum(b.open) ? String(b.open) : DASH],
      [L.m_closed, isNum(b.closed) ? String(b.closed) : DASH],
      [L.m_openR, sR(b.openR)],
      [L.m_realR, sR(b.realR)]
    ];
    var m = '<div class="metrics six">' + cells.map(function (x) {
      return "<div><span>" + esc(x[0]) + "</span><b>" + esc(x[1]) + "</b></div>";
    }).join("") + "</div>";
    var head = list(L.pos_cols).map(function (h, i) {
      return "<th" + (i === 3 ? ' class="rn"' : "") + ">" + esc(h) + "</th>";
    }).join("");
    var rows = list(b.pos).map(function (p) {
      return '<tr><td class="t">' + esc(p[0]) + "</td><td>" + esc(p[1] === "long" ? L.long : L.short) +
        "</td><td>" + esc(p[2]) + '</td><td class="n ' + cls(p[3]) + '">' + sR(p[3]) + "</td></tr>";
    }).join("");
    /* the legal line rides the book section, so it always prints at the foot of the last page */
    var legal = V && V.legal ? '<p class="legal">' + esc(V.legal) + ' <span class="m">' + esc(V.handle) +
      "</span> · " + esc(V.site) + "</p>" : "";
    return m + '<div class="scroll"><table class="book"><thead><tr>' + head + "</tr></thead><tbody>" + rows +
      '</tbody></table></div><p class="prose">' + rich(c.portfolio_note) + "</p>" + legal;
  }

  function boardRows(is, V) {
    var s = is.state || {};
    var rows = [
      [V.b_votes, txt(s.env) + " " + scoreTxt(s.score), ""],
      [V.b_cond, (isNum(s.cond) ? s.cond : DASH) + " / 100", ""]
    ];
    list(is.idx).slice(0, 3).forEach(function (a) {
      rows.push([a.t, pct(a.chg), cls(a.chg)]);
    });
    if (is.led) {
      rows.push([V.b_led, txt(is.led[0]) + " " + pct(is.led[1], 1), ""]);
    }
    if (is.paid) {
      rows.push([V.b_paid, txt(is.paid[0]) + " " + pct(is.paid[1], 1), ""]);
    }
    return rows.map(function (r) {
      return '<div class="brd-row"><span>' + esc(r[0]) + '</span><b class="' + r[2] + '">' + esc(r[1]) + "</b></div>";
    }).join("");
  }

  /* topic cards are review information: preview pages only, never in a member PDF */
  function eduPick(c, V) {
    if (printMode) {
      return "";
    }
    var chosen = (c.education && c.education.chosen) || "A";
    return '<div class="edu-pick">' + list(c.education && c.education.options).map(function (o) {
      var on = o.key === chosen;
      return '<div class="card ' + (on ? "on" : "off") + '"><div class="k">' + esc(o.key) + " · " +
        esc(on ? V.pick_on_word : V.pick_off_word) + "</div><b>" + esc(o.title) + "</b><p>" + esc(o.why) + "</p></div>";
    }).join("") + "</div>";
  }

  function mast(is, V) {
    return '<div class="mast"><span class="brand">FLUXUS CAPITAL</span><span>' +
      esc(is.weekly ? V.weekly : V.daily) + " · No. " + esc(is.no) + '</span></div><hr class="r ink">';
  }

  function folio(is, V, n, b, dl) {
    var mark = b ? '<span class="fl">' + dropSvg(dl, 2, "fmark", "", 4) + "</span>" : "";
    return '<div class="folio' + (b ? " b" : "") + '">' + mark + "<span>Fluxus Capital · " +
      esc(is.weekly ? V.weekly : V.daily) + "</span><span>" + n + " / 4</span></div>";
  }

  function sec(first, title, note, body, extra) {
    return '<section class="sec' + (first ? " first" : "") + (extra ? " " + extra : "") + '"><h3>' + esc(title) +
      (note ? ' <span class="h3n">' + esc(note) + "</span>" : "") + "</h3>" + body + "</section>";
  }

  /* ---------------------------------------------------------------- layout A · 登记体 */
  function layoutA(is, c, V) {
    var L = c.labels;
    var dl = dropLine(is.spx);
    var s = is.state || {};
    var nVotes = list(is.verd && is.verd.votes).length;
    var s1 = '<article class="sheet a">' + mast(is, V) + dropSvg(dl, 2.5, "thin", V.droparia) + regLine(is, dl) +
      '<h2 class="hl-a">' + esc(c.title) + '</h2><p class="byline">' + esc(c.subtitle) + "</p>" +
      sec(false, L.big_picture, "", '<p class="prose">' + rich(c.big_picture) + "</p>") +
      sec(false, L.index_action, "", safe(function () { return indexTable(is, c); })) +
      (is.weekly ? sec(false, V.score, "", safe(function () { return scorecard(is); })) : "") +
      folio(is, V, 1, false, dl) + "</article>";
    var fn = c.founders_note ? sec(false, V.founders, "", '<p class="prose">' + rich(c.founders_note) + "</p>", "note-blk") : "";
    var s2 = '<article class="sheet a">' + mast(is, V) +
      sec(true, L.market_state, "", safe(function () {
        return statebar(stateCells(is, c)) + '<div class="state-row" style="margin-top:14px"><span class="env">' +
          esc(s.env) + '</span><span class="score">' + scoreTxt(s.score) + "<small> / " + nVotes + " " +
          esc(V.votes) + "</small></span></div>" + voteStrip(is.verd, V) + legend(V) +
          '<p class="prose" style="margin-top:12px">' + rich(c.state_line) + "</p>";
      })) +
      (is.weekly ? sec(false, V.sessions, "", safe(function () { return daysTable(is, c); })) : "") +
      sec(false, L.conditions, (isNum(s.cond) ? s.cond : DASH) + " / 100", safe(function () { return condChart(is.cond, V); })) +
      fn +
      sec(false, V.ll, V.top3, safe(function () {
        return '<div class="lwrap">' + boardTable(is.groups.industry, L.industries, V) +
          boardTable(is.groups.theme, L.themes, V) + "</div>";
      })) +
      folio(is, V, 2, false, dl) + "</article>";
    var wk = is.weekly ? safe(function () { return weeklyK(is, c); }) : "";
    var s3 = '<article class="sheet a">' + mast(is, V) +
      sec(true, L.working, "", ledger(c.led)) +
      sec(false, L.laggards, "", ledger(c.lagged)) +
      (wk ? sec(false, L.weekly_k, "", wk) : "") +
      (c.sentiment ? sec(false, L.sentiment, "", '<p class="prose">' + rich(c.sentiment) + "</p>") : "") +
      sec(false, L.tomorrow, "", olist(c.tomorrow, "ol-a")) +
      sec(false, L.rules, "", olist(c.rules, "ol-a")) +
      folio(is, V, 3, false, dl) + "</article>";
    var edu = c.education || {};
    var bk = safe(function () { return book(is, c, V); });
    var s4 = '<article class="sheet a">' + mast(is, V) +
      sec(true, L.education, edu.title, eduPick(c, V) + '<p class="prose">' + rich(edu.body) + "</p>" +
        safe(function () { return figure(is.fig && is.fig[c.lang]); }) + '<p class="schem">' + esc(V.schem) + "</p>", "edu") +
      (bk ? sec(false, L.portfolio, "", bk, "book-sec") : "") +
      folio(is, V, 4, false, dl) + "</article>";
    return s1 + s2 + s3 + s4;
  }

  /* ---------------------------------------------------------------- layout B · 掉落体 */
  function layoutB(is, c, V) {
    var L = c.labels;
    var dl = dropLine(is.spx);
    var s = is.state || {};
    var nVotes = list(is.verd && is.verd.votes).length;
    var head = txt(c.title).split(/\s+—\s+|——/);
    var hl = head.map(esc).join("<br>");
    var cover = '<article class="sheet b cover"><div class="mast"><span class="brand">FLUXUS CAPITAL</span><span>' +
      esc((is.when || {})[c.lang]) + '</span></div><div class="hero">' + dropSvg(dl, 7, "hero", V.droparia) + "</div>" +
      regLine(is, dl) + '<hr class="r ink"><h2 class="hl-b">' + hl + '</h2><div class="cover-grid">' +
      '<p class="prose lead">' + rich(c.big_picture) + '</p><aside class="board"><div class="brd-h">' + esc(V.board) +
      "</div>" + safe(function () { return boardRows(is, V); }) + "</aside></div>" + folio(is, V, 1, true, dl) + "</article>";
    var s2 = '<article class="sheet b"><div class="kicker">' + esc(V.tape) + '</div><h3 class="hb">' + esc(L.index_action) +
      "</h3>" + safe(function () { return tiles(is, c); }) +
      (is.weekly ? '<div class="kicker sp">' + esc(V.score) + "</div>" + safe(function () { return scorecard(is); }) : "") +
      '<div class="kicker sp">' + esc(L.market_state) + "</div>" +
      safe(function () {
        return statebar(stateCells(is, c), true) + '<div class="state-b" style="margin-top:16px"><span class="env-b">' +
          esc(s.env) + '</span><span class="score-b">' + scoreTxt(s.score) + "<small>/ " + nVotes + "</small></span></div>" +
          voteStrip(is.verd, V, true) + legend(V) + '<p class="prose" style="margin-top:12px">' + rich(c.state_line) + "</p>";
      }) +
      (is.weekly ? '<div class="kicker sp">' + esc(V.sessions) + "</div>" + safe(function () { return daysTable(is, c); }) : "") +
      '<div class="kicker sp">' + esc(L.conditions) + " · <b>" + (isNum(s.cond) ? s.cond : DASH) + " / 100</b></div>" +
      safe(function () { return condChart(is.cond, V); }) + folio(is, V, 2, true, dl) + "</article>";
    var wk = is.weekly ? safe(function () { return weeklyK(is, c); }) : "";
    var g = is.groups || {};
    var s3 = '<article class="sheet b"><div class="split-b"><div><div class="kicker">' + esc(L.working) + "</div>" +
      ledger(c.led) + '</div><div><div class="kicker">' + esc(L.laggards) + "</div>" + ledger(c.lagged) + "</div></div>" +
      (c.sentiment ? '<div class="kicker sp">' + esc(L.sentiment) + '</div><p class="prose">' + rich(c.sentiment) + "</p>" : "") +
      '<div class="kicker sp">' + esc(V.rot_d) + '</div><div class="bars2">' +
      safe(function () { return barsPanel(g.industry && g.industry.d1, L.industries, V.d1); }) +
      safe(function () { return barsPanel(g.theme && g.theme.d1, L.themes, V.d1); }) + "</div>" +
      '<div class="kicker sp">' + esc(V.rot_w) + '</div><div class="bars2">' +
      safe(function () { return barsPanel(g.industry && g.industry.w1, L.industries, V.w1); }) +
      safe(function () { return barsPanel(g.theme && g.theme.w1, L.themes, V.w1); }) + "</div>" +
      (wk ? '<div class="kicker sp">' + esc(L.weekly_k) + "</div>" + wk : "") + folio(is, V, 3, true, dl) + "</article>";
    var edu = c.education || {};
    var bk = safe(function () { return book(is, c, V); });
    var left = (c.founders_note ? '<div class="kicker">' + esc(V.founders) + '</div><p class="prose">' +
      rich(c.founders_note) + '</p><div class="kicker sp">' : '<div class="kicker">') + esc(L.tomorrow) + "</div>" +
      olist(c.tomorrow, "ol-b") + (bk ? '<div class="kicker sp">' + esc(L.portfolio) + "</div>" + bk : "");
    var s4 = '<article class="sheet b"><div class="pull edu"><div class="kicker">' + esc(L.education) +
      '</div><h3 class="hb big">' + esc(edu.title) + "</h3>" + eduPick(c, V) + '<p class="prose lead">' + rich(edu.body) +
      "</p></div>" + safe(function () { return figure(is.fig && is.fig[c.lang]); }) + '<p class="schem">' + esc(V.schem) +
      '</p><div class="split-b" style="margin-top:34px"><div>' + left + '</div><div><div class="kicker">' + esc(L.rules) +
      "</div>" + olist(c.rules, "ol-b rules") + "</div></div>" + folio(is, V, 4, true, dl) + "</article>";
    return cover + s2 + s3 + s4;
  }

  /* ---------------------------------------------------------------- state + wiring */
  var app = document.getElementById("app");
  var DATA = null;
  try {
    DATA = JSON.parse(document.getElementById("recap-data").textContent);
  } catch (err) {
    DATA = null;
  }
  var layouts = (DATA && Array.isArray(DATA.layouts) && DATA.layouts.length) ? DATA.layouts : ["A", "B"];
  var storeKey = (DATA && DATA.store_key) || "fluxusRecapPage";
  var st = { issue: "", lang: "ZH", layout: layouts[0] };
  var themeParam = "";
  try {
    var saved = JSON.parse(window.localStorage.getItem(storeKey) || "{}");
    Object.keys(st).forEach(function (k) {
      if (saved[k]) {
        st[k] = saved[k];
      }
    });
  } catch (err) {
    /* storage unavailable: defaults */
  }
  String(window.location.hash || "").replace(/^#/, "").split("&").forEach(function (kv) {
    var p = kv.split("=");
    if (!p[0]) {
      return;
    }
    var v = decodeURIComponent(p[1] || "");
    if (Object.prototype.hasOwnProperty.call(st, p[0]) && v) {
      st[p[0]] = v;
    } else if (p[0] === "print") {
      printMode = true;
    } else if (p[0] === "theme") {
      themeParam = v;
    }
  });
  if (printMode) {
    themeParam = "light";
    document.documentElement.classList.add("print-mode");
  }
  if (themeParam) {
    document.documentElement.setAttribute("data-theme", themeParam);
  }

  var buttons = Array.prototype.slice.call(document.querySelectorAll("[data-set]"));

  function render() {
    if (!app) {
      return;
    }
    if (!DATA || !Array.isArray(DATA.issues) || !DATA.issues.length) {
      app.innerHTML = '<p class="prose">' + DASH + "</p>";
      return;
    }
    var is = DATA.issues.filter(function (x) { return x.tag === st.issue; })[0] || DATA.issues[0];
    st.issue = is.tag;
    var lang = (is.V && is.V[st.lang]) ? st.lang : "ZH";
    var c = is.V[lang];
    var V = (DATA.chrome && DATA.chrome[lang]) || {};
    var layout = printMode ? "A" : (layouts.indexOf(st.layout) >= 0 ? st.layout : layouts[0]);
    app.innerHTML = safe(function () {
      return layout === "B" ? layoutB(is, c, V) : layoutA(is, c, V);
    });
    app.setAttribute("data-rendered", is.tag + "|" + lang + "|" + layout);
    document.documentElement.lang = lang === "ZH" ? "zh-Hans" : "en";
    buttons.forEach(function (b) {
      b.setAttribute("aria-pressed", st[b.getAttribute("data-set")] === b.getAttribute("data-val") ? "true" : "false");
    });
    if (!printMode) {
      try {
        window.localStorage.setItem(storeKey, JSON.stringify(st));
      } catch (err) {
        /* ignore */
      }
    }
  }

  buttons.forEach(function (b) {
    b.addEventListener("click", function () {
      st[b.getAttribute("data-set")] = b.getAttribute("data-val");
      render();
    });
  });

  render();

  /* fonts are optional: the page is complete before they arrive; this only marks when they do */
  if (document.fonts && document.fonts.ready && document.fonts.ready.then) {
    document.fonts.ready.then(function () {
      document.documentElement.classList.add("fonts-ready");
    }, function () {
      /* fallback stacks already in use */
    });
  }
})();
