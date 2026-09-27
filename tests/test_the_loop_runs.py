"""The problem-solving loop, run in this domain.

Every stage the engine offers either answers or declines by a name the engine
publishes -- never an exception, never silence. This is one half of a two-domain
test; `bmc-sensor-audit` carries the other, on a domain that shares no noun with
this one. The question both halves answer is about the ENGINE: did running the
loop here need anything it does not offer every domain?

Each stage is asked of the session this package's own feeder builds, with
nothing added for the test, so what passes here is what `detect` meets. The
series is thirty monthly captures -- enough for every arm of the model to answer
-- from the shipped fixture, whose numbers are invented and say so.

The model declares what each stage reads: which way a failure travels
(`hypothesize`), one lever an operator can pull and the rounds a plan may
choose between (`file_action`, `plan`), one coupling with its number withheld
(`learn`), and when a case closes (`open_case`). The coupling cannot be fitted
from a real monthly series for ten years, so on this series `learn` declines by
name, and a labelled-synthetic series of 121 captures shows the fit itself.

Every decline is read by the engine's own walker, from every list the engine
reports one under, and checked against the names it publishes. This file used
to carry its own copy of that walk, reading two of those lists; the copy in the
other domain read four. A refusal from the learn leg arrives under the one this
copy did not read, so the check would have passed over exactly the stage this
file now exercises. A decline outside the published names is one no reader could
switch on.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from arbiter_engine import api
from arbiter_engine.subenvelope import (PUBLISHED_REASONS, declined_reasons,
                                        unpublished_reasons)

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "examples" / "operating.model.yaml"
CAPTURE = ROOT / "examples" / "acme.capture.json"

#: A reporting month, the cadence the feeder assumes, and a fixed instant for
#: the stages that file something and grade it later.
MONTH = timedelta(days=30)
AT = datetime(2026, 9, 1)

#: A department the model declares a causal parent for -- two executives lead it
#: -- and that the series finds a breach on.
LED = "dept-sales"
LEADERS = {"exec-cro", "exec-vp-sales"}


def _series():
    sys.path.insert(0, str(ROOT / "battery"))
    from operating_health_audit import capture
    import make_series

    return make_series.series(capture.load(CAPTURE), 30, transition=True)


def _fresh(at=AT):
    """A session of its own, fed as of `at`, for a stage that files something."""
    from operating_health_audit import feeder

    with api.as_of(at):
        return feeder.open_session(str(MODEL), _series())


@pytest.fixture(scope="module")
def session():
    from operating_health_audit import feeder

    return feeder.open_session(str(MODEL), _series())


@pytest.fixture(scope="module")
def sensed(session):
    return api.check(session).to_dict()


class TestEveryStageAnswersOrDeclinesByName:

    def test_sense(self, sensed):
        assert sensed["findings"], "a thirty-capture series of this fixture finds nothing"
        assert unpublished_reasons(sensed) == []

    def test_model(self, session):
        described = api.model_describe(session).to_dict()
        assert described["model"]["axiom_parameters"]["homeostasis_baseline_days"] == {
            "value": 3650, "source": "declared"}
        assert unpublished_reasons(described) == []

    def test_hypothesize(self, session, sensed):
        """The declared direction reaches the ranking: a breach on a department
        is explained by the executives who lead it, and by nothing undeclared.
        With no strength declared, no candidate carries a posterior."""
        assert LED in {f["entity_id"] for f in sensed["findings"]}
        payload = api.hypothesize(session, LED).to_dict()
        candidates = payload["hypothesis"]["candidates"]
        assert {c["cause"] for c in candidates} == LEADERS
        assert all(c["posterior"] is None for c in candidates)
        assert unpublished_reasons(payload) == []

    def test_the_missing_strength_is_named(self, session):
        """`cpt_missing` is the true answer while nobody has a strength to give,
        and the inference the ranking rests on says so by name."""
        payload = api.infer(session, LED).to_dict()
        assert "cpt_missing" in declined_reasons(payload)
        assert unpublished_reasons(payload) == []

    def test_the_ranking_says_why_it_has_no_number(self, session):
        """F10: the ranking carries the decline its inferences made, and each
        cause names its own. It was a strict xfail until the engine did."""
        payload = api.hypothesize(session, LED).to_dict()
        assert "cpt_missing" in declined_reasons(payload)
        assert all(c["declined"] == ["cpt_missing"]
                   for c in payload["hypothesis"]["candidates"])

    def test_plan(self, session):
        """The model declares an objective and the hiring rounds a plan may
        choose between, so the plan ranks them. The rounds do not tie: a hire
        is scored by how far it moves a department from its own HOMEOSTASIS
        baseline, which is what the objective reads. And it declares how far a
        plan looks -- two rounds at once -- so the plan searches pairs, where it
        used to stop at one round under a stamp saying nobody had chosen."""
        payload = api.plan(session).to_dict()
        leg = payload["plan"]
        assert leg["ranked"] and leg["best"]
        assert "no_objective" not in declined_reasons(payload)
        assert len({c["objective"] for c in leg["candidates"]}) > 1, (
            "every round scored the same; the lever moves nothing the objective reads")
        assert any(f.startswith("imagined_homeostasis") and f.endswith(":headcount")
                   for c in leg["candidates"] for f in c["findings"])
        assert leg["checked"]["max_depth"] == 2
        assert "search_depth_not_declared" not in leg["assumptions"]
        assert any(len(c["actions"]) == 2 for c in leg["candidates"]), (
            "the model declares a depth of two and no pair of rounds was rolled out")
        assert unpublished_reasons(payload) == []

    def test_learn(self, session):
        """One coupling is declared, with its gain withheld, and thirty monthly
        captures are twenty-nine changes: far below the 120 the engine fits a
        gain from. So every edge it runs along declines `insufficient_samples`
        by name, under `not_fitted` -- a list the copy this file used to carry
        never read."""
        proposed = api.model_describe(session).to_dict()["model"]["proposed_transitions"]
        assert proposed["fitted"] == []
        assert proposed["checked"]["couplings_seen"] == len(DEPARTMENTS)
        assert set(declined_reasons(proposed)) == {"insufficient_samples"}
        assert unpublished_reasons(proposed) == []


#: The four departments, each reporting into a division along the edge the
#: model's one coupling runs on.
DEPARTMENTS = ("dept-sales", "dept-marketing", "dept-engineering", "dept-support")

#: Two waves of people moving, ORTHOGONAL and of mean zero over four months.
#: The two departments of a division get one each, so neither's movement can be
#: mistaken for the other's and the gain a fit should recover is exactly one.
WAVES = ((2, -2), (1, 1, -1, -1))


def _coupled(count):
    """A LABELLED-SYNTHETIC series, not an organisation's history.

    The shipped capture held still, except that each department's headcount
    moves by one of two fixed waves every month and its division's total moves
    by the same people. Built so the one coupling the model declares has an
    answer known in advance -- a department's hire adds exactly one to its
    division's total -- and so nothing else in it is evidence of anything.
    """
    from operating_health_audit import capture

    baseline = capture.load(CAPTURE)
    parent = {p.name: p.edges.get("reports_to") for p in baseline.points
              if p.unit_type == "Department"}
    wave = {d: WAVES[i % 2]
            for division in sorted(set(parent.values()))
            for i, d in enumerate(sorted(n for n in parent if parent[n] == division))}

    def moved(unit, month):
        return sum(wave[unit][j % len(wave[unit])] for j in range(month))

    series = []
    for month in range(count):
        points = []
        for point in baseline.points:
            values = dict(point.values)
            if point.name in parent:
                values["headcount"] = point.values["headcount"] + moved(point.name, month)
            elif point.unit_type == "Division":
                values["total_headcount"] = point.values["total_headcount"] + sum(
                    moved(d, month) for d, division in parent.items()
                    if division == point.name)
            points.append(capture.Reading(
                name=point.name, unit_type=point.unit_type, path=point.path,
                values=values, state=point.state, edges=dict(point.edges)))
        series.append(capture.Export(points=tuple(points), complete=True,
                                     source=f"synthetic, month {month}"))
    return series


def _proposed(series):
    from operating_health_audit import feeder

    session = feeder.open_session(str(MODEL), series)
    return api.model_describe(session).to_dict()["model"]["proposed_transitions"]


class TestTheCouplingIsFittedOnlyFromEnoughChanges:
    """The learn stage's mechanism, shown on a series built for it. The floor is
    the engine's -- 120 paired changes -- and at a monthly cadence that is ten
    years, so a real series here would decline for that long."""

    def test_one_capture_short_of_the_floor_declines_by_name(self):
        proposed = _proposed(_coupled(120))
        assert proposed["fitted"] == []
        assert set(declined_reasons(proposed)) == {"insufficient_samples"}

    def test_at_the_floor_every_edge_is_fitted_and_nothing_is_written(self):
        before = MODEL.read_bytes()
        proposed = _proposed(_coupled(121))
        assert MODEL.read_bytes() == before, "a proposal was written into the model"
        assert declined_reasons(proposed) == []
        fitted = {f["edge"].split("->")[0]: f for f in proposed["fitted"]}
        assert sorted(fitted) == sorted(DEPARTMENTS)
        for proposal in fitted.values():
            low, high = proposal["interval"]
            assert proposal["n"] == 120
            assert proposal["gain"] == pytest.approx(1.0)
            assert low < 1.0 < high
            assert proposal["response_model"] == "step"
            # No record of what happened to replay against: a refusal carrying
            # its reason, never a zero.
            assert proposal["replay"]["status"] == "replay_unavailable"


def _hire(session, people=10):
    with api.as_of(AT):
        return api.file_action(
            session, {"template": "add_headcount", "entity_id": LED,
                      "parameters": {"people": people}},
            AT, "a hiring plan approved at the September review",
            horizon_s=MONTH.total_seconds(), step_s=MONTH.total_seconds()).to_dict()


class TestAnActionIsFiledAndGradedAgainstTheNextCapture:

    @pytest.mark.parametrize("added, action, no_action", [
        (10, (1, 0), (0, 1)),     # the next capture shows the ten people
        (0, (0, 1), (1, 0)),      # it shows nobody arrived
    ])
    def test_the_next_capture_picks_an_arm(self, added, action, no_action):
        session = _fresh()
        before = session.entities[LED].properties["headcount"]
        payload = _hire(session)
        assert payload["execution"]["checked"]["pairs_filed"] == 1
        assert unpublished_reasons(payload) == []

        later = AT + MONTH
        with api.as_of(later):
            session.add_observations(LED, "headcount", [(later, before + added)])
        with api.as_of(later + timedelta(seconds=session.ledger.grace_s + 1)):
            api.check(session)
        arms = session.ledger.calibration()["executions"]["arms"]
        assert (arms["action"]["confirmed"], arms["action"]["falsified"]) == action
        assert (arms["no_action"]["confirmed"], arms["no_action"]["falsified"]) == no_action


class TestACaseOpensOnAFindingAndResolves:

    SUBJECT = ("proc-sales-cycle", "error_rate_pct")

    def test_two_clean_captures_close_it(self):
        session = _fresh()
        unit, indicator = self.SUBJECT
        with api.as_of(AT):
            api.check(session)
            opened = api.open_case(session, unit, indicator,
                                   basis="a critical error rate at the September review")
            api.check(session)
        payload = opened.to_dict()
        assert unpublished_reasons(payload) == []
        case_id = payload["case"]["case_id"]
        assert (payload["case"]["severity"], payload["case"]["consecutive_checks"]) == (
            "warning", 2)
        for month in (1, 2):
            when = AT + month * MONTH
            with api.as_of(when):
                session.entities[unit].properties[indicator] = 2.0
                session.add_observations(unit, indicator, [(when, 2.0)])
                api.check(session)
        case = session.ledger.case_book.get(case_id)
        assert [e["outcome"] for e in case.stages["check"]] == ["found", "clean", "clean"]
        assert case.status == "resolved"
        book = api.case_book(session).to_dict()["cases"]
        assert (book["opened"], book["resolved"]) == (1, 1)


def _planned(tmp_path, **planning):
    """`plan` over the loop's own series, on a copy of the model whose planning
    block is changed by `planning` -- the shipped file is never written."""
    import yaml
    from operating_health_audit import feeder

    model = yaml.safe_load(MODEL.read_text())
    model["domain"]["planning"].update(planning)
    path = tmp_path / "planned.model.yaml"
    path.write_text(yaml.safe_dump(model, sort_keys=False))
    return api.plan(feeder.open_session(str(path), _series())).to_dict()


class TestTheSearchStopsAtItsBudgetAndSaysSo:
    """`max_rollouts` is a stop, and a stop that cut a search short has to say
    so, with the count of what it left out: a plan chosen from part of the
    field reads exactly like one chosen from all of it. The declared search
    fits inside the default budget, so the shipped model shows only one side of
    that. A copy with the budget set below the field shows the other."""

    def test_the_declared_search_is_rolled_out_whole(self, session):
        payload = api.plan(session).to_dict()
        assert payload["plan"]["checked"]["plans_untested"] == 0
        assert "budget_exhausted" not in declined_reasons(payload)

    def test_a_budget_below_the_field_is_declined_with_its_count(self, session,
                                                                 tmp_path):
        field = api.plan(session).to_dict()["plan"]["checked"]["candidates_evaluated"]
        short = _planned(tmp_path, max_rollouts=field - 4)
        assert "budget_exhausted" in declined_reasons(short)
        assert short["plan"]["checked"]["plans_untested"] == 4
        assert unpublished_reasons(short) == []


def test_the_stage_report_matches_what_the_run_did(session):
    """`model_describe` says, per stage, whether the model declares what that
    stage reads -- and each claim is checked against what the stage then did."""
    stages = {name: row["declared"] for name, row in
              api.model_describe(session).to_dict()["model"]["stages"].items()}
    assert stages == {"check": True, "hypothesize": True, "plan": True,
                      "act": True, "learn": True, "case": True}
    assert api.hypothesize(session, LED).to_dict()["hypothesis"]["candidates"]
    assert api.plan(session).to_dict()["plan"]["ranked"]
    assert _hire(_fresh())["execution"]["checked"]["pairs_filed"] == 1
    learned = api.model_describe(session).to_dict()["model"]["proposed_transitions"]
    assert not learned["fitted"] and "insufficient_samples" in declined_reasons(learned)
    assert "case_id" in api.open_case(_fresh(), "proc-sales-cycle",
                                      "error_rate_pct").to_dict()["case"]


def test_the_vocabularies_are_not_empty():
    """Before believing a negative, prove the probe can produce one."""
    assert "insufficient_samples" in PUBLISHED_REASONS
    assert "no_objective" in PUBLISHED_REASONS
    assert unpublished_reasons({"not_checked": [{"reason": "made_up_here"}]}) == [
        "made_up_here"]


def test_a_refusal_the_learn_leg_names_wrongly_is_caught(session):
    """The incident the shared walker exists for. The learn leg's real answer,
    with one unpublished reason put into `not_fitted`: the walk this file used
    to carry read only `not_checked` and `declines`, and would pass it."""
    proposed = api.model_describe(session).to_dict()["model"]["proposed_transitions"]
    doctored = dict(proposed, not_fitted=list(proposed["not_fitted"]) + [
        {"edge": "dept-sales->div-commercial", "reason": "made_up_here"}])
    assert unpublished_reasons(doctored) == ["made_up_here"]

    def two_lists(node):
        if isinstance(node, dict):
            return [item.get("reason") for key, value in node.items()
                    if key in ("not_checked", "declines") and isinstance(value, list)
                    for item in value if isinstance(item, dict)] + [
                reason for value in node.values() for reason in two_lists(value)]
        if isinstance(node, list):
            return [reason for item in node for reason in two_lists(item)]
        return []

    assert "made_up_here" not in two_lists(doctored)
