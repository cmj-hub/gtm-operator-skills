---
name: waterfall-email
description: "Score a cheapest-first email waterfall: use inputs you hold before any paid finder, stop a row on a 4xx, and refuse sendable until verify says deliverable. Use when the user says: \"find work emails for this list\", \"which finder first\", \"route my enrichment credits\". For the verify gate, see found-vs-deliverable. For ICP checks, see qualify-before-enrich."
argument-hint: "[person or draft | score]"
allowed-tools: Read Write(./gtm/**) Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/score.py:*)
license: MIT
models: ""
---

# Waterfall email

An email waterfall is a cheapest-first cascade that finds a work email for a person you already named. You burn the inputs you hold before any paid finder. A 4xx from a vendor stops the row — you fix the input. Found is not sendable until verify = deliverable.

The build guide teaches a human. This pack teaches an agent.

## Start

If `$ARGUMENTS` is `score`, run the scorer on `gtm/waterfall-email.json` and report each line. Otherwise `$ARGUMENTS` names a person or is empty; work through the checklist. The draft lives at `gtm/waterfall-email.json`; create `gtm/` if missing.

## What you hold

Write one JSON object:

```json
{
  "person": "Ops lead at Northwind",
  "field": "work_email",
  "inputs_held": ["crm email", "company domain", "first.last pattern"],
  "cascade_order": [
    "crm email",
    "company domain",
    "first.last pattern",
    "cheap finder",
    "verify"
  ],
  "on_4xx": "fix_input",
  "rows": [
    {
      "id": "northwind-ops",
      "email": "ops@northwind.example",
      "verify": "deliverable",
      "sendable": true,
      "step_reached": "verify"
    }
  ]
}
```

1. `person`. Who you are finding for.
2. `field`. Almost always `work_email`.
3. `inputs_held`. Data already on the row or in the CRM: an existing address, the company domain, a known pattern. These run first.
4. `cascade_order`. Checks in spend order. Every held input appears before any paid finder. A `verify` step belongs at the end.
5. `on_4xx`. Must be `fix_input` or `stop`. Never `retry_next_vendor`.
6. `rows`. One object per person. `verify` is `deliverable`, `catch-all`, `unknown`, `invalid`, `risky`, or `unverified`. `sendable` is true only when `verify` is `deliverable`.

## Banned

| Banned | Why | Fix |
| --- | --- | --- |
| `on_4xx: retry_next_vendor` | A 4xx is bad input or a blocked request. The next vendor will burn the same broken row. | Set `on_4xx` to `fix_input` or `stop`. Repair the row, then re-run. |
| `sendable: true` while `verify` is not `deliverable` | Found is a guess. Catch-all, unknown, invalid, risky, and unverified are not a send list. | Keep `sendable` false until verify returns `deliverable`. |
| Paid finder before held inputs | You paid for a field you already held. | Put every `inputs_held` name first in `cascade_order`. |

## Kickoff

Copy this list and tick it in order.

- [ ] 1. Name the person and the field (`work_email`).
- [ ] 2. List `inputs_held` — CRM email, domain, pattern — before naming any finder.
- [ ] 3. Write `cascade_order` cheapest-first; end with `verify`.
- [ ] 4. Set `on_4xx` to `fix_input` or `stop`.
- [ ] 5. For each row with an email, set `verify` and `sendable` (true only when deliverable).
- [ ] 6. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/score.py --file gtm/waterfall-email.json`.

Go back to step 2 if step 6 exits 1. Stop when it exits 0.

## Run

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/score.py --file ${CLAUDE_SKILL_DIR}/examples/waterfall-good.json
python3 ${CLAUDE_SKILL_DIR}/scripts/score.py --file ${CLAUDE_SKILL_DIR}/examples/waterfall-4xx-retry.json
python3 ${CLAUDE_SKILL_DIR}/scripts/score.py --file ${CLAUDE_SKILL_DIR}/examples/waterfall-found-unverified.json
```

| File | Exit | Why |
| --- | --- | --- |
| `examples/waterfall-good.json` | 0 | Held inputs first, 4xx stops, verify = deliverable. |
| `examples/waterfall-4xx-retry.json` | 1 | Retries the next vendor after a 4xx. |
| `examples/waterfall-found-unverified.json` | 1 | Marks found sendable before deliverable verify. |
| `examples/waterfall-paid-first.json` | 1 | Paid finder before held inputs. |

Exit 2 means the input could not be read. Broken JSON does not echo the raw input.

Use `--stdin` to pipe the object, and `--json` for one result object (`ok`, `verdict`, `reasons`, `fixes`, `next`).

## Works with the suite

- **Before this:** prospect-list (`/prospect-list:who-to-contact`) names who is worth a slot; qualify-before-enrich refuses a paid lookup on a failing ICP row.
- **With this:** found-vs-deliverable names the verify buckets; this pack owns the cascade order and the 4xx stop.
- **After this:** cold-email (`/cold-email:cold-email`) writes the first touch only to `sendable: true` rows.

Python 3 standard library only. No network. No spend. No send.
