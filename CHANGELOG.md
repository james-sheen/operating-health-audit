# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
