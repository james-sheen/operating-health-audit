# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **A role is declared only where an axiom reads it.** The model declared a
  `role:` on every numeric indicator, and on eighteen of them no declared axiom
  reads one -- only RESPONSIVENESS and CONSISTENCY do -- so the engine reported
  eighteen unread fields on every load. They are gone; `cycle_time_days` keeps
  `latency`, which RESPONSIVENESS reads. On the shipped case study the findings,
  declines and exit code are unchanged, byte for byte. A test now holds the
  model's unread fields and unreachable axioms at none.

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
