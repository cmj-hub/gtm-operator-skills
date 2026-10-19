#!/usr/bin/env python3
"""Score an inbound-from-domain route card, or refuse CRM write-back.

Stdlib only. No network. Does not write to a CRM. Does not call a paid API.

  python3 scripts/score.py --file gtm/inbound.json
  python3 scripts/score.py --stdin
  python3 scripts/score.py --file gtm/inbound.json --json

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
MIN_EVIDENCE = 1

KINDS = {
    "corporate": "corporate",
    "company": "corporate",
    "work": "corporate",
    "free-mail": "free-mail",
    "freemail": "free-mail",
    "free_mail": "free-mail",
    "free mail": "free-mail",
    "consumer": "free-mail",
    "disposable": "disposable",
    "temp": "disposable",
    "throwaway": "disposable",
    "personal-looking": "personal-looking",
    "personal": "personal-looking",
    "personal_looking": "personal-looking",
}

ROUTES = {
    "high-touch": "high-touch",
    "high_touch": "high-touch",
    "high touch": "high-touch",
    "self-serve": "self-serve",
    "self_serve": "self-serve",
    "self serve": "self-serve",
    "need-more": "need-more",
    "need_more": "need-more",
    "need more": "need-more",
    "more": "need-more",
    "personal": "personal",
    "disqualify": "disqualify",
    "dq": "disqualify",
    "drop": "disqualify",
}

# Domains that are free-mail providers (local allowlist for the sample loop).
# The pack does not fetch a live list; agents may extend this in their draft.
FREE_MAIL = {
    "gmail.com",
    "googlemail.com",
    "yahoo.com",
    "yahoo.co.uk",
    "hotmail.com",
    "outlook.com",
    "live.com",
    "msn.com",
    "icloud.com",
    "me.com",
    "mac.com",
    "aol.com",
    "proton.me",
    "protonmail.com",
    "pm.me",
    "gmx.com",
    "gmx.net",
    "mail.com",
    "yandex.com",
    "zoho.com",
}

DISPOSABLE = {
    "mailinator.com",
    "guerrillamail.com",
    "10minutemail.com",
    "tempmail.com",
    "trashmail.com",
    "yopmail.com",
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
    return " ".join(re.sub(r"[^\w\s-]", " ", text.lower()).replace("_", " ").split())


def as_bool(value: object) -> tuple[bool | None, str]:
    if isinstance(value, bool):
        return value, "true" if value else "false"
    if isinstance(value, str) and value.strip():
        folded = fold(value)
        if folded in {"true", "yes", "y", "1", "write", "crm"}:
            return True, value.strip()
        if folded in {"false", "no", "n", "0", "skip", "hold"}:
            return False, value.strip()
        return None, value.strip()
    if value is None:
        return None, ""
    return None, str(value)


def email_parts(email: str) -> tuple[str, str] | None:
    if "@" not in email or " " in email:
        return None
    local, _, domain = email.partition("@")
    domain = domain.lower().strip(".")
    if not local or not domain or "." not in domain:
        return None
    return local, domain


def evidence_list(value: object) -> list[str] | None:
    if isinstance(value, list):
        items = [nonempty_text(v) for v in value]
        if any(not i for i in items):
            return None
        return items
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return None


def evaluate(data: dict) -> dict:
    email = nonempty_text(data.get("email"))
    raw_domain = nonempty_text(data.get("domain")).lower().strip(".")
    raw_kind = nonempty_text(data.get("kind"))
    company_guess = nonempty_text(data.get("company_guess"))
    raw_route = nonempty_text(data.get("route"))
    crm_write_bool, raw_crm = as_bool(data.get("crm_write"))
    evidence = evidence_list(data.get("evidence"))

    kind = KINDS.get(fold(raw_kind), "")
    route = ROUTES.get(fold(raw_route), "")

    reasons: list[str] = []

    parsed = email_parts(email) if email else None
    if not email:
        reasons.append("missing email; name the inbound address")
    elif parsed is None:
        reasons.append("email is not shaped like an address; write local@domain")

    email_domain = parsed[1] if parsed else ""

    if not raw_domain:
        reasons.append("missing domain; extract the domain from the inbound email")
    elif parsed and raw_domain != email_domain:
        reasons.append(
            "domain does not match the email; set domain to the part after @"
        )

    if not raw_kind:
        reasons.append(
            "missing kind; use corporate, free-mail, disposable, or personal-looking"
        )
    elif not kind:
        reasons.append(
            "kind is not a slot; use corporate, free-mail, disposable, or personal-looking"
        )

    if evidence is None:
        reasons.append(
            "missing evidence; list one public fact about the domain (free-mail list, disposable list, company-shaped domain)"
        )
    elif len(evidence) < MIN_EVIDENCE:
        reasons.append(
            "evidence is empty; add one checkable fact that drove the kind"
        )

    if not raw_route:
        reasons.append(
            "missing route; use high-touch, self-serve, need-more, personal, or disqualify"
        )
    elif not route:
        reasons.append(
            "route is not a slot; use high-touch, self-serve, need-more, personal, or disqualify"
        )

    if raw_crm == "" and data.get("crm_write") is None:
        reasons.append(
            "missing crm_write; set false — no CRM write-back in the free pack"
        )
    elif crm_write_bool is None:
        reasons.append("crm_write is not a boolean; use false")
    elif crm_write_bool is True:
        reasons.append(
            "CRM write-back is banned in the free pack; set crm_write false and keep the route card as the artifact"
        )

    # Kind ↔ route consistency (local lists are illustrative for the sample loop).
    check_domain = raw_domain or email_domain
    if kind == "free-mail" and route == "high-touch":
        reasons.append(
            "free-mail routed to high-touch; route free-mail to personal or need-more"
        )
    if kind == "disposable" and route != "disqualify":
        reasons.append(
            "disposable domain is not disqualify; set route to disqualify"
        )
    if kind == "corporate" and route == "personal":
        reasons.append(
            "corporate domain routed to personal; use high-touch, self-serve, or need-more"
        )
    if check_domain in FREE_MAIL and kind == "corporate":
        reasons.append(
            "known free-mail domain marked corporate; set kind to free-mail"
        )
    if check_domain in DISPOSABLE and kind != "disposable":
        reasons.append(
            "known disposable domain marked otherwise; set kind to disposable"
        )
    if check_domain in FREE_MAIL and kind not in {"", "free-mail"} and kind != "free-mail":
        # Already covered above when kind is corporate; catch personal-looking misuse.
        if kind == "personal-looking":
            reasons.append(
                "known free-mail domain marked personal-looking; set kind to free-mail"
            )
    if kind == "corporate" and not company_guess:
        reasons.append(
            "corporate kind missing company_guess; derive a short name from the domain"
        )

    if not reasons:
        verdict = f"a {route} route from the domain"
    elif crm_write_bool is True:
        verdict = "a CRM write-back"
    elif kind == "free-mail" and route == "high-touch":
        verdict = "a free-mail high-touch route"
    elif kind == "disposable" and route != "disqualify":
        verdict = "a disposable kept alive"
    else:
        verdict = "not a domain route"

    ok = not reasons
    return {
        "ok": ok,
        "verdict": verdict,
        "reasons": reasons,
        "email": email if ok else None,
        "domain": (raw_domain or email_domain) if ok else None,
        "kind": kind if ok else None,
        "company_guess": company_guess if ok else None,
        "route": route if ok else None,
        "crm_write": crm_write_bool if ok else None,
        "evidence": evidence if ok else None,
    }


NEXT_PASS = "hand the route card to a human; do not write the CRM from this pack."
NEXT_FAIL = "fix the lines above and run this again."
EXAMPLE = (
    "Exit 0 scored, 1 refused, 2 unreadable input.\n\n"
    "example:\n  python3 scripts/score.py --file examples/inbound-good.json"
)


def split_reason(reason: str) -> tuple[str, str]:
    wrong, _, fix = reason.partition("; ")
    return wrong, fix or "fix this field"


def next_step(result: dict) -> str:
    if not result["ok"]:
        return NEXT_FAIL
    return NEXT_PASS


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Score inbound-from-domain: enrich from email domain, route in seconds.",
        epilog=EXAMPLE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--file",
        help="Path to a JSON route card (gtm/inbound.json)",
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
            print(f"domain: {result['domain']}")
            print(f"kind: {result['kind']}")
            if result.get("company_guess"):
                print(f"company_guess: {result['company_guess']}")
            print(f"route: {result['route']}")
            print(f"crm_write: {str(result['crm_write']).lower()}")
        for reason in result["reasons"]:
            wrong, fix = split_reason(reason)
            print(f"- {wrong} → {fix}")
        print(f"Next: {result['next']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
