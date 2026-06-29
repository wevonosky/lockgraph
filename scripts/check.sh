#!/usr/bin/env bash
# Run every Python check for lockgraph with one command. Mirrors what CI runs.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# Sync the project plus its dev group so every tool and test dep resolves.
uv sync --all-extras

uv run ruff format --check .
uv run ruff check .
uv run pyrefly check
uv run pytest
