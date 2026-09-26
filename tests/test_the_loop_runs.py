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

The model declares what each stage reads, or declares on purpose that it does
not: which way a failure travels (`hypothesize`), one lever an operator can
pull (`file_action`), and when a case closes (`open_case`); no objective and no
coupling, so `plan` and `learn` decline or come back empty, by name.

The published names are read from where the engine keeps them: its top-level
decline enum and one closed vocabulary per discipline. Both are deeper than the
names the engine promises, and are imported anyway because the test's subject is
exactly that promise -- a decline outside those sets is one no reader could
switch on.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from arbiter_engine import api
from arbiter_engine.subenvelope import VOCABULARIES
from arbiter_engine.types import NotEvaluatedReason

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "examples" / "operating.model.yaml"
CAPTURE = ROOT / "examples" / "acme.capture.json"

PUBLISHED = {reason.value for reason in NotEvaluatedReason}.union(*VOCABULARIES.values())

#: A reporting month, the cadence the feeder assumes, and a fixed instant for
#: the stages that file something and grade it later.
MONTH = timedelta(days=30)
AT = datetime(2026, 9, 1)

#: A department the model declares a causal parent for -- two executives lead it
#: -- and that the series finds a breach on.
LED = "dept-sales"
LEADERS = {"exec-cro", "exec-vp-sales"}


def _reasons(payload) -> list:
    """Every decline reason anywhere in a payload, however deeply it is mounted."""
    found = []

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in ("not_checked", "declines") and isinstance(value, list):
                    found.extend(item.get("reason") for item in value
                                 if isinstance(item, dict))
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(payload)
    return found


def _unpublished(payload) -> list:
    return sorted({r for r in _reasons(payload) if r not in PUBLISHED})


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
        assert _unpublished(sensed) == []

    def test_model(self, session):
        described = api.model_describe(session).to_dict()
        assert described["model"]["axiom_parameters"]["homeostasis_baseline_days"] == {
            "value": 3650, "source": "declared"}
        assert _unpublished(described) == []

    def test_hypothesize(self, session, sensed):
        """The declared direction reaches the ranking: a breach on a department
        is explained by the executives who lead it, and by nothing undeclared.
        With no strength declared, no candidate carries a posterior."""
        assert LED in {f["entity_id"] for f in sensed["findings"]}
        payload = api.hypothesize(session, LED).to_dict()
        candidates = payload["hypothesis"]["candidates"]
        assert {c["cause"] for c in candidates} == LEADERS
        assert all(c["posterior"] is None for c in candidates)
        assert _unpublished(payload) == []

    def test_the_missing_strength_is_named(self, session):
        """`cpt_missing` is the true answer while nobody has a strength to give,
        and the inference the ranking rests on says so by name."""
        payload = api.infer(session, LED).to_dict()
        assert "cpt_missing" in _reasons(payload)
        assert _unpublished(payload) == []

    def test_the_ranking_says_why_it_has_no_number(self, session):
        """F10: the ranking carries the decline its inferences made, and each
        cause names its own. It was a strict xfail until the engine did."""
        payload = api.hypothesize(session, LED).to_dict()
        assert "cpt_missing" in _reasons(payload)
        assert all(c["declined"] == ["cpt_missing"]
                   for c in payload["hypothesis"]["candidates"])

    def test_plan(self, session):
        """The model declares one lever and no objective, and the lever names no
        candidate values -- so the honest answer is a named refusal, and a plan
        that declined nothing here would be claiming a search it had nothing to
        rank."""
        payload = api.plan(session).to_dict()
        reasons = _reasons(payload)
        assert {"no_objective", "no_candidates"} & set(reasons), reasons
        assert _unpublished(payload) == []

    def test_learn(self, session):
        """Nothing is coupled in this model, so there is no gain to propose; the
        leg is present and empty rather than absent."""
        proposed = api.model_describe(session).to_dict()["model"]["proposed_transitions"]
        assert isinstance(proposed, dict)
        assert _unpublished(proposed) == []


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
        assert _unpublished(payload) == []

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
        assert _unpublished(payload) == []
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


def test_the_stage_report_matches_what_the_run_did(session):
    """`model_describe` says, per stage, whether the model declares what that
    stage reads -- and each claim is checked against what the stage then did."""
    stages = {name: row["declared"] for name, row in
              api.model_describe(session).to_dict()["model"]["stages"].items()}
    assert stages == {"check": True, "hypothesize": True, "plan": False,
                      "act": True, "learn": False, "case": True}
    assert api.hypothesize(session, LED).to_dict()["hypothesis"]["candidates"]
    assert "no_objective" in _reasons(api.plan(session).to_dict())
    assert _hire(_fresh())["execution"]["checked"]["pairs_filed"] == 1
    assert not api.model_describe(session).to_dict()["model"]["proposed_transitions"].get(
        "fitted")
    assert "case_id" in api.open_case(_fresh(), "proc-sales-cycle",
                                      "error_rate_pct").to_dict()["case"]


def test_the_vocabularies_are_not_empty():
    """Before believing a negative, prove the probe can produce one."""
    assert "insufficient_samples" in PUBLISHED and "no_objective" in PUBLISHED
    assert _unpublished({"not_checked": [{"reason": "made_up_here"}]}) == ["made_up_here"]
