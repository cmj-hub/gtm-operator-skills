---
name: found-vs-deliverable-kickoff
description: "Router for the found-vs-deliverable pack. Use when the user says: \"where do I start\", \"is this email sendable\", bare /found-vs-deliverable. Names the next step: score the sample, draft a found row, or run verify. For the scoring itself, see found-vs-deliverable."
argument-hint: "[status | sample]"
allowed-tools: Read Bash(python3 */skills/found-vs-deliverable/scripts/score.py:*)
models: ""
---

# Found vs deliverable — kickoff

Fifteen minutes. One address. Find then verify.

## Start

1. If `$ARGUMENTS` is `sample`, run the good and catch-all examples and show both exits.
2. If `$ARGUMENTS` is `status`, report whether `gtm/verify.json` exists and what the scorer says.
3. Otherwise detect state and route.

## State

| State | Next |
| --- | --- |
| No `gtm/verify.json` | Score the samples first (below), then draft one found row with `sendable: false`. |
| Draft exists, never scored | Run `found-vs-deliverable` with `score`. |
| Score exits 1 | Fix the `- … → …` lines; re-score. |
| Score exits 0, `sendable: true` | Say `Next: /cold-email:cold-email`. |
| Score exits 0, held bucket | Keep the row in its bucket. Do not send. Offer to draft the next found address. |

## Sample loop (the worked example)

```bash
python3 skills/found-vs-deliverable/scripts/score.py --file skills/found-vs-deliverable/examples/verify-good.json
python3 skills/found-vs-deliverable/scripts/score.py --file skills/found-vs-deliverable/examples/verify-catchall.json
```

Good exits 0: verified deliverable, sendable. Catch-all exits 1: never send catch-all as valid. Then write yours to `gtm/verify.json`.

## Welcome

```
Find then verify.

Buckets: deliverable | catch-all | unknown | invalid
Banned: never send catch-all as "valid". Found is not sendable until verify = deliverable.

1. Score the sample (good vs catch-all)     ← start here
2. Draft one found row (sendable false)
3. Bring a verify result; set the bucket
4. sendable true only when bucket is deliverable
5. Score gtm/verify.json

Ready to score the sample?
```

## Rules to repeat

- Catch-all, unknown, and invalid stay `sendable: false`.
- `stage: found` stays `sendable: false` until verify returns deliverable.
- This pack does not call a paid verifier. You bring the bucket; the scorer gates send.
