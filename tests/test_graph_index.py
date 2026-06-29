"""Tests for build_index: canonical keying and member detection."""

from pathlib import Path

from lockgraph.graph import build_index
from lockgraph.lock import load_lock
from lockgraph.models import Index


def test_members_keyed_by_canonical_name(workspace_index: Index) -> None:
    assert set(workspace_index.members) == {
        "core",
        "liba",
        "libb",
        "toy-workspace",
        "web",
        "worker",
    }


def test_member_directories_are_relative_to_lockfile(workspace_index: Index) -> None:
    dirs = {name: member.directory for name, member in workspace_index.members.items()}
    assert dirs["core"] == "libs/core"
    assert dirs["web"] == "apps/web"
    assert dirs["toy-workspace"] == "."


def test_third_party_is_a_package_but_not_a_member(workspace_index: Index) -> None:
    assert "iniconfig" in workspace_index.packages
    assert "iniconfig" not in workspace_index.members


def test_canonicalization_unifies_member_and_dependency_names(fixtures_dir: Path) -> None:
    index = build_index(load_lock(fixtures_dir / "edge_canonical.lock"))
    assert "shared-lib" in index.members
    assert index.members["shared-lib"].directory == "shared"
