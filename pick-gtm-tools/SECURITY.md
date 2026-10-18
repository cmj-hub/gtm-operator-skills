# Security

## What this pack does on your machine

- Runs one local Python script, standard library only: `skills/pick-gtm-tools/scripts/check_shortlist.py`. It reads the shortlist you pipe to it (`--stdin`) or the file you name (`--file`), refuses input over 200 KB, prints a result, and writes nothing.
- The skill writes no files. The shortlist is the agent's reply.
- Network: the script opens no connection. The agent calls The GTM Directory's public, read-only MCP server at `https://thegtmdirectory.com/api/mcp` over HTTPS (or its JSON API at `https://thegtmdirectory.com/api/v1/` when no MCP client is present). In Claude Code the plugin's `.mcp.json` adds that server; nothing else is added. Requests carry the search terms and tool slugs the agent sends, and nothing from your project.
- No telemetry. No credentials are asked for or stored. The TGD server needs no key or account.
- Nothing is sent, posted, purchased or published by the pack.

## Reporting a vulnerability

Email jay@jaymountconsulting.com with "security" and the repo name in the subject, or open a private advisory under this repo's Security tab. Do not open a public issue for a vulnerability. Expect a reply within five business days.

## Supported versions

Only the latest release on `main` gets fixes.
