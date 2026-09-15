"""This domain, offered to the shared core as a registered vertical.

All sixteen members are answered rather than left to default: a report printing
`point` for a division is a report in somebody else's noun.

WHAT ONLY THIS DOMAIN CAN SEE. An operating model is mostly a set of claims
about structure -- who reports into whom, who leads what, what funds what. A
department that is present, enabled and reporting healthy numbers while reporting
into nothing is invisible to every structural test the core applies, because the
core pairs a declaration against a capture by NAME and this unit is present under
its name. It arrives through `capture_findings`, and because the core's exit code
scores only its own regression kinds, it is scored by this package's exit
contract instead.

THE SAME ADDRESS IS NOT THE SAME UNIT. `same_point` compares type as well as
name. An organisation that retires a department and stands up a project under the
same identifier has not kept a unit; it has replaced one. Answering yes there
would report continuity across a reorganisation, which is the single thing an
operating review is most often run to find.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from presence_audit.diff import Finding
from presence_audit.regression import Change

#: Every class a declared unit can fall into. `unrecognised` is last and is not
#: a type anything declares: it is where a type this vocabulary does not know
#: goes, counted and reported and never asserted about.
KINDS = ("division", "department", "executive", "project", "process", "unrecognised")

#: The kinds the audit is about. All five real ones -- an operating model that
#: audited only its departments would be answering a smaller question than the
#: one it was handed. Said out loud rather than done by omission.
AUDITED = ("division", "department", "executive", "project", "process")

#: Declared type -> kind. A dict rather than `.lower()`, because lowercasing is
#: a rule about spelling and this is a rule about membership: a type this
#: vocabulary has never heard of must land on `unrecognised` rather than on a
#: lowercase version of itself that no later check will match.
_BY_TYPE = {"Division": "division", "Department": "department",
            "Executive": "executive", "Project": "project", "Process": "process"}

#: Every declared unit type is expected to report. Narrower first, excluding
#: Executive, and the case study refuted it: executives report a tenure, a span
#: and a rating, and the model declares MONOTONICITY, BOUNDEDNESS, HOMEOSTASIS
#: and STABILITY across them. What executives lack is a STATUS column, which is
#: a fact about the export's shape and not about the unit.
_EXPECTED_LIVE = ("Division", "Department", "Executive", "Project", "Process")

#: The relationship each unit type is declared to have. One place, because the
#: model declares the same pairing for CONNECTIVITY and the two disagreeing
#: would mean Stage 1 and Stage 2 reporting different structures.
REQUIRED_EDGE = {"division": "reports_to", "department": "reports_to",
                 "executive": "leads", "project": "funds", "process": "depends_on"}


class OperatingVocabulary:
    """The sixteen members, for the units of an operating model."""

    def __init__(self, declared_types: Mapping[str, str] | None = None) -> None:
        #: Declared name -> declared type, supplied at registration. The
        #: protocol hands `capture_findings` the capture alone, and a captured
        #: row carries the type its EXPORTER wrote, which is not necessarily the
        #: type the organisation DECLARED. Without the declaration a finding
        #: about a mis-structured unit fires on the exporter's word for it.
        self._declared_types = dict(declared_types or {})

    # --- classification ----------------------------------------------------
    @property
    def kinds(self) -> Sequence[str]:
        return KINDS

    @property
    def count_keys(self) -> Mapping[str, str]:
        return {k: f"{k}s" for k in AUDITED}

    def classify(self, declared_type: str | None) -> str:
        return _BY_TYPE.get(declared_type or "", "unrecognised")

    def is_auditable(self, kind: str) -> bool:
        return kind in AUDITED

    def is_expected_live(self, declared_type: str | None) -> bool:
        return (declared_type or "") in _EXPECTED_LIVE

    def template_pattern(self, declared_name: str) -> object:
        """Always None. An operating model names the actual division; there is
        no wildcard row to expand, and returning a match-anything pattern for an
        unrecognised variable is how a declaration stops being able to report an
        absence."""
        return None

    # --- pairing -----------------------------------------------------------
    def same_point(self, old: object, new: object) -> bool:
        old_type = getattr(old, "unit_type", None)
        new_type = getattr(new, "unit_type", None)
        if old_type and new_type and old_type != new_type:
            return False
        return True

    def captures_comparable(self, before: object, after: object) -> bool:
        """Both complete, or the per-unit comparisons are SKIPPED. A partial
        export and a shrunken organisation are the same points list."""
        return bool(getattr(before, "complete", False)) and bool(getattr(after, "complete", False))

    # --- what changed ------------------------------------------------------
    def point_changes(self, old: object, new: object, *,
                      comparable: bool = False) -> Sequence[object]:
        if not comparable:
            return ()
        changes = []
        was, now = getattr(old, "state", None), getattr(new, "state", None)
        if was != now and (was or now):
            changes.append(Change(kind="state_changed", sensor=getattr(new, "name", ""),
                                  detail=f"state moved from {was!r} to {now!r}",
                                  before_path=getattr(old, "path", ""),
                                  after_path=getattr(new, "path", "")))
        before_edges = dict(getattr(old, "edges", {}) or {})
        after_edges = dict(getattr(new, "edges", {}) or {})
        for relation, target in before_edges.items():
            if relation not in after_edges:
                changes.append(Change(
                    kind="edge_lost", sensor=getattr(new, "name", ""),
                    detail=f"{relation} to {target!r} is no longer reported, so this "
                           f"unit reports into nothing by that relation",
                    before_path=getattr(old, "path", ""),
                    after_path=getattr(new, "path", "")))
            elif after_edges[relation] != target:
                changes.append(Change(
                    kind="edge_moved", sensor=getattr(new, "name", ""),
                    detail=f"{relation} moved from {target!r} to {after_edges[relation]!r}",
                    before_path=getattr(old, "path", ""),
                    after_path=getattr(new, "path", "")))
        lost = sorted(set(getattr(old, "values", {}) or {}) - set(getattr(new, "values", {}) or {}))
        if lost:
            changes.append(Change(
                kind="indicator_stopped_reporting", sensor=getattr(new, "name", ""),
                detail=f"stopped reporting {', '.join(lost)}; the unit is still present, "
                       f"so this is a gap in the export rather than in the organisation",
                before_path=getattr(old, "path", ""), after_path=getattr(new, "path", "")))
        return tuple(changes)

    def capture_changes(self, before: object, after: object) -> Sequence[object]:
        if bool(getattr(before, "complete", False)) and not bool(getattr(after, "complete", False)):
            return (Change(kind="export_became_partial", sensor="",
                           detail="the later export is not complete, so every absence in "
                                  "it is unattributable between the organisation and the "
                                  "exporter", before_path="", after_path=""),)
        return ()

    # --- what only this domain sees ----------------------------------------
    def capture_findings(self, capture: object, *, declaration: object = None) -> Sequence[object]:
        """A unit that is present and reporting and structurally detached.

        Invisible to the core: it is declared, it is matched, it is enabled and
        it has a reading. Nothing about the pairing is wrong. What is wrong is
        that it reports into nothing, and only this domain knows which relation
        each kind of unit is supposed to have.
        """
        declared = dict(self._declared_types)
        if declaration is not None:
            declared.update({getattr(p, "name", ""): getattr(p, "unit_type", "")
                             for p in getattr(declaration, "points", ()) or ()})
        findings = []
        for point in getattr(capture, "points", ()) or ():
            name = getattr(point, "name", "")
            # The DECLARED type governs. A row the exporter called a Project and
            # the organisation declared a Process is judged as a Process.
            kind = self.classify(declared.get(name) or getattr(point, "unit_type", None))
            if kind not in AUDITED:
                continue
            wanted = REQUIRED_EDGE.get(kind)
            edges = dict(getattr(point, "edges", {}) or {})
            if wanted and wanted not in edges:
                findings.append(Finding(
                    kind="detached_unit", sensor=name,
                    detail=f"present and reporting, and declares no {wanted}; a "
                           f"{kind} that reports into nothing is either dissolved or "
                           f"mis-exported, and the export cannot say which",
                    declared_in="", live_path=getattr(point, "path", "")))
        return tuple(findings)

    def peer_groups(self, declaration: object) -> Sequence[Mapping[str, object]]:
        """Empty, and deliberately. Two departments under one division are not
        redundant readings of one thing -- they are two departments. This domain
        has no notion of a second instrument on the same quantity, and inventing
        one would make the generator pair units that merely sit together."""
        return ()

    # --- the domain's words ------------------------------------------------
    @property
    def noun(self) -> Sequence[str]:
        return ("operating unit", "operating units")

    def count_labels(self) -> Mapping[str, Sequence[str]]:
        return {
            "divisions": ("Divisions", ""),
            "departments": ("Departments", ""),
            "executives": ("Executives", "tenure, span of control and rating"),
            "projects": ("Projects", ""),
            "processes": ("Processes", ""),
        }

    def regression_kinds(self) -> Sequence[str]:
        """Which of this domain's own kinds are regressions.

        `state_changed` is NOT one: a state moving is what an operating review
        reports on, and in the improving direction it is the good news. Whether a
        particular state is bad is the engine's judgement at Stage 2, against the
        `bad:` set the model declares -- deciding it here would put the same rule
        in two places with nothing keeping them equal.
        """
        return ("detached_unit", "edge_lost", "indicator_stopped_reporting",
                "export_became_partial")

    def report_sections(self) -> Mapping[str, object]:
        return {"structure": _structure}


def _structure(capture: object) -> Mapping[str, Any]:
    """The reporting lines actually present, counted by relation. A reader
    asking *did the org chart change* gets an answer without reading every
    unit."""
    by_relation: dict[str, int] = {}
    detached = []
    for point in getattr(capture, "points", ()) or ():
        edges = dict(getattr(point, "edges", {}) or {})
        for relation in edges:
            by_relation[relation] = by_relation.get(relation, 0) + 1
        if not edges:
            detached.append(getattr(point, "name", ""))
    return {"edges_by_relation": dict(sorted(by_relation.items())),
            "units_with_no_edge": sorted(detached)}


def register() -> str:
    from presence_audit import vocabulary as _vocabulary
    _vocabulary.register(OperatingVocabulary())
    return "operating-health: operating units and the lines between them"
