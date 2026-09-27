"""A capture of nothing is refused wherever it enters, in one sentence.

Found from outside, by running the API: `feeder.run` handed a path, a string, a
parsed dict or an export with no units ran clean -- exit 0, 0 entities. The
command line did the same from a file whose `units` list was empty or whose
units carried no name: `detect` exited 0, `regression` said `ran` with no
changes, and `gate` answered `ready`. Only `presence` noticed, as fourteen
absences. `from_csv` had refused an empty file from the start; the other doors
never learned to.

Each test names the door and the input. The controls at the end hold what must
not move: the shipped capture's eleven findings, and presence clean on it.
"""
from __future__ import annotations

import copy
import json
import math
import subprocess
import sys

import pytest

from conftest import CAPTURE, DECLARATION, MODEL, ROOT


def _raw() -> dict:
    return json.loads(CAPTURE.read_text())


def _write(tmp_path, name: str, body: dict):
    path = tmp_path / name
    path.write_text(json.dumps(body))
    return path


def _nameless(*positions: int) -> dict:
    raw = copy.deepcopy(_raw())
    for i in positions or range(len(raw["units"])):
        raw["units"][i].pop("name", None)
    return raw


def _with_value(export, unit: str, quantity: str, value):
    """The shipped capture with one unit reporting `value` for one quantity."""
    from operating_health_audit import capture

    return capture.Export(complete=True, captured_at=export.captured_at, points=tuple(
        capture.Reading(name=p.name, unit_type=p.unit_type, path=p.path, state=p.state,
                        edges=p.edges,
                        values={**p.values, quantity: value} if p.name == unit else p.values)
        for p in export.points))


# --- the loader ---------------------------------------------------------------

class TestTheLoaderRefusesACaptureOfNothing:
    @pytest.mark.parametrize("units", [[], None], ids=["empty list", "no key"])
    def test_a_capture_with_no_units(self, tmp_path, units) -> None:
        from operating_health_audit import capture

        raw = _raw()
        if units is None:
            del raw["units"]
        else:
            raw["units"] = units
        with pytest.raises(capture.CaptureError) as refused:
            capture.load(_write(tmp_path, "empty.json", raw))
        assert "holds no units" in str(refused.value)
        assert capture.EMPTY_CAPTURE in str(refused.value)

    def test_units_that_are_not_a_list(self, tmp_path) -> None:
        from operating_health_audit import capture

        with pytest.raises(capture.CaptureError, match="`units` is a dict"):
            capture.load(_write(tmp_path, "odd.json", dict(_raw(), units={"a": 1})))

    def test_one_nameless_unit_is_refused_by_its_position(self, tmp_path) -> None:
        """Not dropped. A capture one unit smaller than its export agrees with
        itself about every count afterwards."""
        from operating_health_audit import capture

        with pytest.raises(capture.CaptureError) as refused:
            capture.load(_write(tmp_path, "one.json", _nameless(3)))
        message = str(refused.value)
        assert "units[3] has no name" in message
        assert "units[2]" not in message and "units[4]" not in message

    def test_every_unit_nameless_is_refused_and_counted(self, tmp_path) -> None:
        """What used to load as an empty capture and run clean."""
        from operating_health_audit import capture

        with pytest.raises(capture.CaptureError, match=r"and 9 more have no name"):
            capture.load(_write(tmp_path, "nameless.json", _nameless()))

    def test_an_entry_that_is_not_a_unit_is_named_by_what_it_is(self, tmp_path) -> None:
        from operating_health_audit import capture

        raw = _raw()
        raw["units"][1] = "Commercial Division"
        with pytest.raises(capture.CaptureError, match=r"units\[1\] \(a str\)"):
            capture.load(_write(tmp_path, "odd.json", raw))


class TestTheCsvReaderRefusesARowWithNoId:
    def test_an_empty_file_keeps_its_sentence(self, tmp_path) -> None:
        from operating_health_audit import capture

        path = tmp_path / "empty.csv"
        path.write_text("id,type,headcount\n")
        with pytest.raises(capture.CaptureError) as refused:
            capture.from_csv(path)
        assert str(refused.value) == f"{path} holds no rows, and {capture.EMPTY_CAPTURE}"

    def test_a_row_with_no_id_is_refused_by_its_line(self, tmp_path) -> None:
        from operating_health_audit import capture

        path = tmp_path / "gap.csv"
        path.write_text("id,type,headcount\ndept-sales,Department,40\n"
                        ",Department,12\ndept-ops,Department,9\n")
        with pytest.raises(capture.CaptureError, match="the row on line 3 has no id"):
            capture.from_csv(path)

    def test_a_file_with_no_id_column_is_refused(self, tmp_path) -> None:
        """It used to write a capture of no units and report it written."""
        from operating_health_audit import capture

        path = tmp_path / "named.csv"
        path.write_text("name,type,headcount\nsales,Department,40\n")
        with pytest.raises(capture.CaptureError, match="has no `id` column"):
            capture.from_csv(path)

    def test_a_file_with_an_id_on_every_row_still_reads(self, tmp_path) -> None:
        from operating_health_audit import capture

        path = tmp_path / "ok.csv"
        path.write_text("id,type,headcount\ndept-sales,Department,40\n")
        assert [p.name for p in capture.from_csv(path).points] == ["dept-sales"]


class TestTheCsvReaderRefusesACellThatIsNotANumber:
    """`float` raised on one, uncaught, and a traceback exits 1 -- which this
    package's contract reads as findings about the organisation."""

    @staticmethod
    def _csv(tmp_path, *rows):
        path = tmp_path / "wide.csv"
        path.write_text("\n".join(("id,type,headcount,turnover_pct",) + rows) + "\n")
        return path

    @pytest.mark.parametrize("token", ["N/A", "n/a", "-", "unknown"])
    def test_a_word_where_a_number_belongs_is_refused_by_line_and_column(
            self, tmp_path, token) -> None:
        """`N/A` is refused, not read as the empty cell: it can mean *not
        applicable* or *not available*, and only the exporter knows which."""
        from operating_health_audit import capture

        path = self._csv(tmp_path, f"dept-sales,Department,40,{token}")
        with pytest.raises(capture.CaptureError) as refused:
            capture.from_csv(path)
        assert (f"line 2, column `turnover_pct` ({token!r}) is not a number"
                in str(refused.value))

    def test_every_such_cell_is_named(self, tmp_path) -> None:
        from operating_health_audit import capture

        path = self._csv(tmp_path, "dept-sales,Department,N/A,N/A",
                         "dept-ops,Department,9,-")
        with pytest.raises(capture.CaptureError) as refused:
            capture.from_csv(path)
        message = str(refused.value)
        for where in ("line 2, column `headcount`", "line 2, column `turnover_pct`",
                      "line 3, column `turnover_pct`"):
            assert where in message
        assert "are not numbers" in message

    def test_blank_and_none_still_read_as_absent(self, tmp_path) -> None:
        """The other direction. The empty cell is the documented absence, and
        `None` is how a writer spells one."""
        from operating_health_audit import capture

        path = self._csv(tmp_path, "dept-sales,Department,40,", "dept-ops,Department,None,3")
        read = {p.name: dict(p.values) for p in capture.from_csv(path).points}
        assert read == {"dept-sales": {"headcount": 40.0}, "dept-ops": {"turnover_pct": 3.0}}

    def test_nan_and_inf_still_read(self, tmp_path) -> None:
        """`float` takes them, and the next test holds why they are let through."""
        from operating_health_audit import capture

        values = capture.from_csv(self._csv(tmp_path, "dept-sales,Department,nan,inf")).points[0].values
        assert math.isnan(values["headcount"]) and math.isinf(values["turnover_pct"])

    def test_the_engine_declines_a_non_finite_reading_by_name(self, export) -> None:
        """The premise of letting `nan` through, pinned: the engine answers it
        `undefined_for_values` rather than judging it. Should that stop being
        true, this reader has to start refusing it."""
        from operating_health_audit import feeder

        out = feeder.run(str(MODEL), [_with_value(export, "dept-sales", "turnover_pct",
                                                  float("nan"))])
        declined = {(d.get("axiom"), d.get("reason")) for d in out["not_checked"]
                    if d.get("entity_id") == "dept-sales" and "turnover" in str(d)}
        assert ("BOUNDEDNESS", "undefined_for_values") in declined, declined

    def test_a_row_with_more_cells_than_columns_is_refused_by_line(self, tmp_path) -> None:
        """It raised AttributeError: the reader files the extra cells as a list."""
        from operating_health_audit import capture

        with pytest.raises(capture.CaptureError,
                           match="the row on line 2 has more cells than the header has columns"):
            capture.from_csv(self._csv(tmp_path, "dept-sales,Department,40,3,9,9"))

    def test_the_capture_command_answers_could_not_run(self, tmp_path) -> None:
        out_file = tmp_path / "out.json"
        code, out = _run("capture", self._csv(tmp_path, "dept-sales,Department,40,N/A"),
                         "--out", out_file)
        assert (code, out["exit_code"]) == (2, 2)
        assert "is not a number" in out["could_not_run"]
        assert not out_file.exists()


# --- the API ------------------------------------------------------------------

def _items():
    from operating_health_audit import capture

    return [CAPTURE, str(CAPTURE), _raw(), capture.Export(points=())]


class TestTheFeederRefusesASeriesItCannotFeed:
    @pytest.mark.parametrize("which", range(4),
                             ids=["a Path", "a str", "a parsed dict", "an export of nothing"])
    def test_each_input_the_report_ran(self, which) -> None:
        from operating_health_audit import feeder

        out = feeder.run(str(MODEL), [_items()[which]])
        assert out["exit_code"] == 2
        assert out["findings"] == [] and out["engine"] is None
        assert out["could_not_run"].startswith("captures[0]")

    def test_an_empty_capture_partway_through_a_series(self, export) -> None:
        """A month of nothing is the same defect one month at a time."""
        from operating_health_audit import capture, feeder

        out = feeder.run(str(MODEL), [export, capture.Export(points=()), export])
        assert out["exit_code"] == 2
        assert out["could_not_run"].startswith("captures[1] holds no units")

    def test_open_session_raises_the_sentence_run_answers(self) -> None:
        """The other stages of the loop open their session here, not in `run`."""
        from operating_health_audit import feeder

        with pytest.raises(feeder.CaptureUnusable) as refused:
            feeder.open_session(str(MODEL), [str(CAPTURE)])
        assert str(refused.value) == feeder.run(str(MODEL), [str(CAPTURE)])["could_not_run"]

    def test_a_broken_model_is_still_reported_first(self, tmp_path) -> None:
        from operating_health_audit import feeder

        bad = tmp_path / "bad.yaml"
        bad.write_text("domain: [this is not: a mapping\n")
        with pytest.raises(feeder.ModelUnreadable):
            feeder.run(str(bad), [str(CAPTURE)])


class TestPresenceRefusesAnExportOfNothing:
    """Fourteen absences, before: every declared unit reported missing from an
    export that held none. An export holding no units cannot say which units
    are absent, so the API refuses as the command line does."""

    @pytest.mark.parametrize("which", range(4),
                             ids=["a Path", "a str", "a parsed dict", "an export of nothing"])
    def test_each_input(self, declaration, which) -> None:
        from operating_health_audit import presence

        out = presence.run(declaration, _items()[which])
        assert out["exit_code"] == 2 and out["findings"] == []
        assert out["could_not_run"].startswith("the export")

    def test_the_api_answers_what_the_command_line_answers(self, tmp_path, declaration) -> None:
        from operating_health_audit import capture, presence

        api = presence.run(declaration, capture.Export(points=()))
        code, cli = _run("presence", DECLARATION,
                         _write(tmp_path, "empty.json", dict(_raw(), units=[])))
        assert (api["exit_code"], code) == (2, 2)
        for said in (api["could_not_run"], cli["could_not_run"]):
            assert "holds no units" in said and said.endswith(capture.EMPTY_CAPTURE)

    def test_a_capture_of_one_unit_is_still_compared(self, declaration) -> None:
        """The other direction. One unit is a capture, and the rest are absent."""
        from operating_health_audit import capture, presence

        first = declaration.points[0]
        one = capture.Export(complete=True, captured_at="2026-09-15T00:00:00Z", points=(
            capture.Reading(name=first.name, unit_type=first.unit_type,
                            path=f"probe#{first.name}", state="healthy",
                            values={"headcount": 1.0}, edges=dict(first.edges)),))
        out = presence.run(declaration, one)
        assert "could_not_run" not in out
        absent = [f for f in out["findings"] if f["kind"] == "declared_absent"]
        assert len(absent) == len(declaration.points) - 1


class TestAReadingTheEngineRefusesIsRefusedInItsWords:
    """A word where the model declares a number reached the engine, whose
    refusal escaped as a traceback exiting 1 -- read as findings."""

    @pytest.mark.parametrize("value", ["N/A", None], ids=["a word", "null"])
    def test_run_answers_could_not_run_with_the_engines_message(self, export, value) -> None:
        from operating_health_audit import feeder

        series = [_with_value(export, "dept-sales", "turnover_pct", value)]
        out = feeder.run(str(MODEL), series)
        assert out["exit_code"] == 2 and out["findings"] == []
        assert out["could_not_run"].startswith(f"dept-sales.turnover_pct: reading {value!r}")
        with pytest.raises(feeder.CaptureUnusable) as refused:
            feeder.open_session(str(MODEL), series)
        assert str(refused.value) == out["could_not_run"]

    def test_a_numeric_string_is_still_a_number(self, export) -> None:
        """The other direction: the engine casts `"3.5"`, so nothing is refused."""
        from operating_health_audit import feeder

        out = feeder.run(str(MODEL), [_with_value(export, "dept-sales", "turnover_pct", "3.5")])
        assert "could_not_run" not in out and out["findings"]

    @pytest.mark.parametrize("error", [
        ValueError("add_observations got a mix of bare readings and (timestamp, value) pairs"),
        RuntimeError("the store is gone")], ids=["a ValueError naming no reading", "another error"])
    def test_only_the_refusal_of_a_reading_is_caught(self, export, monkeypatch, error) -> None:
        """A failure that is not the engine refusing the reading being fed is not
        this package's to translate, and propagates as it did."""
        from arbiter_engine import api

        from operating_health_audit import feeder

        def fails(*_args, **_kwargs):
            raise error

        monkeypatch.setattr(api.EngineSession, "add_observations", fails)
        with pytest.raises(type(error)) as raised:
            feeder.run(str(MODEL), [export])
        assert not isinstance(raised.value, feeder.CaptureUnusable)

    def test_detect_answers_in_the_engines_words(self, tmp_path) -> None:
        raw = _raw()
        unit = next(u for u in raw["units"] if u["name"] == "dept-sales")
        unit["values"]["turnover_pct"] = "N/A"
        code, out = _run("detect", MODEL, _write(tmp_path, "worded.json", raw))
        assert (code, out["exit_code"]) == (2, 2)
        assert out["could_not_run"].startswith("dept-sales.turnover_pct: reading 'N/A'")


def test_regression_refuses_two_exports_of_nothing() -> None:
    """*Nothing moved* is true of an organisation with no units."""
    from operating_health_audit import capture, regression

    empty = capture.Export(points=())
    out = regression.run(empty, empty)
    assert out["exit_code"] == 2
    assert out["could_not_run"].startswith("before and after hold no units")


# --- the command line ---------------------------------------------------------

def _run(*argv) -> tuple[int, dict]:
    done = subprocess.run(
        [sys.executable, "-m", "operating_health_audit.cli", *map(str, argv)],
        capture_output=True, text=True, cwd=str(ROOT),
        env={"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin"})
    return done.returncode, json.loads(done.stdout)


@pytest.mark.parametrize("body", ["empty", "nameless"])
@pytest.mark.parametrize("verb", ["detect", "regression", "presence", "gate"])
def test_every_verb_refuses_the_file(tmp_path, verb, body) -> None:
    """`presence` answered fourteen absences here before; it refuses now, with the
    same sentence as the rest, because the file holds no organisation to compare."""
    path = _write(tmp_path, f"{body}.json",
                  dict(_raw(), units=[]) if body == "empty" else _nameless())
    argv = {"detect": ("detect", MODEL, path),
            "regression": ("regression", path, path),
            "presence": ("presence", DECLARATION, path),
            "gate": ("gate", DECLARATION, "--capture", path)}[verb]
    code, out = _run(*argv)
    assert code == 2 and out["exit_code"] == 2
    said = out["refused_because"] if verb == "gate" else [out["could_not_run"]]
    assert any(("holds no units" if body == "empty" else "have no name") in s for s in said)
    if verb == "gate":
        assert out["ready"] is False


# --- what must not move -------------------------------------------------------

def test_the_shipped_capture_answers_as_it_did(export, declaration) -> None:
    from operating_health_audit import feeder, presence

    out = feeder.run(str(MODEL), [export])
    assert (out["exit_code"], len(out["findings"])) == (2, 11)
    assert presence.run(declaration, export)["exit_code"] == 0
