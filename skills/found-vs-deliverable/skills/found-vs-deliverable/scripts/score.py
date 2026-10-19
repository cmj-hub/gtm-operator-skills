#!/usr/bin/env python3
"""Score a found-vs-deliverable verify row, or refuse a sendable catch-all.

Stdlib only. No network. Does not send. Does not call a verifier API.

  python3 scripts/score.py --file gtm/verify.json
  python3 scripts/score.py --stdin
  python3 scripts/score.py --file gtm/verify.json --json

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

# Canonical buckets. Aliases fold into the canonical name.
BUCKETS = {
    "deliverable": "deliverable",
    "valid": "deliverable",
    "ok": "deliverable",
    "safe": "deliverable",
    "catch-all": "catch-all",
    "catchall": "catch-all",
    "catch_all": "catch-all",
    "catch all": "catch-all",
    "unknown": "unknown",
    "unverifiable": "unknown",
    "unverified": "unknown",
    "invalid": "invalid",
    "bad": "invalid",
    "bounce": "invalid",
    "undeliverable": "invalid",
}

STAGES = {
    "found": "found",
    "raw": "found",
    "discovered": "found",
    "verified": "verified",
    "verify": "verified",
    "checked": "verified",
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
    """Lowercase, drop punctuation noise, collapse whitespace."""
    return " ".join(re.sub(r"[^\w\s-]", " ", text.lower()).replace("_", " ").split())


def as_bool(value: object) -> tuple[bool | None, str]:
    """Return (bool_or_None, raw_display). None means missing/unreadable."""
    if isinstance(value, bool):
        return value, "true" if value else "false"
    if isinstance(value, str) and value.strip():
        folded = fold(value)
        if folded in {"true", "yes", "y", "1", "send", "sendable"}:
            return True, value.strip()
        if folded in {"false", "no", "n", "0", "hold", "drop", "skip"}:
            return False, value.strip()
        return None, value.strip()
    if value is None:
        return None, ""
    return None, str(value)


def email_ok(email: str) -> list[str]:
    if "@" not in email or " " in email:
        return ["email is not shaped like an address; write local@domain"]
    local, _, domain = email.partition("@")
    if not local or not domain or "." not in domain:
        return ["email is not shaped like an address; write local@domain"]
    return []


def evaluate(data: dict) -> dict:
    email = nonempty_text(data.get("email"))
    raw_stage = nonempty_text(data.get("stage"))
    raw_bucket = nonempty_text(data.get("bucket"))
    # Accept alias key "verify" for bucket.
    if not raw_bucket:
        raw_bucket = nonempty_text(data.get("verify"))
    sendable_bool, raw_sendable = as_bool(data.get("sendable"))

    stage = STAGES.get(fold(raw_stage), "")
    bucket = BUCKETS.get(fold(raw_bucket), "")

    reasons: list[str] = []
    if not email:
        reasons.append("missing email; name the address you found")
    else:
        reasons.extend(email_ok(email))

    if not raw_stage:
        reasons.append("missing stage; use found or verified")
    elif not stage:
        reasons.append("stage is not a slot; use found or verified")

    if not raw_bucket:
        reasons.append(
            "missing bucket; use deliverable, catch-all, unknown, or invalid"
        )
    elif not bucket:
        reasons.append(
            "bucket is not a slot; use deliverable, catch-all, unknown, or invalid"
        )

    if raw_sendable == "" and data.get("sendable") is None:
        reasons.append("missing sendable; set true only when verify = deliverable")
    elif sendable_bool is None:
        reasons.append("sendable is not a boolean; use true or false")

    # Banned: never send catch-all / unknown / invalid / found as sendable.
    if bucket == "catch-all" and sendable_bool is True:
        reasons.append(
            "catch-all marked sendable (never send catch-all as valid); set sendable false and leave the row in catch-all"
        )
    if bucket == "unknown" and sendable_bool is True:
        reasons.append(
            "unknown marked sendable; set sendable false until a verify returns deliverable"
        )
    if bucket == "invalid" and sendable_bool is True:
        reasons.append(
            "invalid marked sendable; set sendable false and drop or fix the address"
        )
    if stage == "found" and sendable_bool is True:
        reasons.append(
            "found marked sendable (found is not sendable until verify = deliverable); run verify, then set stage verified only if bucket is deliverable"
        )
    if stage == "verified" and bucket == "deliverable" and sendable_bool is False:
        reasons.append(
            "verified deliverable with sendable false; set sendable true, or move the row to a hold bucket outside this gate"
        )
    if stage == "verified" and bucket != "deliverable" and bucket and sendable_bool is False:
        # Correct hold — allowed. No extra reason.
        pass
    if stage == "found" and sendable_bool is False and bucket:
        # Still in find; not sendable. Allowed as a held found row.
        pass

    sendable_pass = (
        stage == "verified" and bucket == "deliverable" and sendable_bool is True
    )
    held_pass = sendable_bool is False and bool(stage) and bool(bucket) and (
        stage == "found" or bucket in {"catch-all", "unknown", "invalid"}
    )

    if not reasons:
        if sendable_pass:
            verdict = "a deliverable verify"
        elif held_pass:
            if stage == "found":
                verdict = "a held found row"
            else:
                verdict = f"a held {bucket} row"
        else:
            reasons.append(
                "row is neither deliverable nor a held bucket; set stage verified + bucket deliverable + sendable true, or keep sendable false"
            )
            verdict = "not a deliverable verify"
    elif bucket == "catch-all" and sendable_bool is True:
        verdict = "a catch-all marked valid"
    elif stage == "found" and sendable_bool is True:
        verdict = "a found row marked sendable"
    elif bucket == "unknown" and sendable_bool is True:
        verdict = "an unknown marked valid"
    elif bucket == "invalid" and sendable_bool is True:
        verdict = "an invalid marked valid"
    else:
        verdict = "not a deliverable verify"

    ok = not reasons
    return {
        "ok": ok,
        "verdict": verdict,
        "reasons": reasons,
        "email": email if ok else None,
        "stage": stage if ok else None,
        "bucket": bucket if ok else None,
        "sendable": sendable_bool if ok else None,
    }



NEXT_SEND = "/cold-email:cold-email"
NEXT_HOLD = "keep the row in its bucket; do not send until verify = deliverable."
NEXT_FAIL = "fix the lines above and run this again."
EXAMPLE = (
    "Exit 0 scored, 1 refused, 2 unreadable input.\n\n"
    "example:\n  python3 scripts/score.py --file examples/verify-good.json"
)


def split_reason(reason: str) -> tuple[str, str]:
    """Each reason reads 'what is wrong; what to change'."""
    wrong, _, fix = reason.partition("; ")
    return wrong, fix or "fix this field"


def next_step(result: dict) -> str:
    if not result["ok"]:
        return NEXT_FAIL
    if result.get("sendable") is True:
        return NEXT_SEND
    return NEXT_HOLD


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Score found-vs-deliverable: find then verify before send.",
        epilog=EXAMPLE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--file",
        help="Path to a JSON object with email, stage, bucket, sendable (gtm/verify.json)",
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
    result["next"] = next_step(result)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["verdict"])
        if result["ok"]:
            print(f"email: {result['email']}")
            print(f"stage: {result['stage']}")
            print(f"bucket: {result['bucket']}")
            print(f"sendable: {str(result['sendable']).lower()}")
        for reason in result["reasons"]:
            wrong, fix = split_reason(reason)
            print(f"- {wrong} → {fix}")
        print(f"Next: {result['next']}")
    return 0 if result["ok"] else 1



if __name__ == "__main__":
    sys.exit(main())
