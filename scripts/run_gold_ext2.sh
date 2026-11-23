#!/usr/bin/env bash
# Grades the second gold extension three times locally and writes ground truth.
set -u
cd "$(dirname "$0")/.."
source .venv-swebench/bin/activate
export DOCKER_DEFAULT_PLATFORM=linux/amd64
python - <<'PY'
import json
from datasets import load_dataset
ids = [l.strip() for l in open('new_gold_candidates2.txt') if l.strip()]
ds = {r['instance_id']: r for r in load_dataset('princeton-nlp/SWE-bench_Lite', split='test')}
with open('predictions_gold_ext2.jsonl', 'w') as f:
    for iid in ids:
        f.write(json.dumps({'instance_id': iid, 'model_name_or_path': 'gold-reference', 'model_patch': ds[iid]['patch']}) + '\n')
print('wrote predictions_gold_ext2.jsonl with', len(ids), 'gold patches')
PY
df -h / | tail -1; docker system df
for i in 1 2 3; do
  python -m swebench.harness.run_evaluation -p predictions_gold_ext2.jsonl -id gold_ext2_local_rep$i --max_workers 2
done
python - <<'PY'
import json, os
ids = [l.strip() for l in open('new_gold_candidates2.txt') if l.strip()]
reps = []
for i in (1, 2, 3):
    p = f'gold-reference.gold_ext2_local_rep{i}.json'
    reps.append(json.load(open(p)) if os.path.exists(p) else None)
print('reports found:', sum(r is not None for r in reps), 'of 3')
stable, excluded = {}, {}
for iid in ids:
    v = []
    for r in reps:
        if r is None: v.append('NO_REPORT')
        elif iid in r.get('resolved_ids', []): v.append('RESOLVED')
        else: v.append('UNRESOLVED')
    (stable if v == ['RESOLVED'] * 3 else excluded)[iid] = v
json.dump({k: 'RESOLVED' for k in stable}, open('ground_truth_gold_ext2.json', 'w'), indent=1)
json.dump(excluded, open('excluded_gold_ext2.json', 'w'), indent=1)
print('stably RESOLVED in all 3 reps:', len(stable), '| excluded:', len(excluded))
for k, v in excluded.items(): print('  excluded', k, v)
PY
