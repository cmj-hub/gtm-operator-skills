# Security

This repo is the marketplace for the GTM operator suite. Each pack is its own repo with its own `SECURITY.md`, which says exactly what that pack runs, reads, writes, and reaches:

- [psp](https://github.com/cmj-hub/claude-psp/blob/main/SECURITY.md)
- [evp](https://github.com/cmj-hub/claude-evp/blob/main/SECURITY.md)
- [prospect-list](https://github.com/cmj-hub/claude-prospect-list/blob/main/SECURITY.md)
- [cold-email](https://github.com/cmj-hub/claude-cold-email/blob/main/SECURITY.md)
- [sales-offer](https://github.com/cmj-hub/claude-sales-offer/blob/main/SECURITY.md)
- [pricing](https://github.com/cmj-hub/claude-pricing/blob/main/SECURITY.md)
- [landing-page](https://github.com/cmj-hub/claude-landing-page/blob/main/SECURITY.md)
- [email-sequence](https://github.com/cmj-hub/claude-email-sequence/blob/main/SECURITY.md)
- [geo](https://github.com/cmj-hub/claude-geo/blob/main/SECURITY.md)
- [founder-brand](https://github.com/cmj-hub/claude-founder-brand/blob/main/SECURITY.md)
- [build-pack](build/SECURITY.md)

## What this repo does on your machine

- `.claude-plugin/marketplace.json` lists the packs. Adding the marketplace installs nothing until you install a pack.
- `build/scripts/check_pack.py` (the build-pack gate) is standard-library Python. It reads the pack directory and cards you name, never edits them, and opens no network connection.
- `scripts/check_suite.py` is standard-library Python. It runs locally, against clones you already have: the gate, each pack's own tests, `git ls-files`, and, when the `claude` CLI is on your PATH, `claude plugin validate --strict` and `claude plugin details`. It opens no network connection itself.
- `tests/` and `build/tests/` are standard-library unit tests on throwaway directories. No network.
- `assets/card.mjs` and `assets/demo.mjs` regenerate the README artwork for maintainers only. They load Google Fonts when run. No pack uses them.
- No telemetry, no credentials asked for or stored, and nothing sent, posted, or published by any script here.

## Reporting a vulnerability

Email jay@jaymountconsulting.com with "security" and the repo name in the subject, or open a private advisory under this repo's Security tab. Do not open a public issue for a vulnerability. Expect a reply within five business days.

## Supported versions

Only the latest release on `main` gets fixes.
