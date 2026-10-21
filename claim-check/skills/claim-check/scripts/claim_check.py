#!/usr/bin/env python3
"""Flag statistics in a draft that have no source URL and no date.

Read-only, standard library only, no network. A statistic is a percentage,
a multiplier (3x), a ratio (1 in 3), a money amount with a magnitude ($4M)
or a large count (27,000 companies). A statistic is sourced when its
sentence or the next sentence in the same paragraph has a URL (or a footnote
or reference link that resolves to one) and a date next to it.

Exit code: 0 when every statistic is sourced and dated, 1 when any is
flagged, 2 when a path cannot be read.
"""

from __future__ import annotations

import argparse
import bisect
import json
import os
import re
import sys
from pathlib import Path

MAX_BYTES = 2_000_000
TEXT_SUFFIXES = {".md", ".mdx", ".txt", ".markdown"}
SKIP_DIRS = {".git", "node_modules", ".next", "dist", "build", "__pycache__"}

MONTHS = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
    r"Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
)
YEAR = r"(?:19|20)\d\d"

URL_RE = re.compile(r"https?://[^\s)>\]\"']+", re.I)
DATE_RES = [
    re.compile(rf"\b{YEAR}-\d\d(?:-\d\d)?\b"),
    re.compile(rf"\b{MONTHS}\.?\s+(?:\d{{1,2}}(?:st|nd|rd|th)?,?\s+)?{YEAR}\b", re.I),
    re.compile(rf"\b\d{{1,2}}\s+{MONTHS}\.?\s+{YEAR}\b", re.I),
    re.compile(rf"\bQ[1-4]\s+{YEAR}\b", re.I),
    re.compile(rf"\b{YEAR}\b"),
]

STAT_RES = [
    ("percent", re.compile(r"(?<![\w.])\d+(?:[.,]\d+)?\s?(?:%|percent\b)", re.I)),
    ("multiplier", re.compile(r"(?<![\w.])\d+(?:\.\d+)?\s?(?:x\b|times\b|-?fold\b)", re.I)),
    ("ratio", re.compile(r"(?<![\w.])\d+\s+(?:out of|in)\s+(?!(?:19|20)\d\d\b)\d+\b", re.I)),
    ("money", re.compile(r"[$€£]\s?\d[\d,.]*\s?(?:[kKmMbB]\b|million\b|billion\b|thousand\b)", re.I)),
    ("count", re.compile(r"(?<![\w$.,])\d{1,3}(?:,\d{3})+\+?\s+[A-Za-z]{3,}")),
]

DEF_RE = re.compile(r"^\s{0,3}\[(\^?[^\]]+)\]:\s*(.*)$")
REF_RE = re.compile(r"\[(\^[^\]\s]+)\]|\]\[([^\]]+)\]")
FENCE_RE = re.compile(r"^\s{0,3}(```|~~~)")
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[\"'(\[]?[A-Z0-9$])")


def clean_text(s: str) -> str:
    """Printable ASCII only: the draft is data, and control or bidi characters never reach the report."""
    return re.sub(r"[^\x20-\x7e]", "?", s)


def strip_frontmatter(lines: list[str]) -> set[int]:
    """Indexes of lines inside a leading YAML frontmatter block."""
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return set(range(0, i + 1))
    return set()


def prose_lines(text: str) -> tuple[list[str], dict[str, str]]:
    """Lines with code, frontmatter, comments and reference definitions blanked; plus the definitions."""
    lines = text.splitlines()
    skip = strip_frontmatter(lines)
    defs: dict[str, str] = {}
    out: list[str] = []
    fenced = False
    in_comment = False
    for i, line in enumerate(lines):
        if i in skip:
            out.append("")
            continue
        if FENCE_RE.match(line):
            fenced = not fenced
            out.append("")
            continue
        if fenced:
            out.append("")
            continue
        if in_comment or "<!--" in line:
            if "<!--" in line:
                in_comment = True
            if "-->" in line:
                in_comment = False
            out.append("")
            continue
        m = DEF_RE.match(line)
        if m:
            defs[m.group(1).lower()] = m.group(2)
            out.append("")
            continue
        out.append(re.sub(r"`[^`]*`", " ", line))
    return out, defs


def find_sentences(lines: list[str]) -> list[tuple[int, str, int]]:
    """(paragraph id, sentence, line number) for every sentence, paragraphs split on blank lines."""
    sentences: list[tuple[int, str, int]] = []
    para = 0
    buf: list[str] = []
    starts: list[int] = []  # offset of each line within the paragraph text
    first_line = 0

    def flush() -> None:
        if not buf:
            return
        text = " ".join(buf)
        pos = 0
        for part in SENT_SPLIT.split(text):
            idx = text.find(part, pos)
            idx = pos if idx < 0 else idx
            pos = idx + len(part)
            k = bisect.bisect_right(starts, idx) - 1
            sentences.append((para, part, first_line + max(k, 0)))

    for n, line in enumerate(lines, start=1):
        if not line.strip():
            flush()
            if buf:
                para += 1
            buf, starts = [], []
            para += 0
            continue
        if not buf:
            first_line = n
            para += 1
        starts.append(sum(len(b) + 1 for b in buf))
        buf.append(line.strip())
    flush()
    return sentences


def resolve(window: str, defs: dict[str, str]) -> str:
    """The window plus the text of any footnote or reference definition it points to."""
    extra = []
    for m in REF_RE.finditer(window):
        key = (m.group(1) or m.group(2) or "").lower()
        if key in defs:
            extra.append(defs[key])
    return window + " " + " ".join(extra)


def has_date(text: str) -> bool:
    no_url = URL_RE.sub(" ", text)
    return any(r.search(no_url) for r in DATE_RES)


def stats_in(sent: str) -> list[tuple[int, str, str]]:
    body = URL_RE.sub(" ", sent)
    body = re.sub(r"\]\([^)]*\)", "]", body)  # markdown link targets are not prose
    return sorted((m.start(), kind, m.group(0).strip()) for kind, rx in STAT_RES for m in rx.finditer(body))


def check_text(text: str) -> list[dict]:
    lines, defs = prose_lines(text)
    sentences = find_sentences(lines)
    findings: list[dict] = []
    for i, (para, sent, line) in enumerate(sentences):
        body = URL_RE.sub(" ", sent)
        claims = stats_in(sent)
        if not claims:
            continue
        window = sent
        # A citation sentence right after the claim ("Source: ...") counts, but a neighbour
        # that makes a statistic of its own cites that one, not this one.
        if i + 1 < len(sentences) and sentences[i + 1][0] == para and not stats_in(sentences[i + 1][1]):
            window += " " + sentences[i + 1][1]
        window = resolve(window, defs)
        sourced = bool(URL_RE.search(window))
        dated = has_date(window)
        status = "ok" if sourced and dated else ("no-date" if sourced else "no-source")
        seen: set[str] = set()
        for pos, kind, token in claims:
            if token in seen:
                continue
            seen.add(token)
            lo = max(0, pos - 50)
            snippet = clean_text(body[lo : pos + len(token) + 50]).strip()
            findings.append({"line": line, "kind": kind, "claim": clean_text(token), "status": status, "context": snippet})
    return findings


def collect(paths: list[str]) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    errors: list[str] = []
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            for root, dirs, names in os.walk(p):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
                for name in sorted(names):
                    if Path(name).suffix.lower() in TEXT_SUFFIXES:
                        files.append(Path(root) / name)
        elif p.is_file():
            files.append(p)
        else:
            errors.append(f"cannot read {clean_text(raw)}")
    return files, errors


def run(paths: list[str]) -> tuple[list[dict], list[str]]:
    files, errors = collect(paths)
    results: list[dict] = []
    for f in files:
        try:
            if f.stat().st_size > MAX_BYTES:
                errors.append(f"skipped {clean_text(str(f))}: over {MAX_BYTES} bytes")
                continue
            text = f.read_bytes().decode("utf-8")
        except (OSError, UnicodeDecodeError):
            errors.append(f"cannot read {clean_text(str(f))} as text")
            continue
        for item in check_text(text):
            results.append({"file": clean_text(str(f)), **item})
    return results, errors


def render(results: list[dict], errors: list[str], show_ok: bool) -> str:
    flagged = [r for r in results if r["status"] != "ok"]
    out = []
    for r in results:
        if r["status"] == "ok" and not show_ok:
            continue
        out.append(f"{r['file']}:{r['line']}  [{r['status']}]  {r['claim']}  ...{r['context']}...")
    counts = {s: sum(1 for r in results if r["status"] == s) for s in ("ok", "no-date", "no-source")}
    out.append("")
    out.append(
        f"{len(results)} statistics: {counts['ok']} sourced and dated, "
        f"{counts['no-date']} with a link but no date, {counts['no-source']} with no link."
    )
    if flagged:
        out.append("Each flagged statistic needs a source URL and a date, or it should go.")
    out.extend(errors)
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Flag statistics with no source URL and date.")
    ap.add_argument("paths", nargs="+", help="files or folders (.md .mdx .txt)")
    ap.add_argument("--json", action="store_true", help="print findings as JSON")
    ap.add_argument("--all", action="store_true", help="also list sourced and dated statistics")
    ap.add_argument("--no-fail", action="store_true", help="exit 0 even when statistics are flagged")
    args = ap.parse_args(argv)
    results, errors = run(args.paths)
    if args.json:
        print(json.dumps({"findings": results, "errors": errors}, indent=2))
    else:
        print(render(results, errors, args.all))
    if errors and not results:
        return 2
    if any(r["status"] != "ok" for r in results) and not args.no_fail:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
