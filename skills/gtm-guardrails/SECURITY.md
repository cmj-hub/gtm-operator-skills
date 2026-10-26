# Security

## What this pack does on your machine

- Two scripts run locally, both standard-library Python 3 with no dependencies:
  - `skills/gtm-guardrails/scripts/score_guardrails.py` reads the draft you hand it (`--file gtm/guardrails.json`, `--stdin`, or `--settings <file>`) and prints a verdict.
  - `skills/gtm-guardrails/scripts/skill_link_scan.py` reads the text files in a folder you name and lists outside links and install commands. It runs nothing it finds. `--csv` writes one file you name.
- The skill writes one draft, `gtm/guardrails.json`. It proposes a `permissions` block for `.claude/settings.json` and writes it only after you approve, merged with what is already there.
- Network: none. No script opens a network connection. The skill pre-approves no web tool.
- No CRM, inbox or other live tool is called by this pack. The skill is told not to run a write tool to test a rule.
- No telemetry. No credentials are asked for or stored. No paid APIs.

## Reporting a vulnerability

Email jay@jaymountconsulting.com with "security" and the repo name in the subject, or open a private advisory under this repo's Security tab. Do not open a public issue for a vulnerability. Expect a reply within five business days.

## Supported versions

Only the latest release on `main` gets fixes.
