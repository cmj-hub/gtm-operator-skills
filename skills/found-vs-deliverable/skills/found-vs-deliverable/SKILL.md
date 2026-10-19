---
name: found-vs-deliverable
description: "Gate a found email behind verify before send. Buckets: deliverable, catch-all, unknown, invalid. Use when the user says: \"can I send to this address\", \"clean my send list\", \"what do I do with catch-all emails\", \"my bounce rate is high\". For finding the address, see waterfall-email. For the email itself, see cold-email."
argument-hint: "[email or row | score]"
allowed-tools: Read Write(./gtm/**) Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/score.py:*)
models: ""
---

# Found vs deliverable

Find then verify. A found address is a candidate. A deliverable address is one you may send to. Catch-all, unknown, and invalid are buckets — they are never "valid."

The build guide teaches a human. This pack teaches an agent.

## Start

If `$ARGUMENTS` is `score`, run the scorer on `gtm/verify.json` and report each line. Otherwise `$ARGUMENTS` names an email or is empty; work through the checklist below. The draft lives at `gtm/verify.json`; create `gtm/` if missing. On bare invocation, load `found-vs-deliverable-kickoff` first if the draft is missing.

## What you hold

Write one JSON object per address:

```json
{
  "email": "alex@northwind.io",
  "stage": "verified",
  "bucket": "deliverable",
  "sendable": true
}
```

1. `email`. The address you found.
2. `stage`. `found` (raw hit) or `verified` (a verify result exists).
3. `bucket`. One of: `deliverable`, `catch-all`, `unknown`, `invalid`.
4. `sendable`. `true` only when `stage` is `verified` and `bucket` is `deliverable`.

## Buckets

| Bucket | Meaning | Sendable? |
| --- | --- | --- |
| `deliverable` | Mailbox accepts mail for this address | Yes, after verify |
| `catch-all` | Domain accepts any local-part; mailbox may not exist | Never |
| `unknown` | Verify could not settle the row | Never |
| `invalid` | Syntax fail, MX fail, or known undeliverable | Never |

## Banned patterns

Copy these. Do not soften them.

- **Never send catch-all as "valid."** A catch-all is a bucket, not a green light. `sendable` stays `false`.
- **Found is not sendable until verify = deliverable.** A raw find (`stage: found`) keeps `sendable: false` until a verify returns `deliverable`.
- **Unknown is not deliverable.** Do not promote `unknown` to `deliverable` to clear a queue.
- **Invalid is not deliverable.** Drop or fix; do not send.

| Passes | Refused |
| --- | --- |
| verified + deliverable + sendable true | catch-all + sendable true |
| verified + catch-all + sendable false (held) | found + sendable true |
| found + sendable false (held found) | unknown or invalid + sendable true |

## Checklist

Copy this list and tick it in order.

- [ ] 1. Write the found address into `email` with `stage: found`, a starting `bucket` (usually `unknown`), and `sendable: false`.
- [ ] 2. Run your verifier (you bring the tool; this pack does not call a paid API). Set `stage: verified` and the real `bucket`.
- [ ] 3. Set `sendable: true` only when `bucket` is `deliverable`. Otherwise keep `sendable: false`.
- [ ] 4. Write the object to `gtm/verify.json` (create `gtm/` if missing).
- [ ] 5. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/score.py --file gtm/verify.json`.

Go back to step 3 if step 5 exits 1. Stop when it exits 0. On a deliverable pass the last line is `Next: /cold-email:cold-email`. On a held bucket it says to keep the row in its bucket.

The scorer runs from this skill's directory (`${CLAUDE_SKILL_DIR}`). Use `--stdin` to pipe the object, and `--json` for one result object (`ok`, `verdict`, `reasons`, `fixes` parallel to `reasons`, `next`). Alias key `verify` is accepted for `bucket`.

## Run

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/score.py --file ${CLAUDE_SKILL_DIR}/examples/verify-good.json
python3 ${CLAUDE_SKILL_DIR}/scripts/score.py --file ${CLAUDE_SKILL_DIR}/examples/verify-catchall.json
```

| File | Exit | Why |
| --- | --- | --- |
| `examples/verify-good.json` | 0 | Verified deliverable, sendable. |
| `examples/verify-held-catchall.json` | 0 | Catch-all held — sendable false. |
| `examples/verify-catchall.json` | 1 | Catch-all marked sendable. |
| `examples/verify-found.json` | 1 | Found marked sendable. |
| `examples/verify-unknown.json` | 1 | Unknown marked sendable. |
| `examples/verify-invalid.json` | 1 | Invalid marked sendable. |

Exit 2 means the input could not be read: missing file, not UTF-8, broken JSON, or not an object. A broken JSON does not echo the raw input.

## Works with the suite

Part of the GTM operator suite (`/plugin marketplace add cmj-hub/gtm-operator-skills`).

- **Writes:** `gtm/verify.json` only. Never touches `brand-config.json`.
- **Before this:** prospect-list (`/prospect-list:who-to-contact`) when you still need who to contact; qualify-before-enrich when ICP fields fail before any find.
- **After this:** cold-email (`/cold-email:cold-email`) for each `sendable: true` row.
- **Not this pack:** domain SPF/DKIM/DMARC health is cold-email deliverability. Dedup and role-fit hygiene of a full CSV is cold-email list quality. This pack gates one found address through verify buckets.

If a companion pack is not installed, name it and its install line (`/plugin install <name>@gtm-operator-skills`); do not do its job inline.

Python 3 standard library only. No network. No send. No paid verifier API inside the pack — you bring the verify result; the pack scores the gate.
