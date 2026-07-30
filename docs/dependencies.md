# Dependencies

## Runtime

None. `ledgerkit` the library and the `ledgerkit` CLI both run on the
standard library alone — `sqlite3`, `decimal`, `argparse`, `tomllib`,
`csv`, `dataclasses`, `importlib.metadata`. There was no point pulling in
a web framework, an ORM, or a CLI framework like Click for a
single-process library with four SQL tables and five subcommands; the
standard library covers all of it cleanly, and it means a clean install
has nothing to resolve, pin-conflict with, or audit beyond Python itself.

## Development

Pinned to exact versions in `pyproject.toml`'s `[project.optional-dependencies]`:

- **pytest** — the test runner.
- **ruff** — linting and formatting, replacing what would otherwise be a
  Black + Flake8 + isort combination with one tool and one config block.
- **mypy** — static type checking, run in strict mode
  (`[tool.mypy] strict = true`) across `src/ledgerkit`.
- **coverage** — test coverage measurement.

None of these ship with the installed package — they're development-only,
under the `dev` extra (`pip install -e ".[dev]"`), and none of their
import paths appear anywhere under `src/ledgerkit/`.

## Why exact pins instead of ranges

A range (`pytest>=8.0`) resolves to whatever the newest matching version
happens to be on the day someone runs `pip install`, which means the
exact set of dependency versions in CI, in a fresh clone six months from
now, and in whatever environment first authored the pin can all silently
diverge. An exact pin (`pytest==9.1.1`) means the same install command
produces the same environment every time, and a dependency bump is a
deliberate, reviewable change to `pyproject.toml` rather something that
happens implicitly on whoever installs last.
