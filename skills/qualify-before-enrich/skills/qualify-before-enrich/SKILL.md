---
name: qualify-before-enrich
description: "Run an ICP field check on every list row before any paid finder or enrichment credit. Refuses a paid lookup on a failing row. Use when the user says: \"clean this list before enriching\", \"credits are burning on bad-fit accounts\", \"should I enrich this row\". For building the ICP, see psp. For writing the email, see cold-email."
argument-hint: "[list path or signal | score]"
allowed-tools: Read Write(./gtm/**) Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/score.py:*)
models: ""
---

# Qualify before enrich

Qualify-before-enrich is the rule that every list row must pass an ICP field check before any paid finder or enrichment credit is spent. A missing industry, wrong company size, or banned title fails the row. Failed rows stay dark. Credits go only to rows that already match.

The build guide teaches a human. This pack teaches an agent.

## Start

If `$ARGUMENTS` is `score`, run the scorer on `gtm/qualify.json` and report each line. Otherwise `$ARGUMENTS` may name a list path or be empty; work the checklist below. The draft lives at `gtm/qualify.json`; create `gtm/` if missing.

## What you hold

One JSON object: an `icp` block and a `rows` array.

```json
{
  "icp": {
    "industries": ["3PL / freight", "warehousing"],
    "employee_min": 50,
    "employee_max": 500,
    "titles_include": ["VP Operations", "Director of Operations", "Head of Ops"],
    "titles_exclude": ["Intern", "SDR", "Recruiter", "Student"],
    "geos": ["US", "CA"]
  },
  "rows": [
    {
      "company": "Northwind Logistics",
      "title": "VP Operations",
      "industry": "3PL / freight",
      "employees": 180,
      "geo": "US",
      "verdict": "enrich"
    }
  ]
}
```

1. `icp`. The pass gate: industries, employee range, titles include/exclude, geos.
2. Each row: `company`, `title`, `industry`, `employees`, `geo`, `verdict`.
3. `verdict` is one of `enrich`, `hold`, or `drop`. Only `enrich` may touch a paid finder.

## Verdicts

| Verdict | Meaning | Paid finder |
| --- | --- | --- |
| `enrich` | All ICP fields present and inside the gate | Allowed |
| `hold` | A required field is missing or blank | Banned until filled |
| `drop` | Fields present and outside the gate | Banned forever for this row |

## Banned patterns

Ship these bans in every run. Do not soften them.

1. **No paid lookup on a failing row.** If expected verdict is `hold` or `drop`, do not call Apollo, ZoomInfo, Hunter, Clay, Clearbit, or any credit-burning finder. Clear `paid_lookup`, `finder_ran`, `enriched`, `enrichment_spent`, and `credits_spent` flags on failing rows.
2. **No inventing ICP fields to pass.** If industry or employee count is unknown, set `hold` and ask. Do not guess Series-B SaaS onto a blank cell.
3. **No enriching a `hold`.** Incomplete is not a soft yes.
4. **No skipping the score step.** Run the scorer before any finder, every batch.
5. **No title-only pass.** A title with no industry, size, or geo is `hold`, never `enrich`.

## ICP from brand-config.json

If `brand-config.json` is at the project root, read `icp` first.

- Map `icp.role_targets` into `titles_include`.
- Map `icp.exclusion_criteria` into `titles_exclude` and industry/geo bans when they are written that way.
- If employee or industry bands live under `icp`, copy them into the draft `icp` block.

If `icp` is missing, say "Run `/gtm:setup` once for the whole suite," or ask only: which industries, which employee band, which titles, which geos. Do not run a long interview here.

## Checklist

Copy this list and tick it in order.

- [ ] 1. Write the `icp` gate into `gtm/qualify.json`.
- [ ] 2. Add every candidate row with the five fields and a claimed `verdict`.
- [ ] 3. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/score.py --file gtm/qualify.json`.
- [ ] 4. Only after exit 0, run a finder on rows whose verdict is `enrich`. Leave `hold` and `drop` dark.

Go back to step 2 if step 3 exits 1. Stop when it exits 0; the last line is `Next: /prospect-list:who-to-contact`. Say it to the user.

The scorer runs from this skill's directory (`${CLAUDE_SKILL_DIR}`). Use `--stdin` to pipe the object, and `--json` for one result object (`ok`, `verdict`, `reasons`, `fixes`, `next`, per-row expected slots).

## Run

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/score.py --file ${CLAUDE_SKILL_DIR}/examples/rows-good.json
python3 ${CLAUDE_SKILL_DIR}/scripts/score.py --file ${CLAUDE_SKILL_DIR}/examples/rows-fail-icp.json
```

| File | Exit | Why |
| --- | --- | --- |
| `examples/rows-good.json` | 0 | ICP pass, verdict enrich, no paid flag. |
| `examples/rows-drop.json` | 0 | Excluded title, verdict drop, finder stays dark. |
| `examples/rows-fail-icp.json` | 1 | Wrong industry + paid lookup on a failing row. |
| `examples/rows-missing-fields.json` | 1 | Blank industry claimed as enrich. |

Exit 2 means the input could not be read: missing file, not UTF-8, broken JSON, or not an object.

## Worked example (15 minutes)

Sample ICP: 3PL / freight or warehousing, 50–500 employees, ops leadership titles, US/CA.

1. Score the good row — exit 0, `Northwind Logistics: enrich`.
2. Score the fail-icp row — exit 1, paid lookup on a failing row (ecommerce retail is outside the gate).
3. Drop yours into `gtm/qualify.json`. Re-score. Only then open a finder on `enrich` rows.

## Works with the suite

This sits in front of list build and first touch (`/plugin marketplace add cmj-hub/gtm-operator-skills`).

- **Reads:** `icp` from `brand-config.json` when present.
- **Writes:** `gtm/qualify.json` only. Never touches `brand-config.json`.
- **Before this:** psp / gtm setup when there is no ICP gate.
- **After this:** prospect-list (`/prospect-list:who-to-contact`) for the signal that earns the slot; cold-email for the first touch.
- **Not this pack:** building the ICP definition itself, sending email, or running the paid finder.

If a companion pack is not installed, name it and its install line; do not do its job inline.

Python 3 standard library only. No network. No paid APIs. No send.
