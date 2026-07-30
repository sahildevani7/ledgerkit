# Documentation index

- [architecture.md](architecture.md) — module layout, dependency
  direction, and the extension seams
- [architecture-decisions.md](architecture-decisions.md) — why a few
  non-obvious things are built the way they are
- [money-and-currency.md](money-and-currency.md) — the `Money`/`Currency`
  design: why not `float`, how `allocate` works, what's deliberately out
  of scope
- [csv-import-format.md](csv-import-format.md) — the one shipped CSV
  dialect's exact format
- [migrations.md](migrations.md) — how the schema migration runner works
  and how to add a migration
- [dependencies.md](dependencies.md) — what's pinned, why, and why there's
  no runtime dependency at all
- [cli.md](cli.md) — every CLI command, its arguments, and examples
- [error-handling.md](error-handling.md) — the error hierarchy, `code`
  values, and CLI exit codes
- [testing.md](testing.md) — test layout, shared fixtures, and
  determinism conventions
- [security.md](security.md) — no network access, what's stored where,
  how input is validated
- [glossary.md](glossary.md) — domain terms as this codebase uses them
- [faq.md](faq.md) — answers to questions that come up repeatedly

Start with `architecture.md` for the shape of the codebase, or `cli.md`
if you just want to use the command line tool.
