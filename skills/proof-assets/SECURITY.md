# Security

## What this pack does on your machine

- One script runs locally: `skills/proof-assets/scripts/score_proof.py`, standard-library Python 3. No dependencies are installed.
- It reads only the draft you hand it (`--file gtm/proof.json` or `--stdin`), or the bundled `examples/`.
- The skill writes one draft, `gtm/proof.json`, in your project's `gtm/` work folder. It may read `gtm/offer-stack.json` for pain ids; it never writes to it. The `ask` mode drafts an email; it never sends one.
- Network: none. No script opens a network connection, and the skill pre-approves no web tool.
- No telemetry. No credentials are asked for or stored. No paid APIs.

## Reporting a vulnerability

Email jay@jaymountconsulting.com with "security" and the repo name in the subject, or open a private advisory under this repo's Security tab. Do not open a public issue for a vulnerability. Expect a reply within five business days.

## Supported versions

Only the latest release on `main` gets fixes.
