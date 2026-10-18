#!/usr/bin/env python3
"""Audit installed Claude Code skills and MCP servers. Read-only.

Lists user, project and plugin skills plus configured MCP servers, estimates
what each costs in context, flags overlapping, long, vague and broken skills,
and prints a short ranked report. It never writes, deletes or edits anything,
and it prints names and sizes only: no file contents, no env values, no headers.

Usage:
  python3 audit.py [--project DIR] [--home DIR] [--top N] [--json]

Python 3.8+, standard library only.
"""
import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

CHARS_PER_TOKEN = 4
LONG_DESC_CHARS = 800
SPEC_DESC_CHARS = 1024
MIN_DESC_CHARS = 50
HEAVY_BODY_TOKENS = 5000
HEAVY_BODY_LINES = 500
OVERLAP_THRESHOLD = 0.5

CUE_RE = re.compile(
    r"\b(use (this )?(skill )?(when|for|to|if|before|after|whenever)|whenever|when (the )?(user|you|someone|asked|asking)"
    r"|when asked|triggers?\b|invoke|activate|also use)",
    re.I,
)
STOPWORDS = set(
    "the and for with that this from into your you are not use when user users asks ask asked wants want also any "
    "can will its has have use used using skill skills tool tools via per one all out about over than then them "
    "their what which who how why more most such each only just like need needs make makes work works help helps "
    "claude code".split()
)
LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
SKILL_VAR_RE = re.compile(r"\$\{CLAUDE_SKILL_DIR\}/([^\s`'\")\]]+)")
PLUGIN_VAR_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\s`'\")\]]+)")
FENCE_RE = re.compile(r"```.*?```", re.S)
SCHEME_RE = re.compile(r"^[a-zA-Z][\w+.-]*:")
PLACEHOLDER_RE = re.compile(r"[*<>{}$|]")


@dataclass
class Skill:
    source: str
    name: str
    path: Path
    description: str
    body: str
    plugin_root: "Path | None" = None
    desc_chars: int = 0
    body_tokens: int = 0
    body_lines: int = 0
    always_on_tokens: int = 0


@dataclass
class Mcp:
    name: str
    scope: str
    transport: str


@dataclass
class Flag:
    code: str
    detail: str


@dataclass
class Pair:
    a: str
    b: str
    a_source: str
    b_source: str
    score: float


SAFE_RE = re.compile(r"[A-Za-z0-9._:@/-]{1,64}")
TRANSPORTS = {"stdio", "http", "sse", "ws"}


def clean(value):
    """Config- and frontmatter-derived text is untrusted: print it only if it is a plain identifier."""
    if isinstance(value, str) and SAFE_RE.fullmatch(value):
        return value
    return "<unprintable>"


def clean_transport(value):
    return value if isinstance(value, str) and value in TRANSPORTS else "other"


def estimate_tokens(text):
    return -(-len(text) // CHARS_PER_TOKEN)


def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    lines = parts[1].splitlines()
    front = {}
    i = 0
    while i < len(lines):
        m = re.match(r"^([A-Za-z][\w-]*)\s*:\s*(.*)$", lines[i])
        i += 1
        if not m:
            continue
        key, raw = m.group(1), m.group(2).strip()
        if re.fullmatch(r"[>|][+-]?", raw):
            chunks = []
            while i < len(lines) and (lines[i].startswith((" ", "\t")) or not lines[i].strip()):
                if lines[i].strip():
                    chunks.append(lines[i].strip())
                i += 1
            raw = " ".join(chunks)
        elif len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
            raw = raw[1:-1]
        front[key] = raw
    return front, parts[2].lstrip("\n")


def load_skill(path, source, plugin_root=None):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    front, body = parse_frontmatter(text)
    name = front.get("name") or Path(path).parent.name
    desc = front.get("description", "")
    return Skill(
        source=source,
        name=name,
        path=Path(path),
        description=desc,
        body=body,
        plugin_root=Path(plugin_root) if plugin_root else None,
        desc_chars=len(desc),
        body_tokens=estimate_tokens(body),
        body_lines=len(body.splitlines()),
        always_on_tokens=estimate_tokens(name) + estimate_tokens(desc),
    )


def read_json(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def skill_files_in(folder):
    """SKILL.md files for a folder that is a skill, or whose children are."""
    folder = Path(folder)
    if (folder / "SKILL.md").is_file():
        return [folder / "SKILL.md"]
    if not folder.is_dir():
        return []
    return sorted(p / "SKILL.md" for p in folder.iterdir() if (p / "SKILL.md").is_file())


def active_plugins(home, project):
    """Yield (plugin_name, install_path) for installed, enabled plugins in scope."""
    installed = read_json(Path(home) / ".claude" / "plugins" / "installed_plugins.json") or {}
    enabled = (read_json(Path(home) / ".claude" / "settings.json") or {}).get("enabledPlugins", {})
    seen = set()
    for key, entries in (installed.get("plugins") or {}).items():
        if enabled.get(key) is False or not isinstance(entries, list):
            continue
        for entry in entries:
            install = entry.get("installPath") if isinstance(entry, dict) else None
            if not install or install in seen:
                continue
            proj_path = entry.get("projectPath")
            if entry.get("scope") in ("project", "local") and proj_path and Path(proj_path) != Path(project):
                continue
            seen.add(install)
            yield key.split("@")[0], Path(install)


def discover_skills(home, project):
    found, seen = [], set()

    def add(path, source, root=None):
        real = Path(path).resolve()
        if real in seen:
            return
        seen.add(real)
        found.append(load_skill(path, source, root))

    for p in sorted((Path(home) / ".claude" / "skills").glob("*/SKILL.md")):
        add(p, "user")
    for p in sorted((Path(project) / ".claude" / "skills").glob("*/SKILL.md")):
        add(p, "project")
    for name, root in active_plugins(home, project):
        if not root.is_dir():
            continue
        manifest = read_json(root / ".claude-plugin" / "plugin.json") or {}
        entries = manifest.get("skills") if isinstance(manifest.get("skills"), list) else []
        for rel in entries:
            if isinstance(rel, str) and ".." not in rel:
                for p in skill_files_in(root / rel):
                    add(p, f"plugin:{name}", root)
        for p in skill_files_in(root / "skills"):
            add(p, f"plugin:{name}", root)
    return found


def servers_from(data):
    block = data.get("mcpServers") if isinstance(data.get("mcpServers"), dict) else data
    return block if isinstance(block, dict) else {}


def mcp_from(servers, scope):
    out = []
    for name, cfg in servers.items():
        if not isinstance(cfg, dict):
            continue
        transport = cfg.get("type") or ("http" if cfg.get("url") else "stdio")
        out.append(Mcp(str(name), scope, str(transport)))
    return out


def discover_mcp(home, project):
    out = []
    user = read_json(Path(home) / ".claude.json") or {}
    out += mcp_from(servers_from({"mcpServers": user.get("mcpServers", {})}), "user")
    local = (user.get("projects") or {}).get(str(project)) or {}
    out += mcp_from(servers_from({"mcpServers": local.get("mcpServers", {})}), "local")
    proj_file = read_json(Path(project) / ".mcp.json")
    if proj_file:
        out += mcp_from(servers_from(proj_file), "project")
    for name, root in active_plugins(home, project):
        data = read_json(root / ".mcp.json")
        if data:
            out += mcp_from(servers_from(data), f"plugin:{name}")
    return out


def description_flags(skill):
    flags = []
    n = skill.desc_chars
    if n > SPEC_DESC_CHARS:
        flags.append(Flag("over-spec", f"description is {n} chars, over the {SPEC_DESC_CHARS} spec limit"))
    elif n > LONG_DESC_CHARS:
        flags.append(Flag("long-description", f"description is {n} chars"))
    if n < MIN_DESC_CHARS:
        flags.append(Flag("vague-description", "too short to say when to use it"))
    elif not CUE_RE.search(skill.description):
        flags.append(Flag("vague-description", "never says when to use it"))
    if skill.body_tokens > HEAVY_BODY_TOKENS or skill.body_lines > HEAVY_BODY_LINES:
        flags.append(Flag("heavy-body", f"~{skill.body_tokens} tokens on trigger"))
    return flags


def missing_references(skill):
    skill_dir = skill.path.parent
    body = FENCE_RE.sub("", skill.body)
    refs = []

    def check(base, rel):
        rel = rel.split("#")[0].split("?")[0].rstrip(".,;:)")
        if not rel or rel.startswith(("/", "~", "#")) or SCHEME_RE.match(rel) or PLACEHOLDER_RE.search(rel):
            return
        if ".." in Path(rel).parts:
            return
        rel = rel[2:] if rel.startswith("./") else rel
        if not (base / rel).exists() and rel not in refs:
            refs.append(rel)

    for target in LINK_RE.findall(body):
        check(skill_dir, target)
    for target in SKILL_VAR_RE.findall(body):
        check(skill_dir, target)
    if skill.plugin_root:
        for target in PLUGIN_VAR_RE.findall(body):
            check(skill.plugin_root, target)
    return refs


def terms(text):
    words = set()
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if len(w) < 3 or w in STOPWORDS:
            continue
        for suffix in ("ing", "es", "ed", "s"):
            if w.endswith(suffix) and len(w) - len(suffix) >= 3:
                w = w[: -len(suffix)]
                break
        if w not in STOPWORDS:
            words.add(w)
    return words


def find_overlaps(skills):
    sets = [terms(s.description) for s in skills]
    pairs = []
    for i in range(len(skills)):
        for j in range(i + 1, len(skills)):
            a, b = skills[i], skills[j]
            if a.name == b.name and a.path.resolve() != b.path.resolve():
                pairs.append(Pair(a.name, b.name, a.source, b.source, 1.0))
                continue
            union = sets[i] | sets[j]
            if not union:
                continue
            score = len(sets[i] & sets[j]) / len(union)
            if score >= OVERLAP_THRESHOLD:
                pairs.append(Pair(a.name, b.name, a.source, b.source, round(score, 2)))
    return sorted(pairs, key=lambda p: -p.score)


ACTION_ORDER = {"disable": 0, "merge": 1, "rewrite": 2, "keep": 3}


def build_report(home, project):
    skills = discover_skills(home, project)
    pairs = find_overlaps(skills)
    overlap_with = {}
    for p in pairs:
        overlap_with.setdefault((p.a, p.a_source), []).append(p.b)
        overlap_with.setdefault((p.b, p.b_source), []).append(p.a)
    rows = []
    for s in skills:
        flags = description_flags(s)
        missing = missing_references(s)
        others = overlap_with.get((s.name, s.source), [])
        codes = [f.code for f in flags]
        if missing:
            action, reason = "disable", "referenced file missing: " + ", ".join(clean(m) for m in missing[:3])
        elif others:
            action, reason = "merge", "overlaps " + ", ".join(clean(o) for o in sorted(set(others))[:3])
        elif any(c in codes for c in ("over-spec", "long-description", "vague-description")):
            action = "rewrite"
            reason = "; ".join(f.detail for f in flags if f.code != "heavy-body")
        else:
            action, reason = "keep", ""
        if "heavy-body" in codes:
            note = next(f.detail for f in flags if f.code == "heavy-body")
            reason = f"{reason}; {note}" if reason else note
        if s.source.startswith("plugin:") and action in ("disable", "rewrite"):
            reason += " (plugin skill: report it to the plugin author or turn the plugin off)"
        if missing:
            codes.append("missing-reference")
        if others:
            codes.append("overlap")
        rows.append(
            {
                "name": clean(s.name),
                "source": clean(s.source),
                "desc_chars": s.desc_chars,
                "always_on_tokens": s.always_on_tokens,
                "body_tokens": s.body_tokens,
                "flags": codes,
                "action": action,
                "reason": reason,
            }
        )
    rows.sort(key=lambda r: (ACTION_ORDER[r["action"]], bool(not r["flags"]), -r["always_on_tokens"], -r["body_tokens"]))
    mcp = [
        {"name": clean(m.name), "scope": clean(m.scope), "transport": clean_transport(m.transport)}
        for m in discover_mcp(home, project)
    ]
    return {
        "totals": {
            "skills": len(rows),
            "always_on_tokens": sum(r["always_on_tokens"] for r in rows),
            "mcp_servers": len(mcp),
            "actions": {a: sum(1 for r in rows if r["action"] == a) for a in ACTION_ORDER},
        },
        "skills": rows,
        "overlaps": [
            {"a": clean(p.a), "b": clean(p.b), "a_source": clean(p.a_source), "b_source": clean(p.b_source), "score": p.score}
            for p in pairs
        ],
        "mcp": mcp,
    }


def render_text(report, top=10):
    t = report["totals"]
    acts = t["actions"]
    out = [
        "Skill audit (read-only; token figures are estimates at 4 characters per token)",
        "",
        f"Skills found: {t['skills']}. Always-on cost of their names and descriptions: about {t['always_on_tokens']} tokens.",
        f"MCP servers configured: {t['mcp_servers']}.",
        f"Suggested actions: {acts['disable']} disable, {acts['merge']} merge, {acts['rewrite']} rewrite, {acts['keep']} keep.",
        "",
        f"Top {min(top, len(report['skills']))} by priority",
    ]
    for n, r in enumerate(report["skills"][:top], 1):
        line = f"  {n}. {r['name']} ({r['source']}): description ~{r['always_on_tokens']} tokens always on, body ~{r['body_tokens']} tokens when triggered. Action: {r['action']}"
        out.append(line + (f". {r['reason']}" if r["reason"] else ""))
    if report["overlaps"]:
        out += ["", "Overlapping trigger descriptions"]
        for p in report["overlaps"][:5]:
            out.append(f"  {p['a']} ({p['a_source']}) and {p['b']} ({p['b_source']}): similarity {p['score']}")
    if report["mcp"]:
        out += ["", "MCP servers (name, scope, transport)"]
        for m in report["mcp"]:
            out.append(f"  {m['name']} ({m['scope']}, {m['transport']})")
        out.append("  Tool descriptions load only when a server connects, so their size is not measured here. Run /context in Claude Code to see it.")
    out += ["", "Nothing was changed."]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Read-only audit of installed skills and MCP servers.")
    ap.add_argument("--project", default=".", help="project folder (default: current directory)")
    ap.add_argument("--home", default=str(Path.home()), help="home folder holding .claude (default: your home)")
    ap.add_argument("--top", type=int, default=10, help="rows in the ranked list (default 10)")
    ap.add_argument("--json", action="store_true", help="print one JSON object")
    a = ap.parse_args(argv)
    project = Path(a.project).resolve()
    if not project.is_dir():
        print(f"not a folder: {project}", file=sys.stderr)
        return 2
    report = build_report(Path(a.home), project)
    print(json.dumps(report, indent=1) if a.json else render_text(report, a.top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
