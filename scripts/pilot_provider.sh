#!/usr/bin/env bash
# Usage: bash scripts/pilot_provider.sh deepseek|openai|gemini|anthropic [STEP_LIMIT]
set -uo pipefail
prov="${1:?provider}"; steps="${2:-60}"
source "$HOME/.swebench-keys.env"
export MSWEA_COST_TRACKING=ignore_errors
iid="$(awk '/^django/{print; exit}' new_gold_candidates.txt)"
cfg="/tmp/pilot-$prov.yaml"
sed -E "s/step_limit:[[:space:]]*250/step_limit: $steps/" "scripts/swebench-$prov.yaml" > "$cfg"
grep -n 'step_limit\|model_name\|temperature' "$cfg"
out="trajectories_api_pilot2/$prov"
rm -rf "$out"
echo "pilot: $prov on $iid, step limit $steps"
start=$(date +%s)
perl -e 'alarm 1500; exec @ARGV' mini-extra swebench --config "$cfg" --subset lite --split test --filter "^${iid}\$" --workers 1 --output "$out" || echo "mini-extra exited with status $?"
echo "elapsed: $(( $(date +%s) - start ))s"
python3 scripts/traj_usage.py "$out" "$prov"
