"""Value types for the parsed lock and the derived workspace graph.

This module imports nothing from its siblings so the parser (`lock`) and the
graph algorithms (`graph`) can both depend on it without an import cycle.
"""

import enum
from dataclasses import dataclass, field


class EdgeKind(enum.Enum):
    """Why a member -> member edge exists."""

    MAIN = "main"
    DEV = "dev"
    OPTIONAL = "optional"


@dataclass(frozen=True, slots=True)
class Source:
    """A package's lock `source` inline table.

    A package is a workspace member iff `editable` or `virtual` is set; that
    key's value is the member directory relative to the lockfile. Unrecognized
    source keys are kept in `extra` so we parse defensively across format bumps.
    """

    editable: str | None = None
    virtual: str | None = None
    registry: str | None = None
    extra: dict[str, object] = field(default_factory=dict)

    @property
    def member_dir(self) -> str | None:
        """Member directory (the editable/virtual value), or None for third-party."""
        return self.editable if self.editable is not None else self.virtual

    @property
    def is_member(self) -> bool:
        """Whether this package is a workspace member."""
        return self.member_dir is not None


@dataclass(frozen=True, slots=True)
class Dependency:
    """One entry in a package's dependency list (name plus optional marker)."""

    name: str
    marker: str | None = None


@dataclass(frozen=True, slots=True)
class Package:
    """A single `[[package]]` entry. `name` is the raw lock value, not canonical."""

    name: str
    version: str | None
    source: Source
    dependencies: tuple[Dependency, ...] = ()
    dev_dependencies: tuple[tuple[str, tuple[Dependency, ...]], ...] = ()
    optional_dependencies: tuple[tuple[str, tuple[Dependency, ...]], ...] = ()


@dataclass(frozen=True, slots=True)
class Lock:
    """The parsed top level of a uv.lock."""

    version: int | None
    revision: int | None
    requires_python: str | None
    packages: tuple[Package, ...]


@dataclass(frozen=True, slots=True)
class Member:
    """A workspace member: canonical name plus its directory relative to the lockfile."""

    name: str
    directory: str


@dataclass(frozen=True, slots=True)
class Edge:
    """A forward member -> member edge, tagged with why it exists."""

    src: str
    dst: str
    kind: EdgeKind


@dataclass(frozen=True, slots=True)
class Index:
    """A built view over a Lock: packages and members keyed by canonical name."""

    packages: dict[str, Package]
    members: dict[str, Member]


class UnknownMemberError(KeyError):
    """Raised when a closure/edge target is not a known workspace member."""

    def __init__(self, target: str) -> None:
        self.target = target
        super().__init__(target)
