#!/usr/bin/env python3
"""Score a cold offer: a leak, a prototype, and email one.

Stdlib only. No network. Does not send.

  python3 scripts/score.py --file gtm/offer.json
  python3 scripts/score.py --stdin
  python3 scripts/score.py --file gtm/offer.json --json
  python3 scripts/score.py --file gtm/offer.json --today 2026-10-04

Optional fields: `scope` (one deliverable) and `deadline` (YYYY-MM-DD; with
--today, not before it).

Each failing line reads `- <what is wrong> (<detail>) -> <what to change>`; the
last line names the next step.

Exit 0 when every check passes, 1 when a check fails, 2 on bad input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path


MAX_INPUT_BYTES = 2_000_000
MAX_EMAIL_WORDS = 120
FIELDS = ("leak", "prototype", "email_one")
# Optional. Scored only when the key is present and not null.
OPTIONAL = ("scope", "deadline")
MAX_SCOPE_WORDS = 12
ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
ONE_RE = re.compile(r"\b(?:one|single)\b", re.IGNORECASE)
# A list of deliverables: a comma, semicolon, plus, ampersand, or "and".
LIST_RE = re.compile(r"[,;+&]|\band\b", re.IGNORECASE)

# Email one sells the paid product when it asks the reader to buy it.
SELL_RE = re.compile(
    r"paid product|retainer|\bbook a demo\b|\bschedule a demo\b|"
    r"\bbuy (?:the|our)\b|\bpurchase\b|\bsubscribe\b|our pricing|"
    r"\bcheckout\b|core service|\bupsell\b|sign up for|"
    r"\bour (?:plans|packages|rates)\b|\bstart (?:the|an?) (?:engagement|subscription)\b",
    re.IGNORECASE,
)

# Email one asks for a meeting when it asks for the reader's time.
MEETING_RE = re.compile(
    r"\b(?:book|schedule|set up|grab|hop on|jump on) (?:a |some )?"
    r"(?:quick |short |brief )?(?:call|meeting|chat|time)\b|"
    r"\bquick (?:call|chat)\b|\bcalendly\b|\bcalendar link\b|"
    r"\b\d+[- ]?min(?:ute)?s? (?:call|chat|meeting)\b|"
    r"\b(?:do you have|got) \d+ minutes\b|\bfind (?:a )?time\b",
    re.IGNORECASE,
)

WORD_RE = re.compile(r"[a-z0-9']+")
STOPWORDS = frozenset(
    "about after again also because been before being does doing each from have "
    "into just more most only over same some such than that their them then "
    "there these they this those through under very what when where which while "
    "with would your yours you're it's".split()
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


def content_words(text: str) -> set[str]:
    words = set()
    for word in WORD_RE.findall(text.lower()):
        if len(word) < 4 or word in STOPWORDS:
            continue
        words.add(word[:-1] if word.endswith("s") and len(word) > 4 else word)
    return words


def matches(pattern: re.Pattern[str], text: str) -> list[str]:
    found = []
    for match in pattern.finditer(text):
        phrase = match.group(0).lower()
        if phrase not in found:
            found.append(phrase)
    return found


def parse_iso_date(value: str) -> date | None:
    """Return the date for a strict YYYY-MM-DD string, else None."""
    if not ISO_DATE_RE.fullmatch(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def names_one_deliverable(scope: str) -> bool:
    """Says one (or single), or is a short phrase with no list in it."""
    if ONE_RE.search(scope):
        return True
    return len(scope.split()) <= MAX_SCOPE_WORDS and not LIST_RE.search(scope)


def check(draft: dict[str, str], today: date | None = None) -> list[dict[str, str]]:
    """Return one failure per broken rule, most serious first.

    `scope` and `deadline` are checked only when the draft carries them.
    `today`, when given, makes a deadline before it fail.
    """
    failures = []
    email_one = draft["email_one"]

    sold = matches(SELL_RE, email_one)
    if sold:
        failures.append({
            "check": "sells",
            "message": "email one that sells the paid product",
            "detail": ", ".join(sold),
            "fix": "Cut the ask to buy. Offer the full report only if they want it.",
        })

    offer_sold = []
    for name in ("leak", "prototype", "scope"):
        found = matches(SELL_RE, draft.get(name, ""))
        offer_sold.extend(f"{name}: {phrase}" for phrase in found)
    if offer_sold:
        failures.append({
            "check": "offer_sells",
            "message": "the offer sells the paid product",
            "detail": ", ".join(offer_sold),
            "fix": "The leak and the prototype are free work. Cut the paid product out of them.",
        })

    asked = matches(MEETING_RE, email_one)
    if asked:
        failures.append({
            "check": "meeting",
            "message": "email one that asks for a meeting",
            "detail": ", ".join(asked),
            "fix": "Cut the meeting ask. Hand over the finding and stop.",
        })

    missing = [name for name in FIELDS + OPTIONAL if name in draft and not draft[name]]
    if missing:
        failures.append({
            "check": "complete",
            "message": "draft is incomplete",
            "detail": "missing " + ", ".join(missing),
            "fix": "Fill leak, prototype, and email_one with non-empty strings. Fill scope and deadline or leave them out.",
        })
        return failures

    leak_words = content_words(draft["leak"])
    shared = leak_words & content_words(email_one)
    need = min(3, (len(leak_words) + 1) // 2)
    if len(shared) < need:
        failures.append({
            "check": "finding",
            "message": "email one does not deliver the finding",
            "detail": f"shares {len(shared)} of {len(leak_words)} key words with the leak, needs {need}",
            "fix": "State the leak in email one, in the words the reader already uses.",
        })

    words = len(email_one.split())
    if words > MAX_EMAIL_WORDS:
        failures.append({
            "check": "length",
            "message": "email one is too long",
            "detail": f"{words} words, limit {MAX_EMAIL_WORDS}",
            "fix": "Cut to the finding, the prototype, and the offer of the report.",
        })

    if "scope" in draft and not names_one_deliverable(draft["scope"]):
        failures.append({
            "check": "scope",
            "message": "scope does not name one deliverable",
            "detail": f"no 'one', and a list or over {MAX_SCOPE_WORDS} words",
            "fix": "Name the one thing they get: one page, one sample, one worked slice.",
        })

    if "deadline" in draft:
        due = parse_iso_date(draft["deadline"])
        if due is None:
            failures.append({
                "check": "deadline",
                "message": "deadline is not a date",
                "detail": "use YYYY-MM-DD",
                "fix": "Write the deadline as a real calendar date, for example 2026-12-15.",
            })
        elif today is not None and due < today:
            failures.append({
                "check": "deadline",
                "message": "deadline is in the past",
                "detail": f"before {today.isoformat()}",
                "fix": "Set a deadline on or after today, or leave it out.",
            })

    return failures


NEXT_PASS = "/landing-page:page"
NEXT_FAIL = "fix the lines above and run this again."
EXAMPLE = "example:\n  python3 scripts/score.py --file examples/offer-good.json --today 2026-10-04"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Score a cold offer draft",
        epilog=EXAMPLE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file", help="Path to a JSON object (gtm/offer.json)")
    parser.add_argument("--input", dest="file", help=argparse.SUPPRESS)
    parser.add_argument("--stdin", action="store_true", help="Read a JSON object from stdin")
    parser.add_argument("--json", action="store_true", help="Print the result as one JSON object")
    parser.add_argument("--today", help="YYYY-MM-DD; a deadline before it fails")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    today = None
    if args.today is not None:
        today = parse_iso_date(args.today.strip())
        if today is None:
            fail_input("--today must be a YYYY-MM-DD date")
    data = load_payload(args)
    if not isinstance(data, dict):
        fail_input("JSON must be an object")

    draft = {name: nonempty_text(data.get(name)) for name in FIELDS}
    for name in OPTIONAL:
        if data.get(name) is not None:
            draft[name] = nonempty_text(data.get(name))
    failures = check(draft, today)
    step = NEXT_FAIL if failures else NEXT_PASS

    if args.json:
        print(json.dumps({"pass": not failures, "failures": failures, "next": step}, indent=2))
        return 1 if failures else 0

    if failures:
        for failure in failures:
            print(f"- {failure['message']} ({failure['detail']}) → {failure['fix']}")
        print(f"Next: {step}")
        return 1

    print(f"leak: {draft['leak']}")
    print(f"prototype: {draft['prototype']}")
    for name in OPTIONAL:
        if name in draft:
            print(f"{name}: {draft[name]}")
    print(f"email one: {draft['email_one']}")
    print(f"Next: {step}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
