#!/usr/bin/env bash
# Usage: bash scripts/run_api_local.sh PROVIDER
# Builds predictions (apply check), then grades them three times locally and writes ground truth.
set -uo pipefail
prov="${1:?provider}"
python3 scripts/build_api_predictions.py "$prov" || exit 1
pred="predictions_api_${prov}.jsonl"
if [ ! -s "$pred" ]; then echo "No patches to grade for $prov"; exit 1; fi
for i in 1 2 3; do
  echo "=== local pass $i ($prov)"
  python -m swebench.harness.run_evaluation -p "$pred" -id "api_${prov}_local_rep$i" --max_workers 2
done
python3 scripts/api_ground_truth.py "$prov"
