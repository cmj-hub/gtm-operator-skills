# Worked example: two homepage lines become proof

A sample, not a client. The companies and people are made up.

## What the homepage said

```text
Tripled pipeline for a leading SaaS brand.
"Amazing team, highly recommend!" (Happy customer)
```

`examples/proof-vague.json` holds both. The scorer refuses eight times:

```bash
python3 scripts/score_proof.py --file examples/proof-vague.json --as-of 2026-10-17
```

```text
- a1 is a result with no before and after → a result is a change: give both numbers, with the unit
- a1 has no number → add it, or call it a testimonial
- a1 claims a multiple with no two numbers behind it → show before and after; the reader does the division
- a1 has no timeframe → say over how long, e.g. first 60 days
- a1 has no source → name what a reader could be shown: a report, a dashboard export, an email, a public page
- a1 has no permission at all → ask before you use it, even unnamed; a buyer can recognise their own numbers
- a1 has no ISO date → when was this measured or said, YYYY-MM-DD
- a2 is praise with nothing in it → ask them what changed, and quote the sentence with the number or the task in it
```

"Tripled" is the line a doubting buyer stops on. Tripled from what? Over how long? Says who?

## Step 1: find the numbers

The founder opened the CRM export the customer had shared. "Pipeline" turned out to be a looser word than the work. What actually moved was reply time on inbound demo requests: two days before, four hours after, over the first 60 days.

That claim is smaller than "tripled pipeline", and the founder can show it.

## Step 2: ask the customer

`ask` mode drafted this. The founder sent it.

```text
Subject: one question about the demo requests

Hi Priya,

Quick one. What were you doing with Friday demo requests before,
and what changed?

If it's all right, I'd like to quote your answer on our site with
your name and title. A yes in reply is all I need. A no is fine too.
```

The reply: "We stopped losing Friday demo requests to Monday. Every one gets a reply the same day. Happy for you to use that with my name."

## Step 3: the assets

```text
a1 result      2 days → 4 hours, time to first reply, first 60 days
               Head of Sales, 30-person logistics software company
               unnamed · verbal · CRM export · 2026-09-30
a2 testimonial "We stopped losing Friday demo requests to Monday..."
               Priya Shah, Head of Sales, Harbor Logistics (sample)
               named · written · her email · 2026-10-03
a3 metric      412 requests routed in Q3, median reply 3 h 50 min
               unnamed · verbal · routing log · 2026-10-01
```

```bash
python3 scripts/score_proof.py --file examples/proof-good.json --as-of 2026-10-17
```

```text
pass: 3 proof asset(s) a buyer can check
Next: /landing-page:page for the proof block; /founder-brand:founder-brand for a proof post; /cold-email:cold-email for one line of it.
```

## What changed

The new lines are smaller. They are also true, dated, checkable, and agreed. "Amazing team" told the reader the customer was polite. "Every one gets a reply the same day" tells the reader what they would get.
