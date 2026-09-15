"""What this package's exit code means, and which finding decides it.

CLEAN is 0, FINDINGS is 1, INCOMPLETE is 2. A kind with no row floors at
INCOMPLETE, never at CLEAN: a run that met something it has no opinion about has
not audited it, and reporting that as clean is the failure this table exists to
prevent.

THE TABLE IS DERIVED FROM ITS UPSTREAMS AND NOT TRANSCRIBED. The core's
regression kinds and the engine's decline reasons both arrive by import, and a
test asserts every member of both has a row. A floor table that agrees with an
upstream on the day it was written and silently stops is the shape that let six
of the engine's twelve declines fall to `unclassified` in a sibling package --
the right answer, for the wrong reason, reported as *unscorable* rather than as
decided.
"""

from __future__ import annotations

from typing import Iterable, Mapping, Sequence

CLEAN, FINDINGS, INCOMPLETE = 0, 1, 2

#: kind -> (floor, why). The why is not decoration: a floor with no stated
#: reason is a preference, and this table is where the decision is recorded.
FLOORS: Mapping[str, tuple[int, str]] = {
    # --- the core's own regression kinds ---------------------------------
    "declared_absent": (FINDINGS,
        "a unit the operating model declares is not in the export; this is the "
        "finding the audit exists to produce"),
    "declared_disabled": (FINDINGS,
        "declared and reported as not operating, which is a decision somebody "
        "made and the model has not caught up with"),
    "declared_unreadable": (FINDINGS,
        "present and reporting nothing at all, so no quantity about it can be "
        "judged and its absence from every later check is silent"),

    # --- kinds only this domain raises -----------------------------------
    "detached_unit": (FINDINGS,
        "present and reporting and structurally detached; either dissolved or "
        "mis-exported, and the export cannot say which"),
    "edge_lost": (FINDINGS,
        "a reporting line that existed in the earlier export is gone, so the "
        "unit now reports into nothing by that relation"),
    "indicator_stopped_reporting": (FINDINGS,
        "the unit is still present and has stopped reporting a quantity, which "
        "is a gap in the export rather than in the organisation"),
    "export_became_partial": (INCOMPLETE,
        "the later export is not complete, so every absence in it is "
        "unattributable between the organisation and the exporter"),

    # --- reported, and deliberately not scored ---------------------------
    "edge_moved": (CLEAN,
        "a unit moved under a different parent. That is a reorganisation, which "
        "is reported because a reader wants it and is not a fault"),
    "state_changed": (CLEAN,
        "a state moved, in either direction. WHETHER a state is bad is the "
        "engine's judgement against the model's declared `bad:` set at Stage 2; "
        "deciding it here would put one rule in two places with nothing keeping "
        "them equal"),
    "undeclared_present": (FINDINGS,
        "a unit is reporting that the operating model never declared. For a "
        "hardware walk that is noise; for an operating model it is the shadow "
        "organisation, and it is the second finding a review is run to get"),
    "matched_inexactly": (CLEAN,
        "the declared and captured names differ in form and were paired anyway; "
        "reported so a reader can check the pairing, and not a defect"),
}

#: Engine declines floored CLEAN, and each is a decision rather than a default.
#: `insufficient_samples` is CLEAN because the burn-in is this domain's DECLARED
#: state, not a failure -- see `docs/burn-in.md` for the arithmetic. Flooring it
#: at 2 would make every run exit 2 until the thirtieth capture, which is a
#: verdict about the calendar rather than about the organisation.
_ENGINE_CLEAN = ("insufficient_samples", "no_threshold", "not_applicable",
                 "partially_checked")

#: Everything else the engine can decline with means the model and the data
#: disagree -- a property the model names and the export does not carry, a role
#: nobody declared, an entity type with no indicators. Each is a defect in the
#: setup and none of them is an answer about the organisation.
_ENGINE_INCOMPLETE = (
    "checker_error", "missing_config", "missing_entity_type", "missing_property",
    "missing_role", "no_current_value", "no_rule_for_role", "precondition_unmet",
    "undefined_for_values", "wrong_indicator_type")

for _reason in _ENGINE_CLEAN:
    FLOORS[_reason] = (CLEAN, "the engine declined for a reason this package "
                              "decided is a declared gap rather than an unanswered question")
for _reason in _ENGINE_INCOMPLETE:
    FLOORS[_reason] = (INCOMPLETE, "the engine could not evaluate because the model and "
                                   "the export disagree; that is a defect in the setup")

#: The engine loaded a model and read nothing from it. Not a decline -- there is
#: no envelope to carry one -- and the reason it has its own row: a model whose
#: declarations are all dropped judges nothing, and judging nothing composes
#: CLEAN unless something says otherwise.
FLOORS["model_not_read"] = (INCOMPLETE,
    "the engine dropped every declaration in the model, so the run judged "
    "nothing and a clean verdict would be about an empty question")

#: Kinds that are findings normally and could-not-complete when the caller asked
#: for a complete answer.
WITHHELD = ("export_became_partial",)


def floor(kind: str, *, require_complete: bool = False) -> int:
    known = FLOORS.get(kind)
    if known is None:
        return INCOMPLETE
    if require_complete and kind in WITHHELD:
        return INCOMPLETE
    return known[0]


def unclassified(kinds: Iterable[str]) -> tuple[str, ...]:
    """The kinds this table has never heard of, in order. Reported by name: *no
    row for this* is a different sentence from *this was judged and was bad*."""
    return tuple(k for k in dict.fromkeys(kinds) if k not in FLOORS)


def code_for(kinds: Iterable[str], *, require_complete: bool = False) -> int:
    """The worst floor present decides.

    Composing NOTHING is CLEAN here and INCOMPLETE in the core, and the
    difference is deliberate: the core composes stage results, so no stage
    reporting means nothing ran. This composes FINDINGS, so no findings means the
    comparison ran and found none -- which is the answer the audit exists to be
    able to give.
    """
    return max((floor(k, require_complete=require_complete) for k in kinds),
               default=CLEAN)


def reasons(kinds: Iterable[str]) -> Sequence[tuple[str, int, str]]:
    """Every kind actually seen, with its floor and the stated reason."""
    out = []
    for kind in dict.fromkeys(kinds):
        row = FLOORS.get(kind)
        out.append((kind, INCOMPLETE, "no row in this package's floor table, so "
                                      "this run could not be scored")
                   if row is None else (kind, row[0], row[1]))
    return tuple(out)
