<p align="center">
  <strong>Email waterfall skill for Claude Code</strong>
</p>

# Email waterfall skill for Claude Code

Find work emails cheapest-first. Burn the inputs you hold before any paid finder.

An email waterfall is a cheapest-first cascade that finds a work email for a person you already named. You burn the inputs you hold (CRM address, company domain, known pattern) before any paid finder. A 4xx from a vendor stops the row: you do not retry the next vendor on bad input. Found is not sendable until verify = deliverable.

## In 60 seconds

```text
/plugin marketplace add cmj-hub/claude-waterfall-email
/plugin install waterfall-email@claude-waterfall-email
/waterfall-email:waterfall-email
```

Or score the sample without an agent:

```bash
python3 skills/waterfall-email/scripts/score.py --file skills/waterfall-email/examples/waterfall-good.json
# exit 0: held inputs first, on_4xx=fix_input, verify=deliverable
python3 skills/waterfall-email/scripts/score.py --file skills/waterfall-email/examples/waterfall-4xx-retry.json
# exit 1: on_4xx retries the next vendor → set fix_input or stop
python3 skills/waterfall-email/scripts/score.py --file skills/waterfall-email/examples/waterfall-found-unverified.json
# exit 1: found is not sendable until verify = deliverable
```

The good draft exits 0. The 4xx-retry and found-unverified drafts exit 1.

The build guide teaches a human. The pack teaches an agent.

## Install

As a Claude Code plugin:

```text
/plugin marketplace add cmj-hub/claude-waterfall-email
/plugin install waterfall-email@claude-waterfall-email
```

The skill loads as `/waterfall-email:waterfall-email`. Ask Claude to route a find, or hand it a cascade draft. `/waterfall-email:waterfall-email score` scores `gtm/waterfall-email.json`.

For every agent host the skills installer knows:

```bash
npx skills add cmj-hub/claude-waterfall-email --all -g --full-depth
```

One host:

```bash
npx skills add cmj-hub/claude-waterfall-email --skill '*' -g --full-depth -y -a claude-code
```

Swap `claude-code` for `cursor`, `codex`, `grok`, `github-copilot`, `windsurf`, `cline`, or `opencode`. The scorer is Python in this repo. It does not call a paid API, and it does not buy data.

## What you walk out with in 15 minutes

Artifact: `examples/waterfall-good.json` → your draft at `gtm/waterfall-email.json`.

```bash
cd skills/waterfall-email
python3 scripts/score.py --file examples/waterfall-good.json
python3 scripts/score.py --file examples/waterfall-4xx-retry.json
python3 scripts/score.py --file examples/waterfall-found-unverified.json
python3 scripts/score.py --file examples/waterfall-paid-first.json
```

The good draft exits 0 and prints person, on_4xx, cascade order, and the next step. Each banned draft exits 1 with one `- what is wrong → what to change` line per gap. Then drop in yours.

## What's in the pack

| Path | What it is |
| --- | --- |
| `skills/waterfall-email/SKILL.md` | The skill: cheapest-first order, 4xx stop, deliverable gate, kickoff checklist. |
| `skills/waterfall-email/scripts/score.py` | The scorer. Exit 0 scored, 1 refused, 2 unreadable input. |
| `skills/waterfall-email/examples/` | Good route plus 4xx-retry, found-unverified, and paid-first refusals. |
| `.claude-plugin/` | Plugin and marketplace manifests for Claude Code. |
| `tests/` | `python3 -m unittest discover -s tests` |

## What this pack will not do

It will not call a finder. It will not spend a credit. It will not send mail. It will not accept a 4xx retry onto the next vendor, or a found address marked sendable before deliverable verify.

This pack drafts and scores. It will not pick this quarter's vendor list, log into a data vendor, or refresh a field after its sunset.

## What is an email waterfall?

A cheapest-first cascade that finds a work email for a named person. Held inputs run before paid finders. Verify is the last gate. Sendable means deliverable: nothing else.

## Does a 4xx mean try the next vendor?

No. A 4xx is bad input or a blocked request. Fix the row or stop. Retrying the next vendor burns the same broken request.

## Is a found email ready to send?

No. Found is a guess. Catch-all, unknown, invalid, risky, and unverified stay off the send list until verify = deliverable.

## Do I need live vendor keys to start?

No. The scorer runs on a JSON draft. Bring your cascade order and the verify bucket you already have. The pack does not open a network connection.

## On the site

- [Skill packs catalog](https://jaymountconsulting.com/skills): install paths + every pack
- [Course twin](https://jaymountconsulting.com/learn): human build guides

## Free, no signup

[All free tools](https://jaymountconsulting.com/prototypes)

## Free, by email

[**Growth Audit**](https://jaymountconsulting.com/growth-audit): architecture gaps in the GTM you already run. Free written report.

[**Friday Signal**](https://jaymountconsulting.com/newsletter/signal): one Friday GTM read. No pitch in it.

## Part of the suite
Part of the GTM operator suite: see [gtm-operator-skills](https://github.com/cmj-hub/gtm-operator-skills).

## Companion packs

- [Qualify before enrich](https://github.com/cmj-hub/claude-qualify-before-enrich): ICP check before any finder
- [Found vs deliverable](https://github.com/cmj-hub/claude-found-vs-deliverable): verify buckets
- [Prospect list](https://github.com/cmj-hub/claude-prospect-list): who earns a slot this week
- [Cold email](https://github.com/cmj-hub/claude-cold-email): signal-anchored first touch

## Privacy and security

The scorer is standard-library Python and opens no network connection. It reads only the draft you give it; the skill writes `gtm/waterfall-email.json` and never writes `brand-config.json`. No telemetry, no credentials, no lookups, and nothing is sent. See [SECURITY.md](SECURITY.md).

## Next

Previous: [Qualify before enrich](https://github.com/cmj-hub/claude-qualify-before-enrich)

Next: [Found vs deliverable](https://github.com/cmj-hub/claude-found-vs-deliverable)

## License

MIT. Python 3 standard library only. See [LICENSE](./LICENSE).

## About

Built by [JMC Go-to-Market Systems](https://jaymountconsulting.com).
