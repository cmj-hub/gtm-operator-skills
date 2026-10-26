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
from urllib.parse import urlsplit

URL = re.compile(r'https?://[^\s)\]>"\'`]+')
INSTALL = re.compile(r'\b(npm (i|install)|npx |pip3? install|curl |wget |brew install|uvx |go install)')
FETCH = re.compile(r'\b(WebFetch|fetch|download|follow the (docs|instructions) at)\b', re.I)
TEXT = {".md", ".txt", ".py", ".sh", ".js", ".ts", ".mjs", ".json", ".yaml", ".yml", ".toml", ".html", ""}

GITHUB_HOSTS = ("github.com", "www.github.com", "raw.githubusercontent.com")


def classify(u, own):
    """Label one URL from its parsed host and path. Returns (kind, host).

    A substring match or a regex host would let a link to another site that merely
    mentions github.com/<own> in its query pass as the pack's own repo, or a link with
    example.com as userinfo pass as a placeholder. urlsplit drops userinfo and port,
    so the label follows the real host.
    """
    # Browsers treat "\\" as "/" in http(s) URLs; urlsplit does not. Normalise first
    # so the host here is the host a browser would open.
    u = u.replace("\\", "/")
    try:
        parts = urlsplit(u)
        host = (parts.hostname or "").lower()
    except ValueError:
        return "outside link", ""
    # Userinfo has no honest use in a skill link and is how a host gets disguised.
    if "@" in parts.netloc or not host.isascii():
        return "outside link", host
    if host in ("localhost", "127.0.0.1"):
        return "local", host
    if host == "example.com" or host.endswith((".example.com", ".example", ".test")):
        return "placeholder", host
    if own and host in GITHUB_HOSTS:
        segs = [p for p in parts.path.split("/") if p]
        if [x.lower() for x in segs[:2]] == [x.lower() for x in own.strip("/").split("/")]:
            return "own repo", host
    return "outside link", host


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
                kind, host = classify(u, a.own)
                rows.append({"file": rel, "line": n, "kind": kind, "host": host,
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
    domains = sorted({r["host"] or r["value"] for r in by.get("outside link", [])})
    print(f"\nOutside domains to read and re-check: {len(domains)}")
    for d in domains:
        print(f"  {d}")
    if a.csv:
        with open(a.csv, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=["file", "line", "kind", "agent_told_to_fetch", "value"], extrasaction="ignore")
            w.writeheader(); w.writerows([{k: safe_cell(v) for k, v in r.items()} for r in rows])

def safe_cell(value):
    """Stop a spreadsheet from reading a cell as a formula (CSV injection)."""
    text = str(value)
    return "'" + text if text[:1] in ("=", "+", "-", "@", "\t", "\r") else value

if __name__ == "__main__":
    main()
