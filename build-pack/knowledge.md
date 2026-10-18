# Knowledge

The card is a JSON object at a path you pass in. The script checks the shape. It does not search, and it does not call an API. You fill the fields from the fetch for this pack.

`examples/knowledge.json` is a shape the script accepts. Replace every value.

- `job` — the one job.
- `portal_course` — the portal course slug, or a short gap when no course owns the job.
- `portal_fact` — one passage, 20 to 600 characters. A heading inside the fact is a pasted lesson.
- `tgd_url` — starts with `https://thegtmdirectory.com/category/`.
- `outside_repo` — `owner/name`.
- `outside_artifact` — one artifact that repo ships.
- `gtm_context.query` — the query you sent.
- `kept` — true only when `passage` holds an operator passage you kept. False when the graph was empty or the hits were discarded, and then `note` says which.

```bash
python3 scripts/check_pack.py knowledge <card>
```

`knowledge ok` means the shape passed.
