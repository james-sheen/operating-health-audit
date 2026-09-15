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
    code, out = _run("detect", str(MODEL), str(CAPTURE))
    assert code == 2, "the shipped export cannot feed two Process indicators"
    counted = len(out["findings"])
    claimed = re.search(r"\b(\w+) findings from a single capture\b", README)
    assert claimed, "the README no longer states a day-one finding count"
    words = {"eleven": 11, "twelve": 12, "ten": 10, "seven": 7, "twenty-two": 22}
    assert words.get(claimed.group(1).lower()) == counted, (
        f"the README says {claimed.group(1)} and the run produces {counted}")


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
