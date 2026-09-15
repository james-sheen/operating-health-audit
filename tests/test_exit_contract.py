"""The floor table: complete over both upstreams, and never silent."""
from __future__ import annotations

import pytest

from operating_health_audit import exit_contract as x


def test_every_floor_states_a_reason() -> None:
    """A floor with no reason is a preference."""
    thin = [k for k, (_, why) in x.FLOORS.items() if len(why) < 20]
    assert thin == [], f"{thin} carry no stated reason"


def test_the_table_covers_every_regression_kind_the_core_can_raise() -> None:
    """Derived from the core rather than typed, so a new kind upstream shows up
    here as a red instead of falling quietly to the unclassified floor."""
    from presence_audit.diff import REGRESSION_KINDS

    assert REGRESSION_KINDS, "the core yielded no kinds; this check would pass over nothing"
    uncovered = sorted(set(REGRESSION_KINDS) - set(x.FLOORS) - _CANNOT_OCCUR)
    assert uncovered == [], f"no floor decided for {uncovered}"


#: Kinds the core can raise that this domain cannot produce, with why. Written
#: down rather than left out: an absent row and an impossible kind look identical.
_CANNOT_OCCUR = {
    "interface_divergence",              # belongs to a hardware walk
    "threshold_missing",                 # an operating export carries no per-unit
    "threshold_drift",                   # thresholds; the model declares them and
    "threshold_direction_conflict",      # the engine holds them
}


def test_the_exclusions_are_real_kinds_and_not_typos() -> None:
    """A misspelled exclusion silently widens the check above."""
    from presence_audit.diff import REGRESSION_KINDS

    stray = sorted(_CANNOT_OCCUR - set(REGRESSION_KINDS))
    assert stray == [], f"{stray} are excused and are not kinds the core raises"


def test_the_table_covers_the_engines_whole_decline_vocabulary() -> None:
    """The other upstream, derived the same way.

    `NotEvaluatedReason` is a closed enum. Six of a sibling package's twelve had
    no row once, and got the right answer for the wrong reason: anything unknown
    floors at 2, so nothing failed and nothing could -- while the run reported
    them as *unscorable* rather than as decided.
    """
    from arbiter_engine.types import NotEvaluatedReason

    vocabulary = {m.value for m in NotEvaluatedReason}
    assert len(vocabulary) >= 14, (
        f"the engine offered {len(vocabulary)} decline reasons, fewer than this "
        f"package was written against; deriving from a shrunken set would make "
        f"this check pass over almost nothing")
    uncovered = sorted(vocabulary - set(x.FLOORS))
    assert uncovered == [], f"the engine can decline with {uncovered} and this table has no row"


def test_exactly_these_engine_declines_are_clean_and_no_others() -> None:
    """Pinned as a SET rather than a count: a count survives one row being
    swapped for another, which is the edit worth catching."""
    from arbiter_engine.types import NotEvaluatedReason

    vocabulary = {m.value for m in NotEvaluatedReason}
    clean = sorted(r for r in vocabulary if x.FLOORS[r][0] == x.CLEAN)
    decided = {"insufficient_samples", "no_threshold", "not_applicable", "partially_checked"}
    assert clean == sorted(decided & vocabulary)


def test_composing_nothing_is_clean_here_and_incomplete_in_the_core() -> None:
    """Deliberately opposite. The core composes STAGE results, so no stage
    reporting means nothing ran. This composes FINDINGS, so no findings means the
    comparison ran and found none -- the answer the audit exists to give."""
    from presence_audit.exit_contract import compose

    assert x.code_for([]) == x.CLEAN
    assert compose() == x.INCOMPLETE


def test_a_kind_nobody_classified_is_never_clean() -> None:
    assert x.code_for(["a_kind_from_the_future"]) == x.INCOMPLETE
    assert x.unclassified(["a_kind_from_the_future", "detached_unit"]) == ("a_kind_from_the_future",)


def test_the_worst_kind_present_decides() -> None:
    mixed = ["state_changed", "detached_unit", "edge_moved"]
    assert x.code_for(mixed) == x.FINDINGS
    assert x.code_for(mixed + ["export_became_partial"]) == x.INCOMPLETE


@pytest.mark.parametrize("kind", ["edge_moved", "state_changed", "matched_inexactly"])
def test_the_reported_and_not_scored_rows_really_are_zero(kind) -> None:
    """A reorganisation is reported because a reader wants it, and is not a
    fault. If any of these ever floors above CLEAN, every reorganisation becomes
    a finding and the report stops being readable."""
    assert x.floor(kind) == x.CLEAN


def test_withholding_is_findings_and_two_only_when_asked() -> None:
    for kind in x.WITHHELD:
        assert x.floor(kind) == x.INCOMPLETE  # this one is already 2
        assert x.floor(kind, require_complete=True) == x.INCOMPLETE


def test_reasons_are_reported_for_what_was_actually_seen() -> None:
    out = dict((k, why) for k, _f, why in x.reasons(["detached_unit", "a_kind_from_the_future"]))
    assert "detached" in out["detached_unit"]
    assert "no row" in out["a_kind_from_the_future"]
