#!/usr/bin/env python3
"""Gate for one skill pack. Python 3 stdlib. No install.

Patterns that would trip the key scan are assembled at runtime so this
file can live inside a pack it checks.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TGD_PREFIX = "https://thegtmdirectory.com/category/"
OPERATOR_PASS_LICENSE = "LicenseRef-JMC-Operator-Pass"
MIT_GRANT = "Permission is hereby granted, free of charge"
GROUPS = {
    "foundation",
    "offer",
    "outbound",
    "findability",
    "pages",
    "email",
    "social",
    "paid",
    "measurement",
    "motion",
}
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RESERVED_NAME_WORDS = ("anthropic", "claude")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
XML_TAG_RE = re.compile(r"<[A-Za-z/][^>]*>")
GO_BACK_RE = re.compile(r"go back to step|return to step", re.I)
CHECK_AGAIN_RE = re.compile(r"check again|review again", re.I)
INSTALL_MARKERS = (
    "pip install",
    "uv add",
    "npm install",
    "pnpm add",
    "bun add",
    "brew install",
)
SCRIPT_SUFFIXES = {".py", ".sh", ".bash", ".js", ".mjs", ".cjs", ".ts", ".rb"}
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".pytest_cache"}
BINARY_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".zip",
    ".gz",
    ".woff",
    ".woff2",
    ".pdf",
    ".pyc",
}
KEY_BEGIN = "-----" + "BEGIN "
CLOUD_RE = re.compile("AK" + "IA[0-9A-Z]{16}")
VENDOR_RE = re.compile("sk-" + "(?:ant|proj|live|test)-")
ASSIGNED_RE = re.compile(
    "(?im)^\\s*[A-Za-z0-9_.-]*(?:"
    + "API_KEY|SECRET|TOKEN|PASSWORD|PRIVATE_KEY"
    + ")[A-Za-z0-9_.-]*\\s*=(?!=)\\s*(\\S.*)$"
)
# A value that reads the secret from somewhere else, or is a placeholder.
NOT_A_SECRET_RE = re.compile(
    r"""^(?:["']{2}|None|null|true|false|\d+|<[^>]*>|\$\{?\w|os\.|process\.env|getenv"""
    r"""|[A-Za-z_][\w.]*\()"""
)
# Plugin parts and repo plumbing whose markdown is not a skill reference.
PLUGIN_DIRS = {".claude-plugin", ".github", "agents", "commands", "evals", "hooks"}
ENV_EXAMPLES = {".env.example", ".env.sample", ".env.template"}
# Repo docs a pack carries at its root that are not skill references.
REPO_DOCS = {
    "AGENTS.md",
    "CHANGELOG.md",
    "CLAUDE.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "INSTALL.md",
    "README.md",
    "SECURITY.md",
}
# A key with an inline value followed by an indented list item: YAML folds
# the list into the string, so `allowed-tools: Read` + `  - Grep` is "Read - Grep".
MIXED_VALUE_RE = re.compile(r"(?m)^([A-Za-z][\w-]*):[ \t]+[^\s>|].*\n[ \t]+- ")
# Plugin agent keys that Claude Code ignores or that belong to skills.
AGENT_IGNORED = ("permissionMode", "hooks", "mcpServers", "initialPrompt")
IMPORT_LINE_RE = re.compile(r"^\s*(?:import|from)\s+")
FENCE_RE = re.compile(r"```.*?```", re.S)
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="check_pack")
    sub = parser.add_subparsers(dest="cmd", required=True)

    knowledge = sub.add_parser("knowledge")
    knowledge.add_argument("card")

    design = sub.add_parser("design")
    design.add_argument("card")

    pack = sub.add_parser("pack")
    pack.add_argument("directory")
    side = pack.add_mutually_exclusive_group(required=True)
    side.add_argument("--public", action="store_true")
    side.add_argument("--private", action="store_true")

    entire = sub.add_parser("all")
    entire.add_argument("directory")
    entire_side = entire.add_mutually_exclusive_group(required=True)
    entire_side.add_argument("--public", action="store_true")
    entire_side.add_argument("--private", action="store_true")
    entire.add_argument("--knowledge", required=True)
    entire.add_argument("--design", required=True)

    args = parser.parse_args(argv)
    if not hasattr(sys, "stdlib_module_names"):
        print("Refusal: check_pack needs Python 3.10 or newer")
        return 1
    if args.cmd == "knowledge":
        return emit(check_knowledge(Path(args.card)), "knowledge ok")
    if args.cmd == "design":
        return emit(check_design(Path(args.card)), "design ok")
    if args.cmd == "pack":
        return emit(check_pack(Path(args.directory), args.public), "pack ok")

    refusals: list[str] = []
    oks: list[str] = []
    design_found = check_design(Path(args.design))
    stages = (
        (check_knowledge(Path(args.knowledge)), "knowledge ok"),
        (design_found, "design ok"),
        (check_pack(Path(args.directory), args.public), "pack ok"),
    )
    for found, ok in stages:
        if found:
            refusals.extend(found)
        else:
            oks.append(ok)
    if not design_found:
        data, _errors = load_card(Path(args.design))
        if data is not None:
            refusals.extend(check_job(Path(args.directory), data))
    refusals = list(dict.fromkeys(refusals))
    for item in refusals:
        print(f"Refusal: {item}")
    if refusals:
        return 1
    for ok in oks:
        print(ok)
    return 0


def emit(refusals: list[str], ok: str) -> int:
    refusals = list(dict.fromkeys(refusals))
    if refusals:
        for item in refusals:
            print(f"Refusal: {item}")
        return 1
    print(ok)
    return 0


def load_card(path: Path) -> tuple[dict | None, list[str]]:
    if not path.is_file():
        return None, ["card is missing"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None, ["card is not a JSON object"]
    if not isinstance(data, dict):
        return None, ["card is not a JSON object"]
    return data, []


def text_value(data: dict, key: str) -> str:
    value = data.get(key, "")
    return value.strip() if isinstance(value, str) else ""


def check_knowledge(path: Path) -> list[str]:
    data, errors = load_card(path)
    if data is None:
        return errors
    refusals: list[str] = []
    if not text_value(data, "job"):
        refusals.append("card is missing job")
    if not text_value(data, "portal_course"):
        refusals.append("card is missing portal_course")
    fact = data.get("portal_fact", "")
    if not isinstance(fact, str) or len(fact) < 20:
        refusals.append("portal_fact is shorter than 20 characters")
    elif len(fact) > 600:
        refusals.append("portal_fact is longer than 600 characters")
    elif "\n## " in fact or fact.startswith("## "):
        refusals.append("portal_fact is a pasted lesson")
    url = data.get("tgd_url", "")
    if not isinstance(url, str) or not url.startswith(TGD_PREFIX):
        refusals.append("tgd_url is not a directory category")
    repo = data.get("outside_repo", "")
    if not isinstance(repo, str) or not REPO_RE.fullmatch(repo):
        refusals.append("outside_repo is not owner/name")
    if not text_value(data, "outside_artifact"):
        refusals.append("card is missing outside_artifact")
    context = data.get("gtm_context")
    query = ""
    if isinstance(context, dict) and isinstance(context.get("query"), str):
        query = context["query"].strip()
    if not query:
        refusals.append("gtm_context.query is empty")
    kept = data.get("kept")
    if not isinstance(kept, bool):
        refusals.append("card is missing kept")
    elif kept and not text_value(data, "passage"):
        refusals.append("kept a passage and passage is empty")
    elif not kept and not text_value(data, "note"):
        refusals.append("discarded the graph and note is empty")
    return refusals


def check_design(path: Path) -> list[str]:
    data, errors = load_card(path)
    if data is None:
        return errors
    refusals: list[str] = []
    if not text_value(data, "artifact"):
        refusals.append("card is missing artifact")
    if not text_value(data, "refusal"):
        refusals.append("card is missing refusal")
    if data.get("group") not in GROUPS:
        refusals.append("group is not a catalog group")
    topics = data.get("topics")
    if (
        not isinstance(topics, list)
        or len(topics) != 3
        or not all(isinstance(item, str) for item in topics)
        or "agent-skills" not in topics
    ):
        refusals.append("topics must be three, including agent-skills")
    if not isinstance(data.get("ordered"), bool):
        refusals.append("card is missing ordered")
    if not isinstance(data.get("quality"), bool):
        refusals.append("card is missing quality")
    freedom = data.get("freedom")
    if not isinstance(freedom, list):
        refusals.append("freedom is not a list")
    else:
        for step in freedom:
            level = step.get("level") if isinstance(step, dict) else None
            if level not in {"low", "medium", "high"}:
                refusals.append("freedom level is not low, medium, or high")
                continue
            script = step.get("script") if isinstance(step, dict) else None
            named = script.strip() if isinstance(script, str) else ""
            template = step.get("template") if isinstance(step, dict) else None
            templated = template.strip() if isinstance(template, str) else ""
            diff = step.get("if_different") if isinstance(step, dict) else None
            if diff not in {"nothing-much", "consequential"}:
                refusals.append("if_different is not nothing-much or consequential")
            if level == "low" and not named:
                refusals.append("a low-freedom step names no script")
            if level == "medium" and not templated:
                refusals.append("a medium-freedom step names no template")
            if diff == "consequential" and level != "low":
                refusals.append("a consequential step is not low freedom")
    return refusals


def check_job(root: Path, card: dict) -> list[str]:
    if not root.is_dir():
        return []
    skills = [path for path in iter_files(root) if path.name == "SKILL.md"]
    refusals: list[str] = []
    if card.get("ordered") is True:
        for skill in skills:
            text = skill.read_text(encoding="utf-8", errors="replace")
            has_list = "- [ ]" in text or "copy this" in text.lower()
            has_back = GO_BACK_RE.search(text) is not None
            if not has_list or not has_back:
                refusals.append(f"{rel(skill, root)} is an ordered job with no checklist")
    if card.get("quality") is True and not quality_bound(root, skills):
        refusals.append("quality job has no check-again loop")
    refusals.extend(check_bound_scripts(root, card, skills))
    return refusals


def check_bound_scripts(root: Path, card: dict, skills: list[Path]) -> list[str]:
    texts = [
        skill.read_text(encoding="utf-8", errors="replace") for skill in skills
    ]
    blob = "\n".join(texts)
    refusals: list[str] = []
    for step in card.get("freedom") or []:
        if not isinstance(step, dict) or step.get("level") != "low":
            continue
        script = step.get("script")
        if not isinstance(script, str) or not script.strip():
            continue
        named = script.strip()
        if named not in blob:
            refusals.append(f"{named} is not a command in a SKILL.md")
            continue
        if not (root / named).is_file():
            refusals.append(f"{named} is missing")
    return refusals


def quality_bound(root: Path, skills: list[Path]) -> bool:
    for skill in skills:
        text = skill.read_text(encoding="utf-8", errors="replace")
        if CHECK_AGAIN_RE.search(text):
            return True
    for path in iter_files(root):
        if path.suffix.lower() not in SCRIPT_SUFFIXES:
            continue
        stem = path.stem.lower()
        if stem.startswith("score") or "validat" in stem or "lint" in stem:
            return True
    return False


def check_pack(root: Path, public: bool) -> list[str]:
    if not root.is_dir():
        return ["pack directory is missing"]
    refusals: list[str] = []
    refusals.extend(check_readme(root))
    refusals.extend(check_license(root, public))
    refusals.extend(check_security(root, public))
    refusals.extend(check_tree(root))
    refusals.extend(check_plugin(root))
    return refusals


def check_plugin(root: Path) -> list[str]:
    path = root / ".claude-plugin" / "plugin.json"
    if not path.is_file():
        return []
    data, errors = load_card(path)
    if data is None:
        return ["plugin.json is not a JSON object"]
    refusals: list[str] = []
    name = data.get("name")
    if not isinstance(name, str) or NAME_RE.fullmatch(name) is None:
        refusals.append("plugin.json name is not a lowercase hyphen name")
    version = data.get("version")
    if version is not None and (
        not isinstance(version, str) or SEMVER_RE.fullmatch(version) is None
    ):
        refusals.append("plugin.json version is not semver")
    paths = data.get("skills")
    if isinstance(paths, str):
        paths = [paths]
    if paths is None:
        paths = []
    if not isinstance(paths, list) or not all(isinstance(item, str) for item in paths):
        return refusals + ["plugin.json skills is not a path list"]
    found = False
    loaded: list[Path] = []
    for item in ["skills", *paths]:
        base = (root / item).resolve()
        try:
            base.relative_to(root.resolve())
        except ValueError:
            refusals.append(f"plugin.json skills path {item} leaves the pack")
            continue
        if item != "skills" and not base.is_dir():
            refusals.append(f"plugin.json skills path {item} is missing")
            continue
        loaded.append(base)
        if (base / "SKILL.md").is_file() or any(base.glob("*/SKILL.md")):
            found = True
    skills = [path for path in iter_files(root) if path.name == "SKILL.md"]
    if not found and skills:
        refusals.append("plugin.json installs no skills; list the SKILL.md folder in skills")
        return refusals
    for skill in skills:
        folder = skill.parent.resolve()
        if folder in loaded or folder.parent in loaded:
            continue
        refusals.append(
            f"{rel(skill, root)} does not load; move it to skills/<name>/ "
            "or list its folder in plugin.json skills"
        )
    return refusals


def check_readme(root: Path) -> list[str]:
    path = root / "README.md"
    if not path.is_file():
        return ["README.md is missing"]
    head = "\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[:100])
    refusals: list[str] = []
    if not re.search(r"(?m)^# [^#]", head):
        refusals.append("README is missing an H1")
    if not re.search(r"(?i)refus|will not|does not", head):
        refusals.append("README is missing a refusal")
    if "npx skills add" not in head:
        refusals.append("README is missing npx skills add")
    return refusals


def check_license(root: Path, public: bool) -> list[str]:
    path = root / "LICENSE"
    if not path.is_file():
        return ["LICENSE is missing"]
    text = path.read_text(encoding="utf-8", errors="replace")
    refusals: list[str] = []
    if public:
        if "MIT" not in text:
            refusals.append("public LICENSE is missing MIT")
        if OPERATOR_PASS_LICENSE in text:
            refusals.append("public LICENSE carries the Operator Pass license")
    else:
        if OPERATOR_PASS_LICENSE not in text:
            refusals.append("private LICENSE is missing the Operator Pass license")
        if MIT_GRANT in text:
            refusals.append("private LICENSE carries the MIT grant")
    return refusals


def check_security(root: Path, public: bool) -> list[str]:
    """A public pack says what it does on the user's machine and where to report."""
    if not public:
        return []
    path = root / "SECURITY.md"
    if not path.is_file():
        return ["public pack is missing SECURITY.md"]
    if not path.read_text(encoding="utf-8", errors="replace").strip():
        return ["SECURITY.md is empty"]
    return []


def iter_files(root: Path):
    for dirpath, dirnames, filenames in root.walk() if hasattr(Path, "walk") else _walk(root):
        yield from _from_walk(root, dirpath, dirnames, filenames)


def _walk(root: Path):
    import os

    for dirpath, dirnames, filenames in os.walk(root):
        yield Path(dirpath), dirnames, filenames


def _from_walk(root: Path, dirpath: Path, dirnames: list[str], filenames: list[str]):
    dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]
    for name in filenames:
        if name == ".DS_Store":
            continue
        yield Path(dirpath) / name


def check_tree(root: Path) -> list[str]:
    refusals: list[str] = []
    skills: list[Path] = []
    markdown: list[Path] = []
    saw_env = False
    for path in sorted(iter_files(root), key=lambda item: item.as_posix()):
        if path.name.startswith(".env") and path.name not in ENV_EXAMPLES:
            saw_env = True
        if path.name == "SKILL.md":
            skills.append(path)
        if path.suffix.lower() == ".md":
            markdown.append(path)
        refusals.extend(check_keys(root, path))
        if path.suffix.lower() == ".py":
            refusals.extend(check_imports(root, path))
        elif path.suffix.lower() == ".md":
            refusals.extend(check_imports(root, path, fenced_only=True))
    if saw_env:
        refusals.append(".env file in the pack")
    if not skills:
        refusals.append("SKILL.md is missing")
    for skill in skills:
        refusals.extend(check_skill(root, skill))
    refusals.extend(check_agents(root))
    for path in markdown:
        refusals.extend(check_contents(root, path))
    for skill in skills:
        refusals.extend(check_links(root, skill))
    refusals.extend(check_orphans(root, skills, markdown))
    return refusals


def check_orphans(root: Path, skills: list[Path], markdown: list[Path]) -> list[str]:
    linked: set[Path] = set()
    for skill in skills:
        for _raw, dest in md_targets(skill, root):
            if dest is not None and dest.is_file():
                linked.add(dest.resolve())
    refusals = []
    for path in markdown:
        if path.name in {"README.md", "SKILL.md", "INSTALL.md"}:
            continue
        if is_repo_doc(root, path):
            continue
        if path.resolve() in linked:
            continue
        refusals.append(f"{rel(path, root)} is not linked from SKILL.md")
    return refusals


def is_repo_doc(root: Path, path: Path) -> bool:
    parts = Path(rel(path, root)).parts
    if parts[0] in PLUGIN_DIRS:
        return True
    return len(parts) == 1 and path.name in REPO_DOCS


def check_keys(root: Path, path: Path) -> list[str]:
    if path.suffix.lower() in BINARY_SUFFIXES:
        return []
    try:
        data = path.read_bytes()[:2_000_000]
    except OSError:
        return []
    if b"\x00" in data:
        return []
    text = data.decode("utf-8", errors="replace")
    if KEY_BEGIN in text or CLOUD_RE.search(text) or VENDOR_RE.search(text):
        return [f"key material in {rel(path, root)}"]
    for match in ASSIGNED_RE.finditer(text):
        if not NOT_A_SECRET_RE.match(match.group(1).strip()):
            return [f"key material in {rel(path, root)}"]
    return []


def check_imports(root: Path, path: Path, fenced_only: bool = False) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    refusals: list[str] = []
    in_fence = False
    for index, line in enumerate(lines):
        if fenced_only and line.startswith("```"):
            in_fence = not in_fence
            continue
        if fenced_only and not in_fence:
            continue
        if not IMPORT_LINE_RE.match(line):
            continue
        for module in modules_on_line(line):
            if module.startswith("."):
                continue
            top = module.split(".")[0]
            if not top or is_stdlib(top) or is_local(top, path, root):
                continue
            window = lines[max(0, index - 5) : index + 1]
            if any(marker in item for item in window for marker in INSTALL_MARKERS):
                continue
            refusals.append(f"{rel(path, root)} imports {top} with no install line")
    return refusals


def modules_on_line(line: str) -> list[str]:
    relative = re.match(r"^\s*from\s+(\.+)\s*import\b", line)
    if relative and not re.match(r"^\s*from\s+\.+[A-Za-z_]", line):
        return ["."]
    from_named = re.match(r"^\s*from\s+(\.*)([A-Za-z_][A-Za-z0-9_\.]*)\s+import\b", line)
    if from_named:
        return [from_named.group(1) + from_named.group(2)]
    imported = re.match(r"^\s*import\s+(.+)$", line)
    if not imported:
        return []
    names = []
    for part in imported.group(1).split(","):
        name = part.strip().split()[0] if part.strip() else ""
        if name:
            names.append(name)
    return names


def is_stdlib(name: str) -> bool:
    names = getattr(sys, "stdlib_module_names", frozenset())
    return name in names


def is_local(name: str, source: Path, root: Path) -> bool:
    bases = [source.parent, root]
    for base in bases:
        if (base / f"{name}.py").is_file():
            return True
        if (base / name / "__init__.py").is_file():
            return True
        if (base / name).is_dir():
            return True
    return name in local_modules(root)


_LOCAL: dict[Path, set[str]] = {}


def local_modules(root: Path) -> set[str]:
    key = root.resolve()
    if key not in _LOCAL:
        names = set()
        for path in iter_files(root):
            if path.suffix == ".py":
                names.add(path.stem)
                if path.name == "__init__.py":
                    names.add(path.parent.name)
        _LOCAL[key] = names
    return _LOCAL[key]


def check_skill(root: Path, path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    front, body = split_frontmatter(text)
    label = rel(path, root)
    refusals: list[str] = []
    if not re.search(r"(?m)^models\s*:", front):
        refusals.append(f"{label} is missing models")
    name = front_field(front, "name")
    if name is None or len(name) > 64 or NAME_RE.fullmatch(name) is None:
        refusals.append(f"{label} name is not a lowercase hyphen name")
    elif any(word in name for word in RESERVED_NAME_WORDS):
        refusals.append(f"{label} name uses a reserved word")
    description = front_field(front, "description")
    if not description:
        refusals.append(f"{label} description is empty")
    elif len(description) > 1024:
        refusals.append(f"{label} description is over 1024 characters")
    elif XML_TAG_RE.search(description):
        refusals.append(f"{label} description carries an XML tag")
    elif "when" not in description.lower():
        refusals.append(f"{label} description does not say when")
    refusals.extend(check_mixed(label, front))
    if body.startswith("\n"):
        body = body[1:]
    if len(body.splitlines()) >= 500:
        refusals.append(f"{label} body is 500 lines or more")
    return refusals


def check_agents(root: Path) -> list[str]:
    folder = root / "agents"
    if not folder.is_dir():
        return []
    refusals: list[str] = []
    for path in sorted(folder.rglob("*.md"), key=lambda item: item.as_posix()):
        label = rel(path, root)
        front, _body = split_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
        if not front.strip():
            refusals.append(f"{label} has no frontmatter")
            continue
        if not front_field(front, "name"):
            refusals.append(f"{label} is missing name")
        if not front_field(front, "description"):
            refusals.append(f"{label} description is empty")
        if re.search(r"(?m)^allowed-tools\s*:", front):
            refusals.append(f"{label} uses allowed-tools; an agent takes tools")
        for key in AGENT_IGNORED:
            if re.search(rf"(?m)^{key}\s*:", front):
                refusals.append(f"{label} sets {key}, which a plugin agent ignores")
        refusals.extend(check_mixed(label, front))
    return refusals


def check_mixed(label: str, front: str) -> list[str]:
    return [
        f"{label} frontmatter {match.group(1)} mixes a value and a list"
        for match in MIXED_VALUE_RE.finditer(front + "\n")
    ]


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text
    return parts[1], parts[2]


def front_field(front: str, key: str) -> str | None:
    lines = front.splitlines()
    for index, line in enumerate(lines):
        if not re.match(rf"^{re.escape(key)}\s*:", line):
            continue
        raw = line.split(":", 1)[1].strip()
        if re.fullmatch(r"[>|][+-]?", raw):
            chunks = []
            for nxt in lines[index + 1 :]:
                if nxt.startswith((" ", "\t")):
                    chunks.append(nxt.strip())
                    continue
                if nxt.strip() == "":
                    continue
                break
            return " ".join(part for part in chunks if part)
        if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in {'"', "'"}:
            raw = raw[1:-1]
        return raw
    return None


def check_contents(root: Path, path: Path) -> list[str]:
    if path.name == "SKILL.md" or is_repo_doc(root, path):
        return []
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text.splitlines()) <= 100:
        return []
    label = rel(path, root)
    lines = text.splitlines()
    index = None
    for i, line in enumerate(lines):
        if re.match(r"^#{1,6}\s+Contents\s*$", line):
            index = i
            break
    if index is None:
        return [f"{label} is over 100 lines and has no Contents"]
    if index >= 100:
        return [f"{label} Contents starts after line 100"]
    bullets = contents_bullets(text)
    if bullets is None:
        return [f"{label} is over 100 lines and has no Contents"]
    refusals = []
    for title in later_h2(text):
        if not any(title in bullet for bullet in bullets):
            refusals.append(f"{label} Contents is missing heading {title}")
    return refusals


def contents_bullets(text: str) -> list[str] | None:
    lines = strip_fences(text).splitlines()
    start = None
    for index, line in enumerate(lines):
        if re.match(r"^#{1,6}\s+Contents\s*$", line):
            start = index + 1
            break
    if start is None:
        return None
    bullets = []
    for line in lines[start:]:
        if re.match(r"^#{1,6}\s+\S", line):
            break
        match = re.match(r"^\s*[-*]\s+(.*\S)\s*$", line)
        if match:
            bullets.append(match.group(1))
    return bullets


def later_h2(text: str) -> list[str]:
    lines = strip_fences(text).splitlines()
    seen = False
    titles = []
    for line in lines:
        if re.match(r"^#{1,6}\s+Contents\s*$", line):
            seen = True
            continue
        if not seen:
            continue
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match and match.group(1) != "Contents":
            titles.append(match.group(1))
    return titles


def check_links(root: Path, skill: Path) -> list[str]:
    linked = md_targets(skill, root)
    refusals: list[str] = []
    dests = set()
    for raw, dest in linked:
        if dest is None or not dest.is_file():
            refusals.append(f"{rel(skill, root)} links {raw} and the file is missing")
            continue
        dests.add(dest.resolve())
    for dest in sorted(dests, key=lambda item: item.as_posix()):
        if dest.name == "SKILL.md":
            continue
        for raw, nested in md_targets(dest, root):
            if nested is None or not nested.is_file():
                refusals.append(f"{rel(dest, root)} links {raw} and the file is missing")
                continue
            resolved = nested.resolve()
            if resolved == skill.resolve() or resolved in dests:
                continue
            refusals.append(
                f"{rel(dest, root)} links {rel(nested, root)} and SKILL.md does not"
            )
    return refusals


def md_targets(path: Path, root: Path) -> list[tuple[str, Path | None]]:
    found = []
    text = strip_fences(path.read_text(encoding="utf-8", errors="replace"))
    for raw in MD_LINK_RE.findall(text):
        target = raw.split("#", 1)[0].strip()
        if not target.endswith(".md"):
            continue
        if "://" in target or target.startswith("mailto:"):
            continue
        dest = (path.parent / target).resolve()
        try:
            dest.relative_to(root.resolve())
        except ValueError:
            found.append((raw, None))
            continue
        found.append((target, dest))
    return found


def strip_fences(text: str) -> str:
    return FENCE_RE.sub("", text)


def rel(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


if __name__ == "__main__":
    sys.exit(main())
