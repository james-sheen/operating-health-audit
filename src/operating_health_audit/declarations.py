"""The target operating model -- the units an organisation says it runs.

This is the DECLARATION half of a presence audit. It answers *what should be
there*, and it is deliberately not derived from the export: a declaration
generated from what was found can never report an absence, which is the finding
this package exists to produce.

The core's `DeclarationSource` and `DeclaredPoint` are structural protocols, so
these are plain dataclasses that satisfy them rather than subclasses.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from .formats import DECLARATION_FORMAT

#: Every unit type an operating model may declare. Taken from the domain the
#: Core was tested with, unchanged: five is the set that domain named, and
#: adding a sixth here without adding it to the model would give the engine an
#: entity type it has no indicators for.
UNIT_TYPES = ("Division", "Department", "Executive", "Project", "Process")


class DeclarationError(ValueError):
    """The declaration could not be read as one. Distinct from *it read fine and
    said nothing*, which is a finding rather than an error."""


@dataclass(frozen=True)
class Unit:
    """One declared operating unit. Satisfies the core's `DeclaredPoint`."""

    name: str
    unit_type: str
    display_name: str = ""
    #: Where in the declaration this came from -- a section, a page, a row. The
    #: core prints it so a reader can go and look, so it is never invented.
    source: str = ""
    disabled: bool = False
    #: The relationships this unit is declared to have, as {relation: target}.
    #: Checked by the engine at Stage 2 through CONNECTIVITY, and carried here
    #: because Stage 1 is where the claim is written down.
    edges: Mapping[str, str] = field(default_factory=dict)
    thresholds: Mapping[str, Any] = field(default_factory=dict)

    # --- the core's DeclaredPoint protocol ---------------------------------
    @property
    def type(self) -> str:
        return self.unit_type

    @property
    def expects_reading(self) -> bool:
        """Every declared unit is expected to report something.

        This read `Division, Department, Project, Process` first, on the belief
        that an Executive reports no quantity of its own. The case study says
        otherwise: an Executive reports a tenure, a span of control and a rating,
        and the domain declares axioms over all three. The belief came from the
        export having no STATUS column for executives, which is a fact about one
        column rather than about the unit.
        """
        return True

    @property
    def is_templated(self) -> bool:
        """No unit in an operating model is a template. A declaration names the
        actual division; there is no wildcard row to expand."""
        return False


@dataclass(frozen=True)
class OperatingModel:
    """The whole declaration. Satisfies the core's `DeclarationSource`."""

    points: Sequence[Unit] = ()
    sources: Sequence[str] = ()
    #: Rows that were read and are not usable -- a unit with no name, a type
    #: nothing recognises. Reported rather than dropped: a row silently skipped
    #: makes the declaration smaller and every later count agree with itself.
    anomalies: Sequence[str] = ()
    #: Sources that could not be read at all.
    unreadable: Sequence[str] = ()
    reviewed_by: str = ""
    reviewed_on: str = ""

    @property
    def reviewed(self) -> bool:
        """A declaration nobody signed is a draft. Both halves, because a name
        with no date and a date with no name are each half a review."""
        return bool(self.reviewed_by) and bool(self.reviewed_on)


def load(path: str | Path) -> OperatingModel:
    """Read a declaration file. Raises `DeclarationError` for anything that is
    not one, so a caller never has to tell a traceback from a finding."""
    try:
        raw = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as problem:
        raise DeclarationError(f"{path} could not be read as a declaration: {problem}") from None
    if not isinstance(raw, dict) or raw.get("format") != DECLARATION_FORMAT:
        raise DeclarationError(
            f"{path} is not a {DECLARATION_FORMAT}; it declares "
            f"{raw.get('format') if isinstance(raw, dict) else type(raw).__name__}")

    units, anomalies = [], list(raw.get("anomalies") or ())
    for row in raw.get("units") or ():
        name = (row or {}).get("name")
        kind = (row or {}).get("type")
        if not name:
            anomalies.append("a unit with no name was declared and cannot be matched")
            continue
        if kind not in UNIT_TYPES:
            anomalies.append(f"{name}: declared type {kind!r} is not one this audit knows")
            continue
        units.append(Unit(name=name, unit_type=kind,
                          display_name=row.get("display_name") or name,
                          source=row.get("source") or "",
                          disabled=bool(row.get("disabled")),
                          edges=dict(row.get("edges") or {}),
                          thresholds=dict(row.get("thresholds") or {})))
    return OperatingModel(points=tuple(units),
                          sources=tuple(raw.get("sources") or ()),
                          anomalies=tuple(anomalies),
                          unreadable=tuple(raw.get("unreadable") or ()),
                          reviewed_by=raw.get("reviewed_by") or "",
                          reviewed_on=raw.get("reviewed_on") or "")
