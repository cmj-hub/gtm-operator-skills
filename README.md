<p align="center">
  <img src="./assets/header.png" alt="GTM Operator Skills — five MIT skill packs for B2B operators" width="100%">
</p>

# gtm-operator-skills

Five MIT skill packs for B2B operators.

The build guide teaches the framework to a human. The pack teaches the same framework to an agent.

Give the instrument. Sell the compounding.

## Install the suite

One command per pack. Writes into Claude Code, Cursor, Codex, Grok, Copilot, Windsurf, Cline, OpenCode, and the rest of the [skills CLI](https://skills.sh) list.

```bash
npx skills add cmj-hub/claude-psp --all -g --full-depth
npx skills add cmj-hub/claude-evp --all -g --full-depth
npx skills add cmj-hub/claude-cold-email --all -g --full-depth
npx skills add cmj-hub/claude-founder-brand --all -g --full-depth
npx skills add cmj-hub/claude-pricing --all -g --full-depth
npx skills add cmj-hub/claude-cold-offer --all -g --full-depth
```

Claude Code, the five as a marketplace:

```text
/plugin marketplace add cmj-hub/gtm-operator-skills
/plugin install psp
/plugin install evp
/plugin install cold-email
/plugin install founder-brand
/plugin install pricing
```

## The packs

Foundation, outbound, social, and offer have a public pack. Findability, pages, email, paid, measurement, and motion are added on this page when that pack is public.

| Group | Job | Pack | What it is | 15-minute artifact |
|---|---|---|---|---|
| Foundation | Pain | [claude-psp](https://github.com/cmj-hub/claude-psp) | A Pain Signal Profile is a five-part buying brief. It replaces a static ICP. | Score the sample 100 vs 37, then do yours |
| Foundation | Proposition | [claude-evp](https://github.com/cmj-hub/claude-evp) | An Early Value Proposition is a ≤22-word line matched to a Schwartz awareness tier. | Three tier lines from the sample PSP |
| Outbound | The letter | [claude-cold-email](https://github.com/cmj-hub/claude-cold-email) | Four jobs in under 90 words: signal, pain, EVP, binary ask. Demographics are not a signal. | One T1, linted |
| Social | Social post | [claude-founder-brand](https://github.com/cmj-hub/claude-founder-brand) | Pillar / Proof / Process / Person. Refuses thought-leader cadence. | One Proof post from a real receipt |
| Foundation | Price | [claude-pricing](https://github.com/cmj-hub/claude-pricing) | Pricing surgery: WTP, value metric, reference frame, three-tier contrast, pocket-price leaks. | `decoy_validator` on the sample tiers |
| Offer | Cold offer | [claude-cold-offer](https://github.com/cmj-hub/claude-cold-offer) | A leak, a prototype, and email one. The scorer refuses email one that sells the paid product. | `score.py` on the sample draft |

Each pack is MIT. No paid APIs inside. Scorers are Python you can run without an LLM.

The gate for the next pack is [build/SKILL.md](build/SKILL.md). Run it from that directory. It is not a sixth install.

## The split

| Layer | What it is | Where it lives |
|---|---|---|
| Instrument | Framework, banned list, scorer, one worked example | These repos |
| Hosted | The same jobs, in a browser, no install | [Free tools](https://jaymountconsulting.com/prototypes) |
| Reference | Frameworks, playbooks, prompt library | [Frameworks](https://jaymountconsulting.com/frameworks) · [Prompt Library](https://jaymountconsulting.com/resources/prompt-library) |
| Growth Audit | Where your own book stands today | [Growth Audit](https://jaymountconsulting.com/growth-audit) |

This suite drafts and scores. It will not pick this quarter's PSP, ingest your CRM, or update when Gmail changes the spam window. Those are judgement calls and live data. This pack gives you the instrument and the rubric; you bring the account.


## Free, no signup

- **[All 30+ free tools](https://jaymountconsulting.com/prototypes)** — the same jobs these packs do, hosted. No account, no key.
- [Frameworks](https://jaymountconsulting.com/frameworks) — the written method behind each pack
- [Playbooks](https://jaymountconsulting.com/playbooks) · [Prompt Library](https://jaymountconsulting.com/resources/prompt-library) · [Calculator Pack](https://jaymountconsulting.com/resources/calculator-pack)

## Free, by email

[**Growth Audit**](https://jaymountconsulting.com/growth-audit) — where your go-to-market stack is leaking, sent to your inbox.

That one does ask for an email, and it enrols you in a short follow-up on the same topic. Unsubscribe whenever.

[**The Friday Signal**](https://jaymountconsulting.com/newsletter/signal) — one free edition a week on building GTM systems that compound. No pitch in it.

## Site

[jaymountconsulting.com/skills](https://jaymountconsulting.com/skills)

## License

MIT on every pack. Built by [Jay Mount Consulting](https://jaymountconsulting.com).

## Regenerating the artwork

`assets/social-preview.png` and `assets/header.png` are generated from `assets/spec.json` by a vendored renderer — no CI, no shared workflow, no network beyond the webfonts:

```bash
node assets/card.mjs assets/spec.json assets/
```
