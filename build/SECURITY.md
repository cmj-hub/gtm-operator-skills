# Security

## What this pack does on your machine

- One script runs locally: `scripts/check_pack.py`, standard-library Python 3.10+. No dependencies are installed.
- It reads the pack directory and the knowledge and design cards you name. It reads; it never edits a pack.
- The skill writes nothing on its own. The cards and the pack are files you author.
- Network: none. The script opens no network connection, and the skill pre-approves no tool.
- No telemetry. Nothing is logged or sent anywhere.
- No credentials are asked for or stored. The key scan reports a file path, never the matched value.
- Nothing is published. Release is a pull request a person opens and merges.

The suite policy is in the hub's [SECURITY.md](https://github.com/cmj-hub/gtm-operator-skills/blob/main/SECURITY.md).

## Reporting a vulnerability

Email jay@jaymountconsulting.com with "security" and the repo name in the subject, or open a private advisory under this repo's Security tab. Do not open a public issue for a vulnerability. Expect a reply within five business days.

## Supported versions

Only the latest release on `main` gets fixes.
