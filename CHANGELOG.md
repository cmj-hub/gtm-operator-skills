# Changelog

## Unreleased

### Added
- `skills/<pack>/`: all seventeen packs vendored into this repo, each with its scorer, evals and sample, so one install carries every pack.
- `AGENTS.md`: how any agent installs and uses the packs.
- A paste-one-line install at the top of the README.

### Changed
- Every pack skill description now leads with the phrases a user types and ends with `For X, see Y.` boundaries. Skill bodies are unchanged.
- README restructured: install, pack table, skills by outcome, then the free-first ladder.
- Pack READMEs said the suite installs "all ten"; it installs seventeen.

## 2026-10-19

### Fixed
- `allowed-tools` in SKILL.md files: `Write` and `Edit` scoped to the paths each skill writes (#28).
