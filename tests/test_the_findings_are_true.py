"""FINDINGS.md describes runs and cites its own sections. Both are checkable.

The README already has `test_the_readme_is_true.py`. FINDINGS.md had nothing, and
it is the document where being wrong costs most, because every claim in it is
about somebody else's package as well as this one.

It was wrong twice. F2 asserted that nothing reachable closes the HOMEOSTASIS
baseline, having checked two routes and inferred the absence of a third; the
constructor was open the whole time. And the intro counted the findings that
contradicted what reading had concluded, then went stale the moment correcting F2
made that count one higher.

Neither is the kind of error a linter sees. What catches them is resolution: a
section this document cites has to exist, a number it reports has to be what a run
produces, and a string it quotes has to be one the engine actually emits.
"""

from __future__ import annotations

import re

import pytest

from conftest import CAPTURE, MODEL, ROOT

FINDINGS = (ROOT / "FINDINGS.md").read_text(encoding="utf-8")

#: `**F7.` opens a finding. A bare `F7` anywhere else is a citation of one.
DEFINED = re.compile(r"^\*\*F(\d+)\.", re.MULTILINE)
CITED = re.compile(r"\bF(\d+)\b")


def _defined() -> set[str]:
    return set(DEFINED.findall(FINDINGS))


# --- the document has to resolve against itself ----------------------------

def test_every_finding_number_the_prose_cites_is_one_the_document_defines() -> None:
    """A citation pointing at nothing is either a renumbering that half landed or a
    finding somebody meant to write. Both should fail here rather than be read as
    a cross-reference by somebody checking the work."""
    defined, cited = _defined(), set(CITED.findall(FINDINGS))
    missing = sorted(cited - defined, key=int)
    assert not missing, f"the prose cites F{', F'.join(missing)}, which it never defines"


def test_the_findings_are_numbered_without_a_gap_or_a_repeat() -> None:
    """A gap reads as a withdrawn finding and a repeat reads as two, and the
    document says neither."""
    numbers = [int(n) for n in DEFINED.findall(FINDINGS)]
    assert numbers == sorted(numbers), "the findings are not in order"
    assert len(numbers) == len(set(numbers)), "a finding number is defined twice"
    assert numbers == list(range(1, len(numbers) + 1)), f"numbering has a gap: {numbers}"


def test_the_intro_names_as_many_findings_as_it_says_it_does() -> None:
    """The stale-count bug, pinned. The intro states a number in words and then
    lists the items. Correcting F2 moved the number and nothing would have said so.
    """
    words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
             "six": 6, "seven": 7, "eight": 8, "nine": 9}
    claim = re.search(
        r"(\w+) of them\s+contradicted what reading had already concluded:\s*(.+?)\.",
        FINDINGS, re.S)
    assert claim, "the intro no longer states a count of reading-contradicted findings"
    stated = words.get(claim.group(1).lower())
    assert stated is not None, f"count {claim.group(1)!r} is not a word this test reads"

    listed = [part for part in re.split(r",\s*|\s+and\s+", claim.group(2)) if part.strip()]
    assert stated == len(listed), (
        f"the intro says {stated} and then lists {len(listed)}: {listed}")
    for item in listed:
        found = CITED.search(item)
        if found:
            assert found.group(1) in _defined(), f"the intro names F{found.group(1)}, undefined"


# --- the document has to resolve against the model and the engine ----------

def test_every_indicator_the_prose_names_is_declared_in_the_model() -> None:
    """Indicator names are the tokens most likely to survive a model edit only in
    the prose. Resolved against the shipped model rather than a list here."""
    model = MODEL.read_text(encoding="utf-8")
    declared = set(re.findall(r"^\s*- name:\s*(\S+)", model, re.MULTILINE))
    assert declared, "no indicators parsed out of the model; this check is vacuous"
    # A backticked span may pair an indicator with an axiom, as
    # `throughput/RESPONSIVENESS` does, so resolve TOKENS inside spans and not
    # whole spans. Matching whole spans made this pass vacuously.
    spoken = set()
    for span in re.findall(r"`([^`]+)`", FINDINGS):
        spoken.update(re.split(r"[^\w]+", span))
    for name in ("cycle_time_days", "status", "throughput"):
        assert name in spoken, (
            f"the prose no longer names {name}; this check went vacuous rather "
            f"than failing, which is the shape it exists to catch")
        assert name in declared, f"the prose names {name}, the model does not declare it"


def test_the_engine_strings_the_prose_quotes_are_strings_a_run_emits(
        state_matrix) -> None:
    """`too few state observations` is a `detail` and `insufficient_samples` is a
    `reason`; they sit on the same row under different keys. Quoting one and
    grepping the other is how three separate checks came back empty during this
    repair, each reading as the behaviour being absent."""
    rows = state_matrix[(36, True)]["status_rows"]
    assert rows, "no status declines to check against; the fixture stopped exercising this"
    reasons = {r["reason"] for r in rows}
    details = {(r.get("detail") or "") for r in rows}
    assert "`insufficient_samples`" in FINDINGS, "the prose stopped quoting the reason"
    assert "insufficient_samples" in reasons, "the engine stopped emitting that reason"
    assert "too few state observations" in FINDINGS, "the prose stopped quoting the detail"
    assert any("too few state observations" in d for d in details), (
        "the engine stopped emitting that detail, or it moved to another key")


# --- F1's numbers, and the condition FINDINGS.md leaves out ----------------

@pytest.fixture(scope="module")
def state_matrix():
    """Four runs: state reaching the engine or withheld, at one capture and at
    thirty-six. Withholding reproduces the defect F1 reports, by feeding only
    `values` the way the feeder did before `_fed` carried state."""
    import sys
    sys.path.insert(0, str(ROOT / "battery"))
    from operating_health_audit import capture as cap, feeder
    import make_series

    base = cap.load(CAPTURE)
    out = {}
    for count in (1, 36):
        for withhold in (True, False):
            original = feeder._fed
            if withhold:
                feeder._fed = lambda p: dict(getattr(p, "values", {}) or {})
            try:
                res = feeder.run(str(MODEL),
                                 make_series.series(base, count, transition=count > 1))
            finally:
                feeder._fed = original
            out[(count, withhold)] = {
                "findings": res["findings"],
                "status_rows": [d for d in res["not_checked"]
                                if d.get("indicator") == "status"],
                "bad": [f for f in res["findings"]
                        if "declared_bad_state" in f.get("problem_type", "")],
            }
    return out


def test_f1_the_nine_status_indicators_decline_for_ever_when_state_is_withheld(
        state_matrix) -> None:
    """The load-bearing half. Nine is a shortage at one capture and is the DEFECT at
    thirty-six, where feeding the same series answers all nine. A test asserting
    only the count at one capture would pass while the defect was fixed."""
    assert len(state_matrix[(1, True)]["status_rows"]) == 9
    assert len(state_matrix[(36, True)]["status_rows"]) == 9, (
        "thirty-six captures still declined; that is what for ever means")
    assert len(state_matrix[(36, False)]["status_rows"]) == 0, (
        "feeding state must answer all nine, or the workaround is not working")


def test_f1_the_four_bad_states_appear_at_one_capture_and_not_at_thirty_six(
        state_matrix) -> None:
    """The condition FINDINGS.md does not state. Reproducing F1 at thirty-six
    captures returns zero, because the generator walks each unit off its bad state
    -- a true finding that reads as refuted when replayed at the wrong length."""
    assert len(state_matrix[(1, False)]["bad"]) == 4
    assert len(state_matrix[(1, True)]["bad"]) == 0, (
        "withholding state must hide all four, or they came from somewhere else")
    assert len(state_matrix[(36, False)]["bad"]) == 0, (
        "the transition walk is expected to clear the bad states by thirty-six")


def test_f1_feeding_state_is_what_moves_seven_findings_to_eleven(
        state_matrix) -> None:
    """The headline arithmetic, which FINDINGS.md and docs/burn-in.md both state."""
    assert len(state_matrix[(1, True)]["findings"]) == 7
    assert len(state_matrix[(1, False)]["findings"]) == 11
