# Contributing

Thanks for opening this repo. A few notes before you contribute.

## What kinds of contributions land

- **Bug reports**: open an issue with a reproducible case. The scorer is deterministic, so bugs there are usually small fixes.
- **Calibration improvements**: a case where the script scores wrong is gold. Include the JSON and the exit you expected.

## What does not land

- Softening the banned line: no claim without a source and a permission.
- Adding LLM calls or paid-API dependencies inside the scorer.
- A scorer that accepts a permission the user has not recorded.

## Development setup

```bash
git clone https://github.com/cmj-hub/claude-proof-assets.git
cd claude-proof-assets
python3 -m unittest discover -s tests -v
```

## License

By contributing, you agree your work is MIT-licensed like the rest of the repo.
