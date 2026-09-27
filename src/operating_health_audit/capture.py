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
from collections.abc import Sequence as _Sequence
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from .formats import ACCEPTED_CAPTURE_FORMATS, CAPTURE_FORMAT


class CaptureError(ValueError):
    """The file is not a capture this package can read."""


#: Why a capture holding no units is refused rather than read. One sentence,
#: said by the CSV reader about a file with no rows, by `load` about a file with
#: no units, and by the feeder about a capture handed to it empty, so the three
#: cannot come to disagree about what an empty capture is.
EMPTY_CAPTURE = ("an empty capture reports the same as a complete one about an "
                 "empty organisation")


def _positions(labels: Sequence[str]) -> str:
    """`units[3]`, or `units[3], units[7] and 2 more` -- every refusal names
    where, and a list of every row of a large file would bury the sentence."""
    shown = list(labels[:5])
    if len(labels) > 5:
        return f"{', '.join(shown)} and {len(labels) - 5} more"
    return shown[0] if len(shown) == 1 else f"{', '.join(shown[:-1])} and {shown[-1]}"


def refusal(labelled: Sequence[tuple[str, Any]]) -> str | None:
    """Why these would be read as captures of nothing, or None when none would.

    Each item is `(where, what)` -- `captures[3]` in a series, `before` in a
    comparison. The readers here take `.points` off whatever they are handed,
    and took a missing attribute as no points: a path, a string or a parsed dict
    passed where a loaded capture belongs ran clean, exit 0, with 0 entities.

    Not an `isinstance` check against `Export`: the core's `Capture` is a
    protocol, and a caller's own export type satisfies it the way `Export` does.
    What is checked is what every reader here reads -- a sequence of points,
    holding at least one.
    """
    strangers, empty = [], []
    for where, item in labelled:
        points = getattr(item, "points", None)
        if isinstance(points, (str, bytes)) or not isinstance(points, _Sequence):
            strangers.append(f"{where} (a {type(item).__name__})")
        elif not points:
            empty.append(where)
    if strangers:
        one = len(strangers) == 1
        what = "is not a loaded capture" if one else "are not loaded captures"
        stands = "it stands it holds" if one else "they stand they hold"
        return (f"{_positions(strangers)} {what}; read a file with `capture.load` "
                f"first -- as {stands} no units, and {EMPTY_CAPTURE}")
    if empty:
        return (f"{_positions(empty)} {'holds' if len(empty) == 1 else 'hold'} no "
                f"units, and {EMPTY_CAPTURE}")
    return None


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
    # REFUSED, NOT READ AS NOTHING. A capture with no units used to load as an
    # empty export, and an empty export runs clean through `detect`, reads
    # `ran` with no changes through `regression` and passes `gate` -- every
    # unit passed is true of no units. `from_csv` refused the same thing from
    # the start; this is the JSON reader learning it.
    units = raw.get("units")
    if units is None or units == []:
        raise CaptureError(f"{path} holds no units, and {EMPTY_CAPTURE}")
    if not isinstance(units, list):
        raise CaptureError(f"{path}: `units` is a {type(units).__name__}, not a list "
                           f"of units")
    # A UNIT WITH NO NAME IS REFUSED BY WHERE IT IS, the way the declaration
    # reports one as an anomaly rather than skipping it. It used to be dropped
    # without a word, so a file of fourteen nameless units loaded as an empty
    # capture: dropped, it makes the capture smaller than the export and every
    # later count agree with itself.
    nameless = [f"units[{i}]" + ("" if isinstance(r, dict) else f" (a {type(r).__name__})")
                for i, r in enumerate(units) if not (isinstance(r, dict) and r.get("name"))]
    if nameless:
        raise CaptureError(
            f"{path}: {_positions(nameless)} "
            f"{'has' if len(nameless) == 1 else 'have'} no name, so nothing declared "
            f"can be matched to {'it' if len(nameless) == 1 else 'them'}, and dropping "
            f"{'it' if len(nameless) == 1 else 'them'} would make the capture smaller "
            f"than the export")
    points = tuple(
        Reading(name=r.get("name", ""), unit_type=r.get("type", ""),
                path=r.get("path", ""), values=dict(r.get("values") or {}),
                state=r.get("state"), edges=dict(r.get("edges") or {}),
                is_enabled=bool(r.get("enabled", True)))
        for r in units)
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
    with Path(path).open(newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [(reader.line_num, row) for row in reader]
        columns = list(reader.fieldnames or ())
    if not rows:
        raise CaptureError(f"{path} holds no rows, and {EMPTY_CAPTURE}")
    # THE ROW WITH NO ID IS REFUSED BY ITS LINE, not skipped. Skipped, a file
    # whose every row lacked one -- or whose id column is named something else --
    # wrote a capture of no units and reported it as written.
    if "id" not in columns:
        raise CaptureError(f"{path} has no `id` column, so no row names a unit, and "
                           f"{EMPTY_CAPTURE}")
    unnamed = [f"line {line}" for line, row in rows if not (row.get("id") or "").strip()]
    if unnamed:
        raise CaptureError(
            f"{path}: the row on {_positions(unnamed)} has no id, so nothing declared "
            f"can be matched to it, and dropping it would make the capture smaller "
            f"than the export" if len(unnamed) == 1 else
            f"{path}: the rows on {_positions(unnamed)} have no id, so nothing "
            f"declared can be matched to them, and dropping them would make the "
            f"capture smaller than the export")
    supplied = dict(edges or {})
    points = []
    for _, row in rows:
        ident = (row.get("id") or "").strip()
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
