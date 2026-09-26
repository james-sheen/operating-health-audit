# operating-health-audit

Of the operating units a target operating model declares -- divisions,
departments, executives, projects, processes -- which are present and reporting,
which are absent, which appeared undeclared, and which are breaching the bounds
the organisation published.

It is a vertical: the subject-specific half of an audit whose neutral half is
[`presence-audit`](https://pypi.org/project/presence-audit/) and whose judgement
is [`arbiter-engine`](https://pypi.org/project/arbiter-engine/).

## The two stages

**Stage 1 is presence and needs no engine.** A declaration says what the
organisation runs; an export says what reported. The answer is three-valued --
declared and present, declared and absent, present and undeclared -- plus the
one finding only this domain can see: a unit that is present, enabled, reporting
healthy numbers, and reports into nothing.

**Stage 2 is the engine.** The same export, judged against declared bounds,
declared bad states, and -- once enough captures accumulate -- trends and
baselines.

## What it answers on day one

Eleven findings from a single capture of the shipped fourteen-unit example: four
thresholds exceeded, three in warning, and four units sitting in a state the
model declares bad. `docs/burn-in.md` carries the measured table of what each
further capture unlocks: the last arm, HOMEOSTASIS's baseline, answers from
the thirtieth monthly capture.

## The verbs

```
operating-health-audit declare     <declaration>                 what the model claims
operating-health-audit gate        <declaration> [--capture ...] refuse what is not ready
operating-health-audit capture     <wide.csv> --out <capture>    produce an export
operating-health-audit presence    <declaration> <capture>       the three-valued answer
operating-health-audit regression  <before> <after>              two exports compared
operating-health-audit detect      <model> <capture>...          feed a series to the engine
```

## Exit codes

`0` clean, `1` findings, `2` could-not-complete. The third is never reached by
accident: an unreadable declaration, an unloadable model and a missing engine
each arrive as their own exception and leave as `2` with a sentence saying
which, rather than as a traceback exiting `1`.

Composing nothing is `0` here and `2` in the core, deliberately. The core
composes stage results, so no stage reporting means nothing ran. This composes
findings, so no findings means the comparison ran and found none -- the answer
the audit exists to be able to give.

## Quick start

```bash
pip install operating-health-audit[detect]

operating-health-audit gate      examples/operating.declaration.json
operating-health-audit presence  examples/operating.declaration.json examples/acme.capture.json
operating-health-audit detect    examples/operating.model.yaml       examples/acme.capture.json
```

`examples/acme.capture.asshipped.json` is the same export with the relationships
removed, which is how the source case study actually ships. Every unit comes
back detached, and that is the correct answer about it.

## What this package does not claim

- **It does not know whether a state is bad.** The model declares `normal:`,
  `transient:` and `bad:` sets and the engine judges against them. Stage 1
  reports a state change in either direction and scores it clean.
- **It does not invent structure.** A wide CSV has nowhere to put a reporting
  line, so `capture` produces an export with no edges and the audit says every
  unit is detached. Deriving an org chart from an id prefix would be deriving a
  relationship from a name.
- **It does not report a baseline deviation before thirty captures.**
  HOMEOSTASIS needs thirty samples, which at a monthly cadence is two and a half
  years; the model declares the baseline window that lets it answer then
  (`docs/burn-in.md`).
- **Its example numbers are invented.** No unit, person or figure in
  `examples/` describes a real organisation.
