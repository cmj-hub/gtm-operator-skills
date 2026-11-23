# Scorer result envelopes

## Scope

Add the canonical result_envelope/v1 shape to the JSON output of the nineteen
primary pack scorers. Keep the existing text output, rubric thresholds and exit
codes. Keep legacy JSON fields beside the envelope except for reserved names;
the complete legacy object is available under `result` in every case.

This is the first complete output-contract slice of issue 42. Ancillary graders,
pricing content validation, shared prospect/signal grounding, WebFetch instructions,
outcome/routing model evals and the optional member Atlas path remain separate work.
No pricing recommendations, public marketing claims or manifests change here.

## Contract

Follow the current canonical draft: statuses are ok, partial, abstain and error;
unmeasured confidence is null. Evidence uses url, date and verified, with optional
retrieved_at. Status follows the local rubric decision and explicit unknowns,
never a model confidence or an operator-provided status. Passing a local rubric
does not verify the input claims. State that limit in each response.

Summary is first and at most 150 characters (a conservative token budget).
Exactly one next_action string names the existing next step. Failed rubric checks
produce an abstain reason, closest available output and the required fixes.
Unknown fields must be absent or null; measured zero/false values remain valid.

Signal evidence is always unverified: the scorer makes no network request.
Operator-provided verified and retrieved_at values cannot confer verification.
A syntactically accepted signal remains partial pending source verification.

Receipt identifies the tool, adapter version, null model, zero local monetary
cost, SHA-256 of effective scoring inputs and the scoring date. Input hashing
must be stable under dictionary ordering and change when scoring inputs change.

## Packaging and verification

Each independently installable skill carries a byte-identical stdlib Python
adapter. scripts/check-shared.mjs checks the copies. The canonical JavaScript
implementation and declarations are copied verbatim for offline cross-language
validation; sync them from the released package before merge.

Test before implementation: refusals recover, unknown is never zero/false/cold,
self-reported confidence cannot route, input hashes identify inputs, standalone
signal installs work, all nineteen primary CLIs carry the contract. Run existing
pack tests and validate emitted JSON against the canonical implementation.
