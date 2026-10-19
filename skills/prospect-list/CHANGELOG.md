# Changelog

## 0.4.0 — 2026-10-04

- The draft lives at `gtm/list.json` (the suite's shared work folder), not a scratch `draft.json`.
- Scorer: every refusal line reads `- what is wrong → what to change`; the last line names the next step (`Next: /cold-email:cold-email` on a pass). `--json` adds `fixes` (parallel to `reasons`) and `next`. `--input` is a hidden alias for `--file`. `--help` shows an example.
- The missing-signal reason now says what to change.
- `argument-hint` and `allowed-tools` (Read, Write, the scorer) in the skill; `/prospect-list:who-to-contact score` scores the existing draft.
- Missing `icp`: the skill points to `/gtm:setup` instead of running its own interview.
- README "In 60 seconds" block. Trigger evals under `evals/` and a manual `evals.yml` workflow. Version synced in `marketplace.json`.

### Moved

- `draft.json` → `gtm/list.json`. The skill and the command (`/prospect-list:who-to-contact`) are unchanged.

## 0.3.1 — 2026-10-04

- Plugin icon: `.claude-plugin/icon.png`, set as `icon` in `plugin.json`.
- `SECURITY.md`: what runs locally, no network, how to report a vulnerability.
- README privacy and security section.

## 0.3.0 — 2026-10-04

- SKILL.md reads `psp.signal_anchors`, `psp.primary_pain`, and `icp`
  from a shared `brand-config.json` when present, and points to the psp
  pack when it is missing.
- New "Works with the suite" section. Description names what belongs
  to cold-email's list hygiene.
- Scorer and examples are called as `${CLAUDE_SKILL_DIR}/...`.
- `models: ""` restored in frontmatter (house rule).
- `marketplace.json` entry carries the version.

## 0.2.0

- Ship as a Claude Code plugin: `.claude-plugin/plugin.json` and a
  single-plugin `marketplace.json`, installable with
  `/plugin marketplace add cmj-hub/claude-prospect-list`.
- Move the skill to `skills/who-to-contact/` so the directory matches the
  skill name and the scorer and examples travel with it.
- Scorer refuses a persona label, a signal that repeats the title, a
  signal under three words, and a score that is not `call this week`,
  `hold`, or `drop`. `call` folds to `call this week`.
- Every refusal prints a `fix:` line naming the gap. A missing title is
  no longer reported as a title-only list.
- `--json` prints a machine-readable result.
- Exit codes are documented: 0 scored, 1 refused, 2 unreadable input.
- SKILL.md: sharper trigger description, signal-vs-label table, slot
  rubric, and a rule not to invent a signal to pass. Dropped the empty
  `models` field.
- New examples: `list-hold.json`, `list-persona.json`.
- Tests cover the new refusals, JSON output, and plugin layout. CI runs
  them on every push.

## 0.1.0

- First release: `who-to-contact` skill and `scripts/score.py`.
