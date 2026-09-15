"""Build a series of captures from one baseline, for measuring the burn-in.

NOT A SIMULATION OF AN ORGANISATION. Every value is derived from the baseline by
a declared rule, and the rules are here in the open so a reader can see that the
series was constructed rather than observed. Its one job is to answer *at how
many captures does each axiom arm start answering*, which is a fact about the
ENGINE and not about any organisation.

The drift is deliberately dull: a small deterministic walk, no randomness, so
the sweep is reproducible and a changed floor shows up as a changed number
rather than as noise. `Math.random` style jitter would make the burn-in figure
different on every run, which is the opposite of what a published floor needs.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from operating_health_audit import capture as cap  # noqa: E402

#: A month between captures, matching the model's declared reporting cadence.
STEP = timedelta(days=30)


#: States a unit is walked through when `transition` is asked for, per declared
#: type. Taken from the model's own `normal:`/`transient:`/`bad:` sets: a series
#: that invents a state the model never declared would exercise the classifier
#: rather than the axiom.
STATE_CYCLES = {
    "Division": ("healthy", "restructuring", "declining", "healthy"),
    "Department": ("healthy", "restructuring", "critical", "healthy"),
    "Project": ("on_track", "at_risk", "delayed", "on_track"),
}


def series(baseline: cap.Export, count: int, *, transition: bool = False) -> list[cap.Export]:
    """`count` captures, the first being the baseline itself.

    Each later capture moves every numeric by a fixed small fraction of its own
    starting value, in a direction fixed by the indicator name's hash -- fixed,
    not random, so two runs agree.

    `transition` walks each unit's STATE around its declared cycle. Off by
    default, and that default is the honest one: a constant state is what a
    quiet organisation exports, and STABILITY declining `too few state
    observations` against it is the correct answer rather than a gap. Turning it
    on is how the STABILITY arm gets exercised at all -- measured, a constant
    series leaves nine `status` indicators declining for ever however many
    captures are fed.
    """
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    out = []
    for step in range(count):
        when = (start + STEP * step).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        points = []
        for point in baseline.points:
            values = {}
            for name, value in point.values.items():
                direction = 1 if (sum(map(ord, name)) % 2) else -1
                values[name] = round(value * (1 + direction * 0.01 * step), 4)
            state = point.state
            if transition and state is not None:
                cycle = STATE_CYCLES.get(point.unit_type)
                if cycle:
                    state = cycle[step % len(cycle)]
            points.append(cap.Reading(
                name=point.name, unit_type=point.unit_type, path=point.path,
                values=values, state=state, edges=dict(point.edges)))
        out.append(cap.Export(points=tuple(points), captured_at=when,
                              complete=True, source=f"{baseline.source}#step{step}"))
    return out
