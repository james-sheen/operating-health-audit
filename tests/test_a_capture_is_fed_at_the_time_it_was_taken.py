"""A capture is fed to the engine at the time it was taken.

The feeder used to feed every series as bare values thirty days apart, ending at
the clock, and never read `captured_at`. So calendar months, a skipped month, a
review dated the 31st and a back-filled quarter all reached the engine as one
even ladder, and every window, baseline and learn-stage date was computed from a
spacing this package made up. An outside verification found it by feeding
calendar months through here and getting thirty-day answers.

Fixing the feeder alone would have made the real-data path worse. The CSV reader
stamped the moment a file was IMPORTED, so three monthly spreadsheets
back-filled in one sitting would have reached the engine seconds apart. The
reader now takes the time it is given, with `capture --captured-at`, or none.

The rule: every capture stamped, and the series is placed by its stamps and
judged as of the latest one; none stamped, and it is spaced at the declared
interval as before; anything between is refused by position. `run` says which.
"""

from __future__ import annotations

import dataclasses
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from arbiter_engine import api

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "examples" / "operating.model.yaml"
CAPTURE = ROOT / "examples" / "acme.capture.json"
MONTH_S = 30 * 86400.0
#: The one coupling the model declares, and the edge the learn stage reports it on.
EDGE = "dept-sales->div-commercial"


def _series(count: int, stamps=None):
    """`count` captures of the shipped organisation, moving a little each time,
    stamped with `stamps` -- or unstamped when `stamps` is None."""
    sys.path.insert(0, str(ROOT / "battery"))
    import make_series
    from operating_health_audit import capture

    series = make_series.series(capture.load(CAPTURE), count)
    return [dataclasses.replace(export, captured_at="" if stamps is None else stamps[i])
            for i, export in enumerate(series)]


def _calendar_months(count: int, first=(2016, 1)) -> list[str]:
    """The first of `count` consecutive months, as a capture writes them."""
    year, month = first
    out = []
    for step in range(count):
        y, m = divmod(month - 1 + step, 12)
        out.append(f"{year + y:04d}-{m + 1:02d}-01T00:00:00Z")
    return out


def _instant(stamp: str) -> datetime:
    return datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def _learn_decline(session, at: datetime) -> dict:
    with api.as_of(at):
        proposed = api.model_describe(session).to_dict()["model"]["proposed_transitions"]
    return next(entry for entry in proposed["not_fitted"] if entry["edge"] == EDGE)


def _fed_directly(captures) -> object:
    """The engine fed the way the review fed it: each reading paired with its
    capture's own stamp, straight into `add_observations`, no feeder involved."""
    from operating_health_audit import feeder

    session = feeder._loaded(str(MODEL))
    latest = captures[-1]
    for point in latest.points:
        session.add_entity(point.name, point.unit_type,
                           properties=feeder._fed(point), name=point.name)
    for point in latest.points:
        for relation, target in point.edges.items():
            session.add_relationship(point.name, relation, target)
    pairs: dict[tuple[str, str], list] = {}
    for export in captures:
        when = _instant(export.captured_at)
        for point in export.points:
            for name, value in feeder._fed(point).items():
                pairs.setdefault((point.name, name), []).append((when, value))
    for (unit, name), readings in pairs.items():
        session.add_observations(unit, name, readings)
    return session


class TestCalendarMonthsReachTheEngineAsCalendarMonths:
    """The review's gate: the learn decline through the feeder is the one the
    engine gives when fed the same stamps directly."""

    FIGURES = ("observations", "required", "sampling_interval_seconds",
               "floor_reached_at")

    def test_through_the_feeder_equals_the_engine_fed_directly(self):
        from operating_health_audit import feeder

        stamps = _calendar_months(30)
        captures = _series(30, stamps)
        at = _instant(stamps[-1])
        through = _learn_decline(feeder.open_session(str(MODEL), captures), at)
        direct = _learn_decline(_fed_directly(captures), at)
        assert {k: through[k] for k in self.FIGURES} == {k: direct[k] for k in self.FIGURES}
        # Calendar months: seven gaps in every twelve are 31 days.
        assert through["sampling_interval_seconds"] == 31 * 86400

    def test_an_unstamped_series_is_still_spaced_at_the_interval(self):
        """The control, and the path an export with no stamp still takes."""
        from operating_health_audit import feeder

        captures = _series(30)
        session = feeder.open_session(str(MODEL), captures)
        assert _learn_decline(session, datetime.now(timezone.utc))[
            "sampling_interval_seconds"] == MONTH_S
        assert feeder.timing(captures) == {"timed_by": "interval_seconds",
                                           "interval_seconds": MONTH_S}


class TestTheSeriesIsPlacedByItsStamps:

    def _readings(self, session, unit="dept-sales", name="headcount"):
        return session.reading_history().get_values(unit, name, timedelta(days=36_525))

    def test_captures_named_out_of_order_are_fed_in_the_order_taken(self):
        """The latest by stamp supplies the current values, whatever order the
        files were named in."""
        from operating_health_audit import feeder

        stamps = _calendar_months(3)
        january, february, march = _series(3, stamps)
        session = feeder.open_session(str(MODEL), [march, january, february])
        latest = {p.name: p for p in march.points}["dept-sales"].values["headcount"]
        assert session.entities["dept-sales"].properties["headcount"] == latest
        assert [value for _, value in self._readings(session)][-1] == latest

    def test_a_month_missing_from_the_series_stays_missing(self):
        """January, February, April: a ladder would have closed the gap and moved
        January and February a month later than they were taken."""
        from operating_health_audit import feeder

        stamps = _calendar_months(4)
        captures = _series(4, stamps)
        del captures[2]
        with api.as_of(_instant(stamps[3])):
            fed = [when for when, _ in self._readings(
                feeder.open_session(str(MODEL), captures))]
        assert fed == [_instant(s).replace(tzinfo=None)
                       for s in (stamps[0], stamps[1], stamps[3])]


class TestASeriesThatCannotBePlacedIsRefused:
    """Each by position, as could-not-run from `run` and as `CaptureUnusable`
    from `open_session` -- the same sentence either way."""

    def _refused(self, captures) -> str:
        from operating_health_audit import feeder

        out = feeder.run(str(MODEL), captures)
        assert out["exit_code"] == 2 and out["findings"] == []
        with pytest.raises(feeder.CaptureUnusable) as raised:
            feeder.open_session(str(MODEL), captures)
        assert str(raised.value) == out["could_not_run"]
        return out["could_not_run"]

    def test_a_series_half_stamped(self):
        captures = _series(3, _calendar_months(3))
        captures[1] = dataclasses.replace(captures[1], captured_at="")
        assert self._refused(captures).startswith(
            "captures[1] carries no captured_at and the rest do")

    def test_two_captures_stamped_the_same_instant(self):
        stamp = _calendar_months(1)[0]
        assert self._refused(_series(2, [stamp, stamp])).startswith(
            "captures[0] and captures[1] are stamped the same instant")

    def test_a_stamp_that_is_not_a_time(self):
        captures = _series(2, ["2016-01-01", "end of January"])
        assert self._refused(captures).startswith(
            "the captured_at of captures[1] ('end of January') is not a date and time")


class TestTheRunSaysHowItWasTimed:

    def test_a_stamped_series(self):
        from operating_health_audit import feeder

        stamps = _calendar_months(3)
        assert feeder.run(str(MODEL), _series(3, stamps))["timing"] == {
            "timed_by": "captured_at",
            "first": _instant(stamps[0]).isoformat(),
            "last": _instant(stamps[-1]).isoformat()}

    def test_an_unstamped_series(self):
        from operating_health_audit import feeder

        assert feeder.run(str(MODEL), _series(3))["timing"] == {
            "timed_by": "interval_seconds", "interval_seconds": MONTH_S}

    def test_a_series_taken_long_ago_is_judged_as_of_when_it_was_taken(self):
        """Thirty captures thirty days apart, taken in 2008-2010, answer what the
        same thirty answer unstamped -- a ladder that ends at the clock. Read at
        the wall clock instead, every reading sits more than the model's ten-year
        windows back, and the axioms that read a history have none."""
        from operating_health_audit import feeder

        start = datetime(2008, 1, 1, tzinfo=timezone.utc)
        stamps = [(start + timedelta(days=30 * i)).isoformat() for i in range(30)]

        def outcome(captures):
            out = feeder.run(str(MODEL), captures)
            return (out["exit_code"],
                    sorted((f["axiom"], f["entity_id"], f["problem_type"])
                           for f in out["findings"]),
                    sorted((d["entity_id"], d["reason"]) for d in out["not_checked"]))

        taken = outcome(_series(30, stamps))
        assert taken == outcome(_series(30))
        assert any(axiom == "MONOTONICITY" for axiom, _, _ in taken[1]), (
            "nothing here reads a history, so the clock could not have mattered")


class TestTheIntakeStatesWhenOrNothing:
    """`capture` stamped the moment of import, which is when the file was read."""

    CSV = "id,type,headcount\ndept-sales,Department,40\n"

    def _capture(self, tmp_path, *extra):
        source = tmp_path / "review.csv"
        source.write_text(self.CSV)
        out = tmp_path / "review.json"
        done = subprocess.run(
            [sys.executable, "-m", "operating_health_audit.cli", "capture",
             str(source), "--out", str(out), *extra],
            capture_output=True, text=True, cwd=str(ROOT),
            env={"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin"})
        return done.returncode, json.loads(done.stdout), out

    def test_the_time_it_is_given(self, tmp_path):
        code, said, out = self._capture(tmp_path, "--captured-at", "2026-01-31")
        assert code == 0 and said["captured_at"] == "2026-01-31"
        assert json.loads(out.read_text())["captured_at"] == "2026-01-31"

    def test_no_time_when_none_is_given(self, tmp_path):
        code, said, out = self._capture(tmp_path)
        assert code == 0 and said["captured_at"] is None
        assert json.loads(out.read_text())["captured_at"] == ""

    def test_a_time_that_is_not_one_is_refused(self, tmp_path):
        code, said, out = self._capture(tmp_path, "--captured-at", "last Tuesday")
        assert code == 2 and "is not a date and time" in said["could_not_run"]
        assert not out.exists()
