#!/usr/bin/env bash
# Usage: bash scripts/gen_provider.sh deepseek|openai|gemini|anthropic [WORKERS]
set -uo pipefail
prov="${1:?provider}"; workers="${2:-1}"
source "$HOME/.swebench-keys.env"
export MSWEA_COST_TRACKING=ignore_errors
filter="^($(paste -s -d '|' scripts/api_subset.txt))\$"
out="trajectories_api/$prov"
mkdir -p "$out"
echo "generation: $prov | $(wc -l < scripts/api_subset.txt | tr -d ' ') instances | workers $workers | out $out"
start=$(date +%s)
perl -e 'alarm 14400; exec @ARGV' mini-extra swebench --config "scripts/swebench-$prov.yaml" --subset lite --split test --filter "$filter" --workers "$workers" --output "$out" || echo "mini-extra exited with status $?"
echo "elapsed: $(( $(date +%s) - start ))s"
python3 scripts/traj_usage.py "$out" "$prov" | tee "$out/usage_summary.txt"
