"""Tests for member_closure: correctness, determinism, toggles, cycle safety."""

from pathlib import Path

import pytest

from lockgraph.graph import build_index, member_closure
from lockgraph.lock import load_lock
from lockgraph.models import Index, UnknownMemberError


def names(index: Index, target: str, **kwargs: bool) -> list[str]:
    return [member.name for member in member_closure(index, target, **kwargs)]


def test_closure_is_a_strict_subset_of_all_members(workspace_index: Index) -> None:
    closure = set(names(workspace_index, "web"))
    assert closure == {"core", "liba", "libb", "web"}
    assert closure < set(workspace_index.members)


def test_closure_dedups_the_diamond(workspace_index: Index) -> None:
    # core is reached via both liba and libb but appears exactly once.
    assert names(workspace_index, "web").count("core") == 1


def test_closure_is_sorted_by_canonical_name(workspace_index: Index) -> None:
    result = names(workspace_index, "web")
    assert result == sorted(result)


def test_dev_and_optional_toggles_extend_the_closure(workspace_index: Index) -> None:
    assert names(workspace_index, "worker") == ["core", "worker"]
    assert names(workspace_index, "worker", with_dev=True) == ["core", "liba", "worker"]
    assert names(workspace_index, "worker", with_optional=True) == ["core", "libb", "worker"]


def test_include_self_false_drops_the_target(workspace_index: Index) -> None:
    assert names(workspace_index, "worker", include_self=False) == ["core"]


def test_closure_accepts_non_canonical_target(workspace_index: Index) -> None:
    assert names(workspace_index, "WEB") == ["core", "liba", "libb", "web"]


def test_unknown_target_raises(workspace_index: Index) -> None:
    with pytest.raises(UnknownMemberError):
        member_closure(workspace_index, "iniconfig")
    with pytest.raises(UnknownMemberError):
        member_closure(workspace_index, "ghost")


def test_cycle_terminates(fixtures_dir: Path) -> None:
    index = build_index(load_lock(fixtures_dir / "edge_cycle.lock"))
    assert names(index, "alpha") == ["alpha", "beta"]


def test_self_dependency_terminates(fixtures_dir: Path) -> None:
    index = build_index(load_lock(fixtures_dir / "edge_self_dep.lock"))
    assert names(index, "narcissus") == ["narcissus"]
    assert names(index, "narcissus", include_self=False) == []
