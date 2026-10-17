# Security

What this pack does on your machine:

- `skills/skill-audit/scripts/audit.py` is standard-library Python. It reads these paths and nothing else: `~/.claude/skills/`, `<project>/.claude/skills/`, `~/.claude/plugins/installed_plugins.json`, `~/.claude/settings.json` (the `enabledPlugins` key only), each installed plugin's `plugin.json`, `skills/` folder, and `.mcp.json`, `<project>/.mcp.json`, and `~/.claude.json` (MCP server names, scope, and transport only).
- It reads skill files to measure their size and to check that the files they link to exist. It prints skill names, sizes, and suggested actions. It does not print file contents.
- It never reads or prints MCP `env`, `headers`, `args`, or URL values.
- It writes nothing, deletes nothing, and edits nothing. A test checks that a run leaves a throwaway tree byte-identical.
- Network: None. It starts no MCP server and makes no request.
- No telemetry, no credentials asked for or stored.

To report a vulnerability, email jay@jaymountconsulting.com with "security" and "skill-audit" in the subject, or open a private advisory under the repo's Security tab. Do not open a public issue. Expect a reply within five business days.
