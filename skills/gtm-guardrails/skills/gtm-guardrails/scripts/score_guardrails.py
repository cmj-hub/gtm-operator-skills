#!/usr/bin/env python3
"""Score the guardrails on a CRM-connected agent: read by default, ask before a write.

Stdlib only. No network. Reads the file you hand it and nothing else.

  python3 scripts/score_guardrails.py --file gtm/guardrails.json
  python3 scripts/score_guardrails.py --stdin
  python3 scripts/score_guardrails.py --settings .claude/settings.json --crm crm
  python3 scripts/score_guardrails.py --file examples/guardrails-good.json --json

The draft names the CRM's MCP server(s), carries the Claude Code
`permissions` block you plan to use, and may carry approval cards:

  {"crm_servers": ["crm"],
   "settings": {"permissions": {"allow": [...], "ask": [...], "deny": [...]}},
   "approval_cards": [{"action": ..., "record": ..., "field": ...,
                       "before": ..., "after": ..., "source": ..., "undo": ...}]}

Refused: an allow rule that lets a CRM write run without a prompt (a
whole-server rule, or a glob that matches a write-shaped tool name), any
core write verb with no ask rule, any of delete/remove/merge not denied,
bypassPermissions as the default mode, and an approval card with no
before value, no source, or no undo line.

Exit codes: 0 pass, 1 refused (fix the draft), 2 unreadable input.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from pathlib import Path

MAX_INPUT_BYTES = 2_000_000

# Verbs that change a record. A tool name holding one of these is a write.
WRITE_VERBS = (
    "create",
    "update",
    "upsert",
    "delete",
    "remove",
    "merge",
    "archive",
    "write",
    "set",
    "add",
    "send",
    "post",
    "patch",
    "assign",
    "move",
    "import",
    "bulk",
)
# Verbs that only read. An allow rule should start with one of these.
READ_VERBS = (
    "get",
    "list",
    "search",
    "find",
    "read",
    "query",
    "describe",
    "fetch",
    "lookup",
    "count",
    "retrieve",
)
DELETE_VERBS = ("delete", "remove", "merge")
CARD_FIELDS = ("action", "record", "field", "before", "after", "source", "undo")
SERVER_RE = re.compile(r"^[A-Za-z0-9_.\- ]+$")


def fail_input(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def read_bytes(path: Path) -> bytes:
    try:
        if not path.is_file():
            fail_input(f"file not found: {path}")
        if path.stat().st_size > MAX_INPUT_BYTES:
            fail_input("file is too large")
        return path.read_bytes()
    except OSError:
        fail_input("cannot read file")
    return b""


def parse_json(raw: bytes) -> object:
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        fail_input("input is not UTF-8 JSON")
    return None


def load(args: argparse.Namespace) -> dict:
    sources = [bool(args.file), bool(args.stdin), bool(args.settings)]
    if sum(sources) != 1:
        fail_input("pass one of --file, --stdin, or --settings")
    if args.settings:
        if not args.crm:
            fail_input("--settings needs --crm SERVER (the name /mcp shows)")
        settings = parse_json(read_bytes(Path(args.settings)))
        return {"crm_servers": args.crm, "settings": settings}
    if args.stdin:
        raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(raw) > MAX_INPUT_BYTES:
            fail_input("input is too large")
        data = parse_json(raw)
    else:
        data = parse_json(read_bytes(Path(args.file)))
    if not isinstance(data, dict):
        fail_input("draft is not a JSON object")
    return data


def server_prefix(name: str) -> str:
    """Claude Code turns `.` and spaces in a server name into `_`."""
    return "mcp__" + re.sub(r"[. ]", "_", name.strip()) + "__"


def rule_list(perms: dict, key: str) -> list[str]:
    value = perms.get(key, [])
    if not isinstance(value, list):
        fail_input(f"permissions.{key} is not a list")
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def words(tool: str) -> list[str]:
    return [part for part in re.split(r"[^a-z0-9]+", tool.lower()) if part]


def has_verb(tool: str, verbs: tuple[str, ...]) -> bool:
    found = words(tool)
    return any(verb in found for verb in verbs) or any(
        verb in tool.lower().replace("*", " ") for verb in verbs if len(verb) > 4
    )


# Write verbs that must each sit behind an ask (or deny) rule. "add" and "set"
# are left out on purpose: `*add*` also matches get_address, `*set*` get_settings.
REQUIRED_ASK = ("create", "update", "upsert", "archive", "write", "send", "patch", "import")
GLOB_CHARS = set("*?[")


def probes(prefix: str, verb: str) -> list[str]:
    """Tool names a rule must catch for `verb`: verb first, verb last, verb alone."""
    return [f"{prefix}{verb}_record", f"{prefix}record_{verb}", f"{prefix}{verb}"]


def rule_matches(rule: str, tool: str, prefix: str) -> bool:
    """Does this permission rule match this tool name, as Claude Code reads it?"""
    if rule == prefix[:-2]:  # bare `mcp__server` matches every tool on it
        return tool.startswith(prefix)
    if GLOB_CHARS & set(rule):
        return fnmatch.fnmatchcase(tool, rule)
    return rule == tool


def covered(rules: list[str], prefix: str, verb: str) -> bool:
    return any(rule_matches(rule, tool, prefix) for rule in rules for tool in probes(prefix, verb))


def tool_part(rule: str, prefix: str) -> str | None:
    if rule.startswith(prefix):
        return rule[len(prefix):]
    return None


def check_server(name: str, perms: dict) -> list[str]:
    prefix = server_prefix(name)
    allow = rule_list(perms, "allow")
    ask = rule_list(perms, "ask")
    deny = rule_list(perms, "deny")
    fixes: list[str] = []
    probe_tools = [tool for verb in WRITE_VERBS for tool in probes(prefix, verb)]

    for rule in allow:
        if rule in (prefix[:-2], prefix + "*"):
            fixes.append(
                f"allow rule {rule} lets every {name} tool run, writes included"
                f" → allow only read tools, e.g. {prefix}get_*, {prefix}list_*, {prefix}search_*"
            )
            continue
        tool = tool_part(rule, prefix)
        if tool is None:
            # Not anchored to this server. A glob such as mcp__* or * that reaches
            # this server's tools is refused even though Claude Code skips it today.
            if GLOB_CHARS & set(rule) and any(fnmatch.fnmatchcase(t, rule) for t in probe_tools):
                fixes.append(
                    f"allow rule {rule} is a wildcard that reaches {name} writes"
                    f" → remove it and allow {name} read tools by name or read-verb prefix"
                )
            continue
        if tool.startswith("*"):
            fixes.append(
                f"allow rule {rule} starts with a wildcard, so it also matches writes"
                f" → start it with a read verb, e.g. {prefix}get_*"
            )
        elif has_verb(tool, WRITE_VERBS):
            fixes.append(f"allow rule {rule} runs a CRM write with no prompt → move it to ask")
        elif GLOB_CHARS & set(tool) and not any(tool.lower().startswith(verb) for verb in READ_VERBS):
            fixes.append(
                f"allow rule {rule} is a wildcard that does not start with a read verb"
                f" → list each read tool by its exact name instead"
            )
        elif GLOB_CHARS & set(tool) and any(fnmatch.fnmatchcase(t, rule) for t in probe_tools):
            fixes.append(
                f"allow rule {rule} also matches write-shaped tool names"
                f" → end the read verb with an underscore, e.g. {prefix}get_*"
            )

    unasked = [verb for verb in REQUIRED_ASK if not covered(ask + deny, prefix, verb)]
    if unasked:
        rules = ", ".join(f"{prefix}*{verb}*" for verb in unasked)
        fixes.append(
            f"{name} writes with no ask rule: {', '.join(unasked)}"
            f" → add {rules} to ask, so every write shows you the change first"
        )
    undenied = [verb for verb in DELETE_VERBS if not covered(deny, prefix, verb)]
    if undenied:
        rules = ", ".join(f"{prefix}*{verb}*" for verb in undenied)
        fixes.append(
            f"{name} {', '.join(undenied)} not denied"
            f" → add {rules} to deny; nothing takes these back, so do them by hand in the CRM"
        )
    return fixes


def check_cards(cards: object) -> list[str]:
    if cards is None:
        return []
    if not isinstance(cards, list):
        return ["approval_cards is not a list → make it a list of card objects"]
    fixes: list[str] = []
    for index, card in enumerate(cards, start=1):
        if not isinstance(card, dict):
            fixes.append(f"card {index} is not an object → write it as one object per change")
            continue
        missing = [key for key in CARD_FIELDS if not str(card.get(key, "")).strip()]
        for key in missing:
            if key == "before":
                fixes.append(
                    f"card {index} has no before value → read the record now and copy the"
                    " current value in; without it nobody can put the record back"
                )
            elif key == "source":
                fixes.append(
                    f"card {index} has no source → say where the new value came from:"
                    " a URL, a call note, a file and row"
                )
            elif key == "undo":
                fixes.append(
                    f"card {index} has no undo line → write the one step that puts it back,"
                    " or say plainly that nothing can"
                )
            else:
                fixes.append(f"card {index} has no {key} → fill it in")
        before = str(card.get("before", "")).strip()
        after = str(card.get("after", "")).strip()
        if before and after and before == after:
            fixes.append(f"card {index} changes nothing (before equals after) → drop the card")
    return fixes


def score(data: dict) -> dict:
    servers = data.get("crm_servers")
    if isinstance(servers, str):
        servers = [servers]
    if not isinstance(servers, list) or not servers:
        fail_input("crm_servers is empty: name the CRM's MCP server as /mcp shows it")
    names = []
    for item in servers:
        if not isinstance(item, str) or not SERVER_RE.match(item.strip()):
            fail_input(f"crm_servers holds an unreadable server name: {item!r}")
        names.append(item.strip())

    settings = data.get("settings")
    if not isinstance(settings, dict):
        fail_input("settings is not a JSON object")
    perms = settings.get("permissions", {})
    if not isinstance(perms, dict):
        fail_input("settings.permissions is not a JSON object")

    fixes: list[str] = []
    mode = perms.get("defaultMode", settings.get("defaultMode"))
    if mode == "bypassPermissions":
        fixes.append(
            "defaultMode is bypassPermissions, so CRM writes skip every prompt"
            " → use default, or acceptEdits for file edits only"
        )
    for name in names:
        fixes.extend(check_server(name, perms))
    fixes.extend(check_cards(data.get("approval_cards")))

    cards = data.get("approval_cards") or []
    passed = not fixes
    if passed:
        nxt = (
            "Next: run the undo drill in references/undo-sheet.md with the new user,"
            " then the routine pre-flight if this agent runs on a schedule."
        )
    else:
        nxt = "Next: fix the lines above and run this again."
    return {
        "pass": passed,
        "crm_servers": names,
        "cards": len(cards) if isinstance(cards, list) else 0,
        "fixes": fixes,
        "next": nxt,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="score_guardrails",
        description="Score a CRM-connected agent's permissions and approval cards.",
        epilog="Example: python3 scripts/score_guardrails.py --file examples/guardrails-good.json",
    )
    parser.add_argument("--file", help="path to gtm/guardrails.json")
    parser.add_argument("--stdin", action="store_true", help="read the draft from stdin")
    parser.add_argument("--settings", help="a Claude Code settings.json to score directly")
    parser.add_argument("--crm", action="append", help="CRM MCP server name (repeat for more)")
    parser.add_argument("--json", action="store_true", help="print one JSON object")
    args = parser.parse_args(argv)

    result = score(load(args))
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        servers = ", ".join(result["crm_servers"])
        if result["pass"]:
            print(f"pass: {servers} reads run, writes ask first, deletes are denied")
            if result["cards"]:
                print(f"approval cards: {result['cards']} ready to show")
        else:
            print(f"refused: {len(result['fixes'])} fix(es) for {servers}")
            for fix in result["fixes"]:
                print(f"- {fix}")
        print(result["next"])
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
