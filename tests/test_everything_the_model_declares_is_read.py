"""Everything the shipped model declares is read, and every axiom it declares can run.

The model declared a `role:` on every numeric indicator. Eighteen sat on
indicators whose axioms never read one -- a role has two readers, RESPONSIVENESS
and CONSISTENCY -- and the engine said so on every load: `model_describe` listed
each as an unread field, `axiom_not_declared`. Nothing here looked. Inert rather
than wrong: with the eighteen gone, the case study's findings, declines and exit
code are byte for byte what they were. But a reader of the model took eighteen
declarations to be doing something.

The engine REPORTS a key nobody reads instead of refusing the model, which is
right for an engine and means it will not stop the next one. This does, in both
directions, because each is blind to the other: a role that is absent is not an
unread one, so the check that keeps the eighteen out cannot keep the one role
RESPONSIVENESS needs in.
"""
from __future__ import annotations

from conftest import MODEL


def _described(path) -> dict:
    from arbiter_engine import api
    from arbiter_engine.api import EngineSession
    session = EngineSession()
    session.load_model(str(path))
    return api.model_describe(session).to_dict()["model"]


def _with(tmp_path, entity: str, name: str, change) -> dict:
    """The shipped model with one indicator changed, as the engine describes it."""
    import yaml
    model = yaml.safe_load(MODEL.read_text(encoding="utf-8"))
    change(next(spec for spec in model["domain"]["indicators"][entity]
                if spec["name"] == name))
    copy = tmp_path / "model.yaml"
    copy.write_text(yaml.safe_dump(model), encoding="utf-8")
    return _described(copy)


def _unreachable(described: dict) -> dict:
    return {f"{entity}.{spec['name']}": spec["unreachable_axioms"]
            for entity, specs in described["indicators"].items() for spec in specs
            if spec["unreachable_axioms"]}


def test_nothing_the_shipped_model_declares_goes_unread():
    unread = _described(MODEL)["unread_fields"]
    assert unread == [], [f"{u['entity_type']}.{u['indicator']}: {u['field']} ({u['reason']})"
                          for u in unread]


def test_every_axiom_the_shipped_model_declares_can_run():
    assert _unreachable(_described(MODEL)) == {}


def test_a_role_nothing_reads_is_still_reported(tmp_path):
    """The control for the first test. If the engine stopped reporting unread
    fields, that test would pass on a list nobody filled; so a role goes back on
    an indicator whose only axiom is BOUNDEDNESS, and the report is required."""
    def add_a_role(spec):
        assert spec["axioms"] == ["BOUNDEDNESS"] and "role" not in spec
        spec["role"] = "count"

    unread = _with(tmp_path, "Division", "total_headcount", add_a_role)["unread_fields"]
    assert [(u["indicator"], u["field"], u["reason"]) for u in unread] == [
        ("total_headcount", "role", "axiom_not_declared")]


def test_the_one_role_left_is_the_one_an_axiom_needs(tmp_path):
    """The control for the second. Without `latency` on `cycle_time_days`,
    RESPONSIVENESS there cannot evaluate under any input -- and the unread list
    stays empty, which is why the first test could never have caught it."""
    described = _with(tmp_path, "Process", "cycle_time_days",
                      lambda spec: spec.pop("role"))
    assert _unreachable(described) == {"Process.cycle_time_days": ["RESPONSIVENESS"]}
    assert described["unread_fields"] == []
