#!/usr/bin/env python3
"""List every outside link and install command in a skill pack, file by file.

A skill scanner reads the files you hand it. Any page a skill points the agent
to sits outside that scan. This script lists those pages and any install
commands, so a person can read them before the team installs the pack.

Usage:
  python3 skill_link_scan.py <skill-or-repo-folder> [--own owner/repo] [--csv out.csv]

  --own owner/repo   label links into the pack's own GitHub repo separately
                     (they are read live from a branch, not from your copy)

Python 3.8+, standard library only. It reads text files; it runs nothing.
"""
import argparse, csv, pathlib, re, sys

URL = re.compile(r'https?://[^\s)\]>"\'`]+')
INSTALL = re.compile(r'\b(npm (i|install)|npx |pip3? install|curl |wget |brew install|uvx |go install)')
FETCH = re.compile(r'\b(WebFetch|fetch|download|follow the (docs|instructions) at)\b', re.I)
TEXT = {".md", ".txt", ".py", ".sh", ".js", ".ts", ".mjs", ".json", ".yaml", ".yml", ".toml", ".html", ""}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--own", default="", help="owner/repo of the pack itself")
    ap.add_argument("--csv", help="write findings to this CSV")
    a = ap.parse_args()
    root = pathlib.Path(a.folder)
    if not root.is_dir():
        sys.exit(f"not a folder: {root}")
    rows, files = [], 0
    for f in sorted(root.rglob("*")):
        if not f.is_file() or ".git" in f.parts or f.suffix.lower() not in TEXT:
            continue
        files += 1
        try:
            lines = f.read_text(errors="ignore").splitlines()
        except OSError:
            continue
        rel = str(f.relative_to(root))
        for n, line in enumerate(lines, 1):
            for u in URL.findall(line):
                u = u.rstrip(".,;:")
                kind = "own repo" if a.own and a.own in u else "outside link"
                host = re.sub(r"^https?://([^/:]+).*", r"\1", u).lower()
                if host in ("localhost", "127.0.0.1"):
                    kind = "local"
                elif host == "example.com" or host.endswith((".example.com", ".example", ".test")):
                    kind = "placeholder"
                rows.append({"file": rel, "line": n, "kind": kind,
                             "agent_told_to_fetch": "yes" if FETCH.search(line) else "",
                             "value": u})
            m = INSTALL.search(line)
            if m:
                rows.append({"file": rel, "line": n, "kind": "install command",
                             "agent_told_to_fetch": "", "value": line.strip()[:160]})
    by = {}
    for r in rows:
        by.setdefault(r["kind"], []).append(r)
    print(f"Scanned {files} text files in {root}")
    for kind in ("outside link", "own repo", "install command", "local", "placeholder"):
        items = by.get(kind, [])
        print(f"\n{kind}: {len(items)}")
        for r in items:
            flag = "  [agent told to fetch]" if r["agent_told_to_fetch"] else ""
            print(f"  {r['file']}:{r['line']}  {r['value']}{flag}")
    domains = sorted({re.sub(r"^https?://([^/]+).*", r"\1", r["value"]) for r in by.get("outside link", [])})
    print(f"\nOutside domains to read and re-check: {len(domains)}")
    for d in domains:
        print(f"  {d}")
    if a.csv:
        with open(a.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["file", "line", "kind", "agent_told_to_fetch", "value"])
            w.writeheader(); w.writerows([{k: safe_cell(v) for k, v in r.items()} for r in rows])

def safe_cell(value):
    """Stop a spreadsheet from reading a cell as a formula (CSV injection)."""
    text = str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else value

if __name__ == "__main__":
    main()
