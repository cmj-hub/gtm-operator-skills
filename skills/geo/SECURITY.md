# Security

## What this pack does on your machine

- One script runs locally: `scripts/score.py`, standard-library Python 3. No dependencies are installed.
- It reads only the draft JSON you pass it (`--file gtm/findability.json`, or the bundled `examples/`). For each `evidence` path in the citation record it checks that the path exists, relative to the draft's folder; it never opens or reads those files. The skill reads `psp.vocabulary` from `brand-config.json` when it exists, and never write to it.
- The skill writes JSON drafts under `gtm/` in your project folder: `gtm/findability.json`, one `gtm/findability/<slug>.json` per further experiment, and the answers you save as evidence in `gtm/evidence/`. Nothing else on disk is changed.
- Network: the script opens no network connection. Two modes may reach public pages through the agent, and only when you run them: `indexability` runs read-only `curl` requests (status, headers, HTML, `robots.txt`, sitemap) against the one URL and site you name; `citation-record` asks the agent to run your buyer question in an answer engine it can reach, or asks you to paste the answer. `allowed-tools` pre-approves only Read, Write, and the scorer; no web tool or `curl`, so your agent asks before each request.
- No telemetry. Nothing is logged or sent anywhere by the pack.
- No credentials are asked for or stored.
- Nothing is published. The pack scores a brief; you ship the page.

## Reporting a vulnerability

Email jay@jaymountconsulting.com with "security" and the repo name in the subject, or open a private advisory under this repo's Security tab. Do not open a public issue for a vulnerability. Expect a reply within five business days.

## Supported versions

Only the latest release on `main` gets fixes.
