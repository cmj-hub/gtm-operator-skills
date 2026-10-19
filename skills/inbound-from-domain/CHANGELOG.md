# Changelog

## 0.1.0 — 2026-10-08

- First public MIT release.
- Skill `inbound-from-domain`: enrich inbound from email domain, route in seconds.
- Kickoff skill with sample loop (good vs CRM-write).
- Deterministic scorer: kinds (`corporate`, `free-mail`, `disposable`, `personal-looking`), routes (`build-review`, `operator-pass`, `need-more`, `personal`, `disqualify`).
- Banned: CRM write-back (`crm_write` must be false); free-mail to Build; disposable kept alive.
- Worked example: `alex@northwind.io` → `build-review`.
- Stdlib Python only. Zero paid APIs. No network.
