"""Read a uv.lock into the `Lock` model.

Parsing is deliberately defensive: an unrecognized lock-format `version` warns
but never fails, and malformed package entries are skipped rather than raising.
The member-source keys we rely on are stable across format bumps.
"""

import tomllib
import warnings
from pathlib import Path
from typing import Final

from lockgraph.models import Dependency, Lock, Package, Source

EXPECTED_LOCK_VERSIONS: Final[frozenset[int]] = frozenset({1})


class LockVersionWarning(UserWarning):
    """The lock's top-level format version is outside the known-good set."""


def opt_str(value: object) -> str | None:
    """Return `value` if it is a string, else None."""
    return value if isinstance(value, str) else None


def parse_source(table: object) -> Source:
    """Build a Source from a `source` inline table, keeping unknown keys in `extra`."""
    if not isinstance(table, dict):
        return Source()
    known = {"editable", "virtual", "registry"}
    return Source(
        editable=opt_str(table.get("editable")),
        virtual=opt_str(table.get("virtual")),
        registry=opt_str(table.get("registry")),
        extra={str(key): value for key, value in table.items() if key not in known},
    )


def parse_deps(raw: object) -> tuple[Dependency, ...]:
    """Parse a dependency array into Dependency entries, skipping malformed items."""
    if not isinstance(raw, list):
        return ()
    deps: list[Dependency] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if isinstance(name, str):
            deps.append(Dependency(name=name, marker=opt_str(item.get("marker"))))
    return tuple(deps)


def parse_groups(raw: object) -> tuple[tuple[str, tuple[Dependency, ...]], ...]:
    """Parse a dev/optional group table (group name -> dependency array)."""
    if not isinstance(raw, dict):
        return ()
    return tuple((str(group), parse_deps(deps)) for group, deps in raw.items())


def parse_package(table: dict[str, object]) -> Package | None:
    """Build a Package, or None if the entry lacks a string `name`."""
    name = table.get("name")
    if not isinstance(name, str):
        return None
    return Package(
        name=name,
        version=opt_str(table.get("version")),
        source=parse_source(table.get("source")),
        dependencies=parse_deps(table.get("dependencies")),
        dev_dependencies=parse_groups(table.get("dev-dependencies")),
        optional_dependencies=parse_groups(table.get("optional-dependencies")),
    )


def load_lock(path: str | Path) -> Lock:
    """Read a uv.lock and return its parsed Lock.

    Warns (LockVersionWarning), never raises, when the top-level `version` is not
    in EXPECTED_LOCK_VERSIONS — including when it is absent.
    """
    with Path(path).open("rb") as handle:
        data = tomllib.load(handle)

    version = data.get("version")
    if version not in EXPECTED_LOCK_VERSIONS:
        warnings.warn(
            f"unrecognized uv.lock format version {version!r}; continuing — "
            "the member-source keys lockgraph relies on are stable across format bumps",
            LockVersionWarning,
            stacklevel=2,
        )

    raw_packages = data.get("package")
    entries = raw_packages if isinstance(raw_packages, list) else []
    packages = tuple(
        package
        for entry in entries
        if isinstance(entry, dict)
        if (package := parse_package(entry)) is not None
    )

    revision = data.get("revision")
    return Lock(
        version=version if isinstance(version, int) else None,
        revision=revision if isinstance(revision, int) else None,
        requires_python=opt_str(data.get("requires-python")),
        packages=packages,
    )
