"""Stage 1: the declaration against one export, three-valued.

Declared and present, declared and absent, present and undeclared. The third is
the one a hardware walk treats as noise and an operating review is run to find:
a unit reporting that the operating model never declared is the shadow
organisation.
"""

from __future__ import annotations

from typing import Any, Mapping

from presence_audit import diff, vocabulary as _vocabulary

from . import exit_contract as x
from .formats import PRESENCE_FORMAT
from .vertical import OperatingVocabulary


def run(declaration, export, *, require_complete: bool = False) -> Mapping[str, Any]:
    """Compare, score, and say which kinds decided the code.

    The vocabulary is put in force for THIS CALL rather than registered
    globally, so two audits can run in one process without one deciding the
    other's nouns.
    """
    vocab = OperatingVocabulary({p.name: p.unit_type for p in declaration.points})
    with _vocabulary.using(vocab):
        report = diff.compare(declaration, export)
        extra = vocab.capture_findings(export, declaration=declaration)
        sections = {name: build(export) for name, build in vocab.report_sections().items()}

    findings = list(report.findings)
    seen = {(f.kind, f.sensor) for f in findings}
    findings.extend(f for f in extra if (f.kind, f.sensor) not in seen)

    kinds = [f.kind for f in findings]
    code = x.code_for(kinds, require_complete=require_complete)
    return {
        "format": PRESENCE_FORMAT,
        "captured_at": getattr(export, "captured_at", ""),
        "complete": bool(getattr(export, "complete", False)),
        "declared": len(declaration.points),
        "captured": len(getattr(export, "points", ()) or ()),
        "findings": [{"kind": f.kind, "unit": f.sensor, "detail": f.detail,
                      "declared_in": getattr(f, "declared_in", ""),
                      "path": getattr(f, "live_path", "")} for f in findings],
        "unclassified": list(x.unclassified(kinds)),
        "why": [{"kind": k, "floor": fl, "because": why} for k, fl, why in x.reasons(kinds)],
        "exit_code": code,
        **sections,
    }
