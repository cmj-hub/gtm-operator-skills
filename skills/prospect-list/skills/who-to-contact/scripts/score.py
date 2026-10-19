#!/usr/bin/env python3
"""Print a list score from a signal, or refuse a title-only list.

Stdlib only. No network. Does not send.

  python3 scripts/score.py --file gtm/list.json
  python3 scripts/score.py --stdin
  python3 scripts/score.py --file gtm/list.json --json

Each refusal line reads `- <what is wrong> -> <what to change>`; the last line
names the next step.

Exit codes: 0 scored, 1 refused (fix the draft), 2 unreadable input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


MAX_INPUT_BYTES = 2_000_000
MIN_SIGNAL_WORDS = 3

# The three slots a score can give. Aliases fold into the canonical slot.
SLOTS = {
    "call this week": "call this week",
    "call": "call this week",
    "hold": "hold",
    "drop": "drop",
}

# Labels that describe who someone is, not something they did.
PERSONA_LABELS = {
    "buyer",
    "champion",
    "decision maker",
    "decision-maker",
    "economic buyer",
    "good fit",
    "great fit",
    "high intent",
    "icp",
    "icp fit",
    "ideal customer",
    "in market",
    "in-market",
    "key account",
    "persona",
    "persona match",
    "qualified",
    "strong fit",
    "target account",
    "target persona",
}


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
    """Lowercase, drop punctuation, collapse whitespace."""
    return " ".join(re.sub(r"[^\w\s-]", " ", text.lower()).split())


def signal_problems(title: str, signal: str) -> list[str]:
    folded = fold(signal)
    if folded in PERSONA_LABELS:
        return ["signal is a persona label; write one thing they did this window"]
    if title and folded == fold(title):
        return ["signal repeats the title; write one thing they did this window"]
    if len(folded.split()) < MIN_SIGNAL_WORDS:
        return [f"signal is under {MIN_SIGNAL_WORDS} words; name the observable fact"]
    return []


def evaluate(data: dict) -> dict:
    title = nonempty_text(data.get("title"))
    signal = nonempty_text(data.get("signal"))
    raw_score = nonempty_text(data.get("score"))
    score = SLOTS.get(fold(raw_score), "")

    reasons: list[str] = []
    if not title:
        reasons.append("missing title; name the person")
    if not signal:
        reasons.append("missing signal (a title with no signal is a directory, not a list); write one thing they did this window, or leave them off")
    else:
        reasons.extend(signal_problems(title, signal))
    if not raw_score:
        reasons.append("missing score; give a slot: call this week, hold, or drop")
    elif not score:
        reasons.append("score is not a slot; use call this week, hold, or drop")

    if not reasons:
        verdict = "a list score from a signal"
    elif title and not signal:
        verdict = "a title-only list"
    else:
        verdict = "not a list score"

    return {
        "ok": not reasons,
        "verdict": verdict,
        "reasons": reasons,
        "title": title if not reasons else None,
        "signal": signal if not reasons else None,
        "score": score if not reasons else None,
    }


NEXT_PASS = "/cold-email:cold-email"
NEXT_FAIL = "fix the lines above and run this again."
EXAMPLE = (
    "Exit 0 scored, 1 refused, 2 unreadable input.\n\n"
    "example:\n  python3 scripts/score.py --file examples/list-good.json"
)


def split_reason(reason: str) -> tuple[str, str]:
    """Each reason reads 'what is wrong; what to change'."""
    wrong, _, fix = reason.partition("; ")
    return wrong, fix or "fix this field"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Score who to contact from one buying signal.",
        epilog=EXAMPLE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file", help="Path to a JSON object with title, signal, score (gtm/list.json)")
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
            print(f"title: {result['title']}")
            print(f"signal: {result['signal']}")
            print(f"score: {result['score']}")
        for reason in result["reasons"]:
            wrong, fix = split_reason(reason)
            print(f"- {wrong} → {fix}")
        print(f"Next: {result['next']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
