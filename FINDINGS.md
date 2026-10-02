# Findings

What building this vertical found, in the two upstreams and in itself. Each was
produced by RUNNING something; none came from reading code, and three of them
contradicted what reading had already concluded: F2, F7, and the claim withdrawn
at the end.

## In `arbiter-engine` 0.1.14

**F1 and F2 are one ask and are filed as one**, at
[james-sheen/arbiter#14](https://github.com/james-sheen/arbiter/issues/14) —
both are the session dropping a capability the layer beneath it has. F3 is
not filed. **Both closed upstream in `arbiter-engine` 0.2.11**, which is this
package's engine floor from its 0.1.1; each finding below says how, and the
measurement it was filed on stays as it was.

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

*Worked around* in `feeder._add_state_series`, which wrote to the public
`session.history`. **Closed by engine 0.2.11**: `add_observations` keeps a
reading of a property the model declares `type: STATE` as a state, so the
feeder sends both kinds through it and the workaround is gone.

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

**Closed by engine 0.2.11**: a model declares `axiom_parameters:`, and this one
declares `homeostasis_baseline_days: 3650`. Measured through the session on the
shipped fixture, the 21 declines hold through the twenty-ninth capture and are
gone at the thirtieth. **The five-capture figure above does not reproduce on any
current engine** and is left as measured: HOMEOSTASIS now waits for its own
thirty-sample floor, so five captures decline `insufficient_samples` whatever
the baseline.

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

## In `arbiter-engine` 0.2.13

**F10. `hypothesize` ranks causes it has no number for, and does not say why.**
With the causal direction declared and no strength, `infer` on `dept-sales`
declines `cpt_missing` by name -- *declare `causal.weight` on these edges* -- and
`hypothesize` on the same unit returns the two executives who lead it, each with
`posterior: null`, beside an empty `not_checked`. The ranking is right about WHO
and silent about why it has no number, so a reader of it alone cannot tell *no
strength declared* from *computed and lost*. **Fixed in the engine before 0.2.13
shipped**, found by this migration: the ranking now carries the declines of the
inferences behind it, and each cause names its own as `declined`. The strict xfail
that held it in `tests/test_the_loop_runs.py` came off in the same release as this
package's floor.

## In this package, at 0.1.2

**F11. A capture of nothing ran clean.** `feeder.run` read `.points` off
whatever it was handed and took a missing attribute as none, so a path, a string
or a parsed dict passed in place of a loaded capture fed no units and answered
exit 0 with 0 entities. The loader did the same from a file: `units: []`, or
units without a name, loaded as an empty export, and `detect` exited 0,
`regression` said `ran` with nothing moved, and `gate` answered ready. `from_csv`
had refused an empty file from the first release; `load` never learned it. Found
by an outside verification that ran the API, which read the command line as
unaffected -- it was not. Every door now refuses, in one sentence.

## In this package, at 0.1.4

**F12. Every capture was re-timed.** The feeder fed each series as bare values
thirty days apart, ending at the clock, and never read `captured_at`. So a
skipped month, a review dated the 31st and a back-filled quarter all reached the
engine as the same even ladder, and every window, baseline and learn-stage date
it computed was computed from a spacing this package made up. Found by an
outside verification that fed calendar months through the feeder and got
thirty-day answers -- the reason this package's own loop test had passed on an
engine that could not fit a calendar-monthly series at all. **Reproducing it
found the second half:** `capture` stamped the moment a CSV was imported, so a
feeder that simply trusted stamps would have turned months back-filled in one
sitting into readings seconds apart. Both are fixed together, and the run says
which clock it used.

## In `arbiter-engine` 0.2.17

**F13. The reading a ranking rests on can be a relation.** `hypothesize` names
the entity whose reading would most change its ranking, and gives the reading
as that entity's first declared indicator. On this model a department's first
indicator is `reports_to` and an executive's is `leads`, so a division's finding
names `dept-sales.reports_to` and a department's names `exec-cro.leads`:
relations the CONNECTIVITY check reads, not values anyone can take. The ENTITY
is right -- reading the department two executives lead splits a division's five
candidates three to two -- and `evidence_needed` picks its reading the same way.
The loop test pins the entity and the basis, and leaves the reading unpinned
until the engine names a value.

## In this package, at 0.1.6

**F14. Every engine finding was scored as unclassified.** `detect` took each
finding's kind from `type` or `kind`, and the engine writes neither -- it
reports a finding's kind as `problem_type` -- so from the first release every
engine finding floored the run at `2`, could-not-complete, where the README
promises `1`. The test that pinned the shipped example's exit code asserted `2`
with a reason in its message that was not the reason, and held for the one it
never read. Found by running the example while releasing 0.1.6. Reproducing it
found the second half: `docs/burn-in.md` and the model's comment named
`throughput` and `automation_pct` as the two indicators the export cannot feed,
and measured, the four `missing_property` are `throughput` on both processes and
`margin_pct` on two departments -- `automation_pct` declines for too few
readings. An engine finding now scores `1`, whatever its problem type; the
example still exits `2`, for the reason its `why` names.

## In this package, at 0.1.7

**F15. `detect` dropped the reading its ranking named, and kept no case.** The
engine names the one reading its ranking rests on most, `most_discriminating`,
and `detect` printed the causes and the declines and not that. This model
declares no strength, so every cause carried `None` beside `cpt_missing` -- a
division's finding listed five causes and nothing to do -- while the engine had
named the headcount of the department two executives lead, which splits the five
three to two. And `detect` opened no case: every run was a fresh session, no verb
could record the cause a person confirmed, and the README described the rest of
the loop as running, beside a verb table with no verb that ran it. Found by
re-reading the phase that built those fields against the document it was built
from. `detect` prints the reading, `--ledger` keeps the cases, `confirm` and
`cases` record and read them, and the README says which parts run only in the
loop test.

## In this package, at 0.1.10

**F16. `detect` printed each cause without its own reading.** The engine computes,
for every candidate a ranking holds, what the last check said about it, and
`detect` kept the cause and its posterior and dropped that. On the shipped capture
`exec-cro` reads faulty, critical -- 22 direct reports over a critical 20 -- and
the sales department's ranking printed `['exec-cro', None]` and named a different
reading to take first. Found by an outside direction document, read and not run;
reproduced by running it with the engine's raw answer captured beside the
printed one. `own_readings` now carries each cause's reading beside the pairs.

**F17. The model's record of itself was two releases stale.** Its header said one
capture produces seven findings, four critical and three warning; since the
`status` states were fed it is eleven, four of them `high`. And three executive
indicators declared `plausible_range:`, which nothing on this package's path
reads -- the engine exempts the key by name for a document-ingest pipeline this
package does not run -- so it read as a range check that never ran, while two
shipped ratings, 6.2 and 5.1, sit outside the `[0, 5]` it gave
`performance_rating`. The header now says eleven, and the keys are gone. The two
ratings stay as the case study ships them; whether the scale is five is a
question for whoever states it.

## In this package, at 0.1.11

**F18. The reading to take first was one already taken.** On the shipped
capture both executives leading sales read over their bound -- `exec-cro` 22
direct reports over a critical 20, `exec-vp-sales` 18 over a warning 15 -- and
`detect` named `exec-cro.tenure_years` as the reading to take first: engine
0.2.26 chose among every cause, read or not, by the shape of the declared graph.
Found by an outside direction document's gate, reproduced by running it. From
engine 0.2.27 a ranking names only a reading a cause still needs, so the sales
department's walk is traced to its two executives and names none, and `detect`
prints the walk beside the causes: its state, where the visible fault stops, and
what is still open.

## In `arbiter-engine` 0.2.29

**F19. `gaps` said nothing about where a walk ends.** On the shipped capture the
support department's walk is cut -- no executive leads it in the export -- and
both processes depend on departments that show findings, along a relation this
model gives no direction. Engine 0.2.29's `gaps` located none of it, and a
person's confirmation of a cause outside the declared graph was counted
`not_ranked` and read by nothing. Found by an outside direction document's gate,
reproduced by running it. From engine 0.2.30 `gaps` locates each: `dept-support`
with no cause connected on `leads`, both `depends_on` instances as undeclared
channels, counted by the findings each direction would connect, and a confirmed
cause outside the graph between it and the finding. The larger count is the
direction the model's own comment rules out, which is why the engine prefers
neither. This package prints none of it yet; its loop asserts it.

## In `arbiter-engine` 0.2.30

**F20. A confirmation was read against a rank, and a case kept nothing of the walk.**
On the shipped capture the walk up from `dept-sales` is traced, with `exec-cro` and
`exec-vp-sales` at its frontier. A case kept each cause and its posterior, nothing of
the walk, and a confirmation of `exec-cro` read *rank 1 of 2*: a spelling order, since
this model declares no strength, and nothing said where the executive stood. Found by
an outside direction document's gate, reproduced by running it. From engine 0.2.31 the
case keeps each cause's standing and the walk's state and frontier, and the row reads
`frontier` on a `traced` walk, with the confirmation's basis and one ranking before it,
on a session holding only the ledger, as `confirm` runs. `cases` passed the engine's
summary through by name and dropped the new `reopened`; it carries it now.

## In `arbiter-engine` 0.2.31

**F21. The model could not say which way `depends_on` carries a failure, and `detect`
printed none of where a walk ends.** Its comment said it in words: a failure travels from
the department to the process, against the edge the export carries. The engine read a
causal rule's source as its cause, so declaring it would have blamed the process, and the
processes' walks were cut. Found by an outside direction document's gate, reproduced by
running it. From engine 0.2.32 a rule names its cause's end, and the model declares
`depends_on` with `cause: target`: `proc-onboarding` walks to `dept-support`, where no
executive leads it, and `exec-cro` explains the sales department, its division and its
process. `gaps` had located where each walk ends since engine 0.2.30, and `detect` now
prints it.

**F22. A warning was left out of the evidence.** A case here opens on a warning, and the
engine's own floor counts only `high` and `critical`, so `exec-vp-sales`, over its warning
line, read `deviating` beside `exec-cro`'s `faulty`, and every ranking carried
`evidence_severity_not_declared`. The model now says which severities count:
everything at or above a warning, as its case criterion counts.

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
