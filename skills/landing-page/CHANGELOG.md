# Changelog

## 0.7.0 — 2026-10-04

- The draft lives at `gtm/page.json` (the suite's shared work folder), not `draft.json`.
- Scorer: every failing line reads `- problem → fix`; the last line names the next step (`Next: /email-sequence:lifecycle-email` on a pass). `--json` adds `fixes` (parallel to `problems`) and `next`. `--input` is a hidden alias for `--file`. `--help` shows an example.
- `/landing-page:page score` scores the existing draft; `argument-hint` says so.
- README "In 60 seconds" block. Trigger evals under `evals/` and a manual `evals.yml` workflow.
- `plugin.json` drops the `skills` key; default discovery finds `skills/page/`.

### Moved

- `SKILL.md` → `skills/page/SKILL.md`. The skill calls `${CLAUDE_PLUGIN_ROOT}/scripts/score.py`; `scripts/` and `examples/` stay at the repo root.
- `draft.json` → `gtm/page.json`.

## 0.6.0 — 2026-10-04

- Optional `headline`: one sentence, no URL, shares a word with the offer.
- Optional `proof`: one non-empty line.
- `SKILL.md` maps `evp.primary` to the headline and `evp.proof` to proof.
- New examples: `page-headline.json` passes, `page-headline-refused.json` fails.
- `SECURITY.md` and a README privacy section.

## 0.5.0 — 2026-10-04

- `plugin.json` lists `"skills": ["./"]` so the root skill loads explicitly.
- `SKILL.md` adds `models: ""`, a not-for clause, and reads `evp` and
  `pricing` from `brand-config.json` when present; never invents them.
- "Works with the suite" section: step 7, hands off to email-sequence
  and geo.
- README adds the suite marketplace and `npx skills add` install lines.
- Manifest: author URL, keywords, `gtm`.

## 0.4.0

- Scorer checks what the docs promise: one https URL with a host, one
  offer, one action. A list, an `offers` / `actions` / `ctas` key, or a
  second sentence fails.
- Offer is capped at 200 characters and action at 160.
- A failing draft lists every problem, one per line, after `draft fails`.
- `--json` prints one result object.
- Sitemap detection also catches a `pages` list, a list in `url`, and
  `.xml` paths.
- Unusable input (missing file, broken JSON, not an object) exits 2.
- New example: `examples/page-two-offers.json`.
- `SKILL.md` calls the scorer through `${CLAUDE_SKILL_DIR}` so it runs
  from an installed plugin, adds trigger phrases and writing rules, and
  drops the invalid `models` field.
- `plugin.json` adds `repository` and `keywords`.
- Tests run in GitHub Actions.

## 0.3.0

- Plugin icon and manifest.
