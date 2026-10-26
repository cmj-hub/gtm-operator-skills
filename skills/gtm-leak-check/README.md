# GTM leak check skill for Claude Code

Point it at a domain. It reads public signals and returns three GTM gaps, each with the URL it used.

A GTM leak check is an outside read of a company's public go-to-market: the homepage a stranger sees, the pricing and careers pages if they exist, whether answer engines are allowed to cite it, and which tools the HTML admits. It is not a Growth Audit and it is not a generated playbook.

## In 60 seconds

```text
/plugin marketplace add cmj-hub/claude-gtm-leak-check
/plugin install gtm-leak-check@claude-gtm-leak-check
```

Then:

```bash
python3 skills/gtm-leak-check/scripts/check.py --domain example.com
```

Or with no network:

```bash
python3 skills/gtm-leak-check/scripts/check.py --html-file skills/gtm-leak-check/examples/thin-home.html --page-url https://thin.example/
# Gap 1 of 3: Missing title
#   Source: https://thin.example/
```

The build guide teaches a human. The pack teaches an agent.

## Install

```bash
npx skills add cmj-hub/claude-gtm-leak-check --all -g --full-depth
```

One host:

```bash
npx skills add cmj-hub/claude-gtm-leak-check --skill '*' -g --full-depth -y -a claude-code
```

Swap `claude-code` for `cursor`, `codex`, `grok`, `github-copilot`, `windsurf`, `cline`, or `opencode`.

## What you walk out with in 15 minutes

Artifact: three gaps on stdout, or `gtm/leak-check.json` from `--json`.

Each gap has a name, what we saw, a source URL, and why it matters. A healthy page can print one gap. Tools seen are listed as facts, not as a leak. Sources read are listed at the bottom.

## What this pack will not do

- Log into a CRM, inbox, or ad account
- Change the site
- Call a paid API
- Write a 12-page GTM playbook
- Replace the [Growth Audit](https://jaymountconsulting.com/growth-audit?utm_source=github&utm_medium=readme&utm_campaign=gtm-leak-check)

## What it checks

1. **Site.** Title, description, visible copy, a public next step, noindex. Pricing (thin or missing). Careers vs homepage: a jobs page that names a buyer the homepage never does.
2. **Search and AI-answer.** JSON-LD, llms.txt, robots.txt rules for GPTBot, ClaudeBot, PerplexityBot, Google-Extended.
3. **Stack.** Script tags and generator-style HTML, listed as tools seen. If [The GTM Directory](https://thegtmdirectory.com/?utm_source=github&utm_medium=readme&utm_campaign=gtm-leak-check) MCP is already connected in the session, the skill also asks it which tools list that domain. The Python checker itself uses no MCP and no key.

## FAQ

### What is the GTM leak check?

A free skill for Claude Code and Codex. You install it with one command, point it at a domain, and it reads public signals. It returns three gaps to look at first.

### Does it need an API key?

No. The core run fetches the public homepage, robots.txt, llms.txt, and the pricing and careers (or jobs) pages when they exist.

### Who is it for?

Founder-led B2B teams of 5 to 200 who already work in Claude Code or Codex and want a quick outside read before they change anything.

## Next

- [Friday Signal](https://jaymountconsulting.com/newsletter/signal?utm_source=github&utm_medium=readme&utm_campaign=gtm-leak-check) : free emails on building GTM systems that compound. No pitch in it. One click unsubscribes.
- [Suite catalog](https://github.com/cmj-hub/gtm-operator-skills)

## License

MIT. See [LICENSE](LICENSE).
