# Security

Run `python3 scripts/check_pack.py pack <dir> --public` or `--private`.

The script refuses:

- a `.env` file (`.env.example`, `.env.sample`, and `.env.template` may ship, and they are still scanned)
- key material in a text file: a private-key block, a cloud access-key id, a vendor key prefix, or an assigned secret. A value read from the environment, a function call, an empty string, or a `<placeholder>` is not a secret.
- a public pack with no `SECURITY.md` at its root, or an empty one. It says what the pack does on the user's machine (scripts, files read and written, network, telemetry, credentials) and how to report a vulnerability. A private pack may skip it.
- a public LICENSE missing the word MIT
- a public LICENSE that carries the Operator Pass license id
- a private LICENSE missing that id
- a private LICENSE that carries the MIT grant sentence
- a third-party Python import, in a `.py` file or a code fence, with no install line on that line or in the five above it (`pip install`, `uv add`, `npm install`, `pnpm add`, `bun add`, or `brew install`)

The standard library and a module that lives anywhere in the pack do not need an install line.

A `.claude-plugin/plugin.json` is checked too: a JSON object, a lowercase hyphen `name`, a semver `version`, `skills` paths inside the pack, and at least one SKILL.md it installs.

Repo docs at the pack root (README, CHANGELOG, CONTRIBUTING, AGENTS, CLAUDE, SECURITY, CODE_OF_CONDUCT, INSTALL) and markdown under `agents/`, `commands/`, `hooks/`, `.github/`, and `.claude-plugin/` are not skill references. They need no Contents list and no link from SKILL.md.

No live send, no live ad write, no charge.

The publisher scan is the gate for private-pack URLs and for writing-skill names. This checker does not carry that list.
