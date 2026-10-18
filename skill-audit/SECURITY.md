# Security

What this pack does on your machine:

- `skills/skill-audit/scripts/audit.py` is standard-library Python. It reads these paths and nothing else: `~/.claude/skills/`, `<project>/.claude/skills/`, `~/.claude/plugins/installed_plugins.json`, `~/.claude/settings.json` (the `enabledPlugins` key only), each installed plugin's `plugin.json`, `skills/` folder, and `.mcp.json`, `<project>/.mcp.json`, and `~/.claude.json` (MCP server names, scope, and transport only).
- It reads skill files to measure their size and to check that the files they link to exist. It prints skill names, sizes, and suggested actions. It does not print file contents.
- Names from skill frontmatter, MCP config, and plugin keys are untrusted. They print only if they are plain identifiers (letters, digits, and `._:@/-`, up to 64 characters); anything else prints as `<unprintable>`. MCP transport prints from a fixed set. Description text is never echoed: only lengths and similarity scores.
- It never reads or prints MCP `env`, `headers`, `args`, or URL values.
- It writes nothing, deletes nothing, and edits nothing. A test checks that a run leaves a throwaway tree byte-identical.
- Network: None. It starts no MCP server and makes no request.
- No telemetry, no credentials asked for or stored.

Report privately through GitHub's 'Report a vulnerability' button on this repo. Do not open a public issue.
