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
    "(?im)^[A-Za-z0-9_.-]*(?:"
    + "API_KEY|SECRET|TOKEN|PASSWORD|PRIVATE_KEY"
    + ")[A-Za-z0-9_.-]*\\s*=\\s*\\S+"
)
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
    if args.cmd == "knowledge":
        return emit(check_knowledge(Path(args.card)), "knowledge ok")
    if args.cmd == "design":
        return emit(check_design(Path(args.card)), "design ok")
    if args.cmd == "pack":
        return emit(check_pack(Path(args.directory), args.public), "pack ok")

    refusals: list[str] = []
    oks: list[str] = []
    stages = (
        (check_knowledge(Path(args.knowledge)), "knowledge ok"),
        (check_design(Path(args.design)), "design ok"),
        (check_pack(Path(args.directory), args.public), "pack ok"),
    )
    for found, ok in stages:
        if found:
            refusals.extend(found)
        else:
            oks.append(ok)
    for item in refusals:
        print(f"Refusal: {item}")
    if refusals:
        return 1
    for ok in oks:
        print(ok)
    return 0


def emit(refusals: list[str], ok: str) -> int:
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
            if level == "low" and not named:
                refusals.append("a low-freedom step names no script")
    return refusals


def check_pack(root: Path, public: bool) -> list[str]:
    if not root.is_dir():
        return ["pack directory is missing"]
    refusals: list[str] = []
    refusals.extend(check_readme(root))
    refusals.extend(check_license(root, public))
    refusals.extend(check_tree(root))
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
        if path.name == ".env" or path.name.startswith(".env"):
            saw_env = True
        if path.name == "SKILL.md":
            skills.append(path)
        if path.suffix.lower() == ".md":
            markdown.append(path)
        refusals.extend(check_keys(root, path))
        if path.suffix.lower() == ".py":
            refusals.extend(check_imports(root, path))
    if saw_env:
        refusals.append(".env file in the pack")
    if not skills:
        refusals.append("SKILL.md is missing")
    for skill in skills:
        refusals.extend(check_skill(root, skill))
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
        if path.name in {"README.md", "SKILL.md"}:
            continue
        if path.resolve() in linked:
            continue
        refusals.append(f"{rel(path, root)} is not linked from SKILL.md")
    return refusals


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
    if KEY_BEGIN in text or CLOUD_RE.search(text) or VENDOR_RE.search(text) or ASSIGNED_RE.search(text):
        return [f"key material in {rel(path, root)}"]
    return []


def check_imports(root: Path, path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    refusals: list[str] = []
    for index, line in enumerate(lines):
        if not IMPORT_LINE_RE.match(line):
            continue
        for module in modules_on_line(line):
            if module.startswith("."):
                continue
            top = module.split(".")[0]
            if not top or is_stdlib(top) or is_local(top, path, root):
                continue
            window = lines[max(0, index - 5) : index + 1]
            if any("pip install" in item or "uv add" in item for item in window):
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
    return False


def check_skill(root: Path, path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    front, body = split_frontmatter(text)
    label = rel(path, root)
    refusals: list[str] = []
    if not re.search(r"(?m)^models\s*:", front):
        refusals.append(f"{label} is missing models")
    if body.startswith("\n"):
        body = body[1:]
    if len(body.splitlines()) >= 500:
        refusals.append(f"{label} body is 500 lines or more")
    return refusals


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---"):
        return "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return "", text
    return parts[1], parts[2]


def check_contents(root: Path, path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text.splitlines()) <= 100:
        return []
    label = rel(path, root)
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
