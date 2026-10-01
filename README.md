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
baselines. Each capture is placed at the time it was taken, its `captured_at`,
and the series is judged as of the latest one. A series whose captures carry no
time is spaced thirty days apart instead, and `detect` says which under
`timing`: a declared cadence and a measured one read the same in every figure
downstream.

**Beside each finding, what could explain it, where the walk stopped, and the
reading to take first.** `detect` asks the engine's `hypothesize` about each unit
with a finding and prints the answer beside it: the declared causes, each with
its posterior, what each cause's own reading said under `own_readings` -- `None`
where the engine could not say -- the reason the engine declined, the `walk`, and
`most_discriminating`. The walk gives its `state`, the `frontier` where the
visible fault stops, and the causes still `open` with what each needs; the
reading to take first is one an open cause still needs, and `None` when nothing
is open. The model declares which way a failure travels -- into a department
from the executives who lead it, into a division from the departments reporting
to it -- and no strength, so the causes come without numbers, in the order the
walk stood them. On the shipped capture the sales department is traced to its
two executives and names no reading; the commercial division is partly traced,
and the reading named is the marketing executive's rating, which one capture is
too few samples to judge.

**With `--ledger`, a finding becomes a case.** The file keeps the engine's case
book. Each finding opens a case on its unit and indicator unless one is open,
its ranking is attached, each later capture is checked into it, and it closes
after two clean monthly captures. `confirm` records the cause a person found and
the reading that settled it, and `cases` prints the book, each confirmed cause
read back against the ranking its case held before. This model declares no
strength, so that rank is hop order and then entity id, and each row says so
(`ranked_by: hops`): a first place here is not evidence the ranking was right,
and the book counts first places a posterior decided apart. A case counts captures, so
the series must be stamped and each capture is judged into the book once.

**The rest of the loop runs in `tests/test_the_loop_runs.py`, not in a verb.** A
plan ranks the declared hiring rounds, alone and in pairs, by the findings each
would bring, and an executed hire is filed and graded against the next capture.
The one declared coupling, a department's headcount into its division's total
with its gain withheld, declines `insufficient_samples` until 121 monthly captures
exist, which is ten years. A real review need not wait: its own reporting definition
can declare the gain, and its headcount budget the bound a hiring round would reach
(`docs/burn-in.md`). `gaps` locates what the model cannot
explain -- on the export as shipped, every unit as detached.

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
                                   [--captured-at WHEN]          when it was taken
operating-health-audit presence    <declaration> <capture>       the three-valued answer
operating-health-audit regression  <before> <after>              two exports compared
operating-health-audit detect      <model> <capture>...          feed a series to the engine
                                   [--ledger PATH]               keep cases in this file
operating-health-audit confirm     <ledger> <case> --cause UNIT  record what settled a case
                                   [--reading UNIT.QUANTITY] --basis TEXT
operating-health-audit cases       <ledger>                      every case a ledger keeps
```

## Exit codes

`0` clean, `1` findings, `2` could-not-complete. The third is never reached by
accident: an unreadable declaration, an unloadable model and a missing engine
each arrive as their own exception and leave as `2` with a sentence saying
which, rather than as a traceback exiting `1`.

**`detect` on the shipped capture exits `2`, and says why under `why`.** Its
eleven findings score `1`. Four declared checks score `2`, because the export
carries no value for them -- `throughput` on both processes, and `margin_pct` on
the engineering and support departments, whose margin it does not report -- so
the engine declines them `missing_property`. Two more score `2` because the
model does not say how long a passing state may last: the marketing department
is `restructuring` and the CRM project `at_risk`, states the model lists under
`transient:` with no `timeout:`, so the engine declines their `status`
`missing_config` rather than timing it against a number nobody gave. The worse
wins. With those columns supplied and a `timeout:` declared on each passing
state, the same run exits `1`.

`confirm` and `cases` exit `0`, or `2` with the reason when the ledger or the
case is not there, or the confirmation names no cause.

Composing nothing is `0` here and `2` in the core, deliberately. The core
composes stage results, so no stage reporting means nothing ran. This composes
findings, so no findings means the comparison ran and found none -- the answer
the audit exists to be able to give.

## Quick start

```bash
git clone --branch v0.1.11 https://github.com/james-sheen/operating-health-audit
cd operating-health-audit
pip install '.[detect]'     # not on PyPI: this installs the release you cloned

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
- **It does not know how long a state may last.** A `transient:` state is one a
  unit passes through, and how long it may take is `timeout:`, a fact about the
  organisation under review. The shipped model declares none, so a unit in such
  a state is reported unchecked rather than timed.
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
