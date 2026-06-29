"""PEP 503 name normalization, shared by the parser and every graph projection."""

import re
from typing import Final

CANONICAL_RE: Final[re.Pattern[str]] = re.compile(r"[-_.]+")


def canonical(name: str) -> str:
    """Normalize a project name per PEP 503: lowercase, runs of -_. collapsed to one -."""
    return CANONICAL_RE.sub("-", name).lower()
