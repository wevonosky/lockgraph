"""Shared fixtures: paths to the frozen lockfiles and the built workspace index."""

from pathlib import Path

import pytest

from lockgraph.graph import build_index
from lockgraph.lock import load_lock
from lockgraph.models import Index, Lock

FIXTURES = Path(__file__).parent / "fixtures"
WORKSPACE_LOCK = FIXTURES / "workspace" / "uv.lock"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES


@pytest.fixture
def workspace_lock_path() -> Path:
    return WORKSPACE_LOCK


@pytest.fixture
def workspace_lock() -> Lock:
    return load_lock(WORKSPACE_LOCK)


@pytest.fixture
def workspace_index(workspace_lock: Lock) -> Index:
    return build_index(workspace_lock)
