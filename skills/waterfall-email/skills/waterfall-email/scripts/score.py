#!/usr/bin/env python3
"""Score a cheapest-first email waterfall.

Stdlib only. No network. Does not spend or send.

  python3 scripts/score.py --file gtm/waterfall-email.json
  python3 scripts/score.py --stdin
  python3 scripts/score.py --file draft.json --json

Exit codes: 0 scored, 1 refused (fix the draft), 2 unreadable input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


MAX_INPUT_BYTES = 2_000_000

ON_4XX_OK = {"fix_input", "stop"}
ON_4XX_BANNED = {
    "retry_next_vendor",
    "retry next vendor",
    "retry_next",
    "retry next",
    "continue",
    "next_vendor",
    "next vendor",
}

VERIFY_OK = {
    "deliverable",
    "catch-all",
    "catchall",
    "unknown",
    "invalid",
    "risky",
    "unverified",
}
VERIFY_SENDABLE = {"deliverable"}

PAID_HINTS = (
    "finder",
    "paid",
    "premium",
    "enrich",
    "apollo",
    "hunter",
    "clearbit",
    "zoominfo",
    "rocketreach",
    "lusha",
    "snov",
    "dropcontact",
    "prospeo",
    "cognism",
)


def fail_input(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def read_text(path: Path) -> str:
    try:
        if not path.exists():
            fail_input("file not found")
        if not path.is_file():
            fail_input("not a file")
        if path.stat().st_size > MAX_INPUT_BYTES:
            fail_input("file is too large")
        raw = path.read_bytes()
    except SystemExit:
        raise
    except OSError:
        fail_input("cannot read file")
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        fail_input("file is not UTF-8 text")


def load_payload(args: argparse.Namespace) -> object:
    if args.file and args.stdin:
        fail_input("pass --file or --stdin, not both")
    if args.stdin:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            fail_input("input is too large")
        if raw.startswith(b"\xef\xbb\xbf"):
            raw = raw[3:]
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            fail_input("input is not UTF-8 text")
    elif args.file:
        text = read_text(Path(args.file))
    else:
        fail_input("pass --file or --stdin")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        fail_input("invalid JSON")


def nonempty_text(value: object) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return ""


def fold(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s-]", " ", text.lower()).split())


def text_list(value: object) -> list[str] | None:
    if not isinstance(value, list) or not value:
        return None
    items: list[str] = []
    for item in value:
        text = nonempty_text(item)
        if not text:
            return None
        items.append(text)
    return items


def looks_paid(step: str) -> bool:
    folded = fold(step)
    if folded == "verify" or folded.startswith("verify "):
        return False
    return any(hint in folded for hint in PAID_HINTS)


def as_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        folded = fold(value)
        if folded in {"true", "yes", "1"}:
            return True
        if folded in {"false", "no", "0"}:
            return False
    return None


def evaluate(data: dict) -> dict:
    person = nonempty_text(data.get("person"))
    field = nonempty_text(data.get("field")) or "work_email"
    held = text_list(data.get("inputs_held"))
    order = text_list(data.get("cascade_order"))
    on_4xx_raw = nonempty_text(data.get("on_4xx"))
    on_4xx = fold(on_4xx_raw).replace(" ", "_") if on_4xx_raw else ""
    rows = data.get("rows")

    reasons: list[str] = []

    if not person:
        reasons.append("missing person; name who you are finding for")
    if held is None:
        reasons.append(
            "missing inputs_held; list CRM email, domain, or pattern before any finder"
        )
    if order is None:
        reasons.append(
            "missing cascade_order; write the checks cheapest-first and end with verify"
        )

    if not on_4xx_raw:
        reasons.append("missing on_4xx; set fix_input or stop")
    elif on_4xx in {fold(x).replace(" ", "_") for x in ON_4XX_BANNED} or on_4xx in ON_4XX_BANNED:
        reasons.append(
            "on_4xx retries the next vendor; set on_4xx to fix_input or stop"
        )
    elif on_4xx not in ON_4XX_OK:
        reasons.append("on_4xx must be fix_input or stop; do not retry the next vendor")

    if held is not None and order is not None:
        held_folded = [fold(item) for item in held]
        order_folded = [fold(item) for item in order]
        for name in held_folded:
            if name not in order_folded:
                reasons.append(
                    f"held input missing from cascade_order ({name}); put every inputs_held step in the cascade"
                )
                break
        else:
            positions = [order_folded.index(name) for name in held_folded]
            first_paid = next(
                (i for i, step in enumerate(order) if looks_paid(step)), None
            )
            if first_paid is not None and any(pos > first_paid for pos in positions):
                reasons.append(
                    "paid finder before held inputs; put every inputs_held name first in cascade_order"
                )
            if max(positions) >= first_paid if first_paid is not None else False:
                # covered above; keep structure clear
                pass
        if not any(fold(step) == "verify" or fold(step).startswith("verify ") for step in order):
            reasons.append("cascade_order has no verify step; add verify at the end")

    if not isinstance(rows, list) or not rows:
        reasons.append("missing rows; add one row per person with verify and sendable")
    else:
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                reasons.append(f"row {index} is not an object; use id, email, verify, sendable")
                continue
            row_id = nonempty_text(row.get("id")) or f"row-{index}"
            email = nonempty_text(row.get("email"))
            verify_raw = nonempty_text(row.get("verify"))
            verify = fold(verify_raw).replace(" ", "-") if verify_raw else ""
            if verify == "catchall":
                verify = "catch-all"
            sendable = as_bool(row.get("sendable"))

            if email and not verify_raw:
                reasons.append(
                    f"{row_id}: found email with no verify; set verify before sendable"
                )
            elif verify_raw and verify not in VERIFY_OK and verify != "catch-all":
                reasons.append(
                    f"{row_id}: verify is not a bucket; use deliverable, catch-all, unknown, invalid, risky, or unverified"
                )
            if sendable is None:
                reasons.append(
                    f"{row_id}: missing sendable; true only when verify is deliverable"
                )
            elif sendable is True and verify not in VERIFY_SENDABLE:
                reasons.append(
                    f"{row_id}: found is not sendable until verify = deliverable; set sendable false or re-verify"
                )

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for reason in reasons:
        if reason not in seen:
            seen.add(reason)
            unique.append(reason)
    reasons = unique

    if not reasons:
        verdict = "a cheapest-first waterfall with deliverable verify"
    elif any("next vendor" in r for r in reasons):
        verdict = "a 4xx retry onto the next vendor"
    elif any("sendable until verify" in r for r in reasons):
        verdict = "a found address marked sendable before deliverable verify"
    elif any("paid finder before held" in r for r in reasons):
        verdict = "a paid-first cascade"
    else:
        verdict = "not a waterfall route"

    return {
        "ok": not reasons,
        "verdict": verdict,
        "reasons": reasons,
        "person": person if not reasons else None,
        "field": field if not reasons else None,
        "on_4xx": on_4xx if not reasons else None,
        "cascade_order": order if not reasons else None,
    }


NEXT_PASS = "/cold-email:cold-email on sendable rows only"
NEXT_FAIL = "fix the lines above and run this again."
EXAMPLE = (
    "Exit 0 scored, 1 refused, 2 unreadable input.\n\n"
    "example:\n  python3 scripts/score.py --file examples/waterfall-good.json"
)


def split_reason(reason: str) -> tuple[str, str]:
    wrong, _, fix = reason.partition("; ")
    return wrong, fix or "fix this field"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Score a cheapest-first email waterfall.",
        epilog=EXAMPLE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--file",
        help="Path to a JSON waterfall draft (gtm/waterfall-email.json)",
    )
    parser.add_argument("--input", dest="file", help=argparse.SUPPRESS)
    parser.add_argument("--stdin", action="store_true", help="Read the JSON object from stdin")
    parser.add_argument("--json", action="store_true", help="Print the result as one JSON object")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    data = load_payload(args)
    if not isinstance(data, dict):
        fail_input("JSON must be an object")

    result = evaluate(data)
    result["fixes"] = [split_reason(reason)[1] for reason in result["reasons"]]
    result["next"] = NEXT_PASS if result["ok"] else NEXT_FAIL

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["ok"] else 1

    if result["ok"]:
        print(f"person: {result['person']}")
        print(f"field: {result['field']}")
        print(f"on_4xx: {result['on_4xx']}")
        print("cascade order: " + ", ".join(result["cascade_order"] or []))
        print(f"verdict: {result['verdict']}")
        print(f"Next: {NEXT_PASS}")
        return 0

    print(result["verdict"])
    for reason in result["reasons"]:
        wrong, fix = split_reason(reason)
        print(f"- {wrong} → {fix}")
    print(f"Next: {NEXT_FAIL}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
