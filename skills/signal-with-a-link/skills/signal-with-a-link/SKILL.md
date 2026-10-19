---
name: signal-with-a-link
description: "Score a buying signal as a dated, linkable event; refuse an intent score without a URL and a date. Use when the user says: \"is this a real signal\", \"can I cite this\", \"what should I anchor my email on\". For the five-part profile, see psp. For the email, see cold-email. For who to call, see who-to-contact."
argument-hint: "[kickoff | validate | score | event-or-url]"
allowed-tools: Read Write(./gtm/**) Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/score.py:*)
license: MIT
models: ""
---

# Signal with a link

A signal is a **dated, linkable event**. Something the prospect (or their company) did publicly, on a day you can name, at a URL you can open.

**Banned:** no intent score without a URL and a date.

The build guide teaches a human. This pack teaches an agent.

## Start here — every invocation

> **Scoring something pasted needs no setup.** If the operator handed you a JSON object, a draft path, or a claim to score, run the scorer first and report every line. Offer kickoff afterwards.

1. If `$ARGUMENTS` is `validate`, `score`, or empty with a draft at `gtm/signal.json`, run the scorer and stop.
2. If `$ARGUMENTS` is `kickoff` or `setup`, run the kickoff checklist below.
3. Otherwise treat `$ARGUMENTS` as a company, an event, or a URL, and work the checklist.

The draft lives at `gtm/signal.json`. Create `gtm/` if it is missing.

## What you hold

One JSON object:

```json
{
  "company": "Northwind",
  "event": "Posted a Demand Gen Lead role on LinkedIn",
  "url": "https://www.linkedin.com/jobs/view/4019283741",
  "date": "2026-10-04",
  "source_type": "job_post"
}
```

| Field | Required | Rule |
|---|---|---|
| `event` | yes | The observable thing they did. Not a costume label. |
| `url` | yes | A public `http` or `https` page someone else can open. |
| `date` | yes | ISO `YYYY-MM-DD` of the day the event was published. ≤90 days old. |
| `company` | no | Who did it. |
| `source_type` | no | `job_post`, `funding`, `launch`, `hire`, `pricing_change`, `content`, other. |
| `intent_score` | no | Allowed **only** when both `url` and `date` are present. |

## Signal or not

| Signal (passes) | Not a signal (refused) |
|---|---|
| Posted a Demand Gen Lead role — with LinkedIn job URL + date | "Series B company" |
| Announced Series B on TechCrunch yesterday — with article URL + date | "VP of Marketing" |
| Shipped enterprise pricing — with changelog URL + date | Intent score 87 with no link |
| Hired a new CRO — with press URL + date | A job post with no date |
| Pricing page flipped to "Contact us" — with archive or page URL + date | A funding rumor with no URL |

State is not a signal. A dated link is.

## Banned pattern list

Refuse these before you invent a workaround:

1. **Intent score without URL and date.** Drop the score, or add both fields.
2. **Firmographic costume.** Series stage, headcount, "ICP fit", "high intent", title-only.
3. **Undated claim.** "They hired recently" with no day.
4. **Unlinkable claim.** "I saw it on LinkedIn" with no URL.
5. **Stale link.** Date older than 90 days — find a fresher event.
6. **Future date.** Use the publish day, not tomorrow.

## Kickoff (15 minutes)

Copy this list and tick it in order.

- [ ] 1. Pick one account from your book (or use the Northwind sample).
- [ ] 2. Find one public thing they did in the last 90 days.
- [ ] 3. Paste the page URL. Write the event in one sentence. Write the ISO date.
- [ ] 4. Save as `gtm/signal.json`.
- [ ] 5. Run `python3 ${CLAUDE_SKILL_DIR}/scripts/score.py --file gtm/signal.json`.

Go back to step 3 if step 5 exits 1. Stop when it exits 0; the last line is `Next: /psp:psp`. Say it to the user.

Do not invent a URL. If you cannot open a page, you do not have a signal yet — leave the account off and say so.

## Validate

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/score.py --file gtm/signal.json
python3 ${CLAUDE_SKILL_DIR}/scripts/score.py --file ${CLAUDE_SKILL_DIR}/examples/signal-good.json --as-of 2026-10-08
```

`${CLAUDE_SKILL_DIR}` is this skill's folder. On a plain-skills install, use `scripts/score.py` from the pack root's `skills/signal-with-a-link/`. The scorer is stdlib Python — no network, no key. Add `--json` for one result object. Add `--as-of YYYY-MM-DD` to freeze freshness (tests and demos).

Exit 0 means a dated, linkable signal. Exit 1 means fix the flagged lines first: every reason prints as `- what is wrong → what to change`. Exit 2 means unreadable input.

## Worked example

Score the sample good draft against a fixed day:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/score.py --file ${CLAUDE_SKILL_DIR}/examples/signal-good.json --as-of 2026-10-08
```

| File | Exit | Why |
|---|---|---|
| `examples/signal-good.json` | 0 | Dated LinkedIn job post with a URL. |
| `examples/signal-with-intent.json` | 0 | Intent score allowed because URL + date are present. |
| `examples/signal-no-url.json` | 1 | Event + date, no link. |
| `examples/signal-no-date.json` | 1 | Event + URL, no date. |
| `examples/signal-intent-only.json` | 1 | Intent score with neither URL nor date. |
| `examples/signal-firmographic.json` | 1 | "Series B" is state, not an event. |

## Works with the suite

- **Writes:** `gtm/signal.json` only. Never touches `brand-config.json`.
- **Before this:** nothing required. Kickoff is enough.
- **After this:** psp (`/psp:psp`) to turn the signal into a five-part Pain Signal Profile; prospect-list (`/prospect-list:who-to-contact`) to put a person on this week's list; cold-email (`/cold-email:cold-email`) once the PSP and slot are set.
- **Not this pack:** writing the email, building the full PSP, buying intent data, or live LinkedIn hunt.

If a companion pack is not installed, name it and its install line (`/plugin install <name>@gtm-operator-skills`); do not do its job inline.

Python 3 standard library only. No network. No paid APIs.
