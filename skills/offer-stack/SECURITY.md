# Security

## What this pack does on your machine

- One script runs locally: `skills/offer-stack/scripts/score_stack.py`, standard-library Python 3. No dependencies are installed.
- It reads only the draft you hand it (`--file gtm/offer-stack.json` or `--stdin`), or the bundled `examples/`.
- The skill writes one draft, `gtm/offer-stack.json`, in your project's `gtm/` work folder. It may read `brand-config.json`; it never writes to it.
- Network: none. No script opens a network connection, and the skill pre-approves no web tool.
- No telemetry. No credentials are asked for or stored. No paid APIs.

## Reporting a vulnerability

Email jay@jaymountconsulting.com with "security" and the repo name in the subject, or open a private advisory under this repo's Security tab. Do not open a public issue for a vulnerability. Expect a reply within five business days.

## Supported versions

Only the latest release on `main` gets fixes.
