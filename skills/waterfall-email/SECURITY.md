# Security

## What this pack does on your machine

- One script runs locally: `skills/waterfall-email/scripts/score.py`, standard-library Python 3. No dependencies are installed.
- It reads only the draft you hand it (`--file gtm/waterfall-email.json` or `--stdin`), or the bundled `examples/`.
- The skill writes one draft, `gtm/waterfall-email.json`, in your project's shared `gtm/` work folder. Nothing else on disk is changed.
- Network: none. No script opens a network connection, and the skill pre-approves no web tool (`allowed-tools` lists only Read, Write, and the scorer). You bring the cascade; the pack does not call a finder or spend a credit.
- No telemetry. Nothing is logged or sent anywhere.
- No credentials are asked for or stored.
- Nothing is sent. The pack scores a waterfall route; it never emails, messages, or exports to a CRM.

## Reporting a vulnerability

Email jay@jaymountconsulting.com with "security" and the repo name in the subject, or open a private advisory under this repo's Security tab. Do not open a public issue for a vulnerability. Expect a reply within five business days.

## Supported versions

Only the latest release on `main` gets fixes.
