"""The workspace member graph derived from a parsed Lock.

Everything here keys on PEP 503 canonical names and filters third-party packages
out, so the projections (closure, edges) see only member -> member structure.
"""

from collections import deque

from lockgraph.canonical import canonical
from lockgraph.models import (
    Edge,
    EdgeKind,
    Index,
    Lock,
    Member,
    Package,
    UnknownMemberError,
)


def build_index(lock: Lock) -> Index:
    """Index every package by canonical name and collect the workspace members."""
    packages: dict[str, Package] = {}
    members: dict[str, Member] = {}
    for package in lock.packages:
        name = canonical(package.name)
        packages[name] = package
        member_dir = package.source.member_dir
        if member_dir is not None:
            members[name] = Member(name=name, directory=member_dir)
    return Index(packages=packages, members=members)


def dep_names(
    package: Package,
    *,
    with_dev: bool = False,
    with_optional: bool = False,
) -> list[str]:
    """Canonical dependency names of a package: main, then dev, then optional.

    Order is stable (declaration order within each category) and de-duplicated
    across categories.
    """
    deps = list(package.dependencies)
    if with_dev:
        for _group, group_deps in package.dev_dependencies:
            deps.extend(group_deps)
    if with_optional:
        for _extra, extra_deps in package.optional_dependencies:
            deps.extend(extra_deps)
    return list(dict.fromkeys(canonical(dep.name) for dep in deps))


def member_closure(
    index: Index,
    target: str,
    *,
    with_dev: bool = False,
    with_optional: bool = False,
    include_self: bool = True,
) -> list[Member]:
    """Transitive workspace-member closure of `target`, third-party filtered out.

    Returns members sorted by canonical name; includes `target` itself unless
    `include_self` is False. Cycle-safe. Raises UnknownMemberError if `target`
    is not a known member.
    """
    target = canonical(target)
    if target not in index.members:
        raise UnknownMemberError(target)

    visited: set[str] = set()
    reached: set[str] = set()
    queue: deque[str] = deque([target])
    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        if include_self or current != target:
            reached.add(current)
        package = index.packages[current]
        for name in dep_names(package, with_dev=with_dev, with_optional=with_optional):
            if name in index.members:
                queue.append(name)
    return [index.members[name] for name in sorted(reached)]


def member_edges(
    index: Index,
    *,
    with_dev: bool = False,
    with_optional: bool = False,
) -> list[Edge]:
    """Forward member -> member edges across the whole workspace, tagged by kind.

    Self-loops are dropped; an edge to the same member via both main and dev is
    kept as two distinct edges (the kind is preserved). Sorted and de-duplicated.
    """
    edges: set[Edge] = set()
    for src, package in index.packages.items():
        if src not in index.members:
            continue
        kinded = [(EdgeKind.MAIN, package.dependencies)]
        if with_dev:
            kinded.extend((EdgeKind.DEV, deps) for _group, deps in package.dev_dependencies)
        if with_optional:
            kinded.extend(
                (EdgeKind.OPTIONAL, deps) for _extra, deps in package.optional_dependencies
            )
        for kind, deps in kinded:
            for dep in deps:
                dst = canonical(dep.name)
                if dst != src and dst in index.members:
                    edges.add(Edge(src=src, dst=dst, kind=kind))
    return sorted(edges, key=lambda edge: (edge.src, edge.dst, edge.kind.value))
