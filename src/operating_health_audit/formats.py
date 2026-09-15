"""The format ids this package writes, and the ones it will read.

Two constants and not one string each, because a reader and a writer that spell
the same format differently agree until the day they do not. Versioned in the id
itself: a consumer pinning a range gets told by the id when the shape moved,
rather than discovering it in a KeyError.
"""

from __future__ import annotations

#: The target operating model: what the organisation says it runs.
DECLARATION_FORMAT = "operating-health-audit/declaration/1"

#: One periodic export of what is actually reporting.
CAPTURE_FORMAT = "operating-health-audit/capture/1"

#: The presence answer, and the regression answer.
PRESENCE_FORMAT = "operating-health-audit/presence/1"
REGRESSION_FORMAT = "operating-health-audit/regression/1"

#: Read as well as written. A capture written by an earlier minor version is
#: still readable; the set is pinned so a third cannot appear without somebody
#: saying why in this file.
ACCEPTED_CAPTURE_FORMATS = (CAPTURE_FORMAT,)
