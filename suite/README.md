# gtm — the GTM operator suite in one install

Installs all ten GTM packs and adds two commands that tie them together. It does not draft anything itself; each pack does one job and refuses the generic version of it.

## In 60 seconds

```text
/plugin marketplace add cmj-hub/gtm-operator-skills
/plugin install gtm@gtm-operator-skills
/gtm:setup
/gtm:next
```

`/gtm:setup` asks the shared questions once (who you are, who you sell to, your voice) and writes them to `brand-config.json` and `SOUL.md`. Every pack reads them, so none asks again.

`/gtm:next` reads `brand-config.json` and the `gtm/` folder and names the next pack command, for example `Next: /evp:evp — no value line yet`.

To keep that answer on screen, add the [gtm-operator mod](https://github.com/cmj-hub/gtm-operator-claude-mod): `/plugin install gtm-operator@gtm-operator-skills`. It shows the next step above the prompt, opens a `/gtm-board` pane, and refuses a write that would overwrite a filled `brand-config.json` value.

Other agents (Codex, Cursor, and the rest) install each pack with the skills CLI instead, for example:

```bash
npx skills add cmj-hub/claude-psp --all -g --full-depth
```

## What it installs

psp, evp, prospect-list, cold-email, sales-offer, pricing, landing-page, email-sequence, geo, founder-brand. The order and what each reads are in the [suite README](../README.md#how-the-packs-work-together).

## Files

- `brand-config.json` and `SOUL.md` at your project root, shared by every pack. Packs merge their own fields and never overwrite another pack's.
- `gtm/` at your project root. Each pack saves its draft there under its own name (`gtm/page.json`, `gtm/offer.json`, ...), so packs never overwrite each other.

## Privacy and security

These two skills read and write only `brand-config.json`, `SOUL.md`, and the `gtm/` folder. They run no scripts and open no network connection. See [SECURITY.md](SECURITY.md) and each pack's own SECURITY.md.

## License

MIT. Built by [Jay Mount Consulting](https://jaymountconsulting.com).
