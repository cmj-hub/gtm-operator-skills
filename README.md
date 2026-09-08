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

| Pack | What it is | 15-minute artifact |
|---|---|---|
| [claude-psp](https://github.com/cmj-hub/claude-psp) | A Pain Signal Profile is a five-part buying brief. It replaces a static ICP. | Score the sample 100 vs 37, then do yours |
| [claude-evp](https://github.com/cmj-hub/claude-evp) | An Early Value Proposition is a ≤22-word line matched to a Schwartz awareness tier. | Three tier lines from the sample PSP |
| [claude-cold-email](https://github.com/cmj-hub/claude-cold-email) | Four jobs in under 90 words: signal, pain, EVP, binary ask. Demographics are not a signal. | One T1, linted |
| [claude-founder-brand](https://github.com/cmj-hub/claude-founder-brand) | Pillar / Proof / Process / Person. Refuses thought-leader cadence. | One Proof post from a real receipt |
| [claude-pricing](https://github.com/cmj-hub/claude-pricing) | Pricing surgery: WTP, value metric, reference frame, three-tier contrast, pocket-price leaks. | `decoy_validator` on the sample tiers |

Each pack is MIT. No paid APIs inside. Scorers are Python you can run without an LLM.

## The split

| Layer | What it is | Where it lives |
|---|---|---|
| Instrument | Framework, banned list, scorer, one worked example | These repos |
| Education | How a human learns to run it on their book | The build guide / course |
| Compounding | Next framework, live tools, Friday room | [Operator Pass](https://jaymountconsulting.com/operator-pass) |
| Implementation | Seams in CRM / sequencer / stack | Build Partnership |

This suite drafts and scores. It will not pick this quarter's PSP, ingest your CRM, or update when Gmail changes the spam window. That is the course + Operator Pass: the catalog that keeps moving, the tools that stay calibrated, the Friday room where you bring the artifact.

Founder: $97/mo billed annually ($1,164/yr), locked for life if bought before October 31, 2026. After that: $197/mo billed annually ($2,364/yr), no lock.

## Site

[jaymountconsulting.com/skills](https://jaymountconsulting.com/skills)

## License

MIT on every pack. Built by [Jay Mount Consulting](https://jaymountconsulting.com).
