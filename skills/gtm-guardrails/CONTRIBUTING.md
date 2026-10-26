# Contributing

Thanks for opening this repo. A few notes before you contribute.

## What kinds of contributions land

- **Bug reports**: open an issue with a reproducible case. The scorer is deterministic, so bugs there are usually small fixes.
- **Calibration**: a settings file the scorer gets wrong is the most useful report. Include the JSON and the exit you expected.
- **Doc drift**: Claude Code's permission rules change. A rule here that no longer matches the docs is a bug; link the docs line.

## What does not land

- Softening the banned line: no CRM write without a prompt.
- Adding LLM calls, network calls or paid-API dependencies to the scripts.
- A script that calls a live CRM or inbox.

## Development setup

```bash
git clone https://github.com/cmj-hub/claude-gtm-guardrails.git
cd claude-gtm-guardrails
python3 -m unittest discover -s tests -v
```

## License

By contributing, you agree your work is MIT-licensed like the rest of the repo.
