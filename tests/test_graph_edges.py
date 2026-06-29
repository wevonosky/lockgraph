"""Tests for member_edges: kind tagging, third-party filtering, dedup, sorting."""

from pathlib import Path

from lockgraph.graph import build_index, member_edges
from lockgraph.lock import load_lock
from lockgraph.models import Index


def triples(index: Index, **kwargs: bool) -> list[tuple[str, str, str]]:
    return [(edge.src, edge.dst, edge.kind.value) for edge in member_edges(index, **kwargs)]


def test_main_edges_only_by_default(workspace_index: Index) -> None:
    assert triples(workspace_index) == [
        ("liba", "core", "main"),
        ("libb", "core", "main"),
        ("web", "liba", "main"),
        ("web", "libb", "main"),
        ("worker", "core", "main"),
    ]


def test_dev_and_optional_edges_are_tagged(workspace_index: Index) -> None:
    edges = triples(workspace_index, with_dev=True, with_optional=True)
    assert ("worker", "liba", "dev") in edges
    assert ("worker", "libb", "optional") in edges


def test_third_party_targets_produce_no_edges(workspace_index: Index) -> None:
    assert all(dst != "iniconfig" for _src, dst, _kind in triples(workspace_index))


def test_output_is_sorted_and_deduped(workspace_index: Index) -> None:
    edges = triples(workspace_index, with_dev=True, with_optional=True)
    assert edges == sorted(edges)
    assert len(edges) == len(set(edges))


def test_same_target_via_main_and_dev_yields_two_edges(fixtures_dir: Path) -> None:
    index = build_index(load_lock(fixtures_dir / "edge_dup_edges.lock"))
    assert triples(index, with_dev=True) == [
        ("x", "y", "dev"),
        ("x", "y", "main"),
    ]


def test_self_loops_are_dropped(fixtures_dir: Path) -> None:
    index = build_index(load_lock(fixtures_dir / "edge_self_dep.lock"))
    assert triples(index) == []
