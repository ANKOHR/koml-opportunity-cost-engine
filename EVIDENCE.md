# Local build evidence

Measured on 2026-10-01 using Python 3.12.10 on Windows, CPU only.

* pytest: 36 passed. Required acceptance tests and adversarial tests pass.
* Installed koce subprocess demo (fixtures, run, Markdown report): 0.5922 seconds, exit 0 for all three commands, no tracebacks.
* Installed koce JSON report subprocess: 0.1797 seconds, exit 0.
* 200 synthetic records, 40 decisions, 20 dominated choices, zero false positives.
* Hypothetical selected total 4000.00 GBP; foregone total 4600.00 GBP; avoidable gap 1000.00 GBP. All reconcile with independent expectations and each decision is checked.
* Identical runs give byte-identical result snapshots and fixture files.
* Corrupting the first alternative from 150.00 to 200.25 changes foregone total to 4650.25 and gap total to 1050.25. Outputs are computed from records, not expectations.json.
* Hand-written five-record illustrative input: hypothetical selected 120.00, foregone 160.00, gap 40.00, one dominated decision.

These timings measure local command execution, not time saved. No real trial, measured savings, buyer evidence, or usage evidence exists. The improvement hook and final verdict await the two-week real-use window.
