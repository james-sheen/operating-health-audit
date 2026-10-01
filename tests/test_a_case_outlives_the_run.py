"""A finding becomes a case the next capture is checked into, and a person can
say what settled it.

The engine keeps a case book beside a durable ledger, and nothing here opened
one: every `detect` was a fresh session, so a finding lived for one run, and no
verb could record the cause a person later confirmed (FINDINGS F15). With
`--ledger`, a finding opens a case on its unit and indicator unless one is open,
this capture's ranking is attached, and each later capture is checked into it;
it closes after the model's declared run of clean captures. `confirm` records
the cause and the reading that settled it, and the engine reads it back against
the ranking the case held.

A case counts captures, so each is judged into the book once: a series must be
stamped, and one ending no later than what the book already judged is refused.
"""
from __future__ import annotations

import dataclasses
import json
import subprocess
import sys

import pytest

from conftest import CAPTURE, MODEL, ROOT

SEPTEMBER = "2026-09-15T00:00:00Z"
UNIT, QUANTITY = "proc-sales-cycle", "error_rate_pct"


def _month(export, stamp, **healthy):
    """The shipped capture taken at `stamp`, with `healthy` readings changed:
    `proc_sales_cycle=2.0` sets that process's error rate."""
    points = []
    for point in export.points:
        values = dict(point.values)
        if point.name.replace("-", "_") in healthy:
            values[QUANTITY] = healthy[point.name.replace("-", "_")]
        points.append(dataclasses.replace(point, values=values))
    return dataclasses.replace(export, points=tuple(points), captured_at=stamp)


@pytest.fixture()
def months():
    from operating_health_audit import capture

    shipped = capture.load(CAPTURE)
    assert shipped.captured_at == SEPTEMBER, "the shipped capture's stamp moved"
    return [shipped,
            _month(shipped, "2026-10-15T00:00:00Z", proc_sales_cycle=2.0),
            _month(shipped, "2026-11-15T00:00:00Z", proc_sales_cycle=2.0)]


def _case(result, unit=UNIT, quantity=QUANTITY):
    [case_id] = {f["case_id"] for f in result["findings"]
                 if f["entity_id"] == unit and f["problem_type"].endswith(f":{quantity}")}
    return case_id


class TestACaseOutlivesTheRun:

    def test_each_finding_opens_one_case_and_carries_its_id(self, months, tmp_path):
        from operating_health_audit import feeder

        ledger = str(tmp_path / "ledger.db")
        result = feeder.run(str(MODEL), months[:1], ledger=ledger)
        keys = {(f["entity_id"], f["problem_type"].split(":", 1)[1])
                for f in result["findings"]}
        assert result["cases"]["opened"] == len(keys) == result["cases"]["open"]
        assert all(f["case_id"] for f in result["findings"])
        assert result["cases"]["rankings_attached"] == len(keys)
        assert result["cases"]["declined"] == []

    def test_the_next_capture_is_checked_into_it_and_two_clean_close_it(
            self, months, tmp_path):
        from operating_health_audit import feeder

        ledger = str(tmp_path / "ledger.db")
        case_id = _case(feeder.run(str(MODEL), months[:1], ledger=ledger))
        feeder.run(str(MODEL), months[:2], ledger=ledger)
        feeder.run(str(MODEL), months, ledger=ledger)
        [case] = [c for c in feeder.book(ledger)["cases"] if c["case_id"] == case_id]
        assert [entry["outcome"] for entry in case["stages"]["check"]] == [
            "clean", "clean"]
        assert case["status"] == "resolved"
        # Opened on the September capture and closed on November's, as the
        # model declares: two clean captures in a row.
        assert case["opened_at"].startswith("2026-09-15")
        assert case["resolved_at"].startswith("2026-11-15")

    def test_a_finding_that_stays_keeps_its_case_and_opens_no_second(
            self, months, tmp_path):
        from operating_health_audit import feeder

        ledger = str(tmp_path / "ledger.db")
        first = feeder.run(str(MODEL), months[:1], ledger=ledger)
        second = feeder.run(str(MODEL), months[:2], ledger=ledger)
        assert second["cases"]["opened"] == 0
        stayed = {(f["entity_id"], f["problem_type"]) for f in second["findings"]}
        before = {(f["entity_id"], f["problem_type"]): f["case_id"]
                  for f in first["findings"]}
        for finding in second["findings"]:
            key = (finding["entity_id"], finding["problem_type"])
            if key in before:
                assert finding["case_id"] == before[key]
        assert stayed, "no finding stayed, so this checked nothing"

    def test_each_capture_is_judged_into_the_book_once(self, months, tmp_path):
        """Re-running the same files would record September's check again, and
        two clean checks of one capture would close a case on one month."""
        from operating_health_audit import feeder

        ledger = str(tmp_path / "ledger.db")
        feeder.run(str(MODEL), months[:2], ledger=ledger)
        again = feeder.run(str(MODEL), months[:2], ledger=ledger)
        assert again["exit_code"] == 2
        assert "counts each capture once" in again["could_not_run"]

    def test_an_unstamped_series_keeps_no_cases(self, tmp_path):
        from operating_health_audit import capture, feeder

        bare = dataclasses.replace(capture.load(CAPTURE), captured_at="")
        result = feeder.run(str(MODEL), [bare], ledger=str(tmp_path / "ledger.db"))
        assert result["exit_code"] == 2
        assert result["could_not_run"] == feeder.UNSTAMPED_FOR_CASES
        assert not (tmp_path / "ledger.db").exists() or feeder.book(
            str(tmp_path / "ledger.db"))["opened"] == 0

    def test_without_a_ledger_nothing_about_cases_is_printed(self, months):
        from operating_health_audit import feeder

        result = feeder.run(str(MODEL), months[:1])
        assert "cases" not in result
        assert all("case_id" not in f for f in result["findings"])


class TestAPersonSaysWhatSettledIt:

    def test_the_confirmation_is_read_back_against_the_ranking(self, months, tmp_path):
        """A division's finding: its walk is partly traced, and the reading it
        names is the marketing executive's tenure, the first value declared of
        those still owed. A person reads it, confirms that executive, and says
        that reading settled it."""
        from operating_health_audit import feeder

        ledger = str(tmp_path / "ledger.db")
        result = feeder.run(str(MODEL), months[:1], ledger=ledger)
        [finding] = [f for f in result["findings"] if f["entity_id"] == "div-commercial"]
        named = finding["ranking"]["most_discriminating"]["reading"]
        assert named == "exec-cmo.tenure_years"
        confirmed = feeder.confirm(ledger, finding["case_id"], cause="exec-cmo",
                                   reading=named, basis="the October review")
        assert confirmed["exit_code"] == 0 and confirmed["declined"] == []
        row = confirmed["confirmed"]
        # Ranked by standing: two executives on the frontier, two departments
        # on the trail, and the open one last.
        assert (row["rank"], row["of"], row["ranked_by"]) == (5, 5, "standing")
        assert (row["settling_reading"], row["settling_reading_was_named"]) == (
            named, True)
        book = feeder.book(ledger)["confirmed"]
        assert (book["confirmations"], book["settling_reading_was_named"]) == (1, 1)

    def test_an_unknown_case_is_refused_by_name(self, months, tmp_path):
        from operating_health_audit import feeder

        ledger = str(tmp_path / "ledger.db")
        feeder.run(str(MODEL), months[:1], ledger=ledger)
        refused = feeder.confirm(ledger, "no-such-case", cause="dept-sales",
                                 basis="a guess")
        assert refused["exit_code"] == 2
        assert [d["reason"] for d in refused["declined"]] == ["malformed_request"]

    def test_a_ledger_that_is_not_there_is_refused_not_created(self, tmp_path):
        from operating_health_audit import feeder

        missing = tmp_path / "typo.db"
        with pytest.raises(feeder.LedgerUnreadable, match="there is no ledger"):
            feeder.confirm(str(missing), "any", cause="dept-sales", basis="a guess")
        assert not missing.exists()


def _cli(*argv):
    done = subprocess.run(
        [sys.executable, "-m", "operating_health_audit.cli", *argv],
        capture_output=True, text=True, cwd=str(ROOT),
        env={"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin"})
    return done.returncode, json.loads(done.stdout)


class TestTheVerbs:

    def test_detect_keeps_cases_and_the_two_verbs_read_and_confirm_them(self, tmp_path):
        ledger = str(tmp_path / "ledger.db")
        code, out = _cli("detect", str(MODEL), str(CAPTURE), "--ledger", ledger)
        assert code == out["exit_code"] == 2      # the shipped example's own reason
        case_id = _case(out, "div-commercial", "status")
        # The reading the division's walk names: the one cause still open.
        code, out = _cli("confirm", ledger, case_id, "--cause", "exec-cmo",
                         "--reading", "exec-cmo.tenure_years", "--basis", "a review")
        assert code == 0 and out["confirmed"]["settling_reading_was_named"] is True
        code, out = _cli("cases", ledger)
        assert code == 0 and out["confirmed"]["confirmations"] == 1
        assert out["opened"] == out["open"] > 0
