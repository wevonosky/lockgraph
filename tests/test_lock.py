"""Tests for parsing a uv.lock into the Lock model."""

from pathlib import Path

import pytest

from lockgraph.lock import (
    LockVersionWarning,
    load_lock,
    opt_str,
    parse_deps,
    parse_groups,
    parse_package,
    parse_source,
)
from lockgraph.models import Dependency, Lock, Package


def by_name(lock: Lock) -> dict[str, Package]:
    return {package.name: package for package in lock.packages}


def test_load_lock_top_level(workspace_lock: Lock) -> None:
    assert workspace_lock.version == 1
    assert workspace_lock.revision == 3
    assert workspace_lock.requires_python == ">=3.11"
    assert len(workspace_lock.packages) == 7


def test_load_lock_member_and_third_party_sources(workspace_lock: Lock) -> None:
    packages = by_name(workspace_lock)
    assert packages["core"].source.editable == "libs/core"
    assert packages["toy-workspace"].source.virtual == "."
    assert packages["iniconfig"].source.registry == "https://pypi.org/simple"
    assert packages["iniconfig"].source.is_member is False


def test_load_lock_dynamic_version_is_none(workspace_lock: Lock) -> None:
    assert by_name(workspace_lock)["web"].version is None


def test_load_lock_parses_dev_and_optional_groups(workspace_lock: Lock) -> None:
    worker = by_name(workspace_lock)["worker"]
    assert worker.dependencies == (Dependency(name="core"),)
    assert worker.dev_dependencies == (("dev", (Dependency(name="liba"),)),)
    assert worker.optional_dependencies == (("cli", (Dependency(name="libb"),)),)


def test_load_lock_accepts_str_and_path(workspace_lock_path: Path) -> None:
    from_path = load_lock(workspace_lock_path)
    from_str = load_lock(str(workspace_lock_path))
    assert from_path == from_str


def test_unrecognized_version_warns_but_returns_lock() -> None:
    path = Path(__file__).parent / "fixtures" / "edge_unknown_version.lock"
    with pytest.warns(LockVersionWarning):
        lock = load_lock(path)
    assert lock.version == 99
    assert lock.packages[0].name == "solo"


def test_absent_version_warns(tmp_path: Path) -> None:
    lock_path = tmp_path / "noversion.lock"
    lock_path.write_text('[[package]]\nname = "solo"\nsource = { editable = "." }\n')
    with pytest.warns(LockVersionWarning):
        lock = load_lock(lock_path)
    assert lock.version is None
    assert lock.revision is None


def test_opt_str() -> None:
    assert opt_str("x") == "x"
    assert opt_str(7) is None
    assert opt_str(None) is None


def test_parse_source_non_dict_is_empty() -> None:
    source = parse_source("registry")
    assert source.is_member is False
    assert source.extra == {}


def test_parse_source_keeps_unknown_keys() -> None:
    source = parse_source({"git": "https://example.invalid/r.git", "rev": "abc"})
    assert source.extra == {"git": "https://example.invalid/r.git", "rev": "abc"}


def test_parse_deps_handles_non_list_and_junk_items() -> None:
    assert parse_deps(None) == ()
    assert parse_deps(["not-a-table", {"no": "name"}]) == ()
    assert parse_deps([{"name": "x", "marker": "sys_platform == 'win32'"}]) == (
        Dependency(name="x", marker="sys_platform == 'win32'"),
    )


def test_parse_groups_non_dict_is_empty() -> None:
    assert parse_groups([]) == ()


def test_parse_package_requires_name() -> None:
    assert parse_package({"source": {"editable": "."}}) is None
    assert parse_package({"name": "ok"}) is not None
