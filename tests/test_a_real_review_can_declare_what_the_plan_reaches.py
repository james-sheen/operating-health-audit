"""A real review can declare the gain and the budget instead of fitting them.

`docs/burn-in.md` says the plan reaches nothing on the shipped example, that a
declared reporting identity (`gain: 1`) makes every hiring round reach its
division, and that a declared budget makes a reach carry the division's warning
exactly where the round would break it. Measured on copies of the shipped model,
never the file itself, and every figure the document states is read off the run.
"""
from __future__ import annotations

import json

import yaml

from conftest import CAPTURE, MODEL, ROOT

BURN_IN = " ".join((ROOT / "docs" / "burn-in.md").read_text(encoding="utf-8").split())
WARNING = "imagined_threshold_warning:total_headcount"


def _export():
    from operating_health_audit import capture

    return capture.load(CAPTURE)


def _totals(export):
    return {point.name: point.values["total_headcount"] for point in export.points
            if point.unit_type == "Division"}


def _plan(tmp_path, gain="estimate", bound=None):
    from arbiter_engine import api
    from operating_health_audit import capture, feeder

    model = yaml.safe_load(MODEL.read_text())
    for rule in model["domain"]["relationship_rules"]:
        if rule.get("transition"):
            rule["transition"]["gain"] = gain
    if bound is not None:
        for spec in model["domain"]["indicators"]["Division"]:
            if spec["name"] == "total_headcount":
                spec["warning"] = bound
    path = tmp_path / "model.yaml"
    path.write_text(yaml.safe_dump(model))
    export = _export()
    session = feeder.open_session(str(path), [export])
    with api.as_of(capture.instant(export.captured_at)):
        api.check(session)
        return api.plan(session).to_dict()["plan"]["candidates"]


def test_as_shipped_no_candidate_reaches_anything(tmp_path):
    candidates = _plan(tmp_path)
    assert candidates and not [c for c in candidates if c["reaches"]]
    assert f"none of the {len(candidates)} candidates reaches anything" in BURN_IN


def test_a_declared_identity_makes_every_round_reach_a_division(tmp_path):
    candidates = _plan(tmp_path, gain=1.0)
    reaching = [c for c in candidates if c["reaches"]]
    assert [c["actions"] for c in candidates if not c["reaches"]] == [[]], (
        "a candidate that acts reached nothing, or doing nothing reached something")
    assert all(r["hops"] == 1 and r["entity"].startswith("div-") and not r["findings"]
               for c in reaching for r in c["reaches"])
    assert f"all {len(reaching)} but doing nothing reach a division one hop away" in BURN_IN


def test_a_declared_budget_warns_exactly_where_a_round_breaks_it(tmp_path):
    totals = _totals(_export())
    bound = totals["div-commercial"] + 10
    candidates = _plan(tmp_path, gain=1.0, bound=bound)
    reaches = [(c, r) for c in candidates for r in c["reaches"]]
    warned = [(c, r) for c, r in reaches
              if any(f["problem_type"] == WARNING for f in r["findings"])]
    assert warned and all(r["entity"] == "div-commercial" for _, r in warned)
    for candidate, _ in warned:
        added = sum(a["parameters"]["people"] for a in candidate["actions"]
                    if a["entity_id"] in ("dept-sales", "dept-marketing"))
        assert totals["div-commercial"] + added >= bound, json.dumps(candidate["actions"])
    assert totals["div-operations"] < bound
    stated = (f"{int(bound)}, against a commercial division of "
              f"{int(totals['div-commercial'])} -- {len(warned)} of the {len(reaches)} "
              f"reaches carry that division's warning")
    assert stated in BURN_IN, stated
    assert f"operations, at {int(totals['div-operations'])}" in BURN_IN


def test_the_shipped_model_declares_neither():
    model = yaml.safe_load(MODEL.read_text())
    [transition] = [r["transition"] for r in model["domain"]["relationship_rules"]
                    if r.get("transition")]
    assert transition["gain"] == "estimate"
    [spec] = [s for s in model["domain"]["indicators"]["Division"]
              if s["name"] == "total_headcount"]
    assert "warning" not in spec and "critical" not in spec
