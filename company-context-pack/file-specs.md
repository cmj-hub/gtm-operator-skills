# File specs

Each file opens with a `#` title and a line `Updated: YYYY-MM-DD`. Keep each under about 60 lines. Agents read these every session, so short beats thorough.

## Contents

- company.md
- icp.md
- offer.md
- proof.md
- voice.md
- objections.md
- categories.md
- CONTEXT.md

## company.md

What we sell, to whom, and the price model in words.

- `## What we sell`: two sentences, no adjectives.
- `## Who buys`: one sentence naming the buyer and their company.
- `## Price model`: in words (per seat, per project, monthly fee, usage based). A number only if the user gave one and it is public.
- `## Stage`: team size and how long it has been selling.

## icp.md

Who to write for, and who not to.

- `## Segments`: one bullet per segment. Each has a name and a one-line description.
- `## Firmographics`: size, industry, geography, stack, for each segment.
- `## Buying triggers`: the events that make a buyer look now. Each is something a person could observe.
- `## Roles`: who feels the problem, who signs.
- `## Disqualifiers`: who is out, and why.

## offer.md

What the buyer gets.

- `## Offers`: one bullet per offer: name, what is included, who it is for.
- `## Outcomes`: what changes for the buyer, in their words. Results go in proof.md, not here.
- `## How it starts`: the first step a buyer takes.

## proof.md

Results the user can cite. Each is one bullet in this shape:

```text
- Cut no-shows from 22 to 14 percent over one quarter. Source: customer interview, 2026-03-02.
- Setup took five days on average. Source: unverified
```

A bullet with no `Source:` is refused by the checker. Group bullets under `## Results`, and put quotes under `## Quotes` with the same shape. Say what is missing under `## Gaps` as plain lines, not bullets.

## voice.md

How we sound.

- `## Tone`: three adjectives and one sentence on how they show up (drafted, confirm).
- `## Words we use`: bullets.
- `## Words we avoid`: bullets, with the reason if the user gave one.
- `## Sample lines`: three lines in the user's voice. Use their own writing when a source has it. Mark a line you wrote as `(drafted, confirm)`.

## objections.md

What buyers say before they buy.

- One `##` heading per objection, in the buyer's words.
- One heading for every objection from question 17. The three from 17b get the user's reply under `What we say`. The rest get `Unknown:`.
- Also under each: what is true (only if the user said), and the proof it points at (a line from proof.md, or `Unknown:`).

## categories.md

The alternatives a buyer weighs, as categories.

- One bullet per category: the kind of alternative and why a buyer picks it. Add where it falls short for our buyer only if the user said so.
- Include "do nothing" and "build it in house" if they apply.
- No company or product names. No links.

## CONTEXT.md

The index. Any other skill or agent reads this first.

- A first line: "Read these files before writing anything about this company."
- A bullet per file with a link and one line on when to use it.
- A line on the proof rule: results in proof.md without a source are marked unverified, so do not state them as fact.
- The folder's last-updated date.
