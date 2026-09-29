"""An engine finding is scored as a finding, read by the key the engine writes.

`detect` took each finding's kind from `type` or `kind`. The engine writes
neither: it reports a finding's kind as `problem_type`. So from the first
release every engine finding was scored `unclassified`, which the exit table
floors at could-not-complete, and a run that had found something exited 2 where
the README promises 1 (FINDINGS F14). An engine finding is now one kind with its
own row, whatever its problem type -- the set is open, one per invariant and
indicator, so a row per name could never be derived -- and a finding carrying no
problem type is still refused a score, by name.
"""
from __future__ import annotations

import re

from conftest import CAPTURE, MODEL

from operating_health_audit import capture, exit_contract as x, feeder


def _with_every_column():
    """The shipped capture with the two columns its export does not carry --
    each process's `throughput`, and `margin_pct` on the departments whose
    margin it does not report -- so nothing is left the engine cannot evaluate."""
    shipped = capture.load(CAPTURE)
    points = []
    for point in shipped.points:
        values = dict(point.values)
        if point.unit_type == "Process":
            values.setdefault("throughput", 100.0)
        if point.unit_type == "Department":
            values.setdefault("margin_pct", 20.0)
        points.append(capture.Reading(
            name=point.name, unit_type=point.unit_type, path=point.path,
            values=values, state=point.state, edges=dict(point.edges)))
    return capture.Export(points=tuple(points), complete=True,
                          source="the shipped capture, every declared column filled")


def _with_every_timeout(tmp_path):
    """The shipped model with a `timeout:` on each passing state. It declares
    none -- how long a restructuring may last is the review's to say -- so from
    engine 0.2.22 a unit in one is declined `missing_config`, not timed. The
    number is this fixture's, like the columns `_with_every_column` fills."""
    text = MODEL.read_text()
    timed, count = re.subn(r"^(\s*)(transient: \[[^\]]*\])$", r"\1\2\n\1timeout: 90d",
                           text, flags=re.MULTILINE)
    assert count == text.count("transient:") == 3, "a passing state was left untimed"
    path = tmp_path / "operating.model.timed.yaml"
    path.write_text(timed)
    return path


class TestTheExitCode:

    def test_a_run_that_finds_something_and_answers_everything_exits_1(self, tmp_path):
        out = feeder.run(str(_with_every_timeout(tmp_path)), [_with_every_column()])
        assert out["findings"], "the fixture finds nothing, so this checks nothing"
        assert out["exit_code"] == x.FINDINGS
        floors = {row["kind"]: row["floor"] for row in out["why"]}
        assert floors["engine_finding"] == x.FINDINGS
        assert max(floors.values()) == x.FINDINGS and out["unclassified"] == []

    def test_the_row_scores_a_finding_and_says_why(self):
        level, because = x.FLOORS[x.ENGINE_FINDING]
        assert level == x.FINDINGS and "finding" in because


class TestTheKindIsReadByTheEnginesKey:

    def test_every_problem_type_is_one_scored_kind(self):
        payload = {"findings": [{"problem_type": "threshold_exceeded:turnover_pct"},
                                {"problem_type": "declared_bad_state:status"}]}
        assert feeder._kinds(payload, []) == [x.ENGINE_FINDING, x.ENGINE_FINDING]

    def test_the_keys_it_used_to_read_score_nothing(self):
        """A finding described by `type` or `kind` alone is not one the engine
        wrote, so it is not scored as one."""
        payload = {"findings": [{"type": "threshold_exceeded"},
                                {"kind": "threshold_exceeded"}]}
        assert feeder._kinds(payload, []) == ["unclassified", "unclassified"]
        assert x.code_for(feeder._kinds(payload, [])) == x.INCOMPLETE

    def test_declines_and_an_unread_model_still_count(self):
        payload = {"findings": [{"problem_type": "threshold_warning:x"}],
                   "not_checked": [{"reason": "missing_property"}]}
        kinds = feeder._kinds(payload, ["a dropped declaration"])
        assert kinds == [x.ENGINE_FINDING, "missing_property", "model_not_read"]
        assert x.code_for(kinds) == x.INCOMPLETE
