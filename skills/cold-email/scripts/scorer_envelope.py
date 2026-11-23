"""Stdlib adapter for result_envelope/v1. Synced to installed skills by check-shared.mjs.

The envelope describes local rubric checks, not the truth of submitted claims.
Canonical field shapes live beside this module in result-envelope/index.d.ts.
"""
from datetime import datetime, timezone
import hashlib
import json

VERSION = "scorer-envelope/1"
RESERVED = {"summary", "status", "confidence", "abstain", "unknowns", "assumptions",
            "evidence", "limits", "next_action", "receipt", "result"}


def _lookup(data, path):
    for key in path.split("."):
        if isinstance(data, dict):
            data = data.get(key)
        elif isinstance(data, list) and key.isdigit() and int(key) < len(data):
            data = data[int(key)]
        else:
            return None
    return data


def envelope(result, *, tool, inputs, passed, as_of=None, unknowns=None,
             assumptions=None, evidence=None, next_action=None):
    """Status follows the caller's code decision; input metadata cannot set it.

    Unknown paths address the emitted envelope, e.g. result.rows.0.score.
    Confidence is unmeasured because a rubric score is not a calibrated probability.
    Only code-supplied evidence is exported; legacy evidence stays under result.
    """
    unknowns = [] if unknowns is None else unknowns
    assumptions = [] if assumptions is None else assumptions
    evidence = [] if evidence is None else evidence
    if type(passed) is not bool:
        raise ValueError("passed must be a code-derived boolean")
    if as_of is None:
        as_of = datetime.now(timezone.utc).date().isoformat()
    action = next_action or result.get("next") or "Review the local rubric report."
    if not isinstance(action, str) or not action.strip():
        raise ValueError("next_action must be one non-empty string")
    action = action.strip().removeprefix("Next:").strip()
    fixes = result.get("fixes") or []
    fixes = [item for item in fixes if isinstance(item, str) and item.strip()]
    reasons = result.get("reasons") or []
    reasons = [item for item in reasons if isinstance(item, str) and item.strip()]
    abstain = None if passed else {
        "reason": reasons[0] if reasons else "The draft failed the local rubric checks.",
        "closest": "The available local rubric report is in result.",
        "to_collect": fixes or ["Review the scorer flags and supply the missing inputs."],
    }
    encoded = json.dumps({"inputs": inputs, "as_of": as_of, "assumptions": assumptions},
                         sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode("utf-8")
    env = {
        "summary": ("Local rubric checks passed; source claims are unverified." if passed else
                    "Local rubric checks refused this draft; review the flags and collect the missing inputs."),
        "result": result,
        "status": "abstain" if abstain else "partial" if unknowns else "ok",
        "confidence": {"value": None, "basis": "unmeasured"},
        "abstain": abstain,
        "unknowns": unknowns,
        "assumptions": assumptions,
        "evidence": evidence,
        "limits": ["Local rubric checks only; passing does not verify submitted claims.",
                   "Confidence is unmeasured; rubric scores are not outcome probabilities."],
        "next_action": action,
        "receipt": {"tool": tool, "version": VERSION, "model": None,
                    "inputs_hash": hashlib.sha256(encoded).hexdigest(),
                    "cost": 0, "as_of": as_of},
    }
    # Preserve legacy keys unless the canonical envelope owns their names.
    env.update({key: value for key, value in result.items() if key not in RESERVED})
    for item in unknowns:
        if not isinstance(item, dict) or not item.get("field") or not item.get("why"):
            raise ValueError("unknown must have field and why")
        if _lookup(env, item["field"]) is not None:
            raise ValueError("unknown field must be absent or null: " + item["field"])
    return env
