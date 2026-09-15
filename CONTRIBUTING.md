# Contributing

## The one rule

**Run it.** Every finding in `FINDINGS.md` came from running something, and two
of them contradicted a conclusion that reading had already produced. A patch
justified by reading the code, without a run that shows the behaviour, will be
asked for the run.

## What a change needs

1. **A test that fails without it.** Not a test that passes with it — those are
   different, and the second is satisfied by a test that asserts nothing.
2. **Falsification.** Break the thing your test guards and show it goes red. The
   suite is checked this way: six mutations, six reds.
3. **A reason in prose** where a number is chosen. A floor with no stated reason
   is a preference, and `exit_contract.py` has a test that says so.

## Running the suite

```bash
pip install -e '.[detect]' pytest
python -m pytest tests/ -q
```

Tests that need an upstream import it inside the test, so its absence is a red
with a sentence rather than a quiet skip. A skip is how a check stops running
without anybody noticing.

## What not to do

- Do not derive a relationship from a name. The engine removed that and said
  why; a reporting line guessed from an id prefix is a guess wearing the costume
  of a derivation.
- Do not declare an indicator the capture format cannot feed. It produces a
  `missing_property` decline that reads as a gap in the data when it is a gap
  between the model and the format.
- Do not invent a number to silence a decline. `no_threshold` on a rate nobody
  published is the honest answer.
