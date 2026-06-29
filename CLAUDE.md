# lockgraph

A small, single-package CLI that reads a `uv.lock` and exposes the **workspace-member dependency graph** — the internal member→member edges, with third-party packages filtered out. From that graph it offers several projections:

- **`tree`** — render the member graph (forward or `--invert`ed) for inspection; the workspace's architecture, minus the third-party noise `uv tree` drowns it in.
- **`closure`** — flatten a member's transitive workspace closure to a member/dir list.
- **`copy`** — generate / verify the Docker `COPY` lines needed to build a single member in a uv workspace (the hand-maintained "COPY dance"), with a `check` mode for CI.

## Stack

- Python **3.11+** (we depend on stdlib `tomllib`, so 3.11 is the floor).
- **click** for the CLI.
- **uv** for environments and as the build backend (`uv_build`).
- **pyrefly** for type checking, **ruff** for lint/format, **pytest** for tests.

Code quality and maintainability are the top priority. Everything must pass ruff and pyrefly.

## Domain rules (these are load-bearing, not style)

- **lockgraph reflects the lock, never the pyprojects.** Every projection is computed from `uv.lock`. If the lock is stale relative to the pyprojects, our output is stale too — that's correct behavior, not a bug. Say so in help text; pair `copy check` with `uv lock --check` in docs, don't try to re-derive resolution ourselves.
- **A package is a workspace member iff its lock `source` table has an `editable` or `virtual` key**; that key's value is the member's directory relative to the lockfile. This is the stable part of the schema we bet on.
- **Generated output must be byte-deterministic.** `copy check` works by regenerating and diffing, so generation must sort by PEP 503 canonical name, use fixed whitespace, and fix trailing-slash conventions. Determinism is a contract, not a nicety.
- **Surgical, not whole-dir, COPY.** The source layer emits `<member>/src` plus each member's declared build inputs (`project.readme`, license files, dynamic-version files) — not the whole member directory — to keep Docker layer caching tight. Dropping a declared README breaks the member's editable build.
- **The lock-format `version` is warned on, never fatal.** Parse defensively; the member-source keys we rely on are stable across format bumps.

## Code style

- **No `from __future__ import annotations` by default.** Only add it when genuinely needed (forward refs, etc.).
- **Annotate module-level constants with `Final[...]`** (e.g. `EXPECTED_LOCK_VERSIONS: Final[frozenset[int]] = frozenset({1})`).
- **Strongly avoid leading-underscore "private" names.** Default to public and testable. Reserve `_` for truly trivial internal plumbing with no behavior worth testing. If it has real logic, it's public.
- **Minimal comments — "why", not "what".** Prefer a docstring over a comment block. Bias toward deleting comments that restate the code.
- **Define before reference** — everything is defined above its first use.
- **Don't introduce one-use temporary variables** when the inline expression stays readable; conversely, extract a repeated transformation (e.g. a `.strip()` applied twice) into a local instead of duplicating it.
- **Manage dependencies with `uv add` / `uv remove`**, never by hand-editing `pyproject.toml`.
- Keep the pure graph logic (load, index, closure, edges) free of click — it should be importable and testable as a plain library. click is a thin shell on top.

## Testing

Every piece of functionality ships with meaningful tests (no `assert True` placeholders). Tests live under `tests/`, mirroring `src/lockgraph/`. Fixture lockfiles for the parser go under `tests/fixtures/`.

## Quality checks

Run `scripts/check.sh` before considering a logical block of work done. Individually:

- `uv run ruff format .` then `uv run ruff check`
- `uv run pyrefly check`
- `uv run pytest`
