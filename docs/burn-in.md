# Burn-in: what this audit can answer, and after how many captures

Measured against `arbiter-engine` 0.1.14 and `presence-audit` 0.1.8 by running
`battery/make_series.py` over the shipped case study. Every number below is a
run, not a reading of a constant — the first draft of this document was written
from `types.AXIOM_MINIMUMS` and was wrong in both directions.

## The one-line answer

**Eleven findings from a single capture.** The audit is useful on day one. Three
arms need a history and one can never answer at a monthly cadence.

## The measured table

One capture per month, the cadence the model declares.

| captures | findings | what changed |
|---|---|---|
| 1 | **11** | 4 `threshold_exceeded`, 3 `threshold_warning`, 4 `declared_bad_state` |
| 2 | 11 | — |
| 3 | 11 | MONOTONICITY's reversal arm reaches its floor: 17 declines → 2 |
| 4 | **22** | 11 `monotonicity_reversal` findings appear |
| 5 | 22 | — |
| 10 | 22 | STABILITY resolves completely: 16 declines → 0 |
| 20 | 22 | — |
| 30 | 22 | HOMEOSTASIS **still** 21 declines, and always will |

103 invariants are checked at every row. The count does not grow; what changes
is how many of them can answer.

**THE ELEVEN AT n=4 ARE AN ARTIFACT OF THE FIXTURE AND NOT A FACT ABOUT ACME.**
`make_series.py` walks every numeric by a fixed fraction each step, so a
`monotonicity_reversal` there is the walk reversing, not a division reversing.
They are in the table because the question it answers is *at how many captures
does this arm start answering at all*, which is a fact about the engine. A
finding produced by a fixture is never evidence about an organisation.

## The three things that decide whether an arm answers

**1. The sample floor.** `AXIOM_MINIMUMS`: CONNECTIVITY 1, CONSISTENCY 1,
CONSERVATION 1, MONOTONICITY 3, BOUNDEDNESS 5, STABILITY 10, RESPONSIVENESS 20,
HOMEOSTASIS 30.

Reading those and concluding *nothing answers from one snapshot* is the mistake
this document was written to stop. **BOUNDEDNESS never declines
`insufficient_samples` at all here**, because a declared `warning:`/`critical:`
is evaluated against the CURRENT value and the floor governs the trend arm.
Seven of the eleven day-one findings are BOUNDEDNESS.

**2. The window, which is a CEILING and defaults to ONE HOUR.** Undeclared, a
series captured monthly is one observation however long it runs: everything
older than an hour is outside it. Measured — 36 monthly captures produced
byte-identical declines to a single snapshot until `window:` was declared.

And it must span the SERIES, not the floor. Sized at floor x cadence — 3 samples
x 30 days for MONOTONICITY — the arms still declined, because a longer series
then overruns the window and the history goes stale. Measured: 12 findings sized
to the floors, 18 at a generous ceiling. The model declares `3650d` on every
history arm, which is the honest shape for a number whose only job is to not
exclude what you fed.

**3. Whether the input reaches the engine at all.** STABILITY was declining
`too few state observations` on nine `status` indicators for ever, and walking
every unit around its declared state cycle changed nothing — because the feeder
never fed state. `EngineSession.add_observations` casts every sample with
`float(value)`, so a state raises; `InMemoryObservationHistory.add` takes
`value: Any` and accepts one. The engine declares a `state` indicator type and
runs STABILITY over it, and its own feeder cannot supply the series.

`feeder._add_state_series` writes to the public `session.history` instead.
**Filed upstream.** When a state feeder lands, that function goes.

Feeding state is what produced the four `declared_bad_state` findings — so
before it, the audit was **clean about the four worst units in the
organisation**. A gap in a feeder looks exactly like a quiet organisation.

## HOMEOSTASIS cannot answer at this cadence, and that is not a burn-in

It reads `homeostasis_baseline_days`, **fixed at 7**, and ignores the
indicator's `window:` entirely — 21 declines at 1 capture and 21 at 30, at every
window tried. A 7-day baseline holds at most one monthly observation.

Nothing reachable closes it:

- the domain model cannot set it — **`axiom_parameters` is not read by the
  published engine at all**, so the block in the Core's `consulting.yaml` has no
  effect here;
- `set_threshold_override` reaches HOMEOSTASIS's `z_warning`/`z_critical` and
  not its baseline window, per the engine's own `OVERRIDE_CONSULTED_BY`.

So the seven HOMEOSTASIS indicators are declared and permanently declining. They
stay declared: the decline names the reason, and dropping them would make the
model agree with one engine version instead of with the domain. **Filed
upstream.** Until it lands, no operating review on a monthly cadence gets a
baseline-deviation answer from this engine.

## The kill criterion

If a future engine release makes HOMEOSTASIS reachable and the seven indicators
still decline after 30 captures, the declarations are wrong rather than early,
and they come out. Recorded now, while the reason is fresh, because a burn-in
with no end condition is indistinguishable from a model that never worked.

## What `no_threshold` and `missing_property` are

22 `no_threshold` declines are honest: no operating model publishes a rate for
these, and inventing one would put a number nobody wrote into a model judged
against it. 4 `missing_property` are the two Process indicators the shipped
export has no column for — `throughput` and `automation_pct`. Both are the
engine saying truthfully that this export could not answer them.
