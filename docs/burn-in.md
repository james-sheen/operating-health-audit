# Burn-in: what this audit can answer, and after how many captures

Measured against `arbiter-engine` 0.2.11 and `presence-audit` 0.1.12 by running
`battery/make_series.py` over the shipped case study. Every number below is a
run, not a reading of a constant — the first draft of this document was written
from `types.AXIOM_MINIMUMS` and was wrong in both directions. It was measured
first on 0.1.14, when one arm could never answer at this cadence; the table was
re-measured when 0.2.11 made it answer, and several of its old rows had moved.
Re-measured on 2026-09-27 against 0.2.15 and presence-audit 0.2.1, with the
model's coupling and planning objective declared: every row is unchanged.
Re-measured on 2026-09-29 against 0.2.22 and presence-audit 0.2.5: every finding
is unchanged, and four rows carry declines 0.2.21 did not report (below).
Re-measured on 2026-09-30 against 0.2.23 and presence-audit 0.2.6: every row is
unchanged.
Re-measured on 2026-10-01 against 0.2.25 and presence-audit 0.2.6: every row is
unchanged.

## The one-line answer

**Eleven findings from a single capture.** The audit is useful on day one. Three
arms need a history, and every one of them answers by the thirtieth capture.
One stage of the loop does not: the coupling's gain waits for the 121st.

## The measured table

One capture per month, the cadence the model declares.

| captures | findings | declines | what changed |
|---|---|---|---|
| 1 | **11** | 82 | 4 `threshold_exceeded`, 3 `threshold_warning`, 4 `declared_bad_state` |
| 2 | 7 | 89 | the four bad states walked off by the fixture |
| 3 | 16 | 80 | MONOTONICITY reaches its floor: 17 `insufficient_samples` → 2 |
| 4 | **18** | 80 | 11 `monotonicity_reversal` findings appear |
| 10 | 18 | 73 | STABILITY reaches its floor: 16 `insufficient_samples` → 0 |
| 30 | 18 | 52 | HOMEOSTASIS resolves completely: 21 declines → 0 |

103 invariants are checked at every row. The count does not grow; what changes
is how many of them can answer.

**A unit in a passing state declines until the model says how long it may
last.** The model lists `restructuring` and `at_risk` under `transient:` with no
`timeout:` -- how long a restructuring may take is the review's to say -- and
the engine declines to time such a state `missing_config`, where until 0.2.21 it
timed it against five minutes nobody declared. Two units sit in one on the
shipped capture, and the fixture walks all nine into one at the second capture
of every four -- the second, tenth and thirtieth rows. So 2 of the first row's
declines are these, and 9 of each of those three rows'. No history removes them;
a declared `timeout:` does.

**THE FINDINGS AFTER n=1 ARE AN ARTIFACT OF THE FIXTURE AND NOT A FACT ABOUT
ACME.** `make_series.py` walks every numeric by a fixed fraction each step and
every unit round its declared states, so a `monotonicity_reversal` there is the
walk reversing and a bad state at n=3 is the walk arriving at one. They are in
the table because the question it answers is *at how many captures does this arm
start answering at all*, which is a fact about the engine. A finding produced by
a fixture is never evidence about an organisation.

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

Filed upstream as issue #14, and closed by engine 0.2.11: the session now keeps
a reading of a property the model declares `type: STATE` as a state, and the
feeder sends both kinds through `add_observations`. The workaround that wrote to
the public `session.history` is gone, and the engine floor names that release.

Feeding state is what produced the four `declared_bad_state` findings — so
before it, the audit was **clean about the four worst units in the
organisation**. A gap in a feeder looks exactly like a quiet organisation.

## HOMEOSTASIS answers from the thirtieth capture, because the model says how

It reads `homeostasis_baseline_days`, **seven by default**, and ignores the
indicator's `window:` — so on engine 0.2.10 and earlier it declined 21 times at
1 capture and 21 times at 30, at every window tried. A seven-day baseline holds
at most one monthly observation.

Nothing a model could write reached it then: the published engine read no
`axiom_parameters` at all, and `set_threshold_override` reaches HOMEOSTASIS's
z-scores and not its baseline window. **Filed upstream** with the state feeder,
as issue #14. From engine 0.2.11 the model declares the block, and this one
declares the windows' ten years:

    axiom_parameters:
      homeostasis_baseline_days: 3650

Measured: 21 declines through the twenty-ninth capture, **none at the thirtieth**
— the axiom's own thirty-sample floor is now the only thing it waits for.

## The coupling's gain waits for the 121st capture

The model declares one coupling -- a department's headcount into its
division's total -- and withholds the number, so the engine may fit it. It fits
a gain from 120 paired changes and no fewer, which at one capture a month is
121 captures: ten years. Until then every edge the coupling runs along declines
`insufficient_samples`, by name, and nothing is fitted.

That is the true answer, and it is not a burn-in in the sense of the table:
nothing in this model can bring it closer, and nothing should. Lowering a
statistical floor on invented data would produce a gain with a decimal point
and no series behind it. The loop test shows the mechanism instead, on a
series labelled synthetic and built so the answer is known: at 120 captures all
four edges decline, at 121 all four are fitted, each at a gain of 1.0 -- a
department's hire adds one to its division's total -- with its interval, and
with the replay the engine could not run because no record exists to replay.

## Before a real review: two documents that make the plan answer

The plan ranks the declared hiring rounds by the findings each would bring, and
on the shipped example no round reaches anything: the coupling's gain is
withheld, and a division's `total_headcount` declares no bound. Fitting the gain
waits ten years (above). **A real engagement can declare both instead, each from
a document it already holds:**

- **Its reporting definition.** If the organisation's own reporting says a
  division's headcount is the sum of its departments', the gain is 1 by that
  definition, not by a fit: write `gain: 1` in the coupling's `transition:` and
  name the definition in its `source:`. If the definition counts anyone outside
  the departments -- a division's own executives, contractors, a shared pool --
  it is not an identity, and the gain stays withheld.
- **Its headcount budget.** A division's budgeted headcount is an upper bound
  somebody published: write it as `total_headcount`'s `warning:` or `critical:`,
  with the budget as its basis. With no budget, declare no bound; a number
  nobody wrote is the guess this model exists to refuse.

Measured on copies of the shipped model and capture, against `arbiter-engine`
0.2.20: as shipped, none of the 24 candidates reaches anything. With `gain: 1`,
all 23 but doing nothing reach a division one hop away, and find nothing there.
With a budget as well -- 830, against a commercial division of 820 -- 8 of the
29 reaches carry that division's warning, each from a round adding ten people or
more to one of its departments, and no reach into operations, at 340, carries
one: the plan says which hire would break the budget. The shipped example declares
neither, because its organisation is invented, and so would its definition and
its budget be.

**Keep both documents, and the model they fill, out of this repository.** They
are the organisation's, and a unit small enough that one person joining or
leaving moves its headcount makes that headcount personal data. Cite each
document by the engagement's own reference -- title, version, and its owner by
role -- rather than quoting or attaching it. Keep the filled model, the captures
and the `--ledger` file wherever the engagement keeps its records, and give
`confirm --basis` a role and a record, never a person's name. Nothing from a real
review belongs in `examples/`, which is invented and says so.

## The kill criterion, and how it resolved

Recorded when HOMEOSTASIS could not answer: *if a future engine release makes
HOMEOSTASIS reachable and the seven indicators still decline after 30 captures,
the declarations are wrong rather than early, and they come out.* Engine 0.2.11
made it reachable, and at 30 captures the seven evaluate. **The declarations were
early, not wrong, and they stay.** The criterion was worth writing down: it is
what turned *it still declines* from a standing excuse into a question with an
answer.

## What `no_threshold` and `missing_property` are

22 `no_threshold` declines are honest: no operating model publishes a rate for
these, and inventing one would put a number nobody wrote into a model judged
against it. 4 `missing_property` are two declared checks the shipped export
carries no value for: `throughput` on both processes, and `margin_pct` on the
engineering and support departments, whose margin it does not report. Both are
the engine saying truthfully that this export could not answer them, and they
are what makes `detect` exit `2` on this capture.

This paragraph named `throughput` and `automation_pct` until 0.1.7, and the
model's comment said the same. Measured, `automation_pct` never declines
`missing_property` on one capture: MONOTONICITY needs three readings, so it
declines `insufficient_samples` before it looks for a value.
