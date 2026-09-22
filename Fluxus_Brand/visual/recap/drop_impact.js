/* Fluxus drop impact — the landing mark of the SPX drop line. Visual line source, 2026-09-13.

   The line does not change. Where it lands, the sheet cracks once: a few radial cracks, a broken ring,
   a pinch of glass at the centre. Andy 09-13: 「我指的是最后的落点取代方案，原本的这条线不变」
   「来一点点特效，但不用特别夸张，表达到位就可以了」.

   Chance, not data. The crack is seeded by the issue tag ("0911"), so every issue breaks its own way and
   the same issue always breaks the same way. No market quantity drives it — the emotion-encoded endpoints
   were ruled out the same day (「落点这些方案不行」). Duchamp kept the cracks the Large Glass got in
   transit; the Stoppages let a metre of thread land where it landed. Same length, different shapes.

   Sizes are rendered CSS px, converted with pxPerUnit (rendered px per viewBox unit), so the crack reads
   the same at any line height. Stroke is non-scaling and colour comes from tokens — see drop_impact.css.

   dropImpact(dl, opts) → '<g class="impact">…</g>', appended inside the drop <svg> after the line's <path>
     dl         {d, h} from dropLine()
     opts.seed       issue tag string
     opts.level      "light" | "mid" | "heavy"      (default "mid")
     opts.tone       "ink" | "accent"                (default "ink")
     opts.pxPerUnit  for .drop.thin (46px tall): 46 / (dl.h + 2 * pad)
     opts.pad        the viewBox pad dropSvg used    (default 6)
*/
(function (root) {
  "use strict";

  var LEVELS = {
    light: { rays: 5, r: 14, rings: 0, shards: 3, branch: 0 },
    mid:   { rays: 7, r: 21, rings: 1, shards: 5, branch: 0.35 },
    heavy: { rays: 9, r: 29, rings: 2, shards: 8, branch: 0.55 }
  };

  function rng(seed) {
    var a = 2166136261 >>> 0;
    for (var i = 0; i < seed.length; i++) {
      a ^= seed.charCodeAt(i);
      a = Math.imul(a, 16777619) >>> 0;
    }
    return function () {
      a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function seg(points, width) {
    return '<path style="stroke-width:' + width + '" d="M ' + points.map(function (p) {
      return p[0].toFixed(2) + "," + p[1].toFixed(2);
    }).join(" L ") + '"/>';
  }

  function dropImpact(dl, opts) {
    opts = opts || {};
    var L = LEVELS[opts.level] || LEVELS.mid;
    var pad = opts.pad === undefined ? 6 : opts.pad;
    var u = 1 / (opts.pxPerUnit || 1);
    var rand = rng(String(opts.seed || "drop"));
    var pts = dl.d.replace(/^M\s*/, "").split(/\s*L\s*/);
    var end = pts[pts.length - 1].split(",").map(Number);
    var cx = end[0];
    var cy = end[1];
    /* px of room before a crack runs into the registry line below or the mast rule above */
    var below = (dl.h + pad - cy) / u + 7;
    var above = (cy + pad) / u + 10;
    var out = [];
    var rays = [];
    var step = 2 * Math.PI / L.rays;
    var off = rand() * step;
    var i;
    var k;

    for (i = 0; i < L.rays; i++) {
      var ang = off + i * step + (rand() - 0.5) * step * 0.7;
      var len = L.r * (0.5 + 0.5 * rand());
      var s = Math.sin(ang);
      var c = Math.cos(ang);
      if (s > 0.05) { len = Math.min(len, below / s); }
      if (s < -0.05) { len = Math.min(len, above / -s); }
      len = Math.max(len, 3);
      var p = [];
      var ts = [0.14, 0.42, 0.72, 1];
      for (k = 0; k < ts.length; k++) {
        var j = k === 0 ? 0 : (rand() - 0.5) * 2 * (0.6 + 1.2 * ts[k]);
        p.push([cx + (c * len * ts[k] - s * j) * u, cy + (s * len * ts[k] + c * j) * u]);
      }
      rays.push({ ang: ang, len: len });
      out.push(seg([p[0], p[1], p[2]], 1.1));
      out.push(seg([p[2], p[3]], 0.65));
      if (rand() < L.branch) {
        var ba = ang + (rand() < 0.5 ? -1 : 1) * (0.35 + 0.3 * rand());
        var bl = len * (0.25 + 0.2 * rand());
        out.push(seg([p[1], [p[1][0] + Math.cos(ba) * bl * u, p[1][1] + Math.sin(ba) * bl * u]], 0.55));
      }
    }

    /* the ring: jagged chords between neighbouring cracks, some missing */
    for (var r = 0; r < L.rings; r++) {
      var frac = 0.42 + r * 0.26;
      for (i = 0; i < rays.length; i++) {
        var A = rays[i];
        var B = rays[(i + 1) % rays.length];
        var skip = rand() < 0.35;
        var ra = L.r * frac;
        var rb = L.r * frac * (0.85 + 0.3 * rand());
        if (skip || ra > A.len || rb > B.len) { continue; }
        out.push(seg([
          [cx + Math.cos(A.ang) * ra * u, cy + Math.sin(A.ang) * ra * u],
          [cx + Math.cos(B.ang) * rb * u, cy + Math.sin(B.ang) * rb * u]
        ], 0.5));
      }
    }

    /* a pinch of glass where it hit */
    for (i = 0; i < L.shards; i++) {
      var sa = rand() * 2 * Math.PI;
      var sd = 0.8 + 2.2 * rand();
      var sx = cx + Math.cos(sa) * sd * u;
      var sy = cy + Math.sin(sa) * sd * u;
      var tri = [];
      for (k = 0; k < 3; k++) {
        var ta = sa + k * 2.1 + rand() * 0.8;
        var tr = 0.5 + 0.9 * rand();
        tri.push([sx + Math.cos(ta) * tr * u, sy + Math.sin(ta) * tr * u]);
      }
      out.push('<path class="shard" d="' + seg(tri, 0).replace(/^.*d="|"\/>$/g, "") + ' Z"/>');
    }

    var cls = opts.tone === "accent" ? "impact hot" : "impact";
    return '<g class="' + cls + '" style="transform-origin:' + cx.toFixed(1) + "px " + cy.toFixed(1) + 'px">' +
      out.join("") + "</g>";
  }

  dropImpact.LEVELS = LEVELS;
  root.dropImpact = dropImpact;
  if (typeof module === "object" && module.exports) { module.exports = dropImpact; }
})(typeof window !== "undefined" ? window : globalThis);
