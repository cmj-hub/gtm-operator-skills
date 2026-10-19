#!/usr/bin/env python3
"""Score proof assets: a claim the buyer can check, with permission to use it.

Stdlib only. No network. Reads the draft you hand it and nothing else.

  python3 scripts/score_proof.py --file gtm/proof.json
  python3 scripts/score_proof.py --stdin
  python3 scripts/score_proof.py --file examples/proof-good.json --as-of 2026-10-17 --json

The draft is a list of assets:

  {"assets": [{"id": "a1", "type": "result", "claim": "...",
               "metric": "time to first reply", "before": "2 days", "after": "4 hours",
               "timeframe": "first 60 days", "who": "Head of Sales, 30-person software company",
               "named": false, "permission": "written", "source": "...",
               "date": "2026-09-30"}]}

type is result, testimonial, metric or logo. permission is written,
public, verbal or none.

Refused: a result with no before and after, a multiple with no two
numbers behind it, no timeframe, no source, no date or a stale one, a
named buyer or logo without written or public permission, any asset
with no permission at all, and a
testimonial that is praise with nothing in it.

Exit codes: 0 pass, 1 refused (fix the draft), 2 unreadable input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

MAX_INPUT_BYTES = 2_000_000
TYPES = ("result", "testimonial", "metric", "logo")
PERMISSIONS = ("written", "public", "verbal", "none")
DEFAULT_MAX_AGE_MONTHS = 24
DIGIT_RE = re.compile(r"\d")
DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
MULTIPLE_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*x\b|\b(doubled|tripled|quadrupled|halved|10x|2x|3x)\b", re.I
)
EMPTY_PRAISE = (
    "game changer",
    "game-changer",
    "amazing",
    "incredible",
    "transformed",
    "transformative",
    "best decision",
    "highly recommend",
    "great to work with",
    "exceeded expectations",
    "world-class",
    "a pleasure",
    "can't recommend enough",
)


def fail_input(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def read_payload(args: argparse.Namespace) -> dict:
    if bool(args.file) == bool(args.stdin):
        fail_input("pass --file or --stdin")
    if args.stdin:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    else:
        path = Path(args.file)
        if not path.is_file():
            fail_input(f"file not found: {path}")
        if path.stat().st_size > MAX_INPUT_BYTES:
            fail_input("file is too large")
        raw = path.read_bytes()
    if len(raw) > MAX_INPUT_BYTES:
        fail_input("input is too large")
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail_input("input is not UTF-8 JSON")
    if not isinstance(data, dict):
        fail_input("draft is not a JSON object")
    return data


def text(value: object) -> str:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return value.strip() if isinstance(value, str) else ""


def parse_date(value: str) -> date | None:
    match = DATE_RE.match(value)
    if not match:
        return None
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


def months_between(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + (end.month - start.month) - (end.day < start.day)


def check_asset(asset: dict, index: int, today: date, max_age: int) -> list[str]:
    aid = text(asset.get("id")) or f"a{index}"
    kind = text(asset.get("type")).lower()
    fixes: list[str] = []
    if kind not in TYPES:
        return [f"{aid} has type {kind or 'none'} → use one of {', '.join(TYPES)}"]
    claim = text(asset.get("claim"))
    if not claim:
        fixes.append(f"{aid} has no claim → write the one sentence the buyer will read")

    if kind in ("result", "metric"):
        before, after = text(asset.get("before")), text(asset.get("after"))
        if kind == "result" and (not before or not after):
            fixes.append(
                f"{aid} is a result with no before and after → a result is a change:"
                " give both numbers, with the unit"
            )
        if not text(asset.get("metric")):
            fixes.append(f"{aid} names no metric → say what was measured, e.g. time to first reply")
        if not DIGIT_RE.search(claim + before + after):
            fixes.append(f"{aid} has no number → add it, or call it a testimonial")
        if MULTIPLE_RE.search(claim) and not (DIGIT_RE.search(before) and DIGIT_RE.search(after)):
            fixes.append(
                f"{aid} claims a multiple with no two numbers behind it"
                " → show before and after; the reader does the division"
            )
        if not text(asset.get("timeframe")):
            fixes.append(f"{aid} has no timeframe → say over how long, e.g. first 60 days")

    if kind == "testimonial":
        quote = claim.lower()
        if any(p in quote for p in EMPTY_PRAISE) and not DIGIT_RE.search(claim):
            fixes.append(
                f"{aid} is praise with nothing in it → ask them what changed, and quote the"
                " sentence with the number or the task in it"
            )

    if not text(asset.get("source")):
        fixes.append(
            f"{aid} has no source → name what a reader could be shown: a report, a dashboard"
            " export, an email, a public page"
        )

    named = asset.get("named") is True or kind == "logo"
    permission = text(asset.get("permission")).lower()
    if permission not in PERMISSIONS:
        fixes.append(f"{aid} has no permission → record one of {', '.join(PERMISSIONS)}")
    elif permission == "none":
        fixes.append(
            f"{aid} has no permission at all → ask before you use it, even unnamed;"
            " a buyer can recognise their own numbers"
        )
    elif named and permission not in ("written", "public"):
        fixes.append(
            f"{aid} names the buyer with {permission} permission → get it in writing,"
            " or drop the name and describe the role and company size instead"
        )
    if not text(asset.get("who")) and kind != "logo":
        fixes.append(f"{aid} says nothing about who → a role and a kind of company, at least")

    raw_date = text(asset.get("date"))
    when = parse_date(raw_date)
    if when is None:
        fixes.append(f"{aid} has no ISO date → when was this measured or said, YYYY-MM-DD")
    elif when > today:
        fixes.append(f"{aid} is dated in the future → use the day it was measured or said")
    elif months_between(when, today) > max_age:
        fixes.append(
            f"{aid} is {months_between(when, today)} months old → confirm it is still true,"
            " re-date it, or retire it"
        )
    return fixes


def score(data: dict, today: date, max_age: int) -> dict:
    assets = data.get("assets")
    if not isinstance(assets, list) or not assets:
        fail_input("assets is empty: list at least one proof asset")
    fixes: list[str] = []
    for index, asset in enumerate(assets, start=1):
        if not isinstance(asset, dict):
            fail_input(f"asset {index} is not an object")
        fixes.extend(check_asset(asset, index, today, max_age))
    passed = not fixes
    nxt = (
        "Next: /landing-page:page for the proof block; /founder-brand:founder-brand for a"
        " proof post; /cold-email:cold-email for one line of it."
        if passed
        else "Next: fix the lines above and run this again."
    )
    return {"pass": passed, "assets": len(assets), "fixes": fixes, "next": nxt}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="score_proof",
        description="Score proof assets: checkable, permitted, dated.",
        epilog="Example: python3 scripts/score_proof.py --file examples/proof-good.json --as-of 2026-10-17",
    )
    parser.add_argument("--file", help="path to gtm/proof.json")
    parser.add_argument("--stdin", action="store_true", help="read the draft from stdin")
    parser.add_argument("--as-of", help="score as of this ISO date (tests and demos)")
    parser.add_argument(
        "--max-age-months", type=int, default=DEFAULT_MAX_AGE_MONTHS,
        help=f"older proof is refused (default {DEFAULT_MAX_AGE_MONTHS})",
    )
    parser.add_argument("--json", action="store_true", help="print one JSON object")
    args = parser.parse_args(argv)

    today = date.today()
    if args.as_of:
        parsed = parse_date(args.as_of)
        if parsed is None:
            fail_input("--as-of is not YYYY-MM-DD")
        today = parsed
    if args.max_age_months < 1:
        fail_input("--max-age-months must be 1 or more")

    result = score(read_payload(args), today, args.max_age_months)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result["pass"]:
            print(f"pass: {result['assets']} proof asset(s) a buyer can check")
        else:
            print(f"refused: {len(result['fixes'])} fix(es) across {result['assets']} asset(s)")
            for fix in result["fixes"]:
                print(f"- {fix}")
        print(result["next"])
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
