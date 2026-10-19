# Security

## What this pack does on your machine

- One script runs locally: `skills/inbound-from-domain/scripts/score.py`, standard-library Python 3. No dependencies are installed.
- It reads only the draft you hand it (`--file gtm/inbound.json` or `--stdin`), or the bundled `examples/`.
- The skill writes one draft, `gtm/inbound.json`, in your project's shared `gtm/` work folder. Nothing else on disk is changed.
- Network: none. No script opens a network connection, and the skill pre-approves no web tool (`allowed-tools` lists only Read, Write, and the scorer).
- No CRM write-back. `crm_write` must stay `false`; the pack scores a route card and stops.
- No telemetry. Nothing is logged or sent anywhere.
- No credentials are asked for or stored.
- Nothing is sent. The pack does not email, message, or upsert a CRM.

## Reporting a vulnerability

Email jay@jaymountconsulting.com with "security" and the repo name in the subject, or open a private advisory under this repo's Security tab. Do not open a public issue for a vulnerability. Expect a reply within five business days.

## Supported versions

Only the latest release on `main` gets fixes.
