# Contributing

Thanks for opening this repo. A few notes before you contribute.

## What kinds of contributions land

- **Bug reports** — open an issue with a reproducible case. The scorer is deterministic, so bugs there are usually small fixes.
- **Calibration improvements** — a case where the script scores wrong is gold. Include the JSON and the expected exit.
- **Cross-runtime ports** (Cursor, Codex, others) — discuss in an issue first.

## What does not land

- Softening the banned line: no intent score without a URL and a date.
- Adding LLM calls or paid-API dependencies inside the scorer.
- Renaming the instrument (dated, linkable event).

## Development setup

```bash
git clone https://github.com/cmj-hub/claude-signal-with-a-link.git
cd claude-signal-with-a-link
python3 -m unittest discover -s tests -v
```

## License

By contributing, you agree your work is MIT-licensed like the rest of the repo.
