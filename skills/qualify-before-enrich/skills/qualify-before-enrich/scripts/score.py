#!/usr/bin/env python3
"""Score list rows against ICP before any paid finder.

Stdlib only. No network. No paid APIs.

  python3 scripts/score.py --file gtm/qualify.json
  python3 scripts/score.py --stdin
  python3 scripts/score.py --file gtm/qualify.json --json

Each refusal line reads `- <what is wrong> -> <what to change>`; the last line
names the next step.

Exit codes: 0 scored (every enrich row passes ICP), 1 refused, 2 unreadable.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


MAX_INPUT_BYTES = 2_000_000

VERDICTS = {
    "enrich": "enrich",
    "hold": "hold",
    "drop": "drop",
}

# Flags that mean a paid lookup already happened or is queued on the row.
PAID_FLAGS = (
    "paid_lookup",
    "finder_ran",
    "enriched",
    "enrichment_spent",
    "credits_spent",
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
    return " ".join(re.sub(r"[^\w\s/-]", " ", text.lower()).split())


def as_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def truthy_flag(row: dict, key: str) -> bool:
    value = row.get(key)
    if value is True:
        return True
    if isinstance(value, (int, float)) and value != 0:
        return True
    if isinstance(value, str) and fold(value) in {"true", "yes", "1", "spent", "ran"}:
        return True
    return False


def paid_lookup_on_row(row: dict) -> bool:
    return any(truthy_flag(row, key) for key in PAID_FLAGS)


def normalize_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        text = nonempty_text(item)
        if text:
            out.append(text)
    return out


def icp_problems(icp: object) -> list[str]:
    if not isinstance(icp, dict):
        return ["missing icp; define industries, employee range, titles, and geos before any finder"]
    reasons: list[str] = []
    if not normalize_list(icp.get("industries")):
        reasons.append("icp.industries is empty; name the industries that pass")
    emp_min = as_int(icp.get("employee_min"))
    emp_max = as_int(icp.get("employee_max"))
    if emp_min is None or emp_max is None:
        reasons.append("icp employee range missing; set employee_min and employee_max")
    elif emp_min > emp_max:
        reasons.append("icp employee_min is above employee_max; swap or fix the range")
    includes = normalize_list(icp.get("titles_include"))
    excludes = normalize_list(icp.get("titles_exclude"))
    if not includes and not excludes:
        reasons.append("icp titles missing; set titles_include and/or titles_exclude")
    if not normalize_list(icp.get("geos")):
        reasons.append("icp.geos is empty; name the geos that pass")
    return reasons


def title_matches(title: str, needles: list[str]) -> bool:
    folded_title = fold(title)
    for needle in needles:
        folded = fold(needle)
        if not folded:
            continue
        if folded == folded_title or folded in folded_title:
            return True
    return False


def industry_matches(industry: str, allowed: list[str]) -> bool:
    folded = fold(industry)
    for item in allowed:
        target = fold(item)
        if folded == target or target in folded or folded in target:
            return True
    return False


def compute_slot(row: dict, icp: dict) -> tuple[str, list[str]]:
    """Return (expected_verdict, gaps). hold = incomplete; drop = fail; enrich = pass."""
    gaps: list[str] = []
    company = nonempty_text(row.get("company"))
    title = nonempty_text(row.get("title"))
    industry = nonempty_text(row.get("industry"))
    employees = as_int(row.get("employees"))
    geo = nonempty_text(row.get("geo"))

    if not company:
        gaps.append("missing company")
    if not title:
        gaps.append("missing title")
    if not industry:
        gaps.append("missing industry")
    if employees is None:
        gaps.append("missing employees")
    if not geo:
        gaps.append("missing geo")

    if gaps:
        return "hold", gaps

    fails: list[str] = []
    industries = normalize_list(icp.get("industries"))
    if not industry_matches(industry, industries):
        fails.append(f"industry '{industry}' is outside ICP")

    emp_min = as_int(icp.get("employee_min"))
    emp_max = as_int(icp.get("employee_max"))
    assert emp_min is not None and emp_max is not None
    if employees < emp_min or employees > emp_max:
        fails.append(f"employees {employees} outside {emp_min}-{emp_max}")

    includes = normalize_list(icp.get("titles_include"))
    excludes = normalize_list(icp.get("titles_exclude"))
    if excludes and title_matches(title, excludes):
        fails.append(f"title '{title}' is on titles_exclude")
    if includes and not title_matches(title, includes):
        fails.append(f"title '{title}' is not on titles_include")

    geos = normalize_list(icp.get("geos"))
    if fold(geo) not in {fold(g) for g in geos}:
        fails.append(f"geo '{geo}' is outside ICP")

    if fails:
        return "drop", fails
    return "enrich", []


def evaluate(data: dict) -> dict:
    reasons: list[str] = []
    icp = data.get("icp")
    reasons.extend(icp_problems(icp))

    rows = data.get("rows")
    if not isinstance(rows, list) or not rows:
        reasons.append("missing rows; add at least one list row to qualify")
        return {
            "ok": False,
            "verdict": "not a qualify pass",
            "reasons": reasons,
            "rows": [],
            "enrich_count": 0,
            "hold_count": 0,
            "drop_count": 0,
        }

    if reasons:
        return {
            "ok": False,
            "verdict": "not a qualify pass",
            "reasons": reasons,
            "rows": [],
            "enrich_count": 0,
            "hold_count": 0,
            "drop_count": 0,
        }

    assert isinstance(icp, dict)
    scored_rows: list[dict] = []
    enrich_count = hold_count = drop_count = 0

    for index, raw in enumerate(rows):
        label = f"row {index + 1}"
        if not isinstance(raw, dict):
            reasons.append(f"{label} is not an object; each row needs company, title, industry, employees, geo, verdict")
            continue

        company = nonempty_text(raw.get("company")) or label
        expected, gaps = compute_slot(raw, icp)
        claimed_raw = nonempty_text(raw.get("verdict"))
        claimed = VERDICTS.get(fold(claimed_raw), "")

        if expected == "enrich":
            enrich_count += 1
        elif expected == "hold":
            hold_count += 1
        else:
            drop_count += 1

        row_reasons: list[str] = []
        if not claimed_raw:
            row_reasons.append(f"{company}: missing verdict; set enrich, hold, or drop")
        elif not claimed:
            row_reasons.append(f"{company}: verdict is not a slot; use enrich, hold, or drop")
        elif claimed != expected:
            if expected == "hold":
                detail = ", ".join(gaps) if gaps else "incomplete fields"
                row_reasons.append(
                    f"{company}: claimed '{claimed}' on incomplete row ({detail}); set verdict to hold and fill fields before any finder"
                )
            elif expected == "drop":
                detail = "; ".join(gaps) if gaps else "fails ICP"
                row_reasons.append(
                    f"{company}: claimed '{claimed}' but row fails ICP ({detail}); set verdict to drop and skip paid lookup"
                )
            else:
                row_reasons.append(
                    f"{company}: claimed '{claimed}' but row passes ICP; set verdict to enrich"
                )

        if paid_lookup_on_row(raw) and expected != "enrich":
            row_reasons.append(
                f"{company}: paid lookup on a failing row; clear paid_lookup/finder flags and never spend credits until verdict is enrich"
            )

        reasons.extend(row_reasons)
        scored_rows.append(
            {
                "company": company,
                "expected": expected,
                "claimed": claimed or None,
                "gaps": gaps,
                "ok": not row_reasons,
            }
        )

    ok = not reasons
    if ok:
        verdict = "qualify pass — ICP before finder"
    elif any("paid lookup on a failing row" in r for r in reasons):
        verdict = "paid lookup on a failing row"
    else:
        verdict = "not a qualify pass"

    return {
        "ok": ok,
        "verdict": verdict,
        "reasons": reasons,
        "rows": scored_rows,
        "enrich_count": enrich_count,
        "hold_count": hold_count,
        "drop_count": drop_count,
    }


NEXT_PASS = "/prospect-list:who-to-contact"
NEXT_FAIL = "fix the lines above and run this again."
EXAMPLE = (
    "Exit 0 scored, 1 refused, 2 unreadable input.\n\n"
    "example:\n  python3 scripts/score.py --file examples/rows-good.json"
)


def split_reason(reason: str) -> tuple[str, str]:
    wrong, _, fix = reason.partition("; ")
    return wrong, fix or "fix this field"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Score list rows against ICP before any paid finder.",
        epilog=EXAMPLE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file", help="Path to JSON with icp + rows (gtm/qualify.json)")
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
        print(json.dumps(result, indent=2))
    else:
        print(result["verdict"])
        if result["ok"]:
            print(
                f"enrich: {result['enrich_count']}  hold: {result['hold_count']}  drop: {result['drop_count']}"
            )
            for row in result["rows"]:
                print(f"- {row['company']}: {row['expected']}")
        for reason in result["reasons"]:
            wrong, fix = split_reason(reason)
            print(f"- {wrong} → {fix}")
        print(f"Next: {result['next']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
