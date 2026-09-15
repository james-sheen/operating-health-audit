"""The Acme operating review, end to end.

This package exists because a domain-free core and an engine were tested against
a consulting case study that no vertical could run. These are the assertions that
say it runs now, and they are about the OUTCOME rather than the mechanism: the
units the review should flag, by name.
"""
from __future__ import annotations

import pytest

from conftest import AS_SHIPPED, CAPTURE, MODEL


def test_the_export_as_shipped_has_no_structure_and_every_unit_is_detached(declaration) -> None:
    """The first true thing about the case study: its CSV carries no
    relationships at all. Fourteen units, fourteen detached. An audit that
    reported this as clean would be agreeing with an export that says nothing
    about the organisation's shape."""
    from operating_health_audit import capture, presence

    out = presence.run(declaration, capture.load(AS_SHIPPED))
    detached = [f for f in out["findings"] if f["kind"] == "detached_unit"]
    assert len(detached) == 14
    assert out["exit_code"] == 1


def test_with_the_structure_supplied_the_presence_audit_is_clean(declaration, export) -> None:
    from operating_health_audit import presence

    out = presence.run(declaration, export)
    assert out["findings"] == [], out["findings"]
    assert out["exit_code"] == 0
    assert out["structure"]["edges_by_relation"] == {
        "depends_on": 2, "funds": 3, "leads": 3, "reports_to": 6}


def test_units_that_report_no_state_are_not_reported_as_silent(declaration, export) -> None:
    """THE BUG THIS PACKAGE SHIPPED FIRST, pinned.

    A wide export carries a status column for some unit types and not others.
    Reading a unit's state as its ONLY reading made three Executives and two
    Processes -- every one of them reporting a tenure, a span, a rating, a cycle
    time -- come back `declared_unreadable`. Five units reporting, five reported
    silent, and the presence run looked like a real finding.
    """
    from operating_health_audit import presence

    quiet = [p for p in export.points if p.state is None]
    assert len(quiet) == 5, "the fixture no longer has the units that caused this"
    assert all(p.values for p in quiet), "these units report quantities"
    assert all(p.is_reading for p in quiet)
    out = presence.run(declaration, export)
    assert [f for f in out["findings"] if f["kind"] == "declared_unreadable"] == []


def test_the_engine_finds_the_eleven_the_review_is_run_to_find(export) -> None:
    """MEASURED, from ONE capture.

    The floors in `types.AXIOM_MINIMUMS` do not mean no axiom can answer from a
    snapshot -- BOUNDEDNESS evaluates a declared bound against the CURRENT value,
    and the floor governs the arm that needs a history. Asserted by entity and
    problem so a model edit that silently stops checking turnover fails here.

    ELEVEN, and it was SEVEN until the feeder fed state. `add_observations`
    casts every sample to float, so the four units sitting in a state the model
    declares `bad:` were invisible: the axiom ran, the history held no state,
    and the run was clean about the four worst units in the organisation.
    """
    from operating_health_audit import feeder

    out = feeder.run(str(MODEL), [export])
    got = {(f["entity_id"], f["problem_type"]) for f in out["findings"]}
    assert got == {
        ("div-commercial", "declared_bad_state:status"),
        ("dept-sales", "declared_bad_state:status"),
        ("dept-support", "declared_bad_state:status"),
        ("proj-expansion", "declared_bad_state:status"),
        ("dept-sales", "threshold_exceeded:turnover_pct"),
        ("dept-support", "threshold_exceeded:turnover_pct"),
        ("dept-marketing", "threshold_warning:turnover_pct"),
        ("exec-cro", "threshold_exceeded:direct_reports"),
        ("exec-vp-sales", "threshold_warning:direct_reports"),
        ("proc-onboarding", "threshold_exceeded:error_rate_pct"),
        ("proc-sales-cycle", "threshold_warning:error_rate_pct"),
    }
    assert out["checked"]["invariants"] > 100, (
        "the engine checked almost nothing, and a small findings list from a "
        "small check is not the same claim")


def test_the_engine_read_every_declaration_in_the_model(export) -> None:
    """The silence gate. A model whose declarations are all dropped judges
    nothing, and judging nothing composes clean unless somebody asks."""
    from operating_health_audit import feeder

    out = feeder.run(str(MODEL), [export])
    assert out["silence"]["dropped_declarations"] == []
    assert out["silence"]["series_nothing_consumes"] == []


def test_a_snapshot_declines_the_history_arms_rather_than_passing_them(export) -> None:
    """The burn-in, asserted as a DECLINE rather than assumed. One capture
    cannot answer HOMEOSTASIS or STABILITY, and the honest report of that is a
    decline with a reason -- not silence, and not a pass."""
    from operating_health_audit import feeder

    out = feeder.run(str(MODEL), [export])
    reasons = {d.get("reason") for d in out["not_checked"]}
    assert "insufficient_samples" in reasons
    assert any(d.get("reason") == "insufficient_samples" for d in out["not_checked"])


def test_an_empty_series_cannot_report_a_clean_organisation() -> None:
    """*Every unit passed* is true of no units."""
    from operating_health_audit import feeder

    out = feeder.run(str(MODEL), [])
    assert out["exit_code"] == 2
    assert "no captures" in out["could_not_run"]


def test_a_model_the_engine_cannot_load_is_two_and_not_a_traceback(tmp_path) -> None:
    """`yaml.YAMLError` is not a `ValueError`. Unwrapped it escapes as a
    traceback exiting 1, which this package's contract reads as FINDINGS -- a
    broken model reported as a bad organisation."""
    from operating_health_audit import feeder

    bad = tmp_path / "bad.yaml"
    bad.write_text("domain: [this is not: a mapping\n")
    with pytest.raises(feeder.ModelUnreadable):
        feeder.run(str(bad), [])


def test_a_genuinely_silent_executive_is_reported(declaration) -> None:
    """The other half of the reading fix, and the half the first test missed.

    Making `expects_reading` False for Executives also makes the earlier test
    pass -- a unit nothing expects a reading from cannot be reported as silent.
    That is the wrong fix for the right symptom: it would hide a real executive
    reporting nothing at all, which is exactly what an operating review is meant
    to surface. So this asserts the audit still CAN say it.
    """
    from operating_health_audit import capture, presence

    quiet = capture.Export(complete=True, captured_at="2026-09-15T00:00:00Z", points=tuple(
        capture.Reading(name=p.name, unit_type=p.unit_type, path=f"probe#{p.name}",
                        edges=dict(p.edges))
        if p.unit_type == "Executive" else
        capture.Reading(name=p.name, unit_type=p.unit_type, path=f"probe#{p.name}",
                        state="healthy", values={"headcount": 1.0}, edges=dict(p.edges))
        for p in declaration.points))
    out = presence.run(declaration, quiet)
    silent = {f["unit"] for f in out["findings"] if f["kind"] == "declared_unreadable"}
    executives = {p.display_name or p.name for p in declaration.points
                  if p.unit_type == "Executive"}
    assert silent == executives


def test_an_executive_that_vanishes_from_the_export_is_reported(declaration) -> None:
    """What `expects_reading` actually gates, measured rather than assumed.

    It was narrowed to exclude Executives at first, on a belief about which
    units report. Testing that through `declared_unreadable` proves nothing --
    a present-but-silent unit is reported either way. What the flag really
    filters is the UNMATCHED list: a declared point that expects no reading and
    is absent is dropped without a finding. So an executive who has left, and
    whose row is simply gone from the next export, would vanish silently -- in
    an audit whose whole subject is what the organisation declared and does not
    have.
    """
    from operating_health_audit import capture, presence

    gone = {p.name for p in declaration.points if p.unit_type == "Executive"}
    assert gone, "the fixture declares no executives"
    short = capture.Export(complete=True, captured_at="2026-09-15T00:00:00Z", points=tuple(
        capture.Reading(name=p.name, unit_type=p.unit_type, path=f"probe#{p.name}",
                        state="healthy", values={"headcount": 1.0}, edges=dict(p.edges))
        for p in declaration.points if p.name not in gone))
    out = presence.run(declaration, short)
    absent = {f["unit"] for f in out["findings"] if f["kind"] == "declared_absent"}
    expected = {p.display_name or p.name for p in declaration.points if p.name in gone}
    assert absent == expected, (
        "a declared executive missing from the export produced no finding; "
        "expects_reading has been narrowed and absences are being dropped")


def test_the_history_arms_need_the_declared_windows(export) -> None:
    """The burn-in, guarded. Nothing else in this suite feeds a SERIES, so the
    whole measured table in `docs/burn-in.md` rested on no test at all -- and
    deleting a `window:` from the model changed no result anywhere.

    The window is a CEILING defaulting to one hour. Undeclared, a monthly series
    is one observation however long it runs, and STABILITY never resolves.
    """
    import sys

    sys.path.insert(0, str(MODEL.parents[1] / "battery"))
    from make_series import series

    from operating_health_audit import feeder

    ten = series(export, 10)
    out = feeder.run(str(MODEL), ten)
    stab = [d for d in out["not_checked"]
            if d.get("axiom") == "STABILITY" and d.get("reason") == "insufficient_samples"]
    assert stab == [], (
        "STABILITY still declines at ten monthly captures; either a `window:` "
        "has gone from the model, or the series is not reaching the engine")
    assert len(out["findings"]) > len(feeder.run(str(MODEL), [export])["findings"]), (
        "ten captures found no more than one, so the series bought nothing")
