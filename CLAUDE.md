# Working in this repository

Guidance for anyone (human or automated tool) making changes here.

## Commits

- Commit messages are a single line: imperative mood, under ~70 characters, no
  trailing period. No body, no bullet list, no multi-paragraph explanation.
- Never add a co-author trailer, a "generated with" footer, or any assistance
  attribution to a commit message, PR description, or code comment.
- Run the full test suite and confirm it is green before committing.
- Never push automatically. Commit locally and leave pushing to the repository
  owner unless explicitly asked to push.

## Determinism

- All dates and times come from an injected `Clock` (see `ledgerkit.clock`).
  Never call `datetime.now()` or `date.today()` directly outside
  `SystemClock`.
- All randomness comes from an explicitly seeded generator. No module-level
  `random` use.
- No network access anywhere, including in tests.
- Any output derived from a dict or set must be sorted before rendering.

## Money

- All money arithmetic goes through `ledgerkit.money.Money`. Never use raw
  `float` for amounts. Never mix rounding policies implicitly — pass the
  rounding mode explicitly at the boundary that requires it.

## Tests

- Tests live in `tests/` only. Never co-locate a test module with the source
  module it exercises, and never add doctests to a source module.

## Code hygiene

- No `TODO` or `FIXME` comments describing unimplemented features. If it
  isn't built, it isn't mentioned in a comment.
- No dead code: every protocol, registry, and abstract base has at least one
  real implementation in active use.
- Dependencies are pinned to exact versions in `pyproject.toml`.
