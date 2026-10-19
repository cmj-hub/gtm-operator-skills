# Changelog

## 0.7.0 — 2026-10-04

- The draft lives at `gtm/sequence.json` (the suite's shared work folder), not `draft.json`.
- Scorer: every failing line reads `- gate: field → what to change`; the last line names the next step (`Next: /gtm:next` on a pass). `--json` adds `fixes` (parallel to `reasons`) and `next`. `--input` is a hidden alias for `--file`. `--help` shows an example.
- `/email-sequence:lifecycle-email score` scores the existing draft; `argument-hint` says so.
- README "In 60 seconds" block. Trigger evals under `evals/` and a manual `evals.yml` workflow.
- `plugin.json` drops the `skills` key; default discovery finds `skills/lifecycle-email/`.

### Moved

- `SKILL.md` → `skills/lifecycle-email/SKILL.md`. The skill calls `${CLAUDE_PLUGIN_ROOT}/scripts/score.py`; `scripts/` and `examples/` stay at the repo root. The command `/email-sequence:lifecycle-email` is unchanged.
- `draft.json` → `gtm/sequence.json`.
