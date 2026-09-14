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
