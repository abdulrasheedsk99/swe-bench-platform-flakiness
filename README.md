# SWE-bench Platform Flakiness

Empirical study of whether SWE-bench's Docker-based evaluation harness
produces identical grading verdicts across different free execution
tiers. Companion repository for the TSE submission "Platform Dependency
Without Flakiness: Compatibility Limits of Free CI Infrastructure for
SWE-Bench Evaluation."

## Repository structure

- patches/ -- 18 frozen, git-apply-verified agent-generated patches
  (mini-swe-agent + local Gemma 4, one-shot per instance)
- predictions_gold.jsonl -- 6 gold-reference patches extracted directly
  from the SWE-bench Lite dataset, added as a RESOLVED-verdict control arm
- predictions.jsonl / ground_truth_local.json -- full 24-instance set
  (18 agent + 6 gold)
- predictions_clean23.jsonl / ground_truth_clean23.json -- the 23-instance
  set used for the paper's headline statistic, excluding
  matplotlib__matplotlib-23913 (see below)
- scripts/swebench.yaml -- mini-swe-agent config used for patch generation
- instances.txt -- full instance-selection log across all sampling rounds
- trajectories_v3/, trajectories_backfill/, trajectories_backfill2/ --
  full patch-generation provenance, including unsuccessful attempts
- evidence/ -- permanently committed tier-comparison and diagnostic
  reports (standard-tier and ARM64-tier JSON outputs, local-vs-standard
  matplotlib-23913 repetition data), pulled from CI before artifact expiry
- gold-reference.gold_local_rep*.json -- local-tier validation of the
  gold-patch arm (3 reps, all 6 resolved identically each time)
- .github/workflows/ -- every CI workflow used, including one-off
  diagnostics (manifest inspection, dockerd check, CPU/steal-time check,
  the matplotlib-23913 repetition study)
- FINDINGS.md -- narrative log of the ubuntu-slim exclusion, the ARM64
  exclusion, and the matplotlib-23913 timing-flakiness discovery

## matplotlib__matplotlib-23913: a discovered timing-flaky instance

This instance was found, during this study, to depend on a hardcoded
1-second wall-clock threshold inside matplotlib's own legend.py
(_find_best_position), not on anything about the patch being graded.
It is excluded from the paper's clean 23-instance statistical set for the
same reason Brown et al.'s 34 flagged SWE-bench Lite instances are
excluded from the initial 300 -- see FINDINGS.md for the full evidence
chain (source excerpt, repeated-trial data, CPU/steal-time check).

## Reproducing the core result

Install:

    pip install swebench==4.1.0

Run:

    python -m swebench.harness.run_evaluation -p predictions_clean23.jsonl -id my_run --max_workers 2

Compare resolved_ids/unresolved_ids in the resulting report against
ground_truth_clean23.json.

## Harness version

All results use swebench==4.1.0. Findings specific to a hardcoded
architecture default (see FINDINGS.md) are tied to this version and may
be resolved in future releases.
