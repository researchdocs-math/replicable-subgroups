# Subgroups That Replicate

Quorum mines short conjunctions with positive outcome associations supported
in a prespecified number of heterogeneous sources. It preserves the exact
rejection set of fixed-family Bonferroni partial-conjunction testing while
pruning branches and retiring sources using positive-support certificates.

**Authors:** Cemil Emre Yavas and Lei Chen, School of Computing, Georgia Southern
University. **Contact:** cemil@fairesresearch.org. **Release:** 1.0.0.

## Install

Use Python 3.12 on macOS or Linux. Create an isolated environment and install
the pinned CPU dependencies:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

The reference environment was Python 3.12.1, NumPy 1.26.3, SciPy 1.11.4, and
pandas 2.2.1 on arm64 macOS 14.8.1. Independent simulations used eight CPU
processes on a 12-core system with 18 GB memory. Each process limits numerical
libraries to one thread. Serial benchmarks run separately from the simulation
pool. The largest measured vectorized case used about 580 MiB in a fresh
process; leave additional memory for parallel workers and data reconstruction.

## Verify and reproduce

From this directory:

```sh
python scripts/verify_results.py
python scripts/reproduce.py --smoke --workers 2
python scripts/reproduce.py --workers 8
```

The first command checks the bundled deterministic results. The smoke command
verifies the bound and exact-set tests, then runs two replicates per simulation
condition into separately named smoke files. The full command repeats all
13,000 statistical trials, 25 matched search configurations, replication-count
sensitivities, three additional large-family cases, and fresh-process memory
measurements. It writes numerical results under `results/` and checks them
against `expected/signatures.json`. Full runs replace the recorded results;
use a fresh extraction to preserve an untouched reference copy.

The default full workflow uses the provided processed matrices. To reconstruct
them from the original sources first:

```sh
python scripts/reproduce.py --workers 8 --rebuild-data
```

`download_data.py` retrieves seven original archives with three concurrent
transfers and validates their SHA-256 checksums. About 194 MiB of raw archives
are downloaded. `prepare_data.py` rebuilds the common predicates and independent
design/inference splits. Its random seed is 20261006. Only source-derived
matrices and predicate metadata are needed to run the experimental suite.

For the optional synchronized support-counting experiment, install the
accelerator dependencies and select the GPU run:

```sh
python -m pip install -r requirements-gpu.txt
python scripts/benchmark_devices.py
```

The script detects Metal or CUDA, checks every GPU count against exact CPU
bitsets, and records device timings. The reference GPU results used PyTorch
2.4.1 and Metal. Support counts are identical; timing and peak-memory values
naturally depend on hardware, operating system, load, and library build.
Deterministic checks exclude elapsed time and peak memory, and compare exact
rule membership and contingency counts rather than platform-sensitive decimal
renderings of distribution tails.

## Project map

| File or directory | Purpose |
| --- | --- |
| `src/replicamine/core.py` | Source tables, family cardinalities, tests, certificates, and five matched search implementations |
| `src/replicamine/synthetic.py` | Heterogeneous generators and analytic truth for every rule |
| `scripts/verify_algorithm.py` | 38,753 table-bound checks and 120 randomized exact-set comparisons |
| `scripts/run_simulations.py` | 10,000 principal trials; four inference procedures per trial |
| `scripts/run_stress.py` | 3,000 dependent-source and boundary-null trials |
| `scripts/run_benchmarks.py` | Rotated-order runtime comparisons, source-count sensitivities, and large-family runs |
| `scripts/measure_memory.py` | Nine independent-process memory measurements |
| `scripts/benchmark_devices.py` | Equal-count bitset, NumPy, and GPU microbenchmark |
| `scripts/summarize_results.py` | CSV summaries, exact binomial intervals, and discovery totals |
| `scripts/download_data.py` | Verified acquisition of original public-data archives |
| `scripts/prepare_data.py` | Common-schema preprocessing and design/inference splitting |
| `scripts/verify_results.py` | Deterministic semantic checksums for experiments and matrices |
| `scripts/reproduce.py` | Complete workflow and smoke mode |
| `data/processed/` | Three binary benchmark matrices, source descriptions, and predicate definitions |
| `data/sources.json` | Original URLs, archive lengths, and SHA-256 digests |
| `data/ATTRIBUTION.md` | Dataset credits, licenses, transformations, and interpretation |
| `results/` | Recorded per-run outputs, source tables, and numerical summaries |
| `expected/signatures.json` | Fixed reference signatures for independent reruns |
| `.github/workflows/verify.yml` | Automated CPU smoke and result-integrity checks |
| `CITATION.cff` | Machine-readable software citation and author information |

## Recorded results

The 10,000 principal trials produce 40,000 JSON records because each trial
compares four inference procedures. Every Quorum discovery set agrees with
independent full-family calculations. The three additional stress settings
contain 1,000 trials each and record 12, 26, and 33 false-claim runs for shared
null sources, the r=1 global null, and the r=5 four-signal/one-null setting.

The 25 matched runtime configurations use five repetitions and five methods.
Five replication-count sensitivity runs and 15 large-family runs bring
`benchmark_all.jsonl` to 645 records. `support` denotes the margin-bound
comparator; `positive` denotes positive-bound pruning without source retirement;
`quorum` includes retirement and deferred negative intersections.

| Domain | Inference rows by source | Replication requirement | Family size | Discoveries | Subset-minimal |
| --- | --- | --- | --- | --- | --- |
| Heart sites | 243 / 235 / 94 / 113 | 3 of 4 | 3,203 | 0 | 0 |
| Wine types | 1,088 / 3,169 | 2 of 2 | 31,713 | 36 | 1 |
| Census states | 8,000 each in 5 states | 4 of 5 | 7,640 | 388 | 6 |

All primary analyses use alpha 0.05. The family counts every legal conjunction
up to the specified depth with at most one literal per attribute; the
multiplicity factor is unchanged by outcome-dependent pruning. Different
values of r define separately configured analyses. The benchmark associations
are descriptive and require valid within-source tests for an inferential
interpretation. They are not causal estimates.

## Data and output formats

Each NPZ contains Boolean arrays `X0`, `y0`, `X1`, `y1`, and so on. A matching
JSON file defines source order, literal names, attribute groups, predicates,
and outcome counts. Intervals use `(lower, upper]`; infinite endpoints are
encoded as strings. Rule indices are zero-based literal indices.
`rules_*.json` records each rejected rule, a readable description, its
partial-conjunction p-value, and all source contingency tables and observed
risk differences. Simulation files are one JSON object per line, with fixed
seeds and indicators of false replication and planted-rule recovery. Timings
are seconds. Fresh-process memory values are bytes in `memory.json`;
per-run RSS in `benchmark_all.jsonl` is process-cumulative and should not be
used to compare isolated algorithm memory. CSVs are numerical summaries of
these recorded runs.

## License and citation

The software is released under the MIT license in `LICENSE`. Dataset credits
and source-specific terms are in `data/ATTRIBUTION.md`. Cite the software using
`CITATION.cff` and credit the original datasets when reusing the matrices.
