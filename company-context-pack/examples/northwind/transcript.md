# Northwind interview transcript

## Contents

- Run
- Interview

## Run

Run: /company-context-pack inputs/northwind-site.md

The user (Dana Whitlock, fictional founder of Northwind Analytics) is simulated from an answer sheet. Date: 2026-10-17.

*Step 1: no context/ folder exists, so this is a fresh run. Step 2: $ARGUMENTS holds inputs/northwind-site.md, so no source question.*

## Interview

**Interviewer:** I will ask a few short questions, one at a time, and skip anything your site or docs already cover. I am reading inputs/northwind-site.md.

*Skipped: question 1 because the site states what is sold (reads billing and support data, flags subscription customers likely to cancel in 60 days, a weekly list with a reason per account).*

**Interviewer:** Your site says the company buyer is a B2B software company with 200 to 2,000 paying accounts, so I will use that. Who is the buyer inside it, by job title? This fills company and icp.

**Dana:** Head of customer success, or VP of customer success. That is who we sell to.

*Skipped: question 3 because the site says a flat monthly fee based on accounts tracked, no per-seat charges, annual plans get two months free.*

**Interviewer:** Your site says a team of eleven, so I will use that. How long have you been selling? This fills Stage in company.

**Dana:** Since mid 2023.

**Interviewer:** Here is what I will write for company.md. Sells churn prediction to B2B software companies with 200 to 2,000 accounts, read from billing and help desk data. Price is a flat monthly fee by accounts tracked, no per-seat charge, annual plans get two months free; team of eleven, selling since mid 2023.
Anything to add or fix?

**Dana:** No, that is right.

**Interviewer:** Which customer segments are best for you? Name one to three. This fills Segments in icp.

**Dana:** Two. Mid-market B2B software with 200 to 2,000 accounts on monthly or annual billing. And vertical software companies, like software for clinics or logistics, where churn comes in clusters.

**Interviewer:** For the best segment, the first one: size, industry, region, and tools they already run? This fills Firmographics in icp.

**Dana:** 50 to 400 employees, North America and the UK. They bill in a card and invoice billing system and run their help desk in a hosted help desk.

**Interviewer:** What happens in a buyer's world that makes them look for you now? Things someone could observe, like a hire, a launch, or a missed target. This fills Buying triggers in icp.

**Dana:** A quarter where churn went up. A new head of customer success hired in the last 90 days. A finance request to forecast renewals, or a recent price increase.

**Interviewer:** Who feels the problem, and who signs? This fills Roles in icp.

**Dana:** The head of customer success feels it. The CFO or COO signs when the plan is over a set amount.

**Interviewer:** Who should we never write to, and why? This fills Disqualifiers in icp.

**Dana:** Companies under 100 paying accounts, because there is too little history to score. Consumer subscription apps. And companies with no billing system.

**Interviewer:** Here is what I will write for icp.md. Two segments, mid-market B2B software and vertical software; firmographics are given for the first only (50 to 400 employees, North America and UK, a card and invoice billing system, a hosted help desk). Triggers: a churn-up quarter, a new CS head, a renewal forecast request, a price increase; head of CS feels it, CFO or COO signs; out: under 100 accounts, consumer apps, no billing system.
Anything to add or fix?

**Dana:** No, that covers it.

**Interviewer:** What are your offers, and what is in each? Include any trial, pilot, or free first step that is not on your site. The site shows only a monthly plan and an annual plan. This fills Offers in offer.

**Dana:** A 30 day pilot on one cohort of accounts, free of charge, so they see the list before buying. Then the monthly plan with the Monday list and the reasons. And the annual plan, two months free.

**Interviewer:** What changes for a buyer after they use you? In their words. This fills Outcomes in offer.

**Dana:** "I know where to spend my team's week." And "I stop finding out about a cancel from the invoice."

**Interviewer:** I read from your site that the first step is to connect billing and your help desk, with setup taking about a week. Is that the first step a buyer takes? This fills How it starts in offer.

**Dana:** Close. They send us a read-only export of billing and tickets for one cohort. Setup takes about a week.

**Interviewer:** Here is what I will write for offer.md. Three offers: a free 30 day pilot on one cohort, the monthly plan with the Monday list and reasons, and the annual plan with two months free. Outcomes are your two quotes; it starts when the buyer sends a read-only export of billing and tickets for one cohort, setup about a week.
Anything to add or fix?

**Dana:** No, that is right.

*Question 13 is partly answered by the site: the Lumen Ledger result and its source (Northwind case study, March 2026) go into proof.md as written.*

**Interviewer:** Your site cites Lumen Ledger, quarterly churn from 6.1 to 4.8 percent over two quarters, from the March 2026 case study. I will use that. Which other results can you cite, and where is each written down? This fills Results in proof.

**Dana:** One more, but I have no written source. It is an internal figure from our own dashboard, that the list catches about two thirds of cancellations 30 days ahead.

**Interviewer:** Your site carries a quote from Priya Raman at Lumen Ledger. Do you have permission to use it, and any other customer quotes you can use? This fills Quotes in proof.

**Dana:** Yes, we have permission for Priya's, it is on the site. That is the only one.

**Interviewer:** Here is what I will write for proof.md. Two results: Lumen Ledger churn from 6.1 to 4.8 percent, sourced to the March 2026 case study; and the two thirds catch figure, marked Source: unverified. One quote, Priya Raman's, sourced to your site; a gap line notes there are no other quotes.
Anything to add or fix?

**Dana:** No, that is fine.

**Interviewer:** Describe how you want to sound in three words, then name words you use and words you never use. This fills Tone, Words we use, Words we avoid in voice.

**Dana:** Plain, direct, a little dry. I use "the list", "accounts", and "why this account". I never say "synergy", "AI-powered", "revolutionary", or "health score".

**Interviewer:** Paste two or three things you wrote that sound like you. I will pick sample lines from them. This fills Sample lines in voice.

**Dana:** "Most churn is visible three weeks early. Nobody is looking at the right tickets." And: "Here is the list. Here is why each account is on it. Go call them."

**Interviewer:** Here is what I will write for voice.md. Tone is plain, direct, a little dry, with a one-sentence description I draft and mark for you to confirm; the use and avoid word lists as you gave them. Sample lines are your two pieces, plus a third I draft and mark (drafted, confirm).
Anything to add or fix?

**Dana:** No, go ahead.

**Interviewer:** What do buyers say before they say yes? Their words, up to five. This fills the objection headings in objections.

**Dana:** "We already have a health score." "We do not have enough data." "Our CSMs know their accounts already." And "How is this different from a dashboard in our BI tool?"

**Interviewer:** Which three of those come up most? For each I will ask what you say back. This fills What we say in objections.

**Dana:** I do not have a count. Take the first three I listed.

**Interviewer:** For "We already have a health score": what do you say back?

**Dana:** I do not have a written answer for that one.

**Interviewer:** For "We do not have enough data": what do you say back?

**Dana:** I do not know that either.

**Interviewer:** For "Our CSMs know their accounts already": what do you say back?

**Dana:** I do not know.

**Interviewer:** Here is what I will write for objections.md. Four objections in your words; the first three get What we say as Unknown (no reply given), the BI dashboard one gets Unknown too; what is true and proof are Unknown for all four since you gave none.
Anything to add or fix?

**Dana:** No, that is fine.

**Interviewer:** What do buyers do today instead of buying from you, and why do they pick it? Kinds of things, not company names. This fills categories.

**Dana:** A customer success platform's built-in health score. A spreadsheet the CS team keeps by hand. A data science project built in house. An analyst request to the BI team. Or doing nothing and reacting to cancellations.

**Interviewer:** Here is what I will write for categories.md. Five categories: a built-in score in a customer success suite, a hand-kept spreadsheet, an in-house data science build, an analyst request to the BI team, and do nothing. Each is listed as a kind of alternative; I have no reasons from you for why buyers pick each, so I will mark the reason Unknown rather than guess.
Anything to add or fix?

**Dana:** That works.

*Step 6: wrote context/company.md, icp.md, offer.md, proof.md, voice.md, objections.md, categories.md, CONTEXT.md. Step 7: ran the checker.*

Checker output:
```
context ok: 1 unverified, 14 unknown
Next: tell your other skills and agents to read context/CONTEXT.md first.
```

**Interviewer:** Done. Files written to context/: CONTEXT.md, company.md, icp.md, offer.md, proof.md, voice.md, objections.md, categories.md. Count: 1 unverified result, 14 unknown answers. To point other agents at it, add one line to your project instructions or any skill prompt: "Read context/CONTEXT.md first."
