#!/usr/bin/env python3
"""Check a context/ folder. Python 3.10+, stdlib only, no network.

    python3 check_context.py [--dir context] [--json]
    python3 check_context.py --file context/proof.md
    cat proof.md | python3 check_context.py --stdin

Exit 0 pass, 1 refused, 2 bad input. The last line is a Next: line.
The proof rule: every bullet in proof.md carries "Source:" with a real
source, or "Source: unverified".
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

FILES = ("company", "icp", "offer", "proof", "voice", "objections", "categories")
INDEX = "CONTEXT.md"
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD|FIXME)\b|\[fill|<fill|\{\{", re.I)
BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$")
SOURCE_RE = re.compile(r"\bSource:\s*(.*)$", re.I)
NOT_A_SOURCE = {"", "n/a", "na", "none", "tbd", "?", "see above", "various", "internal"}
LINK_RE = re.compile(r"https?://|www\.|\b[a-z0-9-]+\.(?:com|io|ai|co|net|org)\b", re.I)
UNKNOWN_RE = re.compile(r"\bUnknown:")
UPDATED_RE = re.compile(r"(?m)^Updated: \d{4}-\d{2}-\d{2}\s*$")
SAMPLE_HEADING_RE = re.compile(r"^#{2,3}\s+sample lines\s*$", re.I | re.M)


def bullets(text: str) -> list[str]:
    return [m.group(1) for line in text.splitlines() if (m := BULLET_RE.match(line))]


def check_proof(text: str) -> tuple[list[str], int]:
    refusals: list[str] = []
    unverified = 0
    for item in bullets(text):
        match = SOURCE_RE.search(item)
        value = match.group(1).strip().rstrip(".").strip().lower() if match else ""
        if value == "unverified" or value.startswith("unverified"):
            unverified += 1
        elif value in NOT_A_SOURCE:
            clean = re.sub(r"[\x00-\x1f\x7f]", " ", item)
            snippet = clean[:50] + ("..." if len(clean) > 50 else "")
            refusals.append(
                f'proof.md: "{snippet}" has no Source → '
                "add a Source: with a link, document, or date, or write Source: unverified"
            )
    return refusals, unverified


def check_text(name: str, text: str) -> tuple[list[str], int, int]:
    """Refusals, unverified count, unknown count for one file."""
    label = f"{name}.md"
    refusals: list[str] = []
    unverified = 0
    if not text.strip():
        return [f"{label} is empty → run the interview or update {name}"], 0, 0
    if not re.search(r"(?m)^# \S", text):
        refusals.append(f"{label} has no heading → start the file with a # title")
    if not UPDATED_RE.search(text):
        refusals.append(f"{label} has no Updated line → add Updated: YYYY-MM-DD under the title")
    if "\u2014" in text:
        refusals.append(f"{label} has an em dash → rewrite it as two plain sentences")
    if PLACEHOLDER_RE.search(text):
        refusals.append(f"{label} still has a placeholder → answer it or write Unknown: and what is missing")
    if name == "proof":
        found, unverified = check_proof(text)
        refusals.extend(found)
    if name == "voice":
        match = SAMPLE_HEADING_RE.search(text)
        section = text[match.end():] if match else ""
        section = re.split(r"(?m)^#{1,2}\s", section)[0]
        lines = [b for b in bullets(section)] + [
            l for l in section.splitlines() if l.lstrip().startswith(">")
        ]
        if len(lines) < 3:
            refusals.append("voice.md has fewer than 3 sample lines → add them under ## Sample lines")
    if name == "categories" and LINK_RE.search(text):
        refusals.append(
            "categories.md names a company or carries a link → write the category, not the company"
        )
    return refusals, unverified, len(UNKNOWN_RE.findall(text))


def check_index(text: str) -> list[str]:
    missing = [f"{n}.md" for n in FILES if f"{n}.md" not in text]
    if missing:
        return [f"{INDEX} does not list {', '.join(missing)} → add a line for each file"]
    return []


def check_folder(folder: Path) -> dict:
    refusals: list[str] = []
    unverified = unknown = 0
    for name in FILES:
        path = folder / f"{name}.md"
        if not path.is_file():
            refusals.append(f"{name}.md is missing → run the interview, or update {name}")
            continue
        found, unver, unk = check_text(name, path.read_text(encoding="utf-8"))
        refusals.extend(found)
        unverified += unver
        unknown += unk
    index = folder / INDEX
    if not index.is_file():
        refusals.append(f"{INDEX} is missing → write the index that points other agents at these files")
    else:
        refusals.extend(check_index(index.read_text(encoding="utf-8")))
    return {
        "passed": not refusals,
        "refusals": refusals,
        "unverified": unverified,
        "unknown": unknown,
    }


def report(result: dict, as_json: bool) -> int:
    if as_json:
        print(json.dumps(result))
        return 0 if result["passed"] else 1
    if result["passed"]:
        print(
            f"context ok: {result['unverified']} unverified, {result['unknown']} unknown"
        )
        print("Next: tell your other skills and agents to read context/CONTEXT.md first.")
        return 0
    print("Refusal:")
    for item in result["refusals"]:
        print(f"- {item}")
    print("Next: fix the lines above and run this again.")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check_context")
    parser.add_argument("--dir", default="context")
    parser.add_argument("--file")
    parser.add_argument("--stdin", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.stdin or args.file:
            if args.stdin:
                name, text = "proof", sys.stdin.read()
            else:
                path = Path(args.file)
                name, text = path.stem, path.read_text(encoding="utf-8")
            if name not in FILES:
                print(f"Bad input: {name}.md is not one of {', '.join(FILES)}")
                return 2
            found, unver, unk = check_text(name, text)
            result = {"passed": not found, "refusals": found, "unverified": unver, "unknown": unk}
        else:
            folder = Path(args.dir)
            if not folder.is_dir():
                print(f"Bad input: {folder} is not a folder")
                return 2
            result = check_folder(folder)
    except (OSError, UnicodeDecodeError) as error:
        print(f"Bad input: {error}")
        return 2
    return report(result, args.json)


if __name__ == "__main__":
    sys.exit(main())
