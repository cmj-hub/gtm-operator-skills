# Buying signal skill for Claude Code

A buying signal is a dated, linkable event — something the prospect did publicly, on a day you can name, at a URL you can open. State is not a signal. An intent score without a URL and a date is refused.

## In 60 seconds

```text
/plugin marketplace add cmj-hub/claude-signal-with-a-link
/plugin install signal-with-a-link@claude-signal-with-a-link
/signal-with-a-link:signal-with-a-link kickoff
```

Or score the sample without an agent:

```bash
python3 skills/signal-with-a-link/scripts/score.py --file skills/signal-with-a-link/examples/signal-good.json --as-of 2026-10-08
# exit 0 → a dated, linkable signal → Next: /psp:psp

python3 skills/signal-with-a-link/scripts/score.py --file skills/signal-with-a-link/examples/signal-intent-only.json --as-of 2026-10-08
# exit 1 → intent score without a URL and a date
```

The build guide teaches a human. The pack teaches an agent.

```text
GOOD  Posted Demand Gen Lead · linkedin.com/jobs/… · 2026-10-04     →  exit 0
BAD   intent_score: 87 · no url · no date                            →  exit 1
BAD   "Series B" · example.com/about · 2026-10-01                    →  exit 1
```

## Install

```bash
npx skills add cmj-hub/claude-signal-with-a-link --all -g --full-depth
```

One host:

```bash
npx skills add cmj-hub/claude-signal-with-a-link --skill '*' -g --full-depth -y -a claude-code
```

Swap `claude-code` for `cursor`, `codex`, `grok`, `github-copilot`, `windsurf`, `cline`, or `opencode`.

Claude Code plugin path: see [In 60 seconds](#in-60-seconds).

## What you walk out with in 15 minutes

Artifact: `gtm/signal.json` (from kickoff), scored against the sample first.

```bash
cd skills/signal-with-a-link
python3 scripts/score.py --file examples/signal-good.json --as-of 2026-10-08
python3 scripts/score.py --file examples/signal-intent-only.json --as-of 2026-10-08
python3 scripts/score.py --file examples/signal-no-url.json --as-of 2026-10-08
```

The good draft exits 0 and prints the event, URL, date, and age. The intent-only draft exits 1 with `- intent score without a URL and a date → add both url and date, or drop intent_score`. Then write yours.

## What's in the pack

| Path | What it is |
| --- | --- |
| `skills/signal-with-a-link/SKILL.md` | The instrument: definition, banned list, kickoff, validate. |
| `skills/signal-with-a-link/scripts/score.py` | Deterministic scorer. Exit 0 / 1 / 2. |
| `skills/signal-with-a-link/examples/` | Good, with-intent, no-url, no-date, intent-only, firmographic. |
| `.claude-plugin/` | Plugin + marketplace manifests. |
| `tests/` | `python3 -m unittest discover -s tests` |

## What this pack will not do

It will not hunt LinkedIn for you. It will not buy intent data. It will not write the email or the five-part PSP.

This pack drafts and scores. It will not pick this quarter's signal sources, ingest your CRM, or refresh when a job board changes its URL shape. That is the course + Operator Pass: the catalog that keeps moving, the tools that stay calibrated, the Friday room where you bring the artifact.

## What is a buying signal?

A buying signal is a dated, linkable event: a public action with a URL you can open and an ISO date you can name. A job post four days ago with a LinkedIn URL is a signal. "Series B" is state. An intent score of 87 with no link is a guess.

## Do I need a paid intent vendor to start?

No. The Northwind sample is in `examples/`. Score it. Then paste one URL from your book. Paid lookup is out of scope here, and an intent score is refused until both `url` and `date` are present.

## Does this score intent for me?

Only after the link and the date exist. The banned line is public: no intent score without a URL and a date. The scorer enforces it.

## Will this invent a URL if I do not have one?

No. If you cannot open a page, you do not have a signal yet. Leave the account off.

## On the site

- [Skill packs catalog](https://jaymountconsulting.com/skills) — install paths + every pack
- [Pain Signal Profiles](https://jaymountconsulting.com/frameworks/pain-signal-profiles) — what a passing signal feeds next

## Free, by email

[**Growth Audit**](https://jaymountconsulting.com/growth-audit) — where your go-to-market stack is leaking, sent to your inbox.

[**The Friday Signal**](https://jaymountconsulting.com/newsletter/signal): free emails on building GTM systems that compound. No pitch in it. One click unsubscribes.

## Suite → course → Operator Pass

Companion packs: [claude-psp](https://github.com/cmj-hub/claude-psp) (turn the signal into a five-part brief), [claude-prospect-list](https://github.com/cmj-hub/claude-prospect-list) (who to contact this week), [claude-cold-email](https://github.com/cmj-hub/claude-cold-email) (signal-anchored first touch). Suite install: [gtm-operator-skills](https://github.com/cmj-hub/gtm-operator-skills).

Operator Pass compounds the loop: live calibrated endpoints, the Friday room, and the next framework in order. Founder: **$97/mo billed annually** ($1,164/yr), locked for life if bought before October 31, 2026. After that: $197/mo billed annually ($2,364/yr). → [Operator Pass](https://jaymountconsulting.com/operator-pass)

## Privacy and security

The scorer is standard-library Python and opens no network connection. It reads only the draft you hand it. The skill writes `gtm/signal.json` and nothing else. No telemetry, no credentials, no paid APIs. See [SECURITY.md](SECURITY.md).

## License

MIT. See [LICENSE](./LICENSE).

## About

Built by [Jay Mount Consulting](https://jaymountconsulting.com).
