# Changelog

## 0.7.0 — 2026-10-04

- The draft lives at `gtm/offer.json` (the suite's shared work folder), not a scratch `draft.json`.
- Scorer: every failing line reads `- what is wrong (phrase) → what to change`; the last line names the next step (`Next: /landing-page:page` on a pass). `--json` adds `next`; each failure already carries `fix`. `--input` is a hidden alias for `--file`. `--help` shows an example.
- `/sales-offer:cold-offer score` scores the existing draft; `argument-hint` says so.
- README "In 60 seconds" block. Trigger evals under `evals/` and a manual `evals.yml` workflow.

### Moved

- `draft.json` → `gtm/offer.json`. The skill and the command (`/sales-offer:cold-offer`) are unchanged.
