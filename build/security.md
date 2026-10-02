# Security

Run `python3 scripts/check_pack.py pack <dir> --public` or `--private`.

The script refuses:

- a `.env` file
- key material in a text file: a private-key block, a cloud access-key id, a vendor key prefix, or an assigned secret
- a public LICENSE missing the word MIT
- a public LICENSE that carries the Operator Pass license id
- a private LICENSE missing that id
- a private LICENSE that carries the MIT grant sentence
- a third-party import with no `pip install` or `uv add` comment in the five lines above it

The standard library and a module that lives in the pack do not need an install line.

No live send, no live ad write, no charge.

The publisher scan is the gate for private-pack URLs and for writing-skill names. This checker does not carry that list.
