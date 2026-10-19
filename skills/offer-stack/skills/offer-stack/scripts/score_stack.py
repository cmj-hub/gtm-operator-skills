#!/usr/bin/env python3
"""Score an offer stack: every component removes a pain the buyer has put a number on.

Stdlib only. No network. Reads the draft you hand it and nothing else.

  python3 scripts/score_stack.py --file gtm/offer-stack.json
  python3 scripts/score_stack.py --stdin
  python3 scripts/score_stack.py --file examples/stack-good.json --json

The draft names the buyer, lists the pains with numbers, lists the
components, and states a risk reversal:

  {"buyer": "...",
   "pains": [{"id": "p1", "pain": "...", "count": 3, "unit": "hours",
              "people": 40, "cost_each": 60, "period": "week",
              "source": "discovery call, 2026-10-02"}],
   "components": [{"name": "...", "removes": ["p1"]}],
   "risk_reversal": "...",
   "price": {"amount": 4000, "period": "month"}}

Each pain costs count x people x cost_each x periods a year. The scorer
prints that sum, line by line, so the buyer can check it.

Refused: a pain with no number or no source, no pain sourced from the
buyer, a component that removes no pain, a pain no component removes, a
filler line, no risk reversal or a satisfaction-only one, and a price
that is more than the pain it removes.

Exit codes: 0 pass, 1 refused (fix the draft), 2 unreadable input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MAX_INPUT_BYTES = 2_000_000
# Periods a year. "day" means a working day: 5 days x 52 weeks.
PER_YEAR = {"day": 260, "week": 52, "month": 12, "quarter": 4, "year": 1}
FILLER = (
    "and more",
    "and much more",
    "best-in-class",
    "best in class",
    "world-class",
    "world class",
    "cutting-edge",
    "seamless",
    "premium support",
    "white-glove",
    "unlimited",
    "everything you need",
    "full access",
)
SATISFACTION = (
    "if not satisfied",
    "if you're not satisfied",
    "if you are not satisfied",
    "satisfaction guaranteed",
    "100% satisfaction",
    "if you don't love it",
    "if you do not love it",
    "no questions asked",
)
ASSUMPTION_RE = re.compile(r"^\s*(assum|guess|estimate|tbd|unknown)", re.I)


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
    return value.strip() if isinstance(value, str) else ""


def number(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and value > 0:
        return float(value)
    return None


def money(amount: float, currency: str) -> str:
    whole = f"{amount:,.0f}"
    return f"${whole}" if currency in ("", "USD", "$") else f"{whole} {currency}"


def fmt(value: float) -> str:
    return f"{value:,.0f}" if value == int(value) else f"{value:,.2f}"


def score(data: dict) -> dict:
    fixes: list[str] = []
    currency = text(data.get("currency")) or "USD"
    if not text(data.get("buyer")):
        fixes.append("no buyer → name one buyer: a role at a kind of company, in their words")

    pains = data.get("pains")
    if not isinstance(pains, list) or not pains:
        fail_input("pains is empty: list at least one pain with a number")
    components = data.get("components")
    if not isinstance(components, list) or not components:
        fail_input("components is empty: list what the buyer gets")

    lines: list[str] = []
    totals: dict[str, float] = {}
    sourced_by_buyer = 0
    for index, pain in enumerate(pains, start=1):
        if not isinstance(pain, dict):
            fail_input(f"pain {index} is not an object")
        pid = text(pain.get("id")) or f"p{index}"
        label = text(pain.get("pain"))
        if not label:
            fixes.append(f"pain {pid} has no words → say the pain the way the buyer said it")
        count = number(pain.get("count"))
        cost = number(pain.get("cost_each"))
        people = number(pain.get("people", 1))
        period = text(pain.get("period")).lower()
        unit = text(pain.get("unit")) or "times"
        missing = [
            name
            for name, value in (("count", count), ("cost_each", cost), ("people", people))
            if value is None
        ]
        if missing or period not in PER_YEAR:
            parts = ", ".join(missing + ([] if period in PER_YEAR else ["period"]))
            fixes.append(
                f"pain {pid} has no number for {parts} → how many {unit}, for how many people,"
                f" at what cost each, per {'/'.join(PER_YEAR)}"
            )
        else:
            yearly = count * people * cost * PER_YEAR[period]
            totals[pid] = yearly
            who = "" if people == 1 else f" x {fmt(people)} people"
            lines.append(
                f"{pid}: {fmt(count)} {unit}{who} x {money(cost, currency)}"
                f" x {PER_YEAR[period]} {period}s = {money(yearly, currency)} a year"
            )
        source = text(pain.get("source"))
        if not source:
            fixes.append(
                f"pain {pid} has no source → say who gave the number and when,"
                " or write 'assumption:' and why"
            )
        elif not ASSUMPTION_RE.match(source):
            sourced_by_buyer += 1
    if sourced_by_buyer == 0:
        fixes.append(
            "every number is an assumption → get one number from the buyer"
            " (a call, an email, a form) before you build the stack on it"
        )

    pain_ids = {text(p.get("id")) or f"p{i}" for i, p in enumerate(pains, start=1)}
    removed: set[str] = set()
    for index, comp in enumerate(components, start=1):
        if not isinstance(comp, dict):
            fail_input(f"component {index} is not an object")
        name = text(comp.get("name"))
        if not name:
            fixes.append(f"component {index} has no name → say what the buyer gets")
            continue
        folded = name.lower()
        for phrase in FILLER:
            if phrase in folded:
                fixes.append(
                    f"component '{name}' leans on '{phrase}' → say the one thing it does,"
                    " in the buyer's words"
                )
                break
        targets = comp.get("removes")
        targets = [text(t) for t in targets] if isinstance(targets, list) else []
        targets = [t for t in targets if t]
        if not targets:
            fixes.append(f"component '{name}' removes no pain → tie it to a pain id, or cut it")
            continue
        unknown = [t for t in targets if t not in pain_ids]
        if unknown:
            fixes.append(f"component '{name}' names unknown pain {', '.join(unknown)} → use an id from pains")
        removed.update(t for t in targets if t in pain_ids)
    for pid in sorted(pain_ids - removed):
        fixes.append(f"pain {pid} is left open → add a component that removes it, or drop the pain")

    reversal = text(data.get("risk_reversal"))
    if not reversal:
        fixes.append(
            "no risk reversal → say what happens if it does not work: an outcome you can check,"
            " a date, and what the buyer pays then"
        )
    elif any(phrase in reversal.lower() for phrase in SATISFACTION) and not re.search(r"\d", reversal):
        fixes.append(
            "risk reversal rests on satisfaction → tie it to an outcome you can check by a date"
        )

    total = sum(totals.values())
    price_line = ""
    price = data.get("price")
    if isinstance(price, dict):
        amount = number(price.get("amount"))
        period = text(price.get("period")).lower() or "year"
        if amount is None or period not in PER_YEAR:
            fixes.append("price has no amount or period → give both, or leave price out")
        else:
            yearly_price = amount * PER_YEAR[period]
            if total and yearly_price >= total:
                fixes.append(
                    f"the price ({money(yearly_price, currency)} a year) is more than the pain it removes"
                    f" ({money(total, currency)} a year) → find the bigger pain, cut components, or cut the price"
                )
            elif total:
                price_line = (
                    f"price: {money(yearly_price, currency)} a year,"
                    f" against {money(total, currency)} of pain ({total / yearly_price:.1f}x the price)"
                )

    passed = not fixes
    nxt = (
        "Next: /pricing:pricing anchor, where the pain total is the status-quo anchor;"
        " then /sales-offer:cold-offer for the first touch."
        if passed
        else "Next: fix the lines above and run this again."
    )
    return {
        "pass": passed,
        "pain_lines": lines,
        "pain_total_per_year": round(total, 2),
        "currency": currency,
        "price_line": price_line,
        "fixes": fixes,
        "next": nxt,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="score_stack",
        description="Score an offer stack against the pains the buyer has numbered.",
        epilog="Example: python3 scripts/score_stack.py --file examples/stack-good.json",
    )
    parser.add_argument("--file", help="path to gtm/offer-stack.json")
    parser.add_argument("--stdin", action="store_true", help="read the draft from stdin")
    parser.add_argument("--json", action="store_true", help="print one JSON object")
    args = parser.parse_args(argv)

    result = score(read_payload(args))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for line in result["pain_lines"]:
            print(line)
        if result["pain_lines"]:
            print(f"pain total: {money(result['pain_total_per_year'], result['currency'])} a year")
        if result["price_line"]:
            print(result["price_line"])
        if result["pass"]:
            print("pass: every component removes a numbered pain")
        else:
            print(f"refused: {len(result['fixes'])} fix(es)")
            for fix in result["fixes"]:
                print(f"- {fix}")
        print(result["next"])
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
