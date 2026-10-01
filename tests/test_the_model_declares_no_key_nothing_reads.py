"""The shipped model declares nothing that nothing on this path reads.

`plausible_range:` read as a range check on three executive indicators. The
engine reads no such key: it exempts it by name for a document-ingest pipeline
this package does not run. So the model promised a check that never ran, and two
shipped ratings sat outside the range it gave (FINDINGS F17). The key is checked
in the parsed model rather than its text, because the model's comment names it
to say why it is gone.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

MODEL = Path(__file__).resolve().parents[1] / "examples" / "operating.model.yaml"

#: Keys the engine accepts on an indicator and reads nothing with.
READ_BY_NOTHING_HERE = {"plausible_range"}


def test_no_indicator_declares_a_key_nothing_reads():
    domain = yaml.safe_load(MODEL.read_text(encoding="utf-8"))["domain"]
    declared = {(entity_type, spec.get("name"), key)
                for entity_type, specs in (domain.get("indicators") or {}).items()
                for spec in specs or () for key in spec
                if key in READ_BY_NOTHING_HERE}
    assert not declared, sorted(declared)
