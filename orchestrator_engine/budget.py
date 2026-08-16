"""check_budget — spend-cap arithmetic the model never does in its head."""

from __future__ import annotations


def check_budget(spent_usd: float, cap_usd: float | None, warn_ratio: float = 0.75) -> dict:
    """action: continue | warn | abort. cap None/0 = no cap (continue, noted)."""
    if not cap_usd or cap_usd <= 0:
        return {"ok": True, "action": "continue", "remaining_usd": None, "note": "no cap set"}
    remaining = round(cap_usd - spent_usd, 4)
    if spent_usd >= cap_usd:
        return {
            "ok": False,
            "action": "abort",
            "remaining_usd": remaining,
            "note": "cap reached — exit class ABORT, return partial state",
        }
    if spent_usd >= warn_ratio * cap_usd:
        return {
            "ok": True,
            "action": "warn",
            "remaining_usd": remaining,
            "note": "over warn threshold — finish in-flight slices, dispatch nothing new without human ok",
        }
    return {"ok": True, "action": "continue", "remaining_usd": remaining, "note": ""}
