#!/usr/bin/env python3
"""Score a buying signal: dated, linkable event — or refuse.

Stdlib only. No network. No paid APIs.

  python3 scripts/score.py --file gtm/signal.json
  python3 scripts/score.py --stdin
  python3 scripts/score.py --file examples/signal-good.json --json
  python3 scripts/score.py --file examples/signal-good.json --as-of 2026-10-08

A signal is a dated, linkable event. An intent score without a URL and a
date is refused. Firmographic state is not a signal.

Exit codes: 0 scored, 1 refused (fix the draft), 2 unreadable input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse


MAX_INPUT_BYTES = 2_000_000
MAX_AGE_DAYS = 90
MIN_EVENT_WORDS = 3

# State / costume language — who they are, not what they did.
FIRMOGRAPHIC_LABELS = {
    "b2b saas",
    "decision maker",
    "enterprise",
    "growing fast",
    "high intent",
    "icp",
    "icp fit",
    "in market",
    "in-market",
    "mid market",
    "mid-market",
    "persona",
    "series a",
    "series b",
    "series c",
    "target account",
    "vp marketing",
    "vp of marketing",
    "vp sales",
}

URL_RE = re.compile(r"^https?://", re.IGNORECASE)
DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


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


def parse_iso_date(value: str) -> date | None:
    match = DATE_RE.match(value)
    if not match:
        return None
    try:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except ValueError:
        return None


def url_ok(url: str) -> bool:
    if not URL_RE.match(url):
        return False
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return False
    if not parsed.netloc or "." not in parsed.netloc:
        return False
    return True


def has_intent_score(data: dict) -> bool:
    if "intent_score" not in data:
        return False
    value = data.get("intent_score")
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def event_problems(event: str) -> list[str]:
    folded = fold(event)
    if folded in FIRMOGRAPHIC_LABELS:
        return ["event is firmographic state; write a dated, linkable thing they did"]
    if len(folded.split()) < MIN_EVENT_WORDS:
        return [f"event is under {MIN_EVENT_WORDS} words; name the observable event"]
    return []


def evaluate(data: dict, as_of: date) -> dict:
    event = nonempty_text(data.get("event"))
    url = nonempty_text(data.get("url"))
    raw_date = nonempty_text(data.get("date"))
    company = nonempty_text(data.get("company"))
    intent = has_intent_score(data)

    reasons: list[str] = []

    if intent and (not url or not raw_date):
        reasons.append(
            "intent score without a URL and a date; add both url and date, or drop intent_score"
        )

    if not event:
        reasons.append("missing event; write the dated, linkable thing they did")
    else:
        reasons.extend(event_problems(event))

    if not url:
        reasons.append("missing url; a signal without a link is not a signal")
    elif not url_ok(url):
        reasons.append("url is not a public http(s) link; paste the page you can open")

    parsed_date: date | None = None
    if not raw_date:
        reasons.append("missing date; a signal without a date is not a signal")
    else:
        parsed_date = parse_iso_date(raw_date)
        if parsed_date is None:
            reasons.append("date is not YYYY-MM-DD; use an ISO date like 2026-09-28")
        elif parsed_date > as_of:
            reasons.append("date is in the future; use the day the event was published")
        else:
            age = (as_of - parsed_date).days
            if age > MAX_AGE_DAYS:
                reasons.append(
                    f"date is older than {MAX_AGE_DAYS} days; find a fresher linkable event"
                )

    if not reasons:
        verdict = "a dated, linkable signal"
    elif intent and (not url or not raw_date):
        verdict = "intent without a link and a date"
    elif event and not url and not raw_date:
        verdict = "an undated, unlinkable claim"
    else:
        verdict = "not a signal"

    return {
        "ok": not reasons,
        "verdict": verdict,
        "reasons": reasons,
        "event": event if not reasons else None,
        "url": url if not reasons else None,
        "date": raw_date if not reasons else None,
        "company": company if not reasons else None,
        "age_days": (as_of - parsed_date).days if (not reasons and parsed_date) else None,
        "as_of": as_of.isoformat(),
    }


NEXT_PASS = "/psp:psp"
NEXT_FAIL = "fix the lines above and run this again."
EXAMPLE = (
    "Exit 0 scored, 1 refused, 2 unreadable input.\n\n"
    "example:\n  python3 scripts/score.py --file examples/signal-good.json"
)


def split_reason(reason: str) -> tuple[str, str]:
    wrong, _, fix = reason.partition("; ")
    return wrong, fix or "fix this field"


def parse_as_of(value: str | None) -> date:
    if not value:
        return date.today()
    parsed = parse_iso_date(value.strip())
    if parsed is None:
        fail_input("--as-of must be YYYY-MM-DD")
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Score a dated, linkable buying signal.",
        epilog=EXAMPLE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--file",
        help="Path to a JSON object with event, url, date (gtm/signal.json)",
    )
    parser.add_argument("--input", dest="file", help=argparse.SUPPRESS)
    parser.add_argument("--stdin", action="store_true", help="Read the JSON object from stdin")
    parser.add_argument("--json", action="store_true", help="Print the result as one JSON object")
    parser.add_argument(
        "--as-of",
        help="Score freshness against this YYYY-MM-DD (default: today)",
    )
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    data = load_payload(args)
    if not isinstance(data, dict):
        fail_input("JSON must be an object")

    as_of = parse_as_of(args.as_of)
    result = evaluate(data, as_of)
    result["fixes"] = [split_reason(reason)[1] for reason in result["reasons"]]
    result["next"] = NEXT_PASS if result["ok"] else NEXT_FAIL

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["verdict"])
        if result["ok"]:
            if result["company"]:
                print(f"company: {result['company']}")
            print(f"event: {result['event']}")
            print(f"url: {result['url']}")
            print(f"date: {result['date']}")
            print(f"age_days: {result['age_days']}")
        for reason in result["reasons"]:
            wrong, fix = split_reason(reason)
            print(f"- {wrong} → {fix}")
        print(f"Next: {result['next']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
