"""Every number and command the README states, measured.

A README is the surface most readers see and the one nothing executes. Each
claim here is DERIVED from a run rather than transcribed, so a change that makes
the prose false fails here instead of shipping.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys

import pytest

from conftest import AS_SHIPPED, CAPTURE, DECLARATION, MODEL, ROOT

README = (ROOT / "README.md").read_text()


def _run(*argv) -> tuple[int, dict]:
    done = subprocess.run(
        [sys.executable, "-m", "operating_health_audit.cli", *argv],
        capture_output=True, text=True, cwd=str(ROOT),
        env={"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin"})
    try:
        return done.returncode, json.loads(done.stdout)
    except json.JSONDecodeError:
        raise AssertionError(f"{argv} printed no JSON:\n{done.stdout}\n{done.stderr}")


def test_the_day_one_finding_count_is_what_the_readme_says() -> None:
    """The headline number. Written as a word, so the assertion reads the word."""
    _code, out = _run("detect", str(MODEL), str(CAPTURE))
    counted = len(out["findings"])
    claimed = re.search(r"\b(\w+) findings from a single capture\b", README)
    assert claimed, "the README no longer states a day-one finding count"
    words = {"eleven": 11, "twelve": 12, "ten": 10, "seven": 7, "twenty-two": 22}
    assert words.get(claimed.group(1).lower()) == counted, (
        f"the README says {claimed.group(1)} and the run produces {counted}")


def test_the_shipped_example_exits_2_for_the_reasons_the_readme_gives() -> None:
    """Its findings score `1`; four declared checks the export carries no value
    for, and two passing states the model gives no `timeout:`, score `2`; the
    worse wins. This asserted the code alone, with a reason in its message that
    was not the reason: every finding was scored `unclassified`, which floors at
    `2` by itself, so the check held for a cause it never read (FINDINGS F14).
    The second reason arrived with engine 0.2.22, which declines to time such a
    state where it had timed it against five minutes nobody declared."""
    code, out = _run("detect", str(MODEL), str(CAPTURE))
    assert code == out["exit_code"] == 2
    floors = {row["kind"]: row["floor"] for row in out["why"]}
    assert floors["engine_finding"] == 1 and floors["missing_property"] == 2
    assert sorted(k for k, floor in floors.items() if floor == 2) == [
        "missing_config", "missing_property"]
    assert out["unclassified"] == []
    unanswered = {((d.get("entity") or d.get("entity_id")), d.get("indicator"))
                  for d in out["not_checked"] if d["reason"] == "missing_property"}
    assert unanswered == {("proc-sales-cycle", "throughput"),
                          ("proc-onboarding", "throughput"),
                          ("dept-engineering", "margin_pct"),
                          ("dept-support", "margin_pct")}
    for name in {indicator for _, indicator in unanswered}:
        assert f"`{name}`" in README, f"the README does not name {name}"
    untimed = {((d.get("entity") or d.get("entity_id")), d.get("indicator"))
               for d in out["not_checked"] if d["reason"] == "missing_config"}
    assert untimed == {("dept-marketing", "status"), ("proj-crm", "status")}
    for word in ("`missing_config`", "`transient:`", "`timeout:`",
                 "`restructuring`", "`at_risk`"):
        assert word in README, f"the README does not name {word}"


def test_the_captures_the_coupling_waits_for_are_the_engines() -> None:
    """The README says the one coupling declines until a number of monthly
    captures exist. The number is the ENGINE's, not this package's -- one more
    than the paired changes it fits a gain from -- so it is read off the floor
    the engine reports, and a release that moved the floor fails here."""
    from arbiter_engine import api
    from operating_health_audit import capture, feeder

    claimed = re.search(r"until (\d+) monthly captures", README)
    assert claimed, "the README no longer says when the coupling can be fitted"
    session = feeder.open_session(str(MODEL), [capture.load(CAPTURE)])
    proposed = api.model_describe(session).to_dict()["model"]["proposed_transitions"]
    assert int(claimed.group(1)) == proposed["checked"]["sample_floor"] + 1


def test_the_breakdown_the_readme_gives_is_the_breakdown_measured() -> None:
    """Four exceeded, three warning, four bad states -- asserted separately,
    because a total can stay right while its parts move."""
    _code, out = _run("detect", str(MODEL), str(CAPTURE))
    kinds: dict[str, int] = {}
    for f in out["findings"]:
        kinds[f["problem_type"].split(":")[0]] = kinds.get(f["problem_type"].split(":")[0], 0) + 1
    assert kinds == {"threshold_exceeded": 4, "threshold_warning": 3,
                     "declared_bad_state": 4}


def test_the_example_really_holds_the_number_of_units_the_readme_names() -> None:
    _code, out = _run("presence", str(DECLARATION), str(CAPTURE))
    assert "fourteen-unit" in README
    assert out["declared"] == 14 and out["captured"] == 14


def test_the_as_shipped_export_really_leaves_every_unit_detached() -> None:
    """The README says so in prose. If a future fixture quietly gains edges the
    sentence becomes false and nothing else would notice."""
    code, out = _run("presence", str(DECLARATION), str(AS_SHIPPED))
    detached = [f for f in out["findings"] if f["kind"] == "detached_unit"]
    assert len(detached) == out["captured"] == 14
    assert code == 1


def test_every_verb_the_readme_lists_exists() -> None:
    """Derived from the README table rather than listed here, so a verb added to
    the code and not the prose -- or the reverse -- fails."""
    listed = set(re.findall(r"^operating-health-audit (\w[\w-]*)", README, re.M))
    assert listed, "the README lists no verbs"
    from operating_health_audit.cli import build_parser

    actions = [a for a in build_parser()._actions if hasattr(a, "choices") and a.choices]
    real = set(actions[0].choices)
    assert listed == real, f"README lists {sorted(listed)}, the CLI offers {sorted(real)}"


def test_the_exit_code_sentence_matches_the_contract() -> None:
    from operating_health_audit import exit_contract as x

    assert "`0` clean, `1` findings, `2` could-not-complete" in README
    assert (x.CLEAN, x.FINDINGS, x.INCOMPLETE) == (0, 1, 2)
    assert x.code_for([]) == x.CLEAN, "the README says composing nothing is 0 here"


def _ranking(out, unit):
    [ranking] = {json.dumps(f["ranking"], sort_keys=True) for f in out["findings"]
                 if f["entity_id"] == unit}
    return json.loads(ranking)


def test_the_walks_the_readme_describes_are_the_ones_printed() -> None:
    """The README says the sales department is traced to its two executives and
    names no reading, and the division is partly traced and names the marketing
    executive's tenure, for too few samples."""
    _code, out = _run("detect", str(MODEL), str(CAPTURE))
    words = " ".join(README.split())
    sales = _ranking(out, "dept-sales")
    assert sales["walk"]["state"] == "traced"
    assert len(sales["walk"]["frontier"]) == 2 and sales["most_discriminating"] is None
    assert "the sales department is traced to its two executives and names no reading" in words
    division = _ranking(out, "div-commercial")
    assert division["walk"]["state"] == "partly_traced"
    assert division["most_discriminating"] == {
        "entity": "exec-cmo", "reading": "exec-cmo.tenure_years",
        "basis": "only_open"}
    assert [need["reason"] for entry in division["walk"]["open"]
            for need in entry["needs"]
            if need["reading"] == "exec-cmo.tenure_years"] == ["insufficient_samples"]
    assert "the commercial division is partly traced" in words
    assert "the marketing executive's tenure, which one capture is too few samples" in words
    # Engine 0.2.32: what the chief revenue officer explains below the frontier.
    cro = next(row for row in sales["walk"]["frontier"] if row["entity"] == "exec-cro")
    assert [r["entity"] for r in cro["explains"]] == [
        "dept-sales", "div-commercial", "proc-sales-cycle"]
    assert ("the chief revenue officer explaining the department, its division and "
            "its sales process") in words


def test_where_the_walks_end_is_what_the_readme_says() -> None:
    """The README says `detect` prints where each walk ends, and on the shipped
    capture names the support department, which no executive leads."""
    _code, out = _run("detect", str(MODEL), str(CAPTURE))
    words = " ".join(README.split())
    assert [(row["kind"], row["at"], row["relation"])
            for row in out["where_walks_end"]["located"]] == [
        ("no_cause_connected", "dept-support", "leads")]
    assert "Under `where_walks_end`, `detect` prints where each walk ends" in words
    assert "the support department, which no executive leads" in words


def test_a_case_closes_after_the_number_of_captures_the_readme_says() -> None:
    """Read off the model, which declares it, rather than restated here."""
    import yaml

    declared = yaml.safe_load(MODEL.read_text())["domain"]["cases"]
    words = {1: "one", 2: "two", 3: "three"}
    assert (f"closes after {words[declared['consecutive_checks']]} clean monthly "
            f"captures") in " ".join(README.split())


def test_the_install_line_names_the_release_this_is():
    """The package is not on PyPI, where `pip install operating-health-audit` answers
    404, and the quick start's examples live in the repository, not in the package. So
    the README clones a release tag -- and the tag it names is this version, or the next
    release would leave it pointing at the last one."""
    from operating_health_audit import __version__

    assert (f"git clone --branch v{__version__} "
            "https://github.com/james-sheen/operating-health-audit") in README
    assert "pip install operating-health-audit" not in README


def test_a_missing_engine_is_told_the_readmes_install(monkeypatch):
    """The same 404, from the other door: Stage 2 without the engine said
    `pip install operating-health-audit[detect]`, which the README avoids."""
    import sys

    from operating_health_audit import feeder

    monkeypatch.setitem(sys.modules, "arbiter_engine", None)
    with pytest.raises(feeder.EngineUnavailable) as refused:
        feeder._engine()
    assert "pip install '.[detect]'" in str(refused.value)
    assert "pip install operating-health-audit" not in str(refused.value)
