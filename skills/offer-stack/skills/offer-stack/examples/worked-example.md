# Worked example: a feature list becomes a stack

A sample, not a client. The company and the call are made up. The method is the one in the context file.

## What the founder sent

```text
What's included:
- AI note-taker
- Unlimited dashboards and much more
- Premium support
Money back if you're not satisfied.
```

`examples/stack-feature-list.json` holds it. The scorer refuses it seven times. Three of those carry the lesson:

```text
- pain p1 has no number for count, cost_each, period → how many times, for how many people, at what cost each, per day/week/month/quarter/year
- component 'Premium support' removes no pain → tie it to a pain id, or cut it
- risk reversal rests on satisfaction → tie it to an outcome you can check by a date
```

The list describes the product. It does not say what stops hurting, or by how much.

## The call

The founder asked the five questions on a discovery call with a Head of RevOps at a 40-rep software company. The answers, as written down:

1. **What do you do today instead?** "Reps type their notes into the CRM after each call. The managers spend the forecast call arguing about whose numbers are right."
2. **How often?** "Three hours a week per rep, give or take. The forecast call is weekly, two hours."
3. **How many people?** "Forty reps. Six managers on the forecast."
4. **What does an hour cost you?** "Call it 55 an hour loaded for a rep. 120 for a manager."
5. **What if it's still like this next quarter?** "We lose another quarter of selling time to admin."

A third pain came up but got no number: deals stalling after the demo. The founder wrote it as an assumption and put it on the list for the next call.

## The stack

```text
p1: 3 hours x 40 people x $55 x 52 weeks = $343,200 a year
p2: 2 hours x 6 people x $120 x 52 weeks = $74,880 a year
p3: 2 deals x $3,000 x 12 months = $72,000 a year
pain total: $490,080 a year
price: $48,000 a year, against $490,080 of pain (10.2x the price)
pass: every component removes a numbered pain
```

| Component | Removes |
|---|---|
| Call notes written to the CRM within ten minutes of each call | p1 |
| One forecast view every manager reads from, refreshed before the call | p2 |
| A follow-up task on every deal with no touch three days after a demo | p3 |

The guarantee now names something the buyer can check: "If notes are not in the CRM within ten minutes for 90% of calls by day 30, month two is free."

"Unlimited dashboards" and "premium support" are gone. Nobody on the call said either one would stop a pain.

## What to say, and what not to

The $343,200 is rep time, not cash. The company does not pay the reps less. So the founder says "worth $343,200 a year in selling time", and never "saves you $343,200".

p3 rests on an assumption. Until the buyer confirms it, the founder leads with p1 and p2, which the buyer said out loud.

## Next

The pain total goes to the pricing page as the status-quo anchor: `/pricing:pricing anchor`. The top pain opens the first touch: `/sales-offer:cold-offer`.
