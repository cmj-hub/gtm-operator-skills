# Pick GTM tools with The GTM Directory

Ask your agent which go-to-market tool does a job, and get back a short list where every tool links its page on [The GTM Directory](https://thegtmdirectory.com).

## In 60 seconds

```text
/plugin marketplace add cmj-hub/gtm-operator-skills
/plugin install pick-gtm-tools@gtm-operator-skills
/pick-gtm-tools:pick-gtm-tools cold email my agent can drive, inside Clay
```

The plugin connects The GTM Directory's MCP server for you. It is free, read-only, and needs no key.

Or check a shortlist without an agent:

```bash
python3 skills/pick-gtm-tools/scripts/check_shortlist.py --file examples/shortlist-good.txt       # exit 0: shortlist ok: 3 picks, each with its TGD page and as-of date
python3 skills/pick-gtm-tools/scripts/check_shortlist.py --file examples/shortlist-no-source.txt  # exit 1: - Acme Mailer has no TGD page → add its page_url from search_tools or get_tool
```

> A tool your agent remembers is not a pick. A tool with its page and a dated fact is.

## What you get

One shortlist for one job: three to five tools, each with the facts that match your must-haves (official MCP server, public API, free plan, works inside Clay), the date TGD checked them, and the TGD page to read next. The list ends on the free TGD page for that job, such as https://thegtmdirectory.com/best/cold-email.

Three modes, one command:

- **Shortlist**: "which tool does X?"
- **Compare**: "A or B?" Facts side by side, then the TGD compare page.
- **Starter stack**: "a sending tool and a CRM that plug into Clay." One pick per slot, then https://thegtmdirectory.com/build

## What it refuses

- A tool with no TGD page → it is left out, not filled in from memory.
- A price → dropped. You get the pricing tier and a pointer to the vendor's own pricing page.
- A fact TGD has not verified, read as a "no" → it says "not established on TGD".
- A dump of the directory → at most ten results. TGD's license is cite and link with credit and the as-of date.

The lint, `check_shortlist.py`, holds those lines. It is standard-library Python, it opens no network connection, and it does not judge which tool is better. That part is the TGD page.

## Install

Claude Code, from the suite marketplace (adds the skill and the MCP server):

```text
/plugin marketplace add cmj-hub/gtm-operator-skills
/plugin install pick-gtm-tools@gtm-operator-skills
```

Other agents, with the [skills CLI](https://skills.sh) (Cursor, Codex, Grok, Copilot, Windsurf, Cline, OpenCode and the rest of its list):

```bash
npx skills add cmj-hub/gtm-operator-skills --skill pick-gtm-tools --agent '*' -g --full-depth -y
```

Then connect the server once in that agent. The skills CLI installs the skill, not the server.

## Connect The GTM Directory MCP server

Connector URL (Streamable HTTP, no authentication): `https://thegtmdirectory.com/api/mcp`

Claude Code:

```bash
claude mcp add --transport http gtm-directory https://thegtmdirectory.com/api/mcp
```

Cursor (`.cursor/mcp.json`) and other clients that read an `mcpServers` block:

```json
{
  "mcpServers": {
    "gtm-directory": {
      "url": "https://thegtmdirectory.com/api/mcp"
    }
  }
}
```

Claude and ChatGPT apps: add a custom connector with the URL above. Steps for each client are on https://thegtmdirectory.com/mcp

No MCP client? The skill falls back to TGD's read-only JSON API at `https://thegtmdirectory.com/api/v1/tools`.

## Worked examples

[skills/pick-gtm-tools/references/examples.md](skills/pick-gtm-tools/references/examples.md) has three requests run against the live server on 2026-10-17, with the calls, the trimmed outputs and the reply:

1. A cold email tool an agent can drive over MCP, inside Clay.
2. Attio or Twenty for a CRM an agent reads and writes.
3. A sending tool and a CRM that plug into Clay.

## Tools the server offers

`search_tools` (find tools by job, with category, pricing tier, MCP server and public API filters), `get_tool` (one listing with dated vendor-verified facts), `list_categories`, `compare_tools` (two tools side by side; a fact TGD has not established comes back empty, never "no") and `recommend_stack` (up to 5 ranked tools per slot for one of TGD's published jobs, such as `find-a-work-email`, not for any category). Practitioner mentions are not used. If a server lacks the last two, the skill builds both modes from `search_tools` and `get_tool`.

## Tests

```bash
python3 -m unittest discover -s tests
python3 ../build/scripts/check_pack.py pack . --public
```

## Privacy and security

The skill writes no files. The agent sends your search terms and tool slugs to `thegtmdirectory.com` and nothing from your project. No telemetry, no credentials. See [SECURITY.md](SECURITY.md).

## Free, no signup

- [The GTM Directory MCP server](https://thegtmdirectory.com/mcp): connect it to any agent.
- [Build a stack](https://thegtmdirectory.com/build) and [compare two tools](https://thegtmdirectory.com/compare) on The GTM Directory.

## License

MIT. Built by [JMC Go-to-Market Systems](https://jaymountconsulting.com).
