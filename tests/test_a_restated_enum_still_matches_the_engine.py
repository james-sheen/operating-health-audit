"""The core restates the engine's response-model set, and nothing compared them.

`presence-audit` names the four response models a `couplings:` entry may
declare. It restates them rather than importing them, because Stage 1 does not
depend on the engine and is not going to: the whole point of the split is that
a presence audit answers without one installed.

A restated DEFAULT drifts a number. A restated CLOSED ENUM is worse in both
directions -- it refuses a value the engine accepts, or accepts one the engine
has never heard of -- and the first draft of that tuple, written from memory,
managed both at once: it invented a member and omitted two.

WHY THE TEST LIVES HERE AND NOT IN THE CORE. A guard in `presence-audit` would
have to reach for the engine, which is an optional dependency there, so it
would be written with `importorskip` -- and that repository's CI fails on any
skip, for a stated reason: a skipped test that adapts a really published
implementation is a test that went unrun, and its absence is invisible in a
green run. The core therefore checks only that its own set is closed and that
its loader admits exactly it.

This package pins BOTH, and its `suite` job installs `.[detect]`, so both
imports resolve and this file runs unskipped on all five interpreters. That is
where the oracle spans: one side is the restatement, the other is the thing
restated.

WHAT THIS FILE DOES NOT CLAIM. The engine does not ENFORCE its own enum. A
`response_model:` it does not recognise is swallowed and treated as
exponential, with no decline -- measured 2026-09-24 on the shipped
`pump_tank_planning` model, where `sigmoid`, `EXPONENTIAL` and the empty
string all scored identically to `exponential` while `linear` scored
differently. So the core is STRICTER than the engine by design, and the
assertion below is about the two VOCABULARIES agreeing, not about the engine
rejecting what falls outside its own.
"""

from presence_audit.supplemental import RESPONSE_MODELS

#: Deep import, deliberately and with its eyes open. `ResponseModel` is not on
#: the engine's curated top-level surface, which is precisely why a downstream
#: restatement of it can drift unnoticed -- a supported export would be watched
#: by the engine's own departure check. If this import breaks, the restatement
#: has lost the thing it restates, and that is a finding rather than an
#: inconvenience.
from arbiter_engine.temporal.temporal_edge import ResponseModel


def _engine_set():
    return {member.value for member in ResponseModel}


class TestTheRestatementMatchesTheEngine:

    def test_the_two_sets_are_equal(self):
        core, engine = set(RESPONSE_MODELS), _engine_set()
        assert core == engine, (
            f"the core restates {sorted(core)} and the engine declares "
            f"{sorted(engine)}; only in the core: {sorted(core - engine)}, "
            f"only in the engine: {sorted(engine - core)}. A restated closed "
            f"enum has drifted -- fix the restatement, not this test")

    def test_neither_side_is_empty(self):
        """The floor. Two empty sets are equal, and would pass the test above
        while comparing nothing at all."""
        assert RESPONSE_MODELS, "the core's restatement is empty"
        assert _engine_set(), "the engine declares no response models"

    def test_the_core_keeps_a_tuple_not_a_set(self):
        """The order is the core's published order and a consumer may rely on
        it; the comparison above deliberately does not."""
        assert isinstance(RESPONSE_MODELS, tuple)
        assert len(RESPONSE_MODELS) == len(set(RESPONSE_MODELS)), (
            "a duplicate in the restatement would make the set comparison "
            "above pass while the published tuple says something else")


class TestThisFileRunsRatherThanSkips:
    """What is wanted is not that a test EXISTS but that it RUNS. The first
    attempt at this guard skipped when the engine was absent, which is the
    shape that makes a green suite uninformative."""

    def test_nothing_here_is_conditional_on_the_engine_being_present(self):
        """Asked of the PARSE TREE rather than the source text: a source grep
        for `skip` matches the word in this docstring."""
        import ast
        import pathlib
        tree = ast.parse(pathlib.Path(__file__).read_text())
        skips = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and (
                (isinstance(node.func, ast.Attribute)
                 and node.func.attr in {"skip", "importorskip", "skipif"})
                or (isinstance(node.func, ast.Name)
                    and node.func.id in {"skip", "importorskip"})
            )
        ]
        assert not skips, (
            "this file must fail when the engine is missing, not go quiet")

    def test_the_engine_import_is_top_level(self):
        """A deferred import inside a test would turn a missing engine into a
        collection-time pass for every other test in the file."""
        import ast
        import pathlib
        tree = ast.parse(pathlib.Path(__file__).read_text())
        top = {
            node.module for node in tree.body
            if isinstance(node, ast.ImportFrom) and node.module
        }
        assert "arbiter_engine.temporal.temporal_edge" in top
        assert "presence_audit.supplemental" in top
