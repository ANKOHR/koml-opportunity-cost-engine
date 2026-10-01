# KOML Opportunity Cost Engine

`koce` computes what a selected task gives up among explicitly supplied, mutually exclusive alternatives. CPU only, Python standard library only at runtime, local JSON files, no network calls, no model calls. Values are **HYPOTHETICAL input valuations**, never measured savings or predictions.

## Quickstart

Python 3.10 or newer, setuptools 68 or newer, and pytest for verification:

```powershell
python -m pip install --no-index --no-deps --no-build-isolation -e .
koce fixtures --out demo
koce run --input demo
koce report --format md
python -m pytest -q
```

If the Python user Scripts directory is absent from PATH, use `python -m koml_opportunity_cost_engine.cli` in place of `koce`, or add that directory to PATH. No downloads are required when the prerequisites are installed. The 200-record fixture is generated locally. The manually written five-record example is `examples/tiny`: run `koce compare --input examples/tiny`. Its selected value is 120.00 GBP, best alternative is 160.00 GBP, and avoidable gap is 40.00 GBP, all hypothetical.

## Domain and input reference

The input directory contains `tasks.json`, a UTF-8 JSON object. Other fixture metadata is ignored when tasks.json exists. No CSV or YAML import is implemented; unsupported directories return a named schema error. An entirely empty directory renders zero counts and NO INPUT RECORDS provenance.

```json
{
  "synthetic": true,
  "entered_by": "illustrative example",
  "as_of": "2026-09-30",
  "currency": "GBP",
  "records": [
    {"id":"a","decision":"slot-1","title":"Chosen task","date":"2026-09-30","selected":true,"value":"100.00","synthetic":true},
    {"id":"b","decision":"slot-1","title":"Alternative","date":"2026-09-30","selected":false,"value":"150.00","synthetic":true}
  ]
}
```

All listed root and record fields are required; extra fields are rejected. `synthetic` and `selected` are JSON booleans. IDs must be globally unique. Each decision has exactly one selected task and at least one alternative. IDs, decisions, titles, and entered_by contain 1 to 10,000 characters. Unicode and Windows paths are accepted; U+2014 is rejected. Dates use ISO YYYY-MM-DD, share a date within a decision, and cannot be later than the explicit `as_of`. This is an input cutoff, not the machine clock, so reruns remain deterministic. The operator must supply an honest cutoff.

`value` is a finite nonnegative decimal string, at most 1,000,000,000 GBP, with exact penny precision. No floats, currency conversion, negative values, or fractional pennies. Decimal arithmetic preserves exact totals. `currency` must be GBP.

For Henry's own data entered by him, set root `synthetic` to false, `entered_by` to `Henry`, and every record's `synthetic` to false. Do not relabel fixtures as real. Mixed provenance is rejected. Keep real trials outside the repo. Provenance is an operator assertion; the tool cannot verify authorship or whether a valuation is true.

For each decision:

* Foregone value (opportunity cost) = highest-valued nonselected task.
* Avoidable gap = max(0, foregone value minus selected value).
* Dominated choice = strictly positive avoidable gap.
* Ties choose the lexicographically smallest alternative ID and never flag an equal selected value.

Totals sum across decision groups. The operator must ensure groups describe distinct opportunities and do not double count work. Alternatives must fit the same resource/time slot; the engine does not infer feasibility, durations, dependencies, uncertainty, or utility. A high input value is not evidence that a task will earn that amount.

## Subcommand catalogue

All commands have `--help` with examples.

```powershell
koce fixtures --out demo
koce run --input demo --state .koce-results.json
koce report --format md --out report.md
koce report --format json
koce compare --input demo
koce audit --input demo
```

`fixtures` writes the 200 records, independent expectations, labelling note, and a five-record subset in `demo/tiny`. `run` validates, computes, and atomically replaces a result snapshot (default `.koce-results.json` in the working directory). `report` renders that snapshot without rerunning input; rerun after changing tasks. Both formats carry provenance and figure status. `compare` directly renders all computed comparisons as JSON without persistence. `audit` adds `audit_matches`, the IDs of decisions with a positive hypothetical gap; it retains all decisions and totals so the report reconciles. A successful command exits 0; named failures exit 2. Argparse also exits 2 on usage errors.

## Architecture

```text
fixtures.py -> labelled tasks.json + independent expectations.json
local tasks.json -> cli.load -> core.validate -> core.evaluate
                                               |
                                      deterministic result
                                               |
                              report.render -> stdout or atomic file
```

The core has no I/O. Sorting groups and alternative ties fixes ordering. JSON keys are sorted, decimals have two places, UTF-8 output uses LF, and no clock or random source is used. There is no random seed because the fixtures use a fixed arithmetic pattern. Identical input and invocation produce byte-identical persisted results and rendered reports. Paths in errors and explicit output destinations naturally depend on the invocation. Result snapshots are local generated artifacts and should be regenerated rather than edited.

## Honesty boundary and fixture policy

Every value comparison is labelled hypothetical in code, CLI output, JSON figure_status, Markdown, and this README. Record counts and arithmetic are computed; task valuations are supplied, not measured. The engine does not discover tasks, predict revenue, measure time saved, or measure money saved. There is no savings command because no measured baseline is available.

Synthetic JSON has `synthetic: true` at root and on each record. JSON does not allow header comments, so its accompanying SYNTHETIC.md starts with a synthetic header comment; every fixture file has an internal synthetic label. Expectations are independent hand calculations: 40 selected tasks at 100 = 4000; 20 alternatives at 150 plus 20 at 80 = 4600; 20 positive gaps at 50 = 1000. Exactly the even-numbered decisions are dominated. Test mutations demonstrate computation rather than hardcoded outputs. Synthetic accuracy is evidence of arithmetic correctness, not real-world valuation accuracy.

## Failure modes

Malformed JSON returns ParseError with file, line, and column. Duplicate JSON keys are rejected, with file and line 1 (object-key validation does not retain token locations). Unreadable UTF-8 inputs name the file and line 1. Missing directories or result snapshots return MissingInput with a usage hint. SchemaError identifies offending fields or records and the input path. Future dates relative to as_of, duplicate IDs, invalid selections, inconsistent provenance, oversized strings, and invalid amounts fail the whole run; nothing is silently dropped. Unsupported CSV/YAML directories name the unsupported file and line 1.

WriteError names a bad destination. Atomic replacement uses a temporary file beside the destination and removes it on failure, preserving any existing destination. Fixture generation can leave complete earlier fixture files if a later write fails; reports and result snapshots use atomic writes. No claim is made that imported result snapshots are tamper-proof. Invalid JSON and missing banner fields in snapshots fail with named errors.

## Project factory evidence and improvement hook

Hypothesis: explicit inputs and deterministic tested comparisons give Henry reliable arithmetic for assessing what a chosen task gives up. Acceptance: all 200 planted records reconcile, all 20 planted dominated choices found, zero false positives, demo under 5 seconds, adversarial cases fail by documented rules. Local test and subprocess timing evidence is in EVIDENCE.md. Real use has not occurred and no time or money savings have been measured.

After two weeks of real use, hand-check a sample of at least 20 decisions (or all decisions if fewer). The primary metric is the fraction whose selected ID, best feasible alternative ID, foregone value, gap, or dominated flag disagrees with the operator's hand calculation. Record sample size, errors, run count, dated observations, and causes in a private trial log, not shipped data. If error rate exceeds 10 percent, fix the most frequent cause and rerun the hand check, or kill with a recorded reason. If unused, record that and kill. This is a planned evidence-based improvement, not a completed trial.

VERDICT.md records the current pending verdict and the post-window decision rules. The two-week window starts at first real use; no final verdict is invented before evidence exists.
