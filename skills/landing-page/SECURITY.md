# Security

## What this pack does on your machine

- One script runs: `scripts/score.py`, Python 3 standard library only, on your machine.
- The script reads only the draft JSON you pass with `--file` or `--stdin`. It caps input at 2 MB and does not echo bad input.
- The skill reads `brand-config.json` at your project root, if present, for `evp` and `pricing`. It never writes to it or to `SOUL.md`.
- The skill writes one file: the draft (`gtm/page.json`) in your project. Nothing else is created.
- Network: None. No script opens a network connection. The URL in a draft is parsed as text, never fetched.
- No telemetry. No credentials are asked for or stored.
- Nothing is sent, posted, or published. You publish the page; this pack only scores the draft.

## Reporting a vulnerability

Email jay@jaymountconsulting.com with "security" and the repo name in the subject, or open a private advisory under this repo's Security tab. Do not open a public issue for a vulnerability. Expect a reply within five business days.

## Supported versions

Only the latest release on `main` gets fixes.
