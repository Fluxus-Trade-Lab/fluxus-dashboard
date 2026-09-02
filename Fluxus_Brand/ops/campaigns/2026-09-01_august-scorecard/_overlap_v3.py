#!/usr/bin/env python3
"""V3 vs flagship verbatim-overlap measurement.

Metrics (both reported, gate used both in 06_gate_review.md):
  A. 8-gram overlap  = share of the variant's 8-gram POSITIONS that also occur in the flagship
  B. token coverage  = share of the variant's TOKENS that sit inside some shared >=8-word run
  C. longest common contiguous run (in words)

Normalisation: lowercase -> every non [a-z0-9] becomes a space -> split on whitespace.
Markdown table pipes, dashes, em-dashes and quotes therefore vanish, so a table row and a
prose sentence are compared on words alone.

POSITIVE CONTROL is mandatory: the round-1 V3 (still in 05_distribution.md) must come back
around 26.7% / 41.3%.  A检验 that cannot report a positive tells you nothing when it reports
a negative (Growth Gary, 08-25).
"""
import re, sys, pathlib

CAMP = pathlib.Path("/var/folders/ck/n06ysb_13c1367dlllfzn6yw0000gn/T/tmp.w0RaW3bokE/wt-campaign/"
                    "Fluxus_Brand/ops/campaigns/2026-09-01_august-scorecard")
SCRATCH = pathlib.Path("/private/tmp/claude-501/-Users-taolezhu-Documents-AI-Trading-System/"
                       "f7361e2f-bf81-4643-b176-7c6d0dc7d26c/scratchpad")
N = 8

def norm(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).split()

def git_text(rev_path):
    """Read a file at a git revision (used for the round-1 positive control)."""
    import subprocess
    return subprocess.run(["git", "show", rev_path], capture_output=True, text=True,
                          check=True, cwd=str(CAMP)).stdout

def quoted_block(src, start_pat, end_pat):
    """Pull the '> ' body lines of one '### Vn' section. src = Path or raw text."""
    text = src.read_text(encoding="utf-8") if hasattr(src, "read_text") else src
    lines = text.splitlines()
    out, on = [], False
    for ln in lines:
        if re.match(start_pat, ln):
            on = True; continue
        if on and re.match(end_pat, ln):
            break
        if on and ln.startswith(">"):
            out.append(ln.lstrip(">").strip())
    return "\n".join(out)

def grams(toks, n=N):
    return [tuple(toks[i:i+n]) for i in range(len(toks) - n + 1)]

def measure(var_toks, ref_toks):
    ref = set(grams(ref_toks))
    g = grams(var_toks)
    hit = [tuple(x) in ref for x in g]
    covered = set()
    for i, h in enumerate(hit):
        if h:
            covered.update(range(i, i + N))
    # longest contiguous run: extend greedily over consecutive hit 8-grams
    longest, run_start, best = 0, None, (0, 0)
    i = 0
    while i < len(hit):
        if hit[i]:
            j = i
            while j + 1 < len(hit) and hit[j + 1]:
                j += 1
            length = (j - i) + N          # words spanned by consecutive matching 8-grams
            if length > longest:
                longest, best = length, (i, i + length)
            i = j + 1
        else:
            i += 1
    pct_g = 100.0 * sum(hit) / len(g) if g else 0.0
    pct_t = 100.0 * len(covered) / len(var_toks) if var_toks else 0.0
    return pct_g, pct_t, longest, best

flag_toks = norm((CAMP / "04_flagship.md").read_text(encoding="utf-8"))

targets = {
    "NEW V3 (rebuilt from 03_angle.md brief)":
        (SCRATCH / "v3_body.md").read_text(encoding="utf-8"),
    # ⚠️ 阳性对照必须取 origin/main 上的第 1 轮 V3。工作区那份已被重建稿覆盖，
    # 若仍从工作区取，阳性对照会变成拿新稿当阳性样本 → 报 0.0% → 检验自称失明。
    "POSITIVE CONTROL: round-1 V3 (origin/main 05_distribution.md)":
        quoted_block(git_text("origin/main:Fluxus_Brand/ops/campaigns/"
                              "2026-09-01_august-scorecard/05_distribution.md"),
                     r"^### V3 ", r"^### V4 "),
    "NEGATIVE-SIDE REFERENCE: V2 (gate measured 0.0%)":
        quoted_block(CAMP / "05_distribution.md", r"^### V2 ", r"^### V3 "),
    "NEGATIVE-SIDE REFERENCE: V4 (gate measured 0.0%)":
        quoted_block(CAMP / "05_distribution.md", r"^### V4 ", r"^## "),
}

print(f"reference = 04_flagship.md, {len(flag_toks)} normalised tokens")
print(f"n-gram size = {N}\n")
print(f"{'variant':52} {'words':>6} {'8gram%':>8} {'token%':>8} {'longest':>8}")
print("-" * 88)
rows = {}
for name, raw in targets.items():
    t = norm(raw)
    pg, pt, lg, span = measure(t, flag_toks)
    rows[name] = (t, pg, pt, lg, span)
    print(f"{name:52} {len(t):6d} {pg:7.1f}% {pt:7.1f}% {lg:7d}")

print("\n--- positive-control check ---")
_, pg, pt, lg, _ = rows["POSITIVE CONTROL: round-1 V3 (origin/main 05_distribution.md)"]
ok = pg > 15.0
print(f"round-1 V3 reports {pg:.1f}% 8-gram / {pt:.1f}% token coverage / longest {lg} words")
print("PASS - the check demonstrably reports a positive." if ok else
      "FAIL - the check is blind; fix the script before trusting any negative.")

print("\n--- new V3 verdict (target < 5% 8-gram) ---")
t, pg, pt, lg, span = rows["NEW V3 (rebuilt from 03_angle.md brief)"]
print(f"8-gram overlap {pg:.1f}%  |  token coverage {pt:.1f}%  |  longest shared run {lg} words")
if lg:
    print("longest shared run text: " + " ".join(t[span[0]:span[1]]))
print("PASS" if pg < 5.0 else "FAIL")

print("\n--- new V3 vs its sibling variants (independence, same metric) ---")
for tag, pat in (("V1", (r"^### V1 ", r"^### V2 ")), ("V2", (r"^### V2 ", r"^### V3 ")),
                 ("V4", (r"^### V4 ", r"^## "))):  # V5 第 2 轮已撤下
    sib = norm(quoted_block(CAMP / "05_distribution.md", *pat))
    spg, spt, slg, _ = measure(t, sib)
    print(f"  new V3 vs {tag}: 8-gram {spg:.1f}%  token {spt:.1f}%  longest {slg}")

import os, time
st = os.stat(CAMP / "04_flagship.md")
print("\nflagship fingerprint at measurement time: "
      + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.st_mtime))
      + f" / {st.st_size} bytes  ("
        "re-run this script if the flagship changes again)")
