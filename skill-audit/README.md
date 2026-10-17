# skill-audit

Too many skills and MCP servers installed? This skill reads your Claude Code setup and prints a short ranked report: what each one costs in context, which ones overlap, which descriptions are too long or vague, and which skills point to files that are not there.

It is read-only. It does not delete, disable, or edit anything, and it opens no network connection.

## Install

```text
/plugin marketplace add cmj-hub/gtm-operator-skills
/plugin install skill-audit@gtm-operator-skills
```

Other agents:

```bash
npx skills add cmj-hub/gtm-operator-skills --skill skill-audit -g
```

Then ask: `audit my skills` or run `/skill-audit:skill-audit`.

## What it checks

- Lists user skills, project skills, plugin skills, and configured MCP servers.
- Estimates the always-on cost of each skill (name plus description) and the body cost that loads when it triggers. Four characters per token, so the figures are rough.
- Flags descriptions that are close to another skill's, share a name, run past 800 characters, or never say when to use the skill.
- Flags skills whose linked files are missing.
- Suggests one action per skill: keep, merge, disable, or rewrite the description.

It cannot measure an MCP server's tool descriptions without starting the server. Run `/context` in Claude Code for that.

## Run it without Claude

```bash
python3 skills/skill-audit/scripts/audit.py --top 10
python3 skills/skill-audit/scripts/audit.py --json
```

Python 3.8 or newer, standard library only. See [SECURITY.md](SECURITY.md) for exactly what it reads.

## Test it

```bash
python3 -m unittest discover -s tests
```

Free build guides and Skills: https://jaymountconsulting.com/resources
