"""One periodic export of what the organisation is actually reporting.

This is the OBSERVED half. A capture is a snapshot: the units that reported, the
quantities each reported, and the edges that were actually present. It carries no
opinion -- comparing it against the declaration is `presence`, comparing two of
them is `regression`, and judging the quantities is the engine at Stage 2.

`complete` is the load-bearing flag. A partial export and a shrinking
organisation look identical in the points list, and only the exporter knows
which it produced. Everything downstream that could mistake one for the other is
guarded on it.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .formats import ACCEPTED_CAPTURE_FORMATS, CAPTURE_FORMAT


class CaptureError(ValueError):
    """The file is not a capture this package can read."""


@dataclass(frozen=True)
class Reading:
    """One unit as it appeared in one export. Satisfies `CapturedPoint`."""

    name: str
    unit_type: str = ""
    path: str = ""
    #: The quantities this unit reported, by indicator name. Empty is a real
    #: answer: the unit was there and reported nothing.
    values: Mapping[str, Any] = field(default_factory=dict)
    state: str | None = None
    edges: Mapping[str, str] = field(default_factory=dict)
    is_enabled: bool = True
    units: str = ""
    thresholds: Mapping[str, Any] = field(default_factory=dict)

    # --- the core's CapturedPoint protocol ---------------------------------
    @property
    def reading(self) -> Any:
        """The core asks each point for ONE reading, to tell reporting from not.

        The state when there is one, and otherwise whatever quantities arrived.
        NOT the state alone, which is what this returned first: a wide export
        carries a status column for some unit types and not others, so an
        Executive reporting a tenure, a span and a rating came back `None` and
        the core called it `declared_unreadable`. Measured on the shipped case
        study: five units, three Executives and two Processes, every one of them
        reporting and every one reported as silent.
        """
        if self.state is not None:
            return self.state
        return self.values or None

    @property
    def is_reading(self) -> bool:
        return self.state is not None or bool(self.values)


@dataclass(frozen=True)
class Export:
    """A whole capture. Satisfies the core's `Capture`."""

    points: Sequence[Reading] = ()
    captured_at: str = ""
    complete: bool = True
    errors: Sequence[str] = ()
    source: str = ""


def load(path: str | Path) -> Export:
    try:
        raw = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError) as problem:
        raise CaptureError(f"{path} could not be read as a capture: {problem}") from None
    if not isinstance(raw, dict) or raw.get("format") not in ACCEPTED_CAPTURE_FORMATS:
        raise CaptureError(
            f"{path} is not one of {ACCEPTED_CAPTURE_FORMATS}; it declares "
            f"{raw.get('format') if isinstance(raw, dict) else type(raw).__name__}")
    points = tuple(
        Reading(name=r.get("name", ""), unit_type=r.get("type", ""),
                path=r.get("path", ""), values=dict(r.get("values") or {}),
                state=r.get("state"), edges=dict(r.get("edges") or {}),
                is_enabled=bool(r.get("enabled", True)))
        for r in (raw.get("units") or ()) if (r or {}).get("name"))
    return Export(points=points, captured_at=raw.get("captured_at", ""),
                  complete=bool(raw.get("complete", False)),
                  errors=tuple(raw.get("errors") or ()),
                  source=raw.get("source", ""))


def write(export: Export, path: str | Path) -> None:
    Path(path).write_text(json.dumps({
        "format": CAPTURE_FORMAT,
        "captured_at": export.captured_at,
        "source": export.source,
        "complete": export.complete,
        "errors": list(export.errors),
        "units": [{"name": p.name, "type": p.unit_type, "path": p.path,
                   "values": dict(p.values), "state": p.state,
                   "edges": dict(p.edges), "enabled": p.is_enabled}
                  for p in export.points],
    }, indent=1) + "\n")


#: Columns that are identity rather than quantity, and are never fed as values.
_IDENTITY = ("id", "type", "name", "status")


def from_csv(path: str | Path, *, captured_at: str = "",
             complete: bool = True, edges: Mapping[str, Mapping[str, str]] | None = None) -> Export:
    """Read a wide CSV export -- one row per unit, one column per indicator.

    THE EMPTY CELL IS NOT A ZERO. A wide export carries every indicator column
    for every unit type, so most cells are blank because the column does not
    apply to that row's type. Blank is dropped rather than coerced, because a
    zero fed to BOUNDEDNESS is a reading and an absent quantity is not.

    Edges are supplied separately: a flat CSV has nowhere to put them, and
    inventing them from an id prefix would be deriving a relationship from a
    name, which is the thing the engine removed for good reason.
    """
    rows = list(csv.DictReader(Path(path).open()))
    if not rows:
        raise CaptureError(f"{path} holds no rows, and an empty capture reports "
                           f"the same as a complete one about an empty organisation")
    supplied = dict(edges or {})
    points = []
    for row in rows:
        ident = (row.get("id") or "").strip()
        if not ident:
            continue
        values = {k: float(v) for k, v in row.items()
                  if k not in _IDENTITY and (v or "").strip() not in ("", "None")}
        points.append(Reading(
            name=ident, unit_type=(row.get("type") or "").strip(),
            path=f"{path}#{ident}", values=values,
            state=(row.get("status") or "").strip() or None,
            edges=dict(supplied.get(ident) or {})))
    return Export(points=tuple(points), complete=complete, source=str(path),
                  captured_at=captured_at or datetime.now(timezone.utc)
                  .replace(microsecond=0).isoformat().replace("+00:00", "Z"))
