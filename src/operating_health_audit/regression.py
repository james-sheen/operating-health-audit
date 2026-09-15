"""Stage 1, the other question: two exports compared directly.

No declaration is involved. This answers *what moved between these two* -- a
reporting line that vanished, a unit that stopped reporting a quantity, a state
that transitioned. A reorganisation shows up here and is reported rather than
scored; whether a state is bad is the engine's judgement at Stage 2.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from presence_audit import regression as _core, vocabulary as _vocabulary

from . import exit_contract as x
from .formats import REGRESSION_FORMAT
from .vertical import OperatingVocabulary


def run(before, after, *, prefix_map: Sequence[tuple[str, str]] = (),
        require_complete: bool = False) -> Mapping[str, Any]:
    vocab = OperatingVocabulary()
    with _vocabulary.using(vocab):
        report = _core.compare_walks(before, after, prefix_map=prefix_map)

    changes = list(report.changes)
    kinds = [c.kind for c in changes]
    comparable = vocab.captures_comparable(before, after)
    return {
        "format": REGRESSION_FORMAT,
        "before": getattr(before, "captured_at", ""),
        "after": getattr(after, "captured_at", ""),
        # SAID OUT LOUD. When the exports are not both complete the per-unit
        # comparisons are SKIPPED, and a reader who is not told that reads an
        # empty change list as *nothing moved*.
        "per_unit_comparisons": "ran" if comparable else
            "skipped: both exports must be complete, and at least one is not",
        "changes": [{"kind": c.kind, "unit": c.sensor, "detail": c.detail,
                     "before_path": getattr(c, "before_path", ""),
                     "after_path": getattr(c, "after_path", "")} for c in changes],
        "unclassified": list(x.unclassified(kinds)),
        "why": [{"kind": k, "floor": fl, "because": why} for k, fl, why in x.reasons(kinds)],
        "exit_code": x.code_for(kinds, require_complete=require_complete),
    }
