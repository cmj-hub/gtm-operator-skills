# Security

## What this plugin does on your machine

- Installs the ten suite packs as dependencies. Each pack's own SECURITY.md says what it does.
- `/gtm:setup` reads and writes `brand-config.json` and `SOUL.md` at your project root, filling gaps only, and creates an empty `gtm/` folder.
- `/gtm:next` reads `brand-config.json`, `gtm/`, and `drafts/`. It writes nothing.
- No scripts. No network connection. No telemetry. It asks for no credentials and sends, posts, or publishes nothing.

## Reporting a vulnerability

Email jay@jaymountconsulting.com with "security" and the repo name in the subject, or open a private advisory under this repo's Security tab. Do not open a public issue for a vulnerability. Expect a reply within five business days.

## Supported versions

Only the latest release on `main` gets fixes.
