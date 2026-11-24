# Findings Log

## ubuntu-slim excluded as a quantitative tier (2026-09-14)

GitHub's `ubuntu-slim` runner (1 vCPU, 5GB RAM, 15-min job cap, GA Jan 2026)
cannot run the standard SWE-bench evaluation harness. Diagnostic workflow
(.github/workflows/check-dockerd.yml) confirmed the Docker CLI is present
(v29.6.2) but the `dockerd` daemon binary is absent entirely from the image
(`which dockerd` -> NO_DOCKERD_BINARY). This is consistent with GitHub's own
description of ubuntu-slim executing jobs inside a container rather than a
full VM — nested container support was never included.

Deliberately not worked around (e.g. installing dockerd via apt, DinD
sidecar, Podman substitution): any such fix would mean the harness is no
longer running under ubuntu-slim's actual constraints, answering a
different question than the one this study asks.

Treated as a standalone finding for RQ3 rather than a fourth quantitative
tier: the most resource-constrained free GitHub-hosted runner is
structurally incompatible with the standard SWE-bench harness, independent
of any reliability question.

Quantitative comparison proceeds with three tiers: local (M4 Pro),
GitHub-hosted standard (ubuntu-latest), GitHub-hosted ARM64
(ubuntu-24.04-arm).

## ARM64 excluded as a quantitative tier (2026-09-14)

GitHub's free ubuntu-24.04-arm runner cannot run SWE-bench 4.1.0's standard
evaluation harness, for a root cause distinct from and more fundamental
than image availability.

Evidence chain:
1. `docker pull` of a Lite instance image on the ARM64 runner fails:
   "no matching manifest for linux/arm64/v8 in the manifest list entries."
2. `docker manifest inspect` confirms only two platform entries exist for
   the image: linux/amd64, and one "unknown/unknown" (attestation blob).
   No arm64 entry.
3. Bypassing the registry entirely (`-n none`, forcing a from-scratch
   local `docker build`) reproduces failure differently: the very first
   Dockerfile RUN command (a plain `apt install`) exits 255 with no real
   apt error text -- consistent with an exec-format failure from trying
   to run an x86_64 binary with no QEMU emulation registered.
4. Source-level root cause (swebench/harness/test_spec/test_spec.py):
   `arch: str = "x86_64"` is a hardcoded default. A `platform` property a
   few lines away has dormant, unused ARM64-aware logic
   (`elif self.arch == "arm64": return "linux/arm64/v8"`), but
   `run_evaluation`'s public CLI exposes no flag to ever set arch to
   anything but the x86_64 default.

Conclusion: SWE-bench 4.1.0's documented, public interface cannot target
ARM64 at all, independent of network, registry, or instance choice. This
directly reproduces and precisely localizes the SWE-bench GitHub issue
("ARM64 harness support: fix x86-only Docker assumptions") found during
initial literature review -- not just citing the issue, but independently
diagnosing its exact mechanism.

Not worked around, same reasoning as ubuntu-slim: monkey-patching arch to
"arm64" would test whether SWE-bench's unexposed/unvalidated ARM64 code
path works at all, a different research question than this study asks,
and one with no guarantee the dormant path is even functional.

Final tier set for quantitative comparison: local (M4 Pro) and GitHub
standard (ubuntu-latest) only, both showing 3/3 reps with zero
discrepancies across all 18 instances. ubuntu-slim and ARM64 stand as two
independent, precisely-diagnosed structural exclusion findings.

## matplotlib__matplotlib-23913 flips on GitHub Standard (September 2026)

The gold patch for this instance graded RESOLVED in every local pass (3 initial
passes and 15 later repetitions) but not on the GitHub Standard runner: a first
batch of 5 repetitions returned 5 of 5 RESOLVED, and a second batch of 15
repetitions about 15 minutes later returned 15 of 15 UNRESOLVED.

Evidence chain:
1. The two FAIL_TO_PASS tests, `test_legend_draggable[True]` and
   `test_legend_draggable[False]`, passed in every attempt in both blocks. The flip
   comes from an unrelated PASS_TO_PASS test, `test_warn_big_data_best_loc`.
2. Source: `legend.py`, function `_find_best_position`, times its own placement
   search with `time.perf_counter()` and emits a `UserWarning` only if the search
   takes longer than a hardcoded one second. The test plots 1,000 lines to push the
   search past that mark and asserts the warning. Whether it passes depends on how
   fast the machine runs the search, not on the patch.
3. Confounds checked: the runner OS image was identical across both batches
   (`ubuntu-24.04`, build `20260907.300.1`), and the evaluation image's build date
   (August 15) predates both windows.
4. CPU steal time was 0 and a ten-iteration microbenchmark had a spread of
   0.0001 s on a fresh runner. This is one short sample on an ephemeral runner and
   does not rule out contention.

Interpretation: the local tier runs the harness under Docker's x86_64 emulation,
whose overhead is consistent with pushing the search past one second every time
(the local tier's stability is then not superior stability). Native GitHub
execution sits near the threshold. The elapsed time of the search was not measured
on either tier, and the GitHub-side mechanism (one borderline machine profile
versus different hardware in the two windows) is undetermined; telling them apart
would need trials interleaved across time windows.

Timeline (UTC, 15 September 2026; times from `evidence/github-archive/run-index/`):

| Window | Run | Started | Finished | matplotlib-23913 |
|---|---|---|---|---|
| First flip | `tier-standard-full` 34916160840 (24 instances, one repetition) | 01:09:53 | 01:27:32 | UNRESOLVED |
| Batch 1 | `diagnose-mismatch` 34917591663 (5 repetitions) | 01:31:17 | 01:43:18 | 5 of 5 RESOLVED |
| Batch 2 | `diagnose-mismatch` 34919380657 (15 repetitions) | 01:58:46 | 02:28:17 | 15 of 15 UNRESOLVED |

Batch 2 started 15 minutes after batch 1 finished. The 24-instance run had one
repetition only; the flip prompted the two targeted batches. In every UNRESOLVED
repetition the only failing test is `test_warn_big_data_best_loc` (both
FAIL_TO_PASS tests pass). The Actions run for batch 1 is marked "failure" because
the workflow's final summary step hit a Python `IndentationError` after all five
repetitions and the artifact upload had finished; the workflow was fixed in the
next commit (79774ab). All three runs used runner image `ubuntu-24.04` version
`20260907.300.1`.

Files: `evidence/matplotlib-23913-investigation/` (the 15 local repetition
reports), `evidence/github-archive/` (GitHub-side logs, reports and the run
index; see the README) and the workflows `diagnose-mismatch.yml`,
`check-cpu-evidence.yml` and `check-image-identity.yml`.

Treatment in the paper: the instance is excluded from the clean 101-instance set
and counted separately (upper limit 5.3% on the disagreement rate when it is
included).
