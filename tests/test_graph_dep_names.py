"""Tests for dep_names: category toggles, canonicalization, ordering, dedup."""

from lockgraph.graph import dep_names
from lockgraph.models import Dependency, Index, Package, Source


def make_package() -> Package:
    return Package(
        name="consumer",
        version="0.1.0",
        source=Source(editable="consumer"),
        dependencies=(Dependency(name="Main_Dep"), Dependency(name="shared")),
        dev_dependencies=(("dev", (Dependency(name="dev-dep"), Dependency(name="shared"))),),
        optional_dependencies=(("cli", (Dependency(name="opt.dep"),)),),
    )


def test_main_only_by_default() -> None:
    assert dep_names(make_package()) == ["main-dep", "shared"]


def test_with_dev_appends_dev_group_and_dedups() -> None:
    assert dep_names(make_package(), with_dev=True) == ["main-dep", "shared", "dev-dep"]


def test_with_optional_appends_extras() -> None:
    assert dep_names(make_package(), with_optional=True) == ["main-dep", "shared", "opt-dep"]


def test_with_both_preserves_main_dev_optional_order() -> None:
    assert dep_names(make_package(), with_dev=True, with_optional=True) == [
        "main-dep",
        "shared",
        "dev-dep",
        "opt-dep",
    ]


def test_third_party_dep_names_are_listed(workspace_index: Index) -> None:
    assert dep_names(workspace_index.packages["core"]) == ["iniconfig"]
