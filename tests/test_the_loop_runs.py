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

The published names are read from where the engine keeps them: its top-level
decline enum and one closed vocabulary per discipline. Both are deeper than the
names the engine promises, and are imported anyway because the test's subject is
exactly that promise -- a decline outside those sets is one no reader could
switch on.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from arbiter_engine import api
from arbiter_engine.subenvelope import VOCABULARIES
from arbiter_engine.types import NotEvaluatedReason

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "examples" / "operating.model.yaml"
CAPTURE = ROOT / "examples" / "acme.capture.json"

PUBLISHED = {reason.value for reason in NotEvaluatedReason}.union(*VOCABULARIES.values())


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


@pytest.fixture(scope="module")
def session():
    sys.path.insert(0, str(ROOT / "battery"))
    from operating_health_audit import capture, feeder
    import make_series

    base = capture.load(CAPTURE)
    return feeder.open_session(str(MODEL), make_series.series(base, 30, transition=True))


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
        subject = sensed["findings"][0]["entity_id"]
        payload = api.hypothesize(session, subject).to_dict()
        assert "hypothesis" in payload, "the verb answered with no hypothesis leg"
        assert _unpublished(payload) == []

    def test_plan(self, session):
        """The model declares no action and no objective, so the honest answer is
        a named refusal -- and a plan that declined nothing here would be
        claiming a search it had nothing to run over."""
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


def test_the_vocabularies_are_not_empty():
    """Before believing a negative, prove the probe can produce one."""
    assert "insufficient_samples" in PUBLISHED and "no_objective" in PUBLISHED
    assert _unpublished({"not_checked": [{"reason": "made_up_here"}]}) == ["made_up_here"]
