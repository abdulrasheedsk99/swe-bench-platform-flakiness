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
