# Contributing

Thanks for opening this repo. A few notes on how this project works before you contribute.

## What kinds of contributions land

- **Bug reports**: open an issue with a reproducible case. The scorer is deterministic, so bugs there are usually one-line fixes.
- **Calibration improvements** to the scoring script: if you can show a case where the script scores wrong, that is gold.
- **Cross-runtime ports** (Cursor, Codex, Grok): see companion packs listed in the README.

## What does not land

- CRM write-back inside the free pack. That stays out of the free pack.
- Adding paid-API dependencies to scripts. Scripts must work zero-dep.
- Adding LLM calls inside the scorer. The scorer stays deterministic.
- Publishing private writing skills into this repo.

## Development setup

```bash
git clone https://github.com/cmj-hub/claude-inbound-from-domain.git
cd claude-inbound-from-domain
python3 -m unittest discover -s tests
```

## License

MIT. By contributing you agree your contributions are licensed under the MIT License.
