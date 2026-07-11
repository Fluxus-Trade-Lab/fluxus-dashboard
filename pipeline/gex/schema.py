# pipeline/gex/schema.py
"""gex.json v1 — the data contract every consumer reads."""

VERSION = 1
TENOR_REQUIRED = {"expiry", "net_gex_mm", "flip", "pin", "vol_trigger",
                  "call_wall", "put_wall", "wall_basis", "straddle", "atm_iv",
                  "walls_top_calls", "walls_top_puts", "greeks_coverage",
                  "quality", "delta_vs_prior", "converted"}
TOP_REQUIRED = {"version", "asof", "stale", "opex", "instruments", "read",
                "strategy_fit", "assumptions"}


def build_document(asof, stale, stale_reason, opex, instruments, read,
                   strategy_fit) -> dict:
    return {
        "version": VERSION, "asof": asof, "stale": stale,
        "stale_reason": stale_reason, "opex": opex,
        "instruments": instruments, "read": read,
        "strategy_fit": strategy_fit,
        "assumptions": {
            "dealer_side": "long calls / short puts (v1 baseline heuristic)",
            "gex_formula": "(cgamma*coi - pgamma*poi) * mult * spot^2 * 0.01",
        },
    }


def validate(doc: dict) -> None:
    missing = TOP_REQUIRED - set(doc)
    if missing:
        raise ValueError(f"gex.json missing top-level keys: {sorted(missing)}")
    if doc["version"] != VERSION:
        raise ValueError(f"unsupported version {doc['version']}")
    for sym, inst in doc["instruments"].items():
        for req in ("spot", "basis", "tenors"):
            if req not in inst:
                raise ValueError(f"{sym}: missing '{req}'")
        for tname, tenor in inst["tenors"].items():
            if tenor is None:
                continue  # tenor may be unavailable (e.g., no 0-2DTE expiry)
            miss = TENOR_REQUIRED - set(tenor)
            if miss:
                raise ValueError(f"{sym}.{tname}: missing {sorted(miss)}")
