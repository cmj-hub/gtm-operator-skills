#!/usr/bin/env python3
"""Score a lifecycle email: welcome, bargain, then nurture on the pain.

Stdlib only. No network. Does not send.

  python3 scripts/score.py --file gtm/sequence.json
  python3 scripts/score.py --stdin
  python3 scripts/score.py --file gtm/sequence.json --json

Each failing line reads `- <what is wrong> -> <what to change>`; the last line
names the next step.

Exit 0: welcome, bargain, and nurture pass.
Exit 1: refused (generic drip, cold email, pain mismatch, repeated notes or
subjects, no opt-in in the welcome) or incomplete.
Exit 2: the input could not be read as a JSON object.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


MAX_INPUT_BYTES = 2_000_000
REFUSAL = "a generic drip and a cold email"

DRIP_RE = re.compile(
    r"generic drip|\bday\s*1\b|\bday\s*3\b|\bday\s*7\b|tip series",
    re.IGNORECASE,
)
COLD_RE = re.compile(
    r"cold email|never opted|stranger|\bintroduce our\b|first touch",
    re.IGNORECASE,
)
OPT_IN_RE = re.compile(
    r"\b(?:asked|requested|opted|opt[- ]?in|signed up|sign[- ]?up|subscribed"
    r"|downloaded|registered|joined)\b",
    re.IGNORECASE,
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


FIELDS = ("pain", "welcome", "bargain", "nurture")
PARTS = ("welcome", "bargain", "nurture")
SUBJECTS = ("welcome_subject", "bargain_subject", "nurture_subject")
QUOTES = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'})


def nonempty_text(value: object) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return ""


def normalize(text: str) -> str:
    """Lowercase, straighten quotes, and collapse whitespace."""
    return " ".join(text.translate(QUOTES).lower().split())


def refused(blob: str) -> bool:
    return DRIP_RE.search(blob) is not None or COLD_RE.search(blob) is not None


def check(data: dict) -> tuple[dict, list[str]]:
    """Return the cleaned parts and every reason the draft fails, in gate order.

    Subjects are optional. Once any subject is given, all three are required.
    """
    parts = {key: nonempty_text(data.get(key)) for key in FIELDS + SUBJECTS}
    has_subjects = any(data.get(key) is not None for key in SUBJECTS)
    reasons = []
    scanned = PARTS + SUBJECTS if has_subjects else PARTS
    for key in scanned:
        for label, pattern in (("generic drip", DRIP_RE), ("cold email", COLD_RE)):
            match = pattern.search(parts[key])
            if match:
                reasons.append(f'{label}: {key} says "{match.group(0)}"')
    required = FIELDS + SUBJECTS if has_subjects else FIELDS
    missing = [key for key in required if not parts[key]]
    if missing:
        reasons.append("missing: " + ", ".join(missing))
    pain = normalize(parts["pain"]).rstrip(".!?;:, ")
    if pain and parts["nurture"] and pain not in normalize(parts["nurture"]):
        reasons.append("pain mismatch: nurture does not repeat the pain in their words")
    bodies = [normalize(parts[key]) for key in PARTS if parts[key]]
    if len(bodies) == len(PARTS) and len(set(bodies)) < len(PARTS):
        reasons.append("not three notes: welcome, bargain, and nurture repeat each other")
    if parts["welcome"] and not OPT_IN_RE.search(parts["welcome"]):
        reasons.append("no opt-in: welcome does not say they asked, opted in, or signed up")
    if has_subjects:
        subjects = [normalize(parts[key]) for key in SUBJECTS if parts[key]]
        if len(subjects) == len(SUBJECTS) and len(set(subjects)) < len(SUBJECTS):
            reasons.append("subjects repeat: each note needs its own subject")
        if pain and parts["nurture_subject"] and pain not in normalize(parts["nurture_subject"]):
            reasons.append("pain mismatch: nurture_subject does not name the pain in their words")
    return parts, reasons


NEXT_PASS = "/gtm:next"
NEXT_FAIL = "fix the lines above and run this again."
EXAMPLE = "example:\n  python3 scripts/score.py --file examples/lifecycle-good.json"
FIXES = (
    ("generic drip:", "drop the day-1/day-3/day-7 or tip-series framing; write to their pain"),
    ("cold email:", "they opted in; name what they asked for instead of introducing the product"),
    ("missing:", "fill each named field with text"),
    ("pain mismatch: nurture_subject", "put the pain phrase in nurture_subject, in their words"),
    ("pain mismatch:", "repeat the pain phrase inside nurture, in their words"),
    ("not three notes:", "write welcome, bargain, and nurture each for its own job"),
    ("no opt-in:", "say in the welcome that they asked, opted in, or signed up"),
    ("subjects repeat:", "give each note its own subject line"),
)


def fix_for(reason: str) -> str:
    for prefix, fix in FIXES:
        if reason.startswith(prefix):
            return fix
    return "fix this line"


def verdict(reasons: list[str]) -> str:
    if not reasons:
        return "pass"
    if all(reason.startswith("missing:") for reason in reasons):
        return "draft is incomplete"
    return REFUSAL


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Score a lifecycle email draft. Exit 0 pass, 1 refused or incomplete, 2 bad input.",
        epilog=EXAMPLE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--file", help="Path to a JSON object (gtm/sequence.json)")
    parser.add_argument("--input", dest="file", help=argparse.SUPPRESS)
    parser.add_argument("--stdin", action="store_true", help="Read a JSON object from stdin")
    parser.add_argument("--json", action="store_true", help="Print the result as one JSON object")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    data = load_payload(args)
    if not isinstance(data, dict):
        fail_input("JSON must be an object")

    parts, reasons = check(data)
    status = verdict(reasons)
    fixes = [fix_for(reason) for reason in reasons]
    step = NEXT_FAIL if reasons else NEXT_PASS

    if args.json:
        result = {"pass": not reasons, "verdict": status, "reasons": reasons}
        if not reasons:
            result.update({key: parts[key] for key in PARTS + SUBJECTS if parts[key]})
        result["fixes"] = fixes
        result["next"] = step
        print(json.dumps(result, ensure_ascii=False))
        return 0 if not reasons else 1

    if reasons:
        print(status)
        for reason, fix in zip(reasons, fixes):
            print(f"- {reason} → {fix}")
        print(f"Next: {step}")
        return 1

    for key in PARTS:
        subject = parts[f"{key}_subject"]
        if subject:
            print(f"{key} subject: {subject}")
        print(f"{key}: {parts[key]}")
    print(f"Next: {step}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
