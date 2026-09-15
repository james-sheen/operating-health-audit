"""The command line. Every verb prints JSON and returns this package's code.

0 clean, 1 findings, 2 could-not-complete -- and the third is never reached by
accident: an unreadable declaration, an unloadable model and a missing engine
all arrive here as their own exception type and leave as 2 with a sentence
saying which, rather than as a traceback exiting 1.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Mapping, Sequence

from . import exit_contract as x
from . import capture as _capture
from . import declarations as _declarations
from . import presence as _presence
from . import regression as _regression


def _emit(payload: Mapping[str, Any]) -> int:
    print(json.dumps(payload, indent=1, default=str))
    return int(payload.get("exit_code", x.INCOMPLETE))


def _could_not(message: str) -> int:
    print(json.dumps({"exit_code": x.INCOMPLETE, "could_not_run": message}, indent=1))
    return x.INCOMPLETE


def cmd_declare(args) -> int:
    try:
        decl = _declarations.load(args.declaration)
    except _declarations.DeclarationError as problem:
        return _could_not(str(problem))
    kinds: dict[str, int] = {}
    for unit in decl.points:
        kinds[unit.unit_type] = kinds.get(unit.unit_type, 0) + 1
    return _emit({
        "declared": len(decl.points), "by_type": dict(sorted(kinds.items())),
        "sources": list(decl.sources), "anomalies": list(decl.anomalies),
        "unreadable": list(decl.unreadable),
        "reviewed": decl.reviewed,
        "reviewed_note": "" if decl.reviewed else
            "a declaration nobody signed is a draft; both a name and a date are needed",
        # Anomalies are rows that were READ AND NOT USABLE. They are a finding,
        # not a warning: a row dropped quietly makes every later count agree
        # with itself about a declaration that is smaller than the document.
        "exit_code": x.FINDINGS if decl.anomalies or decl.unreadable else x.CLEAN,
    })


def cmd_capture(args) -> int:
    try:
        export = _capture.from_csv(args.source, complete=not args.partial)
    except (_capture.CaptureError, OSError) as problem:
        return _could_not(str(problem))
    _capture.write(export, args.out)
    return _emit({"wrote": args.out, "units": len(export.points),
                  "complete": export.complete, "exit_code": x.CLEAN})


def _load_pair(declaration: str, capture_path: str):
    return _declarations.load(declaration), _capture.load(capture_path)


def cmd_presence(args) -> int:
    try:
        decl, export = _load_pair(args.declaration, args.capture)
    except (_declarations.DeclarationError, _capture.CaptureError) as problem:
        return _could_not(str(problem))
    return _emit(_presence.run(decl, export, require_complete=args.require_complete))


def cmd_regression(args) -> int:
    try:
        before, after = _capture.load(args.before), _capture.load(args.after)
    except _capture.CaptureError as problem:
        return _could_not(str(problem))
    return _emit(_regression.run(before, after, require_complete=args.require_complete))


def cmd_detect(args) -> int:
    from . import feeder
    try:
        captures = [_capture.load(p) for p in args.captures]
    except _capture.CaptureError as problem:
        return _could_not(str(problem))
    try:
        return _emit(feeder.run(args.model, captures))
    except (feeder.EngineUnavailable, feeder.ModelUnreadable) as problem:
        return _could_not(str(problem))


def cmd_gate(args) -> int:
    """Refuse what is not ready, by name. Run before a release, and before
    believing a clean presence run: a declaration nobody signed and an export
    nobody marked complete both produce confident output."""
    problems = []
    try:
        decl = _declarations.load(args.declaration)
        if not decl.reviewed:
            problems.append("the declaration is unsigned, so it is a draft")
        if decl.anomalies:
            problems.append(f"{len(decl.anomalies)} declared row(s) could not be used")
        if not decl.points:
            problems.append("the declaration names no units, and an empty one "
                            "reports the same as a complete one about an empty org")
    except _declarations.DeclarationError as problem:
        problems.append(str(problem))
    if args.capture:
        try:
            export = _capture.load(args.capture)
            if not export.complete:
                problems.append("the export is not marked complete, so an absence "
                                "in it is unattributable")
        except _capture.CaptureError as problem:
            problems.append(str(problem))
    return _emit({"ready": not problems, "refused_because": problems,
                  "exit_code": x.INCOMPLETE if problems else x.CLEAN})


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="operating-health-audit", description=__doc__)
    verbs = ap.add_subparsers(dest="verb", required=True)

    d = verbs.add_parser("declare", help="what the operating model claims")
    d.add_argument("declaration")
    d.set_defaults(run=cmd_declare)

    c = verbs.add_parser("capture", help="produce an export from a wide CSV")
    c.add_argument("source"); c.add_argument("--out", required=True)
    c.add_argument("--partial", action="store_true",
                   help="mark the export incomplete, which it is unless the "
                        "exporter knows every unit reported")
    c.set_defaults(run=cmd_capture)

    p = verbs.add_parser("presence", help="the three-valued answer")
    p.add_argument("declaration"); p.add_argument("capture")
    p.add_argument("--require-complete", action="store_true")
    p.set_defaults(run=cmd_presence)

    r = verbs.add_parser("regression", help="two exports, compared directly")
    r.add_argument("before"); r.add_argument("after")
    r.add_argument("--require-complete", action="store_true")
    r.set_defaults(run=cmd_regression)

    t = verbs.add_parser("detect", help="feed a series of captures to the engine")
    t.add_argument("model"); t.add_argument("captures", nargs="+")
    t.set_defaults(run=cmd_detect)

    g = verbs.add_parser("gate", help="refuse what is not ready, by name")
    g.add_argument("declaration"); g.add_argument("--capture")
    g.set_defaults(run=cmd_gate)
    return ap


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
