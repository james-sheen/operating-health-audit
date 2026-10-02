# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- The model declares `depends_on` with the cause at the department (`cause: target`), as its
  comment had said in words, and which severities count as a fault travelling (warning and
  above). Both processes are now traced to their departments, and no relation between two
  findings is left without a direction (FINDINGS F21, F22).
- `detect` prints `where_walks_end`, what `gaps` locates from the walk, and each ranking's
  frontier carries what it explains below it and the actions that apply.
- The `detect` extra needs `arbiter-engine` 0.2.32, which reads the new key.

## [0.1.14] — 2026-10-02

### Changed

- `confirm` and `cases` carry where a confirmed cause stood on the walk the case kept, as the
  engine now reads it: the executive confirmed on the sales department stood at the frontier of
  a traced walk, and a process confirmed on the department nobody leads is not connected
  (FINDINGS F20). `cases` also carries how many cases were reopened.
- The `detect` extra needs `arbiter-engine` 0.2.31, which keeps the walk on a case.

## [0.1.13] — 2026-10-01

### Changed

- The loop asserts where each walk ends, as the engine's `gaps` now locates it: the support
  department nobody leads has no cause connected on `leads`, the two processes' dependencies are
  undeclared channels, and a cause confirmed outside the declared graph is located between the
  two (FINDINGS F19). Nothing `detect` prints changes.
- The `detect` extra needs `arbiter-engine` 0.2.30, which says where each walk ends.

## [0.1.12] — 2026-10-01

### Added

- `detect` prints where each walk stopped, under `walk` beside each ranking's causes: its
  `state`, the `frontier` where the visible fault stops, and the causes still `open` with
  what each needs.

### Changed

- The reading to take first is named only while a cause is still open. On the shipped capture
  the sales department is traced to its two executives and names none; it named a reading
  already taken (FINDINGS F18).
- The `detect` extra needs `arbiter-engine` 0.2.27, which walks and orders the causes this way.

## [0.1.11] — 2026-10-01

### Added

- `detect` prints what each cause's own reading said, under `own_readings` beside each
  ranking's causes, as the engine computed it -- `None` where it could not say.

### Fixed

- The model's header said one capture produces seven findings; it is eleven -- four critical,
  four high, three warning.
- The three `plausible_range:` keys are gone from the model: nothing on this path reads them.

## [0.1.10] — 2026-09-30

### Changed

- **`cases` says what each confirmed rank rested on.** Engine 0.2.23 adds
  `ranked_by`, `named_by` and `settling_entity_was_named` to each confirmed row,
  and counts the first places a posterior decided apart from the rest. This model
  declares no strength, so every rank is hop order and then entity id, and the
  book now says so. A review that settles a department's finding on an
  executive's rating, where the ranking named the same executive's tenure, is
  counted as having looked where the ranking pointed.
- **The engine floor is 0.2.23**, which is where those fields begin.

### Fixed

- Without the engine, Stage 2 said `pip install operating-health-audit[detect]`,
  which answers 404: the package is not on PyPI. It now gives the README's
  install, from a clone of the release.
- A test comment still said the reading a ranking names is a relation (FINDINGS
  F13). From engine 0.2.19 it is the type's first declared value, and the test
  pins it.

## [0.1.9] — 2026-09-29

### Changed

- **A passing state the model gives no `timeout:` is reported, not timed.** The
  shipped model lists `restructuring` and `at_risk` under `transient:` and says
  nothing about how long either may last. Engine 0.2.22 declines such a state
  `missing_config` where it had timed it against five minutes nobody declared,
  so `detect` on the shipped capture declines two more checks -- the `status` of
  the marketing department and of the CRM project -- and still exits `2`. The
  README says why; `docs/burn-in.md` is re-measured, every finding unchanged and
  four rows carrying the new declines; and the test of a run that answers
  everything declares a timeout of its own.
- **The engine floor is 0.2.22**, which is where that decline begins.

## [0.1.8] — 2026-09-29

### Added

- **`detect` prints the reading to take first.** Beside each finding's causes,
  `ranking.most_discriminating` names the one reading the engine's ranking rests
  on most -- here, by the declared graph's shape. It was computed and dropped
  (FINDINGS F15).
- **`detect --ledger PATH` keeps cases.** Each finding opens a case on its unit
  and indicator unless one is open, its ranking is attached, and each later
  capture is checked into it until the model's declared run of clean captures
  closes it. Each finding carries its `case_id`. Needs stamped captures, and a
  series the ledger has already judged is refused.
- **`confirm` and `cases`.** `confirm <ledger> <case> --cause UNIT --reading
  UNIT.QUANTITY --basis TEXT` records what settled a case; `cases <ledger>`
  prints the book, each confirmation read back against the ranking before it.

### Changed

- **The engine floor is 0.2.20**, which reads a confirmation's reading back
  against the one the ranking named.

## [0.1.7] — 2026-09-28

### Fixed

- **An engine finding is scored as a finding.** `detect` read each finding's
  kind from `type` or `kind`, which the engine never writes -- it reports
  `problem_type` -- so every finding was scored `unclassified` and a run that
  had found something exited `2`, could-not-complete, where the README promises
  `1`. Every engine finding now scores `1`, whatever its problem type, and one
  carrying no problem type is still refused a score by name (FINDINGS F14).
- **Why the shipped example exits `2` is said, and tested.** Four declared checks
  have no value in the export: `throughput` on both processes and `margin_pct` on
  the engineering and support departments. `docs/burn-in.md` and the model's
  comment named `throughput` and `automation_pct`; `automation_pct` declines for
  too few readings instead. The README states the example's exit code and its
  reason, and a test reads both off the run.

## [0.1.6] — 2026-09-28

### Changed

- **The engine floor is 0.2.18**, forced by a failing control: the loop test
  now reads what 0.2.18 adds, and on 0.2.17 exactly the five tests that read it
  fail while the other 223 pass.

### Added

- **The loop test reads every new field of the loop.** For a department's
  finding `hypothesize` names one of its two leaders as the reading the ranking
  rests on, by the shape of the declared graph; for a division's it names the
  department two executives lead. `gaps` locates nothing on the connected
  series and names what it cannot read, and on the export as shipped locates all
  fourteen units as detached. Every plan round reaches nothing and says
  `gain_not_adopted`, because the one coupling's gain is withheld. A confirmed
  cause is read back against the ranking before it.
- **FINDINGS F13**: the reading a ranking rests on can be a relation on this
  model, so the test pins the entity and leaves the reading unpinned.

## [0.1.5] — 2026-09-27

### Fixed

- **A capture is fed at the time it was taken.** The feeder fed every series as
  values thirty days apart, ending at the clock, and never read `captured_at`,
  so calendar months, a skipped month and a back-filled quarter all reached the
  engine as the same even ladder -- and the learn stage dated its floor from a
  spacing this package made up. When every capture carries a stamp, the series
  is now placed by its stamps, in the order they were taken, and judged as of
  the latest one; when none does, it is spaced at the interval as before. A
  series half stamped, two captures at one instant, or a stamp that is not a
  time is refused by position. `detect` reports which under `timing` (FINDINGS
  F12).
- **`capture` takes `--captured-at`, and no longer invents a time.** It stamped
  the moment a file was imported, so three months back-filled in one sitting
  came out seconds apart -- harmless while the feeder ignored stamps, and
  wrong the moment it read them. Without the option a capture carries no time.
  **A capture written by `capture` before this release carries the time it was
  imported**: re-import it with `--captured-at`, or blank the field so the
  series is spaced at the interval.

## [0.1.4] — 2026-09-27

### Changed

- **A role is declared only where an axiom reads it.** The model declared a
  `role:` on every numeric indicator, and on eighteen of them no declared axiom
  reads one -- only RESPONSIVENESS and CONSISTENCY do -- so the engine reported
  eighteen unread fields on every load. They are gone; `cycle_time_days` keeps
  `latency`, which RESPONSIVENESS reads. On the shipped case study the findings,
  declines and exit code are unchanged, byte for byte. A test now holds the
  model's unread fields and unreachable axioms at none.
- **A plan may pair two hiring rounds.** The model declares `max_depth: 2`, so
  `plan` rolls out each round alone and in pairs, where it stopped at one round
  under the stamp `search_depth_not_declared`. Measured: 24 plans, none scoring
  below doing nothing, so the best plan is unchanged. The loop test shows a
  budget set below the search declined as `budget_exhausted`, with the plans it
  left out counted.

## [0.1.3] — 2026-09-27

### Added

- **A plan ranks the hiring rounds.** The model declares an objective,
  `expected_findings`, and three illustrative rounds for `add_headcount`, so
  `plan` ranks them instead of declining `no_objective`. The rounds do not tie:
  a hire is scored by how far it moves a department from its own HOMEOSTASIS
  baseline.
- **One coupling, with its gain withheld.** A department's `headcount` into its
  division's `total_headcount`, along `reports_to`, as `gain: estimate`. The
  engine fits a gain from 120 paired changes -- ten years of monthly captures --
  so on any series here the learn stage declines `insufficient_samples` by name.
  The loop test shows the fit on a labelled-synthetic series of 121 captures,
  and nothing is ever written into the model.

### Changed

- **The engine floor is 0.2.15**, forced by a failing control: the loop test
  reads every decline through the engine's own walker instead of its own copy,
  which read two of the four lists a decline is reported under and so could not
  see the learn stage's. On 0.2.14 that test cannot be collected.

### Fixed

- **A capture of nothing is refused wherever it enters.** `capture.load`
  refuses a file with no units, in the sentence `capture` already used for a CSV
  with no rows, and a unit with no name by its position instead of dropping it;
  `capture` refuses a CSV row with no `id` by its line, and a file with no `id`
  column. `detect`, `regression`, `presence` and `gate` read through it, so none
  of them answers clean or ready on an empty export any more. On the API,
  `feeder.run` answers `could_not_run` for a series item that is not a loaded
  capture or holds no units, anywhere in the series, `open_session` raises
  `CaptureUnusable` with the same sentence, and `regression.run` and
  `presence.run` refuse captures of nothing (FINDINGS F11).
- **`presence` changed, and was the one that had not run clean.** It reported
  every declared unit absent -- fourteen absences for a file holding nothing --
  and now refuses, on the command line and on the API alike: an export holding
  no units cannot say which units are absent. A capture of one unit is still
  compared, and the rest are reported absent as before.
- **A CSV cell that is not a number is refused by its line and column.**
  `capture` raised an uncaught `ValueError` on a cell such as `N/A`, which exits
  1 and reads as findings; it now answers `could_not_run`, as it does for a row
  with more cells than the header, which raised `AttributeError`. `N/A`, `n/a`
  and `-` are refused rather than read as the empty cell, by choice: blank is the
  one spelling of an absent quantity this reader documents, and `N/A` can mean
  *not applicable*, which blank already says, or *not available*, a reading that
  should exist and does not -- only the exporter knows which. `nan` and `inf`
  still read, because the engine declines a non-finite reading by name.
- **A reading the engine refuses is refused here, in the engine's words.** A
  JSON capture carrying a word where the model declares a number -- `N/A` for
  `turnover_pct` -- reached the engine, and its refusal escaped as a traceback
  exiting 1. `detect` and `feeder.run` now answer `could_not_run` with the
  engine's own message, and `open_session` raises `CaptureUnusable` carrying it.
  Only that refusal is caught, a `ValueError` naming the reading being fed; any
  other failure propagates as before.

## [0.1.2] — 2026-09-26

The loop runs every stage the engine offers, and the model declares what each
stage reads, or says why it does not.

### Changed

- **The core's names.** A finding's and a change's subject is written and read
  as `point`, and change kinds are printed in this package's word --
  `operating_unit_removed` -- whichever core is installed. The range is
  `presence-audit>=0.1.13,<0.3`, and the suite ran on a 0.2.0 build as well.
- **The engine floor is 0.2.13**, forced by a failing control: the loop opens and
  resolves a case and reads the per-stage report, and 0.2.12 has neither.

### Added

- **Which way a failure travels**: `leads` and `reports_to` are declared causal,
  each in the direction its edge runs, with no strength -- nothing gives one. The
  engine's ranking therefore names causes without numbers (FINDINGS F10).
- **One lever**, `add_headcount` on a department, whose `tolerance:` is how close
  the next capture must come to the people added. An executed hire is filed with
  `file_action`, and the next capture decides which arm the world followed.
- **`cases:`**: a case closes after two monthly captures in a row with nothing at
  `warning` or above on its indicator.
- **`detect` prints, beside each finding, what could explain it**: the engine's
  ranking of the declared causes, or the reason it declined. Nothing in it enters
  the exit code.

## [0.1.1] — 2026-09-26

The first tagged release.

### Changed

- A unit's state goes to the engine through `add_observations`, like every
  other reading; the workaround that wrote to the engine's history directly is
  gone. The engine floor is 0.2.11, the release that keeps a declared state as
  a state (FINDINGS F1, filed upstream as issue #14).
- The model declares `axiom_parameters: {homeostasis_baseline_days: 3650}`, so
  HOMEOSTASIS answers from the thirtieth monthly capture instead of declining
  for ever (F2). `docs/burn-in.md` is re-measured on engine 0.2.11: the arm
  that could never answer now resolves at 30 captures, and the kill criterion
  recorded for it resolved the other way -- the declarations were early, not
  wrong.

## [0.1.0] — 2026-09-15

### Added

- First cut. Stage 1 presence, regression and the declarations gate against
  `presence-audit`; Stage 2 detect against `arbiter-engine`.
- A domain model covering five operating-unit types and 27 indicators, with
  CONNECTIVITY declared over the reporting structure.
- `docs/burn-in.md`: the measured table of what each further capture unlocks.
- `FINDINGS.md`: three findings in the engine, three in the source domain,
  three in this package, and one claim withdrawn.
- A cross-check that `presence-audit`'s restated response-model set still
  equals the engine's own enum. The core restates it rather than importing it,
  and a restated closed enum drifts in both directions. This package pins both,
  so the comparison runs here unskipped.

### Changed

- The `presence-audit` floor moves to 0.1.9, which is where `RESPONSE_MODELS`
  first appears. Measured: 0.1.8 fails the new cross-check at import.
