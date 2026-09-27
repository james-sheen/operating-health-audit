"""Stage 2: a SERIES of captures, fed to the engine.

THE ENGINE IS IMPORTED HERE AND NOWHERE ELSE, so the exception table lives in
one place. `yaml.YAMLError` is not a `ValueError`, and a malformed model that
escapes as a traceback exits 1 -- which this package's contract reads as
FINDINGS, meaning a broken model reports as a bad organisation.

A SERIES, NOT A SNAPSHOT, and that is the whole reason this module takes a list.
Every axiom this domain declares except CONNECTIVITY has a sample floor above
one: MONOTONICITY 3, BOUNDEDNESS 5, STABILITY 10, RESPONSIVENESS 20,
HOMEOSTASIS 30. Handed one capture the engine answers the structure and declines
everything else `insufficient_samples`, correctly. `docs/burn-in.md` carries the
arithmetic against a real reporting cadence.

THE SILENCE GATE RUNS HERE. A model whose declarations the loader did not
recognise judges nothing, and judging nothing composes clean unless something
asks. Three accessors are read and reported: declarations dropped, properties
fed that no indicator reads, and series nothing will ever consume.

A CAPTURE IS FED AT THE TIME IT WAS TAKEN. This fed every series as bare values
thirty days apart, ending at the clock, and never read `captured_at` -- so a
skipped month, a review dated the 31st or a back-filled quarter all arrived as
the same even ladder, and every window, baseline and learn-stage date the engine
computed was computed from a spacing this module made up. Found by an outside
verification that fed calendar months through here and got thirty-day answers.
When every capture carries a stamp, the series is fed as `(captured_at, value)`
pairs in stamp order and judged as of the latest one; when none does, it is
spaced at `interval_seconds` and ends at the clock, as before. `run` reports
which, under `timing`, because a declared cadence and a measured one read the
same in every figure downstream.
"""

from __future__ import annotations

from contextlib import nullcontext
from datetime import datetime
from typing import Any, Mapping, Sequence

from . import capture as _capture
from . import exit_contract as x
from .vertical import REQUIRED_EDGE, OperatingVocabulary


class EngineUnavailable(RuntimeError):
    """The detect extra is not installed. Distinct from the engine running and
    declining, which is an answer."""


class ModelUnreadable(ValueError):
    """The model file is not one the engine could load."""


class CaptureUnusable(ValueError):
    """A series this package cannot feed: empty, holding an item that is not a
    loaded capture or is one with no units, or carrying a reading the engine
    refuses. Raised by `open_session`; `run` answers the same sentence as
    `could_not_run` instead of raising."""


#: What `run` says when it is handed no captures at all.
NO_CAPTURES = ("no captures were supplied, and an empty series reports the same "
               "as a complete one about an organisation that never changed")


def unusable(captures: Sequence[Any]) -> str | None:
    """Why this series cannot be fed, or None when it can.

    EVERY ITEM, NOT ONLY THE LATEST. An empty capture partway through a series
    is the whole-series defect a month at a time: each unit's series one reading
    short, and every month after it moved up a slot.
    """
    if not captures:
        return NO_CAPTURES
    return _capture.refusal([(f"captures[{position}]", item)
                             for position, item in enumerate(captures)]) \
        or _stamps(captures)[1]


#: What `timing` names when the series was placed by each capture's own stamp.
TIMED_BY_CAPTURE = "captured_at"
#: And when no capture carried one, so the series was spaced at the interval.
TIMED_BY_INTERVAL = "interval_seconds"


def _stamps(captures: Sequence[Any]) -> tuple[list[datetime | None], str | None]:
    """Each capture's `captured_at` as an instant, and why the series cannot be
    placed in time, if it cannot.

    ALL OR NONE. A series is placed by its stamps or spaced at the declared
    interval; half of each is two clocks in one series, and which months landed
    where would depend on which half was longer. The engine refuses the same mix
    within one call, in a sentence about its own arguments; this says which
    captures, in this package's words, before the engine is reached.
    """
    stamps: list[datetime | None] = []
    unreadable: list[str] = []
    for position, export in enumerate(captures):
        raw = getattr(export, "captured_at", "") or ""
        try:
            stamps.append(_capture.instant(raw))
        except ValueError:
            stamps.append(None)
            unreadable.append(f"captures[{position}] ({raw!r})")
    if unreadable:
        return stamps, (f"the captured_at of {_capture._positions(unreadable)} is not "
                        f"a date and time, so the series cannot be placed in time; "
                        f"give it in ISO 8601, such as 2026-01-31")
    missing = [f"captures[{position}]" for position, when in enumerate(stamps)
               if when is None]
    if missing and len(missing) < len(stamps):
        return stamps, (f"{_capture._positions(missing)} "
                        f"{'carries' if len(missing) == 1 else 'carry'} no captured_at "
                        f"and the rest do; a series is placed by its stamps or spaced "
                        f"at the declared interval, never both -- stamp every capture "
                        f"(`capture --captured-at`), or none")
    first: dict[datetime, int] = {}
    repeated: list[str] = []
    for position, when in enumerate(stamps):
        if when is None:
            continue
        if when in first:
            repeated.append(f"captures[{first[when]}] and captures[{position}]")
        else:
            first[when] = position
    if repeated:
        return stamps, (f"{'; '.join(repeated)} are stamped the same instant, so one "
                        f"unit would carry two readings at one time; a series holds "
                        f"one capture per moment")
    return stamps, None


def timing(captures: Sequence[Any], *,
           interval_seconds: float = 2_592_000.0) -> dict[str, Any]:
    """How this series is placed in time, as `run` reports it.

    `timed_by` is `captured_at` when every capture carries a stamp, and then the
    first and last of them; it is `interval_seconds` when none does, and then the
    interval the series was spaced at. A series `unusable` refuses has no timing.
    """
    stamps, _ = _stamps(captures)
    if stamps and all(when is not None for when in stamps):
        ordered = sorted(stamps)
        return {"timed_by": TIMED_BY_CAPTURE,
                "first": ordered[0].isoformat(), "last": ordered[-1].isoformat()}
    return {"timed_by": TIMED_BY_INTERVAL, "interval_seconds": interval_seconds}


def _latest_stamp(captures: Sequence[Any]) -> datetime | None:
    """The instant a stamped series is judged at: its latest capture."""
    stamps, _ = _stamps(captures)
    if stamps and all(when is not None for when in stamps):
        return max(stamps)
    return None


def _loaded(model_path: str) -> Any:
    """A session with the model loaded and nothing fed."""
    api = _engine()
    session = api.EngineSession()
    try:
        session.load_model(model_path)
    except Exception as problem:            # yaml errors are not ValueError
        raise ModelUnreadable(f"{model_path} could not be loaded as a domain model: "
                              f"{type(problem).__name__}: {problem}") from None
    return session


def _engine():
    try:
        from arbiter_engine import api
    except ImportError as problem:
        raise EngineUnavailable(
            f"Stage 2 needs the engine: pip install operating-health-audit[detect] "
            f"({problem})") from None
    return api


#: The property name a state is fed under. The model declares STABILITY on
#: `status`, so that is the name the engine looks for.
STATE_PROPERTY = "status"


def _fed(point: Any) -> dict[str, Any]:
    """Every quantity this unit reports, INCLUDING its state.

    The state used to be left out, and nothing said so. The model declares
    STABILITY on `status` for three entity types; the feeder passed only
    `values`, so the engine received no observation of the property the axiom
    reads and declined `too few state observations` for ever. Measured: walking
    each unit around its declared state cycle changed nothing at all, because
    the transitions were never fed -- a fixture fix for a feeder bug, which is
    the shape that makes a gap look like a limitation of the data.
    """
    fed = dict(getattr(point, "values", {}) or {})
    state = getattr(point, "state", None)
    if state is not None:
        fed[STATE_PROPERTY] = state
    return fed


def _positioned(captures: Sequence[Any], unit: str,
                indicator: str) -> list[tuple[int, Any]]:
    """`(position, value)` for every capture in which `unit` reported `indicator`."""
    out = []
    for position, export in enumerate(captures):
        for point in getattr(export, "points", ()) or ():
            if point.name == unit and indicator in _fed(point):
                out.append((position, _fed(point)[indicator]))
    return out


def _series(captures: Sequence[Any]) -> dict[tuple[str, str], list[Any]]:
    """Every (unit, quantity) the captures report, in capture order."""
    series: dict[tuple[str, str], list[Any]] = {}
    for export in captures:
        for point in getattr(export, "points", ()) or ():
            for name, value in _fed(point).items():
                series.setdefault((point.name, name), []).append(value)
    return series


def open_session(model_path: str, captures: Sequence[Any], *,
                 interval_seconds: float = 2_592_000.0) -> Any:
    """A session with the model loaded and the series fed, not yet checked.

    Split out of `run` so the other stages of the loop -- `hypothesize`, `plan`
    and whatever the engine adds -- can be asked about the same session `run`
    judges, rather than a second one built to look like it. A series `unusable`
    refuses raises `CaptureUnusable`, after the model is read, so a broken model
    is still reported as broken first.
    """
    session = _loaded(model_path)
    refusal = unusable(captures)
    if refusal:
        raise CaptureUnusable(refusal)

    # IN THE ORDER THEY WERE TAKEN, when they say. The latest capture supplies
    # the units and their current values, and the latest by stamp is the one
    # that is -- whatever order the files were named on a command line in.
    stamps, _ = _stamps(captures)
    timed = all(when is not None for when in stamps)
    if timed:
        order = sorted(range(len(captures)), key=lambda position: stamps[position])
        captures = [captures[position] for position in order]
        stamps = [stamps[position] for position in order]

    latest = captures[-1]
    series = _series(captures)

    for point in getattr(latest, "points", ()) or ():
        session.add_entity(point.name, point.unit_type,
                           properties=_fed(point), name=point.name)
    # CONNECTIVITY reads relationships and nothing else, so an edge that never
    # reaches this call is an edge the engine cannot see however well declared.
    for point in getattr(latest, "points", ()) or ():
        for relation, target in (getattr(point, "edges", {}) or {}).items():
            session.add_relationship(point.name, relation, target)

    # ONE DOOR FOR BOTH KINDS. A state series used to go round the session into
    # `session.history`, because `add_observations` cast every reading to a
    # number (FINDINGS F1, filed upstream as issue #14). From engine 0.2.11 the
    # session keeps a reading of a property the model declares `type: STATE` as
    # a state, so the workaround is gone and the floor names that release.
    #
    # A READING THE ENGINE REFUSES IS REFUSED HERE, IN THE ENGINE'S WORDS. A word
    # where the model declares a number -- `N/A` in a JSON capture's values --
    # raised out of `add_observations` uncaught, and a traceback exits 1, which
    # this package's contract reads as findings. Only that refusal is caught: it
    # is a `ValueError` naming the reading it refused, `<unit>.<quantity>: ...`,
    # which is how the engine reports a number that is not one and a state that
    # is None. Anything else -- a series of the wrong shape, a failure in a
    # store -- is not a refused reading and propagates as it did.
    for (entity, indicator), values in series.items():
        if timed:
            # Paired with the stamp of the capture each came from. A unit absent
            # from one month contributes no reading at that month's instant,
            # where a ladder would have closed the gap and moved every earlier
            # reading a month later than it was taken.
            values = [(stamps[position], value) for position, value
                      in _positioned(captures, entity, indicator)]
        try:
            session.add_observations(entity, indicator, values,
                                     interval_seconds=interval_seconds)
        except ValueError as refused:
            if type(refused) is not ValueError or \
                    not str(refused).startswith(f"{entity}.{indicator}: "):
                raise
            raise CaptureUnusable(str(refused)) from None
    return session


def ranking(api: Any, session: Any, entity_id: str) -> Mapping[str, Any]:
    """What could explain a finding on this unit, from the engine's own verb.

    The causes `hypothesize` ranks, each with its posterior, and every reason it
    declined, by name. Beside the finding rather than in the verdict: a ranking
    is where to look next, not a judgement about the organisation, so nothing
    here enters the exit code. A posterior of None beside no decline is printed
    as it arrived -- this package does not invent the missing word for it.
    """
    leg = api.hypothesize(session, entity_id).to_dict().get("hypothesis") or {}
    return {
        "causes": [[c.get("cause"), c.get("posterior")]
                   for c in leg.get("candidates") or ()],
        "declined": sorted({d.get("reason") for d in leg.get("not_checked") or ()
                            if d.get("reason")}),
    }


def run(model_path: str, captures: Sequence[Any], *,
        interval_seconds: float = 2_592_000.0) -> Mapping[str, Any]:
    """Feed a series and return the engine's envelope plus this package's score.

    `interval_seconds` defaults to thirty days, because an operating review
    reports monthly and the model's `window` is a CEILING on how far back
    observations count rather than a lookback. Declaring a cadence the exporter
    does not run at is how a burn-in silently never completes.
    """
    api = _engine()
    refusal = unusable(captures)
    if refusal:
        # The model is still read first, so a broken one is reported as broken
        # rather than as an unusable series.
        _loaded(model_path)
        return {"exit_code": x.INCOMPLETE, "findings": [], "not_checked": [],
                "engine": None, "could_not_run": refusal}

    try:
        session = open_session(model_path, captures, interval_seconds=interval_seconds)
    except CaptureUnusable as refused:     # a reading the engine refused, by name
        return {"exit_code": x.INCOMPLETE, "findings": [], "not_checked": [],
                "engine": None, "could_not_run": str(refused)}
    series = _series(captures)
    # JUDGED AS OF THE LATEST CAPTURE. A ladder ends at the clock, so its latest
    # reading is always "now"; a stamped series ends when it was taken, and read
    # at the wall clock its windows would slide away from it by however long ago
    # that was -- the same files judged differently on every day they were run.
    judged = _latest_stamp(captures)
    with api.as_of(judged) if judged is not None else nullcontext():
        envelope = api.check(session)
        payload = envelope.to_dict() if hasattr(envelope, "to_dict") else dict(envelope)
        rankings: dict[str, Mapping[str, Any]] = {}
        for finding in payload.get("findings", []):
            unit = finding.get("entity_id")
            if unit and unit not in rankings:
                rankings[unit] = ranking(api, session, unit)

    dropped = session.dropped_declarations()
    kinds = [f.get("type") or f.get("kind") or "unclassified"
             for f in payload.get("findings", [])]
    kinds += [d.get("reason") for d in payload.get("not_checked", []) if d.get("reason")]
    if dropped:
        kinds.append("model_not_read")

    # ONE RANKING PER UNIT, beside each of its findings. Asked once per unit
    # because the verb answers about the unit, whichever of its readings fired,
    # and asked above, inside the same clock the check was read at.
    findings = [{**finding, "ranking": rankings.get(finding.get("entity_id"))}
                for finding in payload.get("findings", [])]

    return {
        "exit_code": x.code_for(kinds),
        "captures_fed": len(captures),
        "series_fed": len(series),
        "timing": timing(captures, interval_seconds=interval_seconds),
        "findings": findings,
        "not_checked": payload.get("not_checked", []),
        "checked": payload.get("checked", {}),
        "engine": payload.get("meta", {}),
        "silence": {
            "dropped_declarations": dropped,
            "properties_no_indicator_reads": session.unread_properties(),
            "series_nothing_consumes": session.unconsumed_observations(),
        },
        "why": [{"kind": k, "floor": fl, "because": why} for k, fl, why in x.reasons(kinds)],
        "unclassified": list(x.unclassified(kinds)),
    }
