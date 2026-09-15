"""Paths, and the rule that an upstream-dependent test FAILS rather than skips.

A skip is how a check stops running without anybody noticing. Every test here
that needs `presence-audit` or `arbiter-engine` imports it inside the test, so
its absence is a red with a sentence rather than a quiet pass.
"""
from __future__ import annotations

import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
DECLARATION = EXAMPLES / "operating.declaration.json"
MODEL = EXAMPLES / "operating.model.yaml"
CAPTURE = EXAMPLES / "acme.capture.json"
AS_SHIPPED = EXAMPLES / "acme.capture.asshipped.json"


@pytest.fixture()
def declaration():
    from operating_health_audit import declarations
    return declarations.load(DECLARATION)


@pytest.fixture()
def export():
    from operating_health_audit import capture
    return capture.load(CAPTURE)
