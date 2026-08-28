"""Every count that appears in results.md, computed here rather than eyeballed.

Round 1 of this study shipped five wrong counts (9 read as 10, 6 as 5, 12 as
13 twice, 11/11 as 8/11). Each was a number I read off a printout instead of
computing. So the counts now come from one place and the prose quotes it.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = json.load(open(HERE / "results.json"))
M = json.load(open(HERE / "results_adr_matched.json"))
INC = R["included"]
SIG = 0.05


def sig(d):
    return d.get("p_holm") is not None and d["p_holm"] < SIG


def pos(d):
    return d.get("delta") is not None and d["delta"] > 0


def measurable(d):
    return d.get("p") is not None


f = {}
tr, ho = R["train"], R["holdout"]

f["n_included"] = len(INC)
f["excluded"] = R["excluded"]
f["n_measurable_train"] = sum(1 for s in INC if measurable(tr[s]["M1_median_excess"]))

# --- M1 -----------------------------------------------------------------
f["M1_sig_pos"] = [s for s in INC if sig(tr[s]["M1_median_excess"]) and pos(tr[s]["M1_median_excess"])]
f["M1_sig_neg"] = [s for s in INC if sig(tr[s]["M1_median_excess"]) and not pos(tr[s]["M1_median_excess"])]
f["M1_not_sig"] = [s for s in INC if measurable(tr[s]["M1_median_excess"]) and not sig(tr[s]["M1_median_excess"])]
f["M1_unmeasurable"] = [s for s in INC if not measurable(tr[s]["M1_median_excess"])]
f["M1_holdout_sig_neg"] = [s for s in INC if measurable(ho[s]["M1_median_excess"])
                           and ho[s]["M1_median_excess"]["p"] < SIG
                           and ho[s]["M1_median_excess"]["delta"] < 0]
f["M1_train_sig_pos_and_holdout_same_sign"] = [
    s for s in f["M1_sig_pos"] if measurable(ho[s]["M1_median_excess"])
    and ho[s]["M1_median_excess"]["delta"] > 0]

# --- raw amplitude ------------------------------------------------------
f["M2_sig_pos"] = [s for s in INC if sig(tr[s]["M2_median_abs"]) and pos(tr[s]["M2_median_abs"])]
f["M2_sig_neg"] = [s for s in INC if sig(tr[s]["M2_median_abs"]) and not pos(tr[s]["M2_median_abs"])]
f["M3_sig_pos"] = [s for s in INC if sig(tr[s]["M3_right_tail_10pct"]) and pos(tr[s]["M3_right_tail_10pct"])]

# --- naive normalisation (round 1, now known to be confounded) ----------
f["M2r_sig_pos_train"] = [s for s in INC if sig(tr[s]["M2r_median_abs_R"]) and pos(tr[s]["M2r_median_abs_R"])]
both = [s for s in INC if measurable(tr[s]["M2r_median_abs_R"]) and measurable(ho[s]["M2r_median_abs_R"])]
f["M2r_measurable_both_splits"] = both
f["M2r_same_sign_both_splits"] = [
    s for s in both if (tr[s]["M2r_median_abs_R"]["delta"] > 0) == (ho[s]["M2r_median_abs_R"]["delta"] > 0)]
f["M2r_holdout_raw_p_lt_05"] = [s for s in both if ho[s]["M2r_median_abs_R"]["p"] < SIG]
f["M3r_sig_pos_train"] = [s for s in INC if sig(tr[s]["M3r_right_tail_2R"]) and pos(tr[s]["M3r_right_tail_2R"])]
f["M3r_holdout_sign_flip"] = [
    s for s in f["M3r_sig_pos_train"] if measurable(ho[s]["M3r_right_tail_2R"])
    and ho[s]["M3r_right_tail_2R"]["delta"] < 0]
f["M3r_holdout_same_sign"] = [
    s for s in f["M3r_sig_pos_train"] if measurable(ho[s]["M3r_right_tail_2R"])
    and ho[s]["M3r_right_tail_2R"]["delta"] > 0]

# --- guards -------------------------------------------------------------
pc = R["positive_control"]
f["pc_caught_at_1pp"] = [s for s in INC if pc[s]["+1.0pp"]["p"] is not None and pc[s]["+1.0pp"]["p"] < SIG]
f["pc_not_caught_at_1pp"] = [s for s in INC if pc[s]["+1.0pp"]["p"] is None or pc[s]["+1.0pp"]["p"] >= SIG]
fpr = R["false_positive_rate"]
f["fpr_in_band"] = [s for s in INC if fpr[s]["share_p_lt_.05"] is not None
                    and 0.04 <= fpr[s]["share_p_lt_.05"] <= 0.06]
f["fpr_out_of_band"] = {s: fpr[s]["share_p_lt_.05"] for s in INC
                        if s not in f["fpr_in_band"]}

# --- ADR-matched (round 2) ---------------------------------------------
S = M["screeners"]
f["adr_curve"] = M["adr_curve"]


def msig(s, split, tag):
    d = S.get(s, {}).get(split, {}).get(tag, {})
    return d.get("p_holm") is not None and d["p_holm"] < SIG and d["delta"] > 0


def msame(s, tag):
    a = S.get(s, {}).get("train", {}).get(tag, {})
    b = S.get(s, {}).get("holdout", {}).get(tag, {})
    return (a.get("delta") is not None and b.get("delta") is not None
            and (a["delta"] > 0) == (b["delta"] > 0))


f["A_sig_train"] = [s for s in INC if msig(s, "train", "A_curve_divide")]
f["B_sig_train"] = [s for s in INC if msig(s, "train", "B_decile_matched")]
f["AB_sig_train"] = [s for s in f["A_sig_train"] if s in f["B_sig_train"]]
f["AB_sig_train_and_A_holdout_same_sign"] = [s for s in f["AB_sig_train"] if msame(s, "A_curve_divide")]
f["A_holdout_sig"] = [s for s in INC if msig(s, "holdout", "A_curve_divide")]
f["naive_only"] = [s for s in f["M2r_sig_pos_train"] if s not in f["AB_sig_train"]]

json.dump(f, open(HERE / "facts.json", "w"), indent=1)
for k, v in f.items():
    print(f"{k:42s} {len(v) if isinstance(v,(list,dict)) else v}  {v if isinstance(v,list) and len(v)<9 else ''}")
