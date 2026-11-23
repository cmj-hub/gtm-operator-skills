# Scorer envelope adapter

The nineteen primary pack scorers emit `result_envelope/v1` in JSON mode.
Text output, rubric thresholds and exit codes retain their existing behavior.
`result` contains the full previous report. Previous top-level fields remain as
aliases except reserved envelope names: inbound's old evidence strings, for
example, are now at `result.evidence`, while top-level `evidence` uses canonical
citation records. Input errors still exit 2 on stderr without echoing input.

`ok` means the local rubric passed. It does not establish that submitted facts
are true. Confidence stays `{value: null, basis: "unmeasured"}`; a rubric score
is not an outcome probability. Failed checks derive `abstain` in code. Unknowns
derive `partial` unless the rubric has already refused. No self-report routes.
Signal citations are explicitly unverified and have no retrieval timestamp;
operator-supplied verification metadata cannot confer verification.

Every output has one next_action string. Each receipt contains the adapter
version, tool identifier, null model, zero local monetary cost, scoring date and
SHA-256 of `{inputs, as_of, assumptions}` serialized as sorted compact UTF-8 JSON.
The hash is a reproducibility aid, not a privacy guarantee for guessable inputs.
It covers the supplied draft and scoring options, not the contents of linked
webpages. No draft content is stored by the adapter.

Each skill has a byte-identical copy of `scorer_envelope.py` so a standalone
install needs neither a repository import nor a runtime dependency. Edit the
source here, then run `node scripts/check-shared.mjs --sync`. CI checks the copies.

`result-envelope/index.mjs` and `index.d.ts` are verbatim canonical contract
copies at the commit in `pin.json`. Python output is checked against that
JavaScript validator in the offline integration tests. To compare with a checked
out package release, run `node scripts/check-shared.mjs --upstream <packages-repo>`.
Before merge, refresh both canonical files and their pin against the released
schema, sync the Python copies, and rerun the cross-language tests.

This slice covers the primary scorer for each pack. Ancillary cold-email,
pricing and founder setup graders still use their previous output. Source-fetch
workflows, shared prospect/signal grounding, pricing content sufficiency and
routing model evals remain follow-up work.
