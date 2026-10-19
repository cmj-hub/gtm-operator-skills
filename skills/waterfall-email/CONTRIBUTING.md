# Contributing

Thanks for opening this repo.

## What kinds of contributions land

- **Bug reports** — open an issue with a reproducible case. The scorer is deterministic, so bugs there are usually one-line fixes.
- **Calibration improvements** — a draft the script scores wrong is gold.
- **Cross-runtime ports** (Cursor, Codex, Gemini CLI) — ship as separate plugins rather than renaming this one.

## What does not land

- Adding LLM calls inside the skill. The scorer stays deterministic.
- Adding paid-API dependencies. Scripts must work zero-dep.
- Softening the bans: no 4xx retry on the next vendor; found is not sendable until verify = deliverable.

## Development

```bash
git clone https://github.com/cmj-hub/claude-waterfall-email.git
cd claude-waterfall-email
python3 -m unittest discover -s tests -v
```
