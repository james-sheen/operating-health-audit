# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
