<p align="center">
  <img src="./assets/lockup.png" width="880" alt="Inbound from domain skill for Claude Code. Enrich inbound from the email domain and route in seconds.">
</p>

# Inbound from domain skill for Claude Code

Enrich inbound from the email domain. Route in seconds. No CRM write-back in the free pack.

## In 60 seconds

```text
/plugin marketplace add cmj-hub/gtm-operator-skills
/plugin install inbound-from-domain@gtm-operator-skills
/inbound-from-domain:inbound-from-domain
```

Or score the sample without an agent:

```bash
python3 skills/inbound-from-domain/scripts/score.py --file skills/inbound-from-domain/examples/inbound-good.json
# exit 0: a high-touch route from the domain
python3 skills/inbound-from-domain/scripts/score.py --file skills/inbound-from-domain/examples/inbound-crm-write.json
# exit 1: a CRM write-back → set crm_write false
```

Part of the GTM operator suite: `/plugin install gtm@gtm-operator-skills` installs the catalog.

Add the [gtm-operator mod](https://github.com/cmj-hub/gtm-operator-claude-mod) to see the suite's next step above your prompt: `/plugin install gtm-operator@gtm-operator-skills`.

Inbound-from-domain enrichment takes an inbound email, extracts the company domain, classifies it (corporate, free-mail, disposable, personal-looking), writes a short public-domain enrichment card, and routes the lead in seconds. high-touch, self-serve, need-more, personal, or disqualify: without writing back to a CRM.

`alex@northwind.io` scores **high-touch**. The same card with `crm_write: true` is **refused**. Python. No LLM. No paid API.

The build guide teaches a human. The pack teaches an agent.

<p align="center">
  <img src="./assets/demo.gif" alt="Inbound from domain: corporate routes to high-touch; CRM write-back fails" width="100%">
</p>

## What this replaces

The first five minutes of “who is this inbound?”: domain classify + route: before a human opens the CRM.

## Install

As a Claude Code plugin:

```text
/plugin marketplace add cmj-hub/claude-inbound-from-domain
/plugin install inbound-from-domain@claude-inbound-from-domain
```

The skill then loads as `/inbound-from-domain:inbound-from-domain`. Ask Claude to route an inbound email, or hand it a draft. `/inbound-from-domain:inbound-from-domain score` scores the draft already in `gtm/inbound.json`.

For every agent host the skills installer knows:

```bash
npx skills add cmj-hub/claude-inbound-from-domain --all -g --full-depth
```

One host:

```bash
npx skills add cmj-hub/claude-inbound-from-domain --skill '*' -g --full-depth -y -a claude-code
```

Swap `claude-code` for `cursor`, `codex`, `grok`, `github-copilot`, `windsurf`, `cline`, or `opencode`. The scorer is Python in this repo. It does not call a paid API, and it does not write a CRM.

## What you walk out with in 15 minutes

Artifact: `gtm/inbound.json` (start from `examples/inbound-good.json`).

```bash
cd skills/inbound-from-domain
python3 scripts/score.py --file examples/inbound-good.json
python3 scripts/score.py --file examples/inbound-crm-write.json
```

The good draft exits 0 and prints a `high-touch` route from `northwind.io`. The CRM-write draft exits 1 and prints one `- what is wrong → what to change` line, then `Next: fix the lines above and run this again.` Free-mail routed to Build fails the same way. Add `--json` for one result object (`fixes` and `next` included). Then drop in yours at `gtm/inbound.json` in your project.

## What's in the pack

| Path | What it is |
| --- | --- |
| `skills/inbound-from-domain/SKILL.md` | The skill: kinds, routes, banned CRM write-back, checklist. |
| `skills/inbound-from-domain-kickoff/SKILL.md` | Fifteen-minute kickoff + sample loop. |
| `skills/inbound-from-domain/scripts/score.py` | The scorer. Exit 0 scored, 1 refused, 2 unreadable input. |
| `skills/inbound-from-domain/examples/` | Good, free-mail, disposable, CRM-write, free-mail-to-Build drafts. |
| `.claude-plugin/` | Plugin and marketplace manifests for Claude Code. |
| `tests/` | `python3 -m unittest discover -s tests` |

## What this pack will not do

It will not write your CRM. It will not call a paid firmographic API. It will not send an auto-reply.

This pack drafts and scores a route card. It will not pick this quarter's PSP, ingest your CRM, or update when a free-mail provider list changes.

## How is this different from a CRM enrichment tool?

A CRM enrichment tool writes firmographics into the record. This pack stops at the route card: domain kind, evidence, and a route. A human owns the write-back.

## Do I need live data to start?

No. Score the sample first. The free-mail and disposable lists in the scorer are enough for the fifteen-minute loop. Bring your own inbound address next.

## Does this look people up?

No. You classify from the domain you already have on the inbound email. The pack scores the card. No network. No paid lookup.

## On the site

- [Inbound from domain pack](https://jaymountconsulting.com/skills/claude-inbound-from-domain): this pack's page
- [Skill packs catalog](https://jaymountconsulting.com/skills): install paths + every pack
- [Course twin](https://jaymountconsulting.com/learn/courses/inbound-from-domain): human build guide for this pack

## Free, no signup

[All free tools](https://jaymountconsulting.com/prototypes)

## Free, by email

[**Growth Audit**](https://jaymountconsulting.com/growth-audit): architecture gaps in the GTM you already run. Free written report.

[**Friday Signal**](https://jaymountconsulting.com/newsletter/signal): one Friday GTM read. No pitch in it.

## Next

Previous: [Qualify before enrich](https://github.com/cmj-hub/claude-qualify-before-enrich)

Next: [Found vs deliverable](https://github.com/cmj-hub/claude-found-vs-deliverable)

## Part of the suite

Part of the GTM operator suite: see [gtm-operator-skills](https://github.com/cmj-hub/gtm-operator-skills).

## Companion packs

- [Qualify before enrich](https://github.com/cmj-hub/claude-qualify-before-enrich): ICP check before any finder
- [Found vs deliverable](https://github.com/cmj-hub/claude-found-vs-deliverable): find then verify before send
- [Waterfall email](https://github.com/cmj-hub/claude-waterfall-email): cheapest-first cascade
- [Prospect list](https://github.com/cmj-hub/claude-prospect-list): who to contact this week
- Suite install: [gtm-operator-skills](https://github.com/cmj-hub/gtm-operator-skills)

## Privacy and security

The scorer is standard-library Python and opens no network connection. It reads only the draft you give it; the skill writes `gtm/inbound.json`, reads `brand-config.json` if present and never writes to it. No telemetry, no credentials, no CRM upsert, nothing sent. See [SECURITY.md](SECURITY.md).

## License

MIT. Python 3 standard library only. See [LICENSE](./LICENSE).

## About

Built by [JMC Go-to-Market Systems](https://jaymountconsulting.com).
