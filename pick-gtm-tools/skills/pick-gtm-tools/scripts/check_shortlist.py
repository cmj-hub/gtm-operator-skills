#!/usr/bin/env python3
"""Citation lint for a GTM tool shortlist. Python 3 stdlib. No network.

A pick is a list item that starts with a bold name: "1. **Name**: ..." or
"- **Name**: ...". Every pick carries its TGD page and an as-of date, the
shortlist names no price, and it ends on a TGD page.

Usage:
    python3 check_shortlist.py --file shortlist.md
    python3 check_shortlist.py --stdin < shortlist.md
    python3 check_shortlist.py --stdin --json

Exit 0 pass, 1 refused, 2 bad input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MAX_BYTES = 200_000
MAX_PICKS = 6
PICK_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+\*\*([^*]+)\*\*")
TOOL_URL_RE = re.compile(r"https://thegtmdirectory\.com/tools/[a-z0-9][a-z0-9-]*")
TGD_URL_RE = re.compile(r"https://thegtmdirectory\.com/\S*")
AS_OF_RE = re.compile(r"(?i)\bas of \d{4}-\d{2}-\d{2}\b")
PRICE_RE = re.compile(
    r"[$€£]\s?\d"
    r"|\b\d[\d,.]*\s?(?:USD|EUR|GBP|dollars|euros|pounds)\b"
    r"|\b\d[\d,.]*\s?(?:/|per |a )(?:mo|month|year|yr|seat|user|mailbox)\b",
    re.I,
)
NEXT_PASS = "Next: send the shortlist."
NEXT_FAIL = "Next: fix the lines above and run this again."


def lint(text: str) -> tuple[list[str], list[str]]:
    lines = text.splitlines()
    picks: list[str] = []
    refusals: list[str] = []
    for line in lines:
        match = PICK_RE.match(line)
        if not match:
            continue
        name = match.group(1).strip()
        picks.append(name)
        if not TOOL_URL_RE.search(line):
            refusals.append(f"- {name} has no TGD page → add its page_url from search_tools or get_tool")
        if not AS_OF_RE.search(line):
            refusals.append(f"- {name} has no as-of date → add the verified_facts as_of date")
    if not picks:
        refusals.append("- no picks found → write each pick as `1. **Name**: facts (as of YYYY-MM-DD). Source: The GTM Directory, <page_url>`")
    elif len(picks) > MAX_PICKS:
        refusals.append(f"- {len(picks)} picks → keep the {MAX_PICKS} or fewer you would defend")
    if PRICE_RE.search(text):
        refusals.append("- a price in the shortlist → drop it; give the pricing tier and point to the vendor's pricing page")
    content = [line for line in lines if line.strip()]
    if not content or PICK_RE.match(content[-1]) or not TGD_URL_RE.search(content[-1]):
        refusals.append("- no closing TGD page → end with one line that links the /best, /compare, /category or /build page for this job")
    return picks, refusals


def read_input(args: argparse.Namespace) -> str | None:
    if args.stdin:
        data = sys.stdin.read(MAX_BYTES + 1)
    else:
        path = Path(args.file)
        if not path.is_file():
            return None
        data = path.read_text(encoding="utf-8", errors="replace")[: MAX_BYTES + 1]
    if len(data) > MAX_BYTES or not data.strip():
        return None
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check_shortlist", description=__doc__.splitlines()[0])
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", help="shortlist file to check")
    source.add_argument("--stdin", action="store_true", help="read the shortlist from stdin")
    parser.add_argument("--json", action="store_true", help="print one JSON object")
    args = parser.parse_args(argv)

    text = read_input(args)
    if text is None:
        message = "bad input: give a non-empty shortlist under 200 KB"
        if args.json:
            print(json.dumps({"status": "bad_input", "error": message}))
        else:
            print(message)
            print("Next: pass --file PATH or pipe the shortlist to --stdin.")
        return 2

    picks, refusals = lint(text)
    status = "refused" if refusals else "pass"
    nxt = NEXT_FAIL if refusals else NEXT_PASS
    if args.json:
        print(json.dumps({"status": status, "picks": picks, "refusals": refusals, "next": nxt}))
    else:
        if refusals:
            print(f"refused: {len(picks)} picks")
            print("\n".join(refusals))
        else:
            print(f"shortlist ok: {len(picks)} picks, each with its TGD page and as-of date")
        print(nxt)
    return 1 if refusals else 0


if __name__ == "__main__":
    sys.exit(main())
