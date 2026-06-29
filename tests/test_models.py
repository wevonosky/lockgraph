"""Tests for the value-type behavior that carries logic (Source, exceptions)."""

import dataclasses

import pytest

from lockgraph.models import Edge, EdgeKind, Member, Source, UnknownMemberError


def test_source_member_dir_prefers_editable() -> None:
    source = Source(editable="libs/core")
    assert source.member_dir == "libs/core"
    assert source.is_member is True


def test_source_member_dir_uses_virtual() -> None:
    source = Source(virtual=".")
    assert source.member_dir == "."
    assert source.is_member is True


def test_source_third_party_is_not_member() -> None:
    source = Source(registry="https://pypi.org/simple")
    assert source.member_dir is None
    assert source.is_member is False


def test_source_keeps_unknown_keys() -> None:
    source = Source(extra={"git": "https://example.invalid/repo.git"})
    assert source.is_member is False
    assert source.extra["git"] == "https://example.invalid/repo.git"


def test_edge_kind_values() -> None:
    assert {kind.value for kind in EdgeKind} == {"main", "dev", "optional"}


def test_models_are_frozen() -> None:
    member = Member(name="core", directory="libs/core")
    with pytest.raises(dataclasses.FrozenInstanceError):
        member.name = "other"  # type: ignore[misc]


def test_unknown_member_error_carries_target() -> None:
    error = UnknownMemberError("ghost")
    assert error.target == "ghost"
    assert isinstance(error, KeyError)


def test_edge_equality_distinguishes_kind() -> None:
    assert Edge("a", "b", EdgeKind.MAIN) != Edge("a", "b", EdgeKind.DEV)
