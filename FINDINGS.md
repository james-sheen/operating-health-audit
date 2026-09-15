# Findings

What building this vertical found, in the two upstreams and in itself. Each was
produced by RUNNING something; none came from reading code, and three of them
contradicted what reading had already concluded: F2, F7, and the claim withdrawn
at the end.

## In `arbiter-engine` 0.1.14

**F1. The session cannot feed a state series, and the engine reads one.**
`EngineSession.add_observations` casts every sample with `float(value)`, so a
state raises `ValueError`. `InMemoryObservationHistory.add` takes `value: Any`
and accepts one. The engine declares a `state` indicator type, `STABILITY`
branches on it, and reads state history out of exactly that store — so a
consumer following the front door can satisfy the numeric axioms and not the
state half of STABILITY. This is the same asymmetry the engine's own
`add_relationship` docstring describes for the third input kind, repeating for
the fourth.

*Cost here*: nine `status` indicators declined `too few state observations` for
ever, and walking every unit around its declared state cycle changed nothing at
all. Feeding state directly produced four `declared_bad_state` findings — so
before it, this package was **clean about the four worst units in the
organisation**. A gap in a feeder looks exactly like a quiet organisation.

*Worked around* in `feeder._add_state_series`, which writes to the public
`session.history`. When a state feeder lands, that function goes.

**F2. HOMEOSTASIS answers nothing at a monthly cadence through the documented
entry point.** It reads `homeostasis_baseline_days`, defaulted to 7, and ignores
the indicator's `window:` — 21 declines at 1 capture and 21 at 30, at every
window tried. At a monthly cadence the baseline admits about one sample, so the
decline is `insufficient_samples` whatever the data does.

*This finding once read that nothing reachable closes it. That was wrong.*
`UnifiedAxiomReasoner(params=AxiomParameters(homeostasis_baseline_days=2000))`
is public, is re-exported from `arbiter_engine.api`, and measured on 0.1.14 it
works: a steady series comes back clean, and a margin falling from 11% to 2%
over five monthly captures comes back `homeostasis_warning`. Two routes were
checked and neither is the way in — `axiom_parameters` occurs once in the
published package, inside a docstring, so no domain file can set it, and
`set_threshold_override` reaches the z-scores and not the baseline window, per
the engine's own `OVERRIDE_CONSULTED_BY`. From those two the finding concluded
there was no route at all.

What is genuinely unreachable is narrower. `EngineSession.__init__` takes no
arguments and `load_model` constructs `UnifiedAxiomReasoner()` with none, so
reaching the parameter means rebuilding the reasoner and replacing
`session.reasoner`. **That is F1 again** — the session dropping a capability the
layer beneath it has, a state series there and an `AxiomParameters` here, each
with a working back door. One upstream ask, not two.

**F3. The window defaults to one hour and is a ceiling, and nothing says so at
the point of use.** Undeclared, 36 monthly captures produce byte-identical
declines to a single snapshot: the whole series falls outside. The decline is
`insufficient_samples`, which reads as *keep collecting* when the truth is
*nothing you collect will ever count*. The record does carry `window_seconds`,
which is how this was found — by reading the number in a decline rather than
trusting the word.

## In the domain the Core was tested with

**F4. One declared pair could not evaluate under any input**, and the engine
reported it unprompted on load: `throughput/RESPONSIVENESS`, because
RESPONSIVENESS is role-gated to `latency` and no role was declared. This model
moves RESPONSIVENESS to `cycle_time_days`, which is the actual latency.

**F5. Five relationship types were declared and none was checked.**
`REPORTS_TO`, `OWNS`, `LEADS`, `DEPENDS_ON`, `FUNDS` were all declared and no
indicator referenced any. A relationship type nothing checks is a comment. This
model declares CONNECTIVITY over the org structure, which answers from one
capture and is most of the day-one value.

**F6. The case study ships no relationships at all.** Its CSV is a flat table of
units. Audited as it ships, all fourteen units come back detached — which is the
correct answer about that export, and the reason
`examples/acme.capture.asshipped.json` is kept beside the structured one.

## In this package

**F7. A unit's state was read as its only reading.** A wide export carries a
status column for some unit types and not others, so three Executives and two
Processes — every one reporting a tenure, a span, a rating or a cycle time —
came back `declared_unreadable`. Five units reporting, five reported silent, and
the presence run looked like a real finding. The comment asserting that
executives report no quantity of their own was simply false.

**F8. Windows sized to the floor were too small.** Sized at floor x cadence, a
longer series overruns the window and the history goes stale. 12 findings sized
to the floors; 18 at a generous ceiling. The window has to span the series, not
the floor.

**F9. A test asserted the wrong contract.** It read the core protocol's *unioned
with the core's set* as a claim about `regression_kinds()`, which returns the
domain's own kinds and nothing else. The union happens in `Finding.is_regression`.
Rewritten to assert it there, and it now also checks the core's seven kinds still
score — the half a vertical could actually break.

## A claim this project made and had to withdraw

**Reading `AXIOM_MINIMUMS` and concluding that nothing can answer from a single
snapshot.** Stated in the model's own header before anything was run. Measured,
one capture of fourteen units produces eleven findings, because BOUNDEDNESS
evaluates a declared bound against the current value and the floor governs only
the arm that needs a history. 103 invariants are checked, not zero.

The constant was real and the conclusion drawn from it was not. It is recorded
here rather than quietly corrected because the shape recurs: a number read out
of a package is not a behaviour, and the run is the only thing that settles
which.

**It recurred, in F2 above.** `homeostasis_baseline_days: int = 7` and
`OVERRIDE_CONSULTED_BY` were both read correctly, and the conclusion drawn from
them — that no route reached the baseline — was refuted by a three-line run. The
first instance read a constant and inferred a behaviour; this one enumerated two
routes and inferred the absence of a third. Enumerating is still reading.
