"""The vocabulary, against the contract and against this domain's own traps."""
from __future__ import annotations

import subprocess
import sys

from conftest import ROOT
from operating_health_audit import capture as _capture
from operating_health_audit.vertical import AUDITED, KINDS, OperatingVocabulary


def test_the_core_conformance_kit_passes() -> None:
    """The kit the core ships, run as a consumer runs it. A green means nothing
    reached past the contract -- not that the contract is enough for this
    domain, which is what the rest of this file is for."""
    done = subprocess.run(
        [sys.executable, "-m", "presence_audit.conformance",
         "operating_health_audit.vertical:register"],
        capture_output=True, text=True, cwd=str(ROOT),
        env={"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin"})
    assert done.returncode == 0, done.stdout + done.stderr
    assert "answers the protocol correctly" in done.stdout


def test_every_member_the_protocol_declares_is_answered() -> None:
    """Derived from the protocol rather than listed, so a sixteenth member
    added upstream fails here instead of falling to a default this domain never
    chose. A vertical that defaults a member is a report in somebody else's
    noun."""
    from presence_audit.vocabulary import Vocabulary

    declared = {n for n in dir(Vocabulary) if not n.startswith("_")}
    assert len(declared) >= 16, f"the protocol offered {len(declared)} members"
    missing = sorted(n for n in declared if not hasattr(OperatingVocabulary(), n))
    assert missing == [], f"{missing} are not answered by this vertical"


def test_classify_never_answers_outside_its_own_kinds() -> None:
    v = OperatingVocabulary()
    for declared in ("Division", "Department", "Executive", "Project", "Process",
                     "Wombat", None, "", "division"):
        assert v.classify(declared) in KINDS
    assert v.classify("Wombat") == "unrecognised"
    assert v.classify("division") == "unrecognised", (
        "lowercasing is a rule about SPELLING; membership is the question here, "
        "and a type nobody declared must not become a type nobody checks")


def test_a_unit_replaced_at_the_same_address_is_not_the_same_unit() -> None:
    """The finding an operating review is most often run to get. An organisation
    that retires a department and stands a project up under the same identifier
    has replaced a unit, not kept one -- and answering yes here reports
    continuity across a reorganisation."""
    v = OperatingVocabulary()
    was = _capture.Reading(name="dept-sales", unit_type="Department")
    still = _capture.Reading(name="dept-sales", unit_type="Department")
    now = _capture.Reading(name="dept-sales", unit_type="Project")
    assert v.same_point(was, still) is True
    assert v.same_point(was, now) is False


def test_an_incomplete_export_skips_the_per_unit_comparisons_and_says_so() -> None:
    """False means SKIPPED, never *ran and found nothing*."""
    from operating_health_audit import regression

    v = OperatingVocabulary()
    whole = _capture.Export(points=(), complete=True)
    partial = _capture.Export(points=(), complete=False)
    assert v.captures_comparable(whole, whole) is True
    assert v.captures_comparable(whole, partial) is False
    out = regression.run(whole, partial)
    assert out["per_unit_comparisons"].startswith("skipped")


def test_a_detached_unit_is_judged_by_its_declared_type_not_the_exporters() -> None:
    """A row the exporter called a Project and the organisation declared a
    Process is judged as a Process, and the relation it needs is the Process
    one. Without the declaration the finding fires on the exporter's word."""
    v = OperatingVocabulary({"thing": "Process"})
    export = _capture.Export(points=(_capture.Reading(
        name="thing", unit_type="Project", edges={"funds": "div-a"}),), complete=True)
    found = v.capture_findings(export)
    assert [f.kind for f in found] == ["detached_unit"], (
        "declared a Process, it needs a depends_on; it has the funds edge a "
        "Project needs, and judged as a Project it would look fine")
    assert "depends_on" in found[0].detail


def test_every_audited_kind_has_a_required_relation() -> None:
    """A kind with no required relation can never be detached, so it silently
    opts out of the one finding only this domain can see."""
    from operating_health_audit.vertical import REQUIRED_EDGE

    assert sorted(REQUIRED_EDGE) == sorted(AUDITED)


def test_this_domains_kinds_are_scored_without_displacing_the_cores() -> None:
    """A vocabulary may say which of ITS kinds count. It may not decide that a
    declared-and-absent unit does not.

    Asserted through `Finding.is_regression`, which is WHERE the union happens.
    The module-level `regression_kinds()` returns the domain's own set and
    nothing else -- by design, and its docstring says so. Reading the protocol's
    *unioned with the core's* as a claim about that accessor is what this test
    asserted first, and the accessor refuted it.
    """
    from presence_audit import vocabulary as voc
    from presence_audit.diff import REGRESSION_KINDS, Finding

    v = OperatingVocabulary()
    assert "detached_unit" in v.regression_kinds()
    assert "state_changed" not in v.regression_kinds(), (
        "a state moving is the engine's judgement at Stage 2, not a regression here")

    with voc.using(v):
        # the domain's own kind scores...
        assert Finding(kind="detached_unit", sensor="d", detail="",
                       declared_in="", live_path="").is_regression
        # ...and the core's still do, which is the half a vertical could break
        for kind in sorted(REGRESSION_KINDS):
            assert Finding(kind=kind, sensor="d", detail="", declared_in="",
                           live_path="").is_regression, (
                f"{kind} stopped scoring once this vertical supplied its own set")
        # and something neither of them names still does not
        assert not Finding(kind="edge_moved", sensor="d", detail="",
                           declared_in="", live_path="").is_regression


def test_the_noun_is_this_domains_word() -> None:
    assert OperatingVocabulary().noun == ("operating unit", "operating units")


def test_the_version_literal_and_pyproject_agree() -> None:
    """Two copies of one number drift, and a release is exactly when nobody is
    looking."""
    import re

    import operating_health_audit as pkg

    text = (ROOT / "pyproject.toml").read_text()
    declared = re.search(r'^version = "([^"]+)"', text, re.M)
    assert declared, "pyproject declares no version"
    assert declared.group(1) == pkg.__version__
