# Changelog

## 0.1.1 — Unreleased

- Bump the installed plugin cache version so existing users can receive this correction.
- Refuse cascades whose final step is not verify, including a finder after an earlier verification. Preserve existing verify-step names, held-input ordering, 4xx policy and row verification rules.

## 0.1.0 — 2026-10-08

- First public MIT release.
- Skill `waterfall-email`: cheapest-first cascade, inputs-you-hold first, kickoff checklist.
- Scorer refuses `on_4xx: retry_next_vendor`, sendable-before-deliverable, and paid-before-held cascades.
- Worked example: Ops lead at Northwind (`examples/waterfall-good.json`).
- Claude Code plugin manifests under `.claude-plugin/`.
