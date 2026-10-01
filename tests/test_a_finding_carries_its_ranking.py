"""`detect` prints, beside each finding, what could explain it.

The engine's `hypothesize` ranks the DECLARED causes of a finding on a unit;
this package asks it once per unit and puts the answer beside every finding
on that unit. It is where to look next, not a verdict: nothing in a ranking
enters the exit code, so a unit outside the declared causal structure is
reported as outside it and scored exactly as before.

Beside the causes, where the walk stopped: its state, the frontier where the
visible fault stops, and the causes still open with what each needs. The
reading to take first is named only while a cause is open.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "examples" / "operating.model.yaml"
CAPTURE = ROOT / "examples" / "acme.capture.json"

pytest.importorskip("arbiter_engine")


@pytest.fixture(scope="module")
def result():
    sys.path.insert(0, str(ROOT / "battery"))
    from operating_health_audit import capture, feeder
    import make_series

    return feeder.run(str(MODEL), make_series.series(capture.load(CAPTURE), 30,
                                                     transition=True))


@pytest.fixture(scope="module")
def shipped():
    """The shipped capture alone: one month, so some checks lack samples."""
    from operating_health_audit import capture, feeder

    return feeder.run(str(MODEL), [capture.load(CAPTURE)])


def _by_unit(result):
    return {f["entity_id"]: f["ranking"] for f in result["findings"]}


def test_every_finding_carries_a_ranking(result):
    assert result["findings"]
    assert all(isinstance(f.get("ranking"), dict) for f in result["findings"])


def test_a_department_is_explained_by_the_executives_who_lead_it(result):
    """The model declares `leads` causal, executive to department."""
    ranking = _by_unit(result)["dept-sales"]
    assert {cause for cause, _ in ranking["causes"]} == {"exec-cro", "exec-vp-sales"}


def test_a_unit_outside_the_declared_structure_says_so_by_name(result):
    ranking = _by_unit(result)["proc-sales-cycle"]
    assert ranking == {"causes": [], "own_readings": {}, "most_discriminating": None,
                       "declined": ["not_identifiable"],
                       "walk": {"state": "cut", "frontier": [], "open": []}}


def test_each_cause_carries_what_its_own_reading_said(result):
    """The engine computes each candidate's own reading, and this package
    printed the causes without it (FINDINGS F16): `exec-cro` leads the sales
    department with 22 direct reports over a critical 20, and the ranking said
    `None` beside it and named a different reading to take first."""
    ranking = _by_unit(result)["dept-sales"]
    assert set(ranking["own_readings"]) == {cause for cause, _ in ranking["causes"]}
    assert ranking["own_readings"]["exec-cro"] == {"state": "faulty",
                                                   "severity": "critical"}


def test_a_traced_unit_says_where_the_fault_stops_and_names_no_reading(result):
    """Both executives leading sales read over their bound: the walk is traced
    to them, and there is no reading left to take (FINDINGS F18). Engine 0.2.26
    named the CRO's tenure here, a reading already taken."""
    ranking = _by_unit(result)["dept-sales"]
    assert ranking["walk"]["state"] == "traced"
    assert [f["entity"] for f in ranking["walk"]["frontier"]] == ["exec-cro",
                                                                  "exec-vp-sales"]
    assert all(f["findings"] for f in ranking["walk"]["frontier"])
    assert ranking["walk"]["open"] == []
    assert ranking["most_discriminating"] is None


def test_the_reading_to_take_first_is_an_open_causes_need(shipped):
    """The engine names the one reading its ranking rests on most. This package
    kept the causes and dropped it (FINDINGS F15). On one capture the marketing
    executive's rating lacks samples, so the division's walk is partly traced
    and that rating is the reading it still needs -- a value a person can read,
    never a relation."""
    ranking = _by_unit(shipped)["div-commercial"]
    assert ranking["walk"]["state"] == "partly_traced"
    assert [entry["entity"] for entry in ranking["walk"]["open"]] == ["exec-cmo"]
    assert ranking["most_discriminating"] == {
        "entity": "exec-cmo", "reading": "exec-cmo.performance_rating",
        "basis": "only_open"}


def test_every_finding_on_one_unit_carries_the_same_ranking(result):
    seen = {}
    for finding in result["findings"]:
        seen.setdefault(finding["entity_id"], finding["ranking"])
        assert finding["ranking"] == seen[finding["entity_id"]]


def test_a_ranking_never_enters_the_verdict(result):
    """A decline about the ranking is advice about where to look, and would
    otherwise floor the run at could-not-complete as a kind with no row."""
    scored = {row["kind"] for row in result["why"]} | set(result["unclassified"])
    declined = {r for f in result["findings"] for r in f["ranking"]["declined"]}
    assert declined, "nothing declined, so this check would pass over nothing"
    assert not declined & scored
