#!/usr/bin/env python3
"""Draw the second gold-reference extension (run from the repository root).

Pool: SWE-bench Lite, minus the 34 instances Brown et al. documented as
non-deterministic (scripts/flaky34.txt), minus every instance already used in this
study, minus matplotlib__matplotlib-23913, restricted to instances with at most
500 PASS_TO_PASS tests. The seed and the per-repository allocation below were fixed
before the first draw. Output: new_gold_candidates2.txt and a tally table.
"""
import collections
import json
import os
import random

from datasets import load_dataset

SEED = 2027
CAP = 500
ALLOC = {"django": 14, "sympy": 10, "scikit-learn": 5, "sphinx": 5, "matplotlib": 5,
         "pytest": 5, "astropy": 2, "xarray": 2, "pylint": 2, "seaborn": 1}

used = set()
for f in ("instances.txt", "new_gold_candidates.txt"):
    used |= {l.strip() for l in open(f) if l.strip()}
for f in ("ground_truth_local.json", "ground_truth_clean23.json",
          "ground_truth_gold_ext.json", "ground_truth_18_only_backup.json"):
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
with open("new_gold_candidates2.txt", "w") as f:
    f.write("\n".join(chosen) + "\n")
print("drawn:", len(chosen), "| wrote new_gold_candidates2.txt")
