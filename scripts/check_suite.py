#!/usr/bin/env python3
"""Check every pack in the marketplace from local clones. Stdlib only.

Usage:
    python3 scripts/check_suite.py [--packs DIR]

DIR holds one clone per pack, named after the repo (claude-psp, claude-evp,
...). It defaults to the parent of this repo. For each pack this runs the
build-pack gate, the pack's own tests, and, when the `claude` CLI is on
PATH, `claude plugin validate --strict` and a load check that every
SKILL.md in the pack becomes a skill. It also checks that the marketplace
entry and the pack's plugin.json agree on the name, and the pack's hygiene:
a SECURITY.md, an icon, repository/license/documentationUrl/supportUrl in
plugin.json, and no tracked .pyc or __pycache__ (`git ls-files`).

Exit 0 when every pack passes, 1 otherwise. Nothing is sent anywhere: this
script opens no network connection. The commands it runs (the gate, each
pack's tests, `claude plugin validate`, `git ls-files`) run locally.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / "build" / "scripts" / "check_pack.py"
NAME_RE = re.compile(r"^name:\s*['\"]?([a-z0-9-]+)", re.M)
MANIFEST_KEYS = ("repository", "license", "documentationUrl", "supportUrl")
DEFAULT_ICON = ".claude-plugin/icon.png"


def run(args: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True)


def skill_names(pack: Path) -> set[str]:
    names = set()
    for path in pack.rglob("SKILL.md"):
        if ".git" in path.parts:
            continue
        match = NAME_RE.search(path.read_text(encoding="utf-8", errors="replace"))
        if match:
            names.add(match.group(1))
    return names


def tracked_bytecode(pack: Path) -> list[str]:
    """Tracked .pyc files or __pycache__ entries. Untracked ones are ignored."""
    listed = run(["git", "-C", str(pack), "ls-files", "-z"])
    if listed.returncode:
        return []
    return [
        path
        for path in listed.stdout.split("\0")
        if path and (path.endswith(".pyc") or "__pycache__" in path.split("/"))
    ]


def hygiene(pack: Path, manifest: dict) -> list[str]:
    """Release hygiene the gate does not check: docs, icon, manifest links, bytecode."""
    problems = []
    if not (pack / "SECURITY.md").is_file():
        problems.append("missing SECURITY.md")
    icon = manifest.get("icon") if isinstance(manifest.get("icon"), str) else DEFAULT_ICON
    icon_path = (pack / icon).resolve()
    if not icon_path.is_relative_to(pack.resolve()) or not icon_path.is_file():
        problems.append(f"missing icon {icon}")
    missing = [key for key in MANIFEST_KEYS if not manifest.get(key)]
    if missing:
        problems.append(f"plugin.json lacks {', '.join(missing)}")
    bytecode = tracked_bytecode(pack)
    if bytecode:
        problems.append(f"tracked bytecode: {', '.join(bytecode[:5])}")
    return problems


def check(entry: dict, packs: Path, claude: str | None) -> list[str]:
    repo = entry["source"]["repo"].split("/", 1)[1]
    pack = packs / repo
    if not pack.is_dir():
        return [f"{repo}: no clone at {pack}"]
    problems = []
    manifest = json.loads((pack / ".claude-plugin" / "plugin.json").read_text())
    if manifest.get("name") != entry["name"]:
        problems.append(f"{repo}: plugin.json name {manifest.get('name')!r} != {entry['name']!r}")
    problems.extend(f"{repo}: {problem}" for problem in hygiene(pack, manifest))
    gate = run([sys.executable, str(GATE), "pack", str(pack), "--public"])
    if gate.returncode:
        problems.append(f"{repo}: gate\n{gate.stdout.strip()}")
    if (pack / "tests").is_dir():
        tests = run([sys.executable, "-m", "unittest", "discover", "-s", "tests"], cwd=pack)
        if tests.returncode:
            problems.append(f"{repo}: tests\n{tests.stderr.strip()[-2000:]}")
    if claude:
        valid = run([claude, "plugin", "validate", "--strict", str(pack)])
        if valid.returncode:
            problems.append(f"{repo}: plugin validate\n{valid.stdout.strip()}")
        details = run([claude, "--plugin-dir", str(pack), "plugin", "details", entry["name"]])
        line = next((l for l in details.stdout.splitlines() if l.strip().startswith("Skills (")), "")
        loaded = set(line.split(")", 1)[1].replace(",", " ").split()) if ")" in line else set()
        missing = skill_names(pack) - loaded
        if missing:
            problems.append(f"{repo}: skills that do not load: {', '.join(sorted(missing))}")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(prog="check_suite")
    parser.add_argument("--packs", default=str(ROOT.parent))
    args = parser.parse_args()
    marketplace = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    claude = shutil.which("claude")
    if not claude:
        print("note: claude CLI not found; skipping validate and load checks")
    failed = False
    for entry in marketplace["plugins"]:
        source = entry["source"]
        if not (isinstance(source, dict) and source.get("source") == "github"):
            continue
        problems = check(entry, Path(args.packs), claude)
        print(f"{'FAIL' if problems else 'ok  '} {entry['name']}")
        for problem in problems:
            print("  " + problem.replace("\n", "\n  "))
        failed = failed or bool(problems)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
