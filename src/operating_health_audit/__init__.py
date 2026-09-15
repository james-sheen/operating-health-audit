"""Of the operating units a target operating model declares, which are present
and reporting, which are absent, and which appeared undeclared.

Stage 1 is the shared core and answers without the engine. Stage 2 is the engine
and judges the quantities. The exit contract is this package's own: 0 clean,
1 findings, 2 could-not-complete.
"""

from __future__ import annotations

__all__ = ["__version__", "DECLARATION_FORMAT", "CAPTURE_FORMAT"]

#: THE version literal. `pyproject.toml` does not read it from here today, so a
#: guard in the suite asserts the two agree -- two copies of one number drift,
#: and a release is exactly when nobody is looking.
__version__ = "0.1.0"

from .formats import CAPTURE_FORMAT, DECLARATION_FORMAT  # noqa: E402
