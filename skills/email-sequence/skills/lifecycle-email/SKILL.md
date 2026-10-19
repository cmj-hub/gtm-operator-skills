---
name: lifecycle-email
description: "Draft and score a lifecycle email sequence for people who already opted in: welcome, delivery of the bargain, then nurture tied to the pain they showed. Use when the user says: \"welcome email\", \"onboarding sequence\", \"nurture sequence\", \"what do I send after the lead magnet\", \"my drip feels generic\". For cold outreach to people who never opted in, see cold-email."
argument-hint: "[the pain they showed | score]"
allowed-tools: Read Write(./gtm/**) Bash(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py:*)
models: ""
---

# Lifecycle email

Someone raised a hand. The sequence has three parts, in this order. Welcome them. Hand over the thing they opted in for. Then keep writing about the pain they already showed.

The build guide teaches a human. This pack teaches an agent.

## Start

If `$ARGUMENTS` is `score`, run the scorer on `gtm/sequence.json` and report each line. Otherwise `$ARGUMENTS` is the pain they showed, or empty; draft the sequence with the checklist below. The draft lives at `gtm/sequence.json`; create `gtm/` if missing.

## From brand-config.json

If `brand-config.json` sits at the project root, read it before drafting. Read only. This pack writes nothing to it.

- `psp.vocabulary` is the buyer's own words. Name the pain in those words, and repeat them in the nurture.
- `evp.primary` and `evp.outcome` say what the bargain delivers. The welcome can point at them; it does not pitch them.

The pain they showed on the form or in the reply still wins over the profile. If a block is missing, use what the user gives you and say which pack makes it: `/plugin install psp@gtm-operator-skills` or `/plugin install evp@gtm-operator-skills`. Do not invent vocabulary or an offer line.

## The three parts

1. Welcome. The first note after the opt-in. It names that they asked (asked, requested, opted in, signed up, downloaded), and it starts the relationship. It is not an introduction to a stranger.
2. Bargain. Delivery of the thing they were promised: the checklist, the sample, the access. The bargain is the exchange, handed over.
3. Nurture. Later notes that stay on the pain they showed on the form or in the reply. The pain is in the words. A calendar of tips is not nurture.

## What the scorer refuses

The scorer refuses a generic drip and a cold email. A generic drip is a day-1, day-3, day-7 tip series, or a note that calls itself a generic drip. A cold email speaks to someone who never opted in, introduces a product to a stranger, or is labeled a cold email.

A welcome can be short. It still has to be for a person who opted in, and the nurture still has to name their pain. The three bodies must be three different notes.

Subjects are optional: `welcome_subject`, `bargain_subject`, `nurture_subject`. Give all three or none. They must differ, and the nurture subject must name the pain.

## Checklist

Copy this list and tick it in order.

- [ ] 1. Name the pain they showed.
- [ ] 2. Fill the sequence shell: welcome, bargain, nurture.
- [ ] 3. Write the draft to `gtm/sequence.json` (create `gtm/` if missing) and run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --file gtm/sequence.json`.
- [ ] 4. Fix every line the scorer prints under the verdict, then run it again.

Check again until the script exits 0. Show the user the three parts it prints.

## Reading a failure

The first line is the verdict. Each line under it reads `- gate: field → what to change`. The last line is `Next: fix the lines above and run this again.` Fix them all before the next run.

| Line | Fix |
| --- | --- |
| `generic drip: <part> says "..."` | Drop the day-1/day-3/day-7 schedule or tip-series framing. Write to their pain, not the calendar. |
| `cold email: <part> says "..."` | They opted in. Stop introducing the product to a stranger; name what they asked for. |
| `missing: <fields>` | Fill every one of `pain`, `welcome`, `bargain`, `nurture` with text, and all three subjects once one is given. |
| `pain mismatch` | Repeat the `pain` phrase inside `nurture` (and `nurture_subject`, if given), in their words. Case, spacing, and end punctuation do not matter. |
| `not three notes` | Welcome, bargain, and nurture are the same text. Write each one for its own job. |
| `no opt-in` | Say in the welcome that they asked, requested, opted in, signed up, or downloaded. |
| `subjects repeat` | Give each note its own subject line. |

Exit 0 passes. Exit 1 is refused or incomplete. Exit 2 means the input was not a readable JSON object.

Do not game the scorer by swapping a flagged phrase for a synonym. If the note is a drip or a cold email, rewrite it.

## Banned: found is not sendable

A found email is not sendable until verify returns deliverable. Catch-all and unknown stay off the send list. This pack scores the sequence; verification is a separate step before any send.

## Run

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --file ${CLAUDE_PLUGIN_ROOT}/examples/lifecycle-good.json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --file ${CLAUDE_PLUGIN_ROOT}/examples/lifecycle-refused.json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --file ${CLAUDE_PLUGIN_ROOT}/examples/lifecycle-subjects.json
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/score.py --file ${CLAUDE_PLUGIN_ROOT}/examples/lifecycle-subjects-refused.json
```

`${CLAUDE_PLUGIN_ROOT}` is the plugin's folder; from a clone, run the same commands from the repo root without the prefix.

The good file exits 0 and prints the welcome, the bargain, the nurture, and `Next: /gtm:next`. The subjects file also passes and prints each subject. The refused files exit 1 and list each gate they failed. Add `--json` for one result object (`pass`, `verdict`, `reasons`, `fixes` parallel to `reasons`, `next`), or pipe the draft with `--stdin`.

The JSON object has four strings: `pain`, `welcome`, `bargain`, and `nurture`, plus the three optional subject strings. A broken JSON exits non-zero and does not echo the raw input.

Python 3 standard library only. No network. No send.

## Works with the suite

This is step 8 of the GTM operator suite (`/plugin marketplace add cmj-hub/gtm-operator-skills`).

- **Reads:** `psp.vocabulary` and `evp` from `brand-config.json`, if present.
- **Writes:** `gtm/sequence.json` only. It never touches another pack's keys.
- **Before this:** landing-page (`/landing-page:page`), when there is no opt-in page yet.
- **Not this:** cold outreach to people who never opted in goes to cold-email (`/cold-email:cold-email`). Re-engaging stalled cold prospects is `cold-email-nurture` in that pack.

When the sequence passes, end with `Next: /gtm:next` (the suite hub names what is left). If a companion pack is not installed, name it and its install line (`/plugin install <name>@gtm-operator-skills`); do not do its job inline.

## Example draft

```json
{
  "pain": "the trial dies after the first login",
  "welcome": "You asked for the trial checklist. This note starts there.",
  "bargain": "The checklist is the bargain. It is attached, the thing you opted in to receive.",
  "nurture": "The next note stays on the pain you showed: the trial dies after the first login."
}
```
