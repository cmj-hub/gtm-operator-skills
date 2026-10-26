# Contributing

## What lands

- Bug reports with a domain or an HTML fixture and the expected gaps.
- Extra public-signal checks that stay stdlib-only.

## What does not land

- Paid APIs, LLM calls inside `check.py`, or CRM logins.
- Turning this into a generated playbook.

```bash
python3 -m unittest discover -s tests -v
```
