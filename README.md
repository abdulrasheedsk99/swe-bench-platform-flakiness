# SWE-bench Platform Flakiness

Does SWE-bench's Docker harness give the same verdict for the same patch on
different free execution platforms? This is the companion repository for the
paper "Platform Dependency Without Flakiness: Compatibility Limits of Free CI
Infrastructure for SWE-Bench Evaluation" (submitted to IEEE Transactions on
Software Engineering). Every patch is frozen before any comparison, so the
execution platform is the only thing that varies.

## Results at a glance

| Question | Result |
|---|---|
| Clean instance set | 101 SWE-bench Lite instances covering all twelve repositories: 18 UNRESOLVED (small local model) and 83 RESOLVED (gold patches) |
| Local vs GitHub Standard (`ubuntu-latest`), gold + small-model arms | 0 disagreements in 303 paired comparisons (101 instances x 3 repetitions); exact two-sided 95% upper limit 3.6% per instance |
| Model arm | 52 patches from four API-served models on 14 instances: 156 more comparisons, 0 disagreements; UNRESOLVED-direction limit 18.5% -> 12.8% |
| Counting the excluded instance | 1 disagreement in 102 instances: upper limit 5.3% |
| Random draws only | 0 disagreements in 78 instances drawn at random from the stable pool: upper limit 4.6% |
| Harness 5.0.2 replay | All 153 clean-set predictions match the 4.1.0 ground truth |
| `ubuntu-slim` runner | Cannot run the harness: no `dockerd` binary |
| ARM64 runner | Cannot run the harness: x86_64 target hardcoded, no command-line override (4.1.0 and 5.0.2) |
| `matplotlib__matplotlib-23913` | Gold instance whose verdict flips on GitHub Standard; hardcoded one-second threshold in `legend.py` (see below and `FINDINGS.md`) |

The local ground truth runs under Docker's x86_64 emulation on Apple Silicon
(M4 Pro), not on a native x86_64 machine. The study uses SWE-bench Lite only,
three repetitions per tier, and instances with at most 500 `PASS_TO_PASS`
tests.

## What is where

| Stage | Instances | Predictions | Ground truth | GitHub Standard reports | Workflow |
|---|---|---|---|---|---|
| Initial arm (18 agent patches + 6 gold) | 24 | `predictions.jsonl` | `ground_truth_local.json` | `evidence/standard-tier/` (the 18 agent-patch instances) | `tier-standard-full.yml` |
| Clean initial set (without matplotlib-23913) | 23 | `predictions_clean23.jsonl` | `ground_truth_clean23.json` | `github_reports_clean23/` (all 23 instances) | `tier-standard-clean23.yml` |
| First gold extension (seed 2026) | 28 | `predictions_gold_ext.jsonl` | `ground_truth_gold_ext.json` | `github_reports_gold_ext/` | `tier-standard-gold-ext.yml` |
| Second gold extension (seed 2027) | 50 | `predictions_gold_ext2.jsonl` | `ground_truth_gold_ext2.json` | `github_reports_gold_ext2/` | `tier-standard-gold-ext2.yml` |
| Model arm (four API models, 52 patches) | 14 | `predictions_api_<provider>.jsonl` | `ground_truth_api_<provider>.json` | `github_reports_api/` | `tier-standard-api.yml` |
| Harness 5.0.2 replay (153 predictions) | 101 | all of the above | all of the above | `github_reports_v5/` | `tier-standard-v5.yml` |
| 5.0.2 probes on x86_64 and ARM64 | - | - | - | `github_reports_swebench5/` | `swebench5-check.yml` |

Other files:

- `patches/` -- the 18 frozen, `git apply`-verified patches from the small local
  model (mini-SWE-agent with Gemma 4 E4B, one attempt per instance).
- `gold-reference.*_local_rep*.json`, `gemma4-32k-mini-swe-agent.local_*_rep*.json`,
  `api-<provider>.api_<provider>_local_rep*.json` -- local-tier reports (three
  repetitions each) that the ground-truth files were built from.
- `excluded_*.json` -- instances that would have been dropped because their local
  verdicts were not identical across the three repetitions (empty for every batch).
- `api_status_<provider>.csv` -- per-instance generation status for the model arm.
- `trajectories_*/` -- generation trajectories and usage logs (small-model and API
  arms, including unsuccessful attempts). Scratch directories are git-ignored.
- `instances.txt`, `new_gold_candidates.txt`, `new_gold_candidates2.txt` -- the
  selection records for the initial arm and the two extensions.
- `evidence/` -- diagnostic reports pulled from CI before artifact expiry: the
  standard-tier and ARM64-tier runs and the matplotlib-23913 repetition data.
- `.github/workflows/` -- every CI workflow used, including one-off diagnostics
  (`check-dockerd`, `check-manifest`, `check-local-build-arm64`,
  `check-image-identity`, `check-cpu-evidence`, `diagnose-mismatch`).
- `FINDINGS.md` -- narrative log of the `ubuntu-slim` exclusion, the ARM64
  exclusion and the matplotlib-23913 investigation.

## Reproducing the headline result

Grading the frozen patches needs no API keys. The ground-truth files were
produced with `swebench==4.1.0`.

1. Install dependencies (Docker must be running; on Apple Silicon, set
   `DOCKER_DEFAULT_PLATFORM=linux/amd64` so the x86_64 images run under emulation):

       python -m venv .venv-swebench && source .venv-swebench/bin/activate
       pip install -r requirements.txt
       export DOCKER_DEFAULT_PLATFORM=linux/amd64

2. Grade one batch, here the second gold extension (repeat three times, with
   different `-id` values, to match the paper):

       python -m swebench.harness.run_evaluation -p predictions_gold_ext2.jsonl -id my_run_rep1 --max_workers 2

3. Compare the report with the ground truth:

       python scripts/compare_to_ground_truth.py ground_truth_gold_ext2.json gold-reference.my_run_rep1.json

   The script prints the number of disagreements and lists them. Expected result
   for every clean batch: 0 disagreements.

To reproduce the GitHub side, run the matching workflow from the Actions tab
(`workflow_dispatch`, input `rep_id` = `rep1`, `rep2`, `rep3`); each uses
`ubuntu-latest`, Python 3.11, `swebench==4.1.0` and two workers. The model-arm
workflow grades all four providers' predictions in one run.

The full batch-to-workflow map is in the table above. `tier-standard-v5.yml`
repeats every batch with `swebench==5.0.2` against the 4.1.0 ground truth.

## Instance selection

- Second extension (seed 2027): `scripts/select_gold_ext2.py` is the exact script
  that produced `new_gold_candidates2.txt` (fixed per-repository allocation, stable
  pool minus the 34 instances in `scripts/flaky34.txt`, 500-test cap). It needs the
  SWE-bench Lite dataset from Hugging Face (`princeton-nlp/SWE-bench_Lite`).
- First extension (seed 2026): the draw was run interactively and its script was not
  saved. The result is recorded in `new_gold_candidates.txt`, and the seed, the
  per-repository allocation, the pool definition and the 500-test cap are described
  in the paper. We tried to reconstruct the script by varying the pool, ordering and
  sampler details; no variant reproduced the committed list exactly, so none is
  included. The list itself, not a re-run of the draw, is the record.
- Initial 24-instance arm: selected before these scripts existed; its record is
  `instances.txt`.

`scripts/verified_overlap.py` lists which of the 101 clean instances also belong to SWE-bench
Verified: 24 of them (`clean_in_verified.txt`). All 24 agreed across tiers, like the rest.

## Patch generation (optional)

`scripts/gen_provider.sh`, `scripts/pilot_provider.sh` and the
`scripts/swebench-*.yaml` configs show how patches were generated with
mini-SWE-agent (version 2.4.6 for the API-model arm, installed separately).
Generation needs provider API keys, which are not part of this repository;
`scripts/setkey.sh` shows how they were supplied. The frozen patches are already
included, so none of this is needed to reproduce the grading results.

## matplotlib__matplotlib-23913

This gold instance flips between RESOLVED and UNRESOLVED on the GitHub Standard
runner. The flip comes from an unrelated `PASS_TO_PASS` test,
`test_warn_big_data_best_loc`, which asserts a warning that `legend.py`
(`_find_best_position`) emits only when its own placement search takes longer
than a hardcoded one second. Under local x86_64 emulation the test passed in
all 15 trials (15 of 15 RESOLVED), consistent with the search always exceeding one
second; on native GitHub execution it flipped (5 of 5 RESOLVED in one batch, 15 of
15 UNRESOLVED about 15 minutes later). The mechanism is inferred from the source and the verdict pattern; the
elapsed time was not measured on either tier. The instance is excluded from the
clean 101-instance set and counted separately (upper limit 5.3% when included).
See `FINDINGS.md` for the evidence.

## Archived GitHub Actions evidence

GitHub deletes run logs and artifacts after 90 days, so `scripts/archive_github_runs.sh`
saved them into `evidence/github-archive/` (archived 24 November 2026):

- `run-index/<workflow>.tsv`: every run of every workflow (run id, created and
  updated time in UTC, conclusion, commit, title). The dispatch times show how
  closely the repetitions ran: in every three-repetition batch they were
  dispatched within 13 minutes of one another, and within seconds for the
  extension and model batches.
- `<workflow>/<run id>/run.log`: the full log of each early and diagnostic run
  (Docker daemon check, image identity, manifest check, CPU check, slim and ARM64
  tests, the first 24-instance run, the matplotlib-23913 batches, the harness 5.0.2
  probe).
- `<workflow>/<run id>/artifacts/`: the reports and logs each run uploaded,
  including the per-repetition reports for the matplotlib-23913 batches.

Reports of the later batches (clean set, extensions, model patches, harness 5.0.2
replay) are committed in the `github_reports_*` folders. Their runs are indexed
here but their logs were not archived.

## Harness versions

Ground truth and the main comparison use `swebench==4.1.0`. The ARM64 and
`ubuntu-slim` findings are tied to 4.1.0 and were rechecked under 5.0.2 (the
architecture default is unchanged; the replay agrees on all 153 predictions).

## License

Code and scripts are released under the MIT License (see `LICENSE`). Gold-reference
patches, test names and instance data are taken from SWE-bench Lite and the
upstream projects it draws on, and keep their own licenses.

## Citation

Citation details will be added when the paper is published.
