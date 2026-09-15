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
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from . import exit_contract as x
from .vertical import REQUIRED_EDGE, OperatingVocabulary


class EngineUnavailable(RuntimeError):
    """The detect extra is not installed. Distinct from the engine running and
    declining, which is an answer."""


class ModelUnreadable(ValueError):
    """The model file is not one the engine could load."""


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


def _add_state_series(session: Any, entity: str, indicator: str,
                      values: Sequence[Any], interval_seconds: float) -> None:
    """Feed a STATE series, which the session's own feeder cannot.

    MEASURED against arbiter-engine 0.1.14. `EngineSession.add_observations`
    casts every sample with `float(value)`, so a state raises ValueError -- while
    `InMemoryObservationHistory.add` takes `value: Any` and accepts one, the
    engine declares a `state` indicator type, and STABILITY reads state history
    out of exactly that store. A consumer following the front door can satisfy
    the numeric axioms and not the state half of STABILITY.

    This writes to `session.history` directly, which is public and is how the
    engine's own docstrings describe reaching an input kind whose feeder is
    missing. Filed upstream as james-sheen/arbiter#14 rather than left as a
    local trick; when a state feeder lands, this function goes and the call
    above becomes unconditional.
    """
    from datetime import timedelta

    from arbiter_engine.api import now_utc

    now = now_utc()
    count = len(values)
    for i, value in enumerate(values):
        session.history.add(entity, indicator, value,
                            now - timedelta(seconds=(count - i) * interval_seconds))


def run(model_path: str, captures: Sequence[Any], *,
        interval_seconds: float = 2_592_000.0) -> Mapping[str, Any]:
    """Feed a series and return the engine's envelope plus this package's score.

    `interval_seconds` defaults to thirty days, because an operating review
    reports monthly and the model's `window` is a CEILING on how far back
    observations count rather than a lookback. Declaring a cadence the exporter
    does not run at is how a burn-in silently never completes.
    """
    api = _engine()
    session = api.EngineSession()
    try:
        session.load_model(model_path)
    except Exception as problem:            # yaml errors are not ValueError
        raise ModelUnreadable(f"{model_path} could not be loaded as a domain model: "
                              f"{type(problem).__name__}: {problem}") from None

    if not captures:
        return {"exit_code": x.INCOMPLETE, "findings": [], "not_checked": [],
                "engine": None,
                "could_not_run": "no captures were supplied, and an empty series "
                                 "reports the same as a complete one about an "
                                 "organisation that never changed"}

    latest = captures[-1]
    series: dict[tuple[str, str], list[Any]] = {}
    for export in captures:
        for point in getattr(export, "points", ()) or ():
            for name, value in _fed(point).items():
                series.setdefault((point.name, name), []).append(value)

    for point in getattr(latest, "points", ()) or ():
        session.add_entity(point.name, point.unit_type,
                           properties=_fed(point), name=point.name)
    # CONNECTIVITY reads relationships and nothing else, so an edge that never
    # reaches this call is an edge the engine cannot see however well declared.
    for point in getattr(latest, "points", ()) or ():
        for relation, target in (getattr(point, "edges", {}) or {}).items():
            session.add_relationship(point.name, relation, target)

    for (entity, indicator), values in series.items():
        if all(isinstance(v, (int, float)) for v in values):
            session.add_observations(entity, indicator, values,
                                     interval_seconds=interval_seconds)
        else:
            _add_state_series(session, entity, indicator, values, interval_seconds)

    envelope = api.check(session)
    payload = envelope.to_dict() if hasattr(envelope, "to_dict") else dict(envelope)

    dropped = session.dropped_declarations()
    kinds = [f.get("type") or f.get("kind") or "unclassified"
             for f in payload.get("findings", [])]
    kinds += [d.get("reason") for d in payload.get("not_checked", []) if d.get("reason")]
    if dropped:
        kinds.append("model_not_read")

    return {
        "exit_code": x.code_for(kinds),
        "captures_fed": len(captures),
        "series_fed": len(series),
        "findings": payload.get("findings", []),
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
