#!/usr/bin/env python3
"""Re-implementation of the first gold-reference extension's seeded draw (seed 2026).

The original draw was run interactively and its script was not saved. This script
applies the procedure described in the paper -- fixed seed, a per-repository allocation
fixed before drawing, the stable pool (SWE-bench Lite minus the 34 instances Brown et
al. documented as non-deterministic, scripts/flaky34.txt), instances already used
excluded, and a cap of 500 PASS_TO_PASS tests -- with the same structure as
scripts/select_gold_ext2.py. Run it from the repository root; it writes
new_gold_candidates.reproduced.txt and compares it with the committed
new_gold_candidates.txt, printing MATCH or DIFFERENT. It never overwrites the
committed list.
"""
import collections
import json
import os
import random

from datasets import load_dataset

SEED = 2026
CAP = 500
ALLOC = {"django": 6, "sympy": 3, "scikit-learn": 3, "sphinx": 3, "pytest": 3,
         "astropy": 2, "xarray": 2, "pylint": 2, "seaborn": 2, "matplotlib": 2,
         "requests": 2, "flask": 1}

used = set()
used |= {l.strip() for l in open("instances.txt") if l.strip()}
for f in ("ground_truth_local.json", "ground_truth_clean23.json", "ground_truth_18_only_backup.json"):
    if os.path.exists(f):
        used |= set(json.load(open(f)))
used.add("matplotlib__matplotlib-23913")
flaky = {l.strip() for l in open("scripts/flaky34.txt") if l.strip()}

rows = {r["instance_id"]: r for r in load_dataset("princeton-nlp/SWE-bench_Lite", split="test")}
print("Lite instances:", len(rows), "| documented flaky:", len(flaky & set(rows)),
      "| stable pool:", len(set(rows) - flaky), "| already used:", len(used & set(rows)))


def n_p2p(row):
    v = row["PASS_TO_PASS"]
    return len(json.loads(v) if isinstance(v, str) else v)


by_repo = collections.defaultdict(list)
lite_count = collections.Counter()
for iid, r in rows.items():
    repo = r["repo"].split("/")[1]
    lite_count[repo] += 1
    if iid in flaky or iid in used or n_p2p(r) > CAP:
        continue
    by_repo[repo].append(iid)

rng = random.Random(SEED)
chosen = []
print("%-14s %5s %9s %9s %6s" % ("repo", "Lite", "eligible", "allocated", "drawn"))
for repo in sorted(lite_count):
    pool = sorted(by_repo[repo])
    k = min(ALLOC.get(repo, 0), len(pool))
    draw = sorted(rng.sample(pool, k)) if k else []
    chosen += draw
    print("%-14s %5d %9d %9d %6d" % (repo, lite_count[repo], len(pool), ALLOC.get(repo, 0), len(draw)))

with open("new_gold_candidates.reproduced.txt", "w") as f:
    f.write("\n".join(chosen) + "\n")
committed = [l.strip() for l in open("new_gold_candidates.txt") if l.strip()]
print("drawn:", len(chosen), "| committed list:", len(committed))
print("MATCH" if sorted(chosen) == sorted(committed) else "DIFFERENT")
