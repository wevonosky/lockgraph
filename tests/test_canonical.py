"""Tests for PEP 503 name canonicalization."""

import pytest

from lockgraph.canonical import canonical


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Foo_Bar", "foo-bar"),
        ("foo.bar", "foo-bar"),
        ("foo__bar", "foo-bar"),
        ("foo--_.bar", "foo-bar"),
        ("Shared_Lib", "shared-lib"),
        ("ALREADY-canon", "already-canon"),
        ("plain", "plain"),
        ("", ""),
    ],
)
def test_canonical(raw: str, expected: str) -> None:
    assert canonical(raw) == expected


def test_canonical_is_idempotent() -> None:
    once = canonical("Foo._Bar")
    assert canonical(once) == once
