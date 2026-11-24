"""Count how many of the 101 clean instances also belong to SWE-bench Verified.

Run from the repository root with the project virtualenv active:
    python scripts/verified_overlap.py
Needs network access to Hugging Face (datasets). Writes clean_in_verified.txt.
"""
import json
from collections import Counter
from datasets import load_dataset

FILES = ["ground_truth_clean23.json", "ground_truth_gold_ext.json", "ground_truth_gold_ext2.json"]
clean = set()
for name in FILES:
    ids = set(json.load(open(name)))
    print(f"{name}: {len(ids)} instances; overlap with earlier files: {len(ids & clean)}")
    clean |= ids
print("clean instances:", len(clean))

lite = {r["instance_id"] for r in load_dataset("SWE-bench/SWE-bench_Lite", split="test")}
verified = {r["instance_id"] for r in load_dataset("SWE-bench/SWE-bench_Verified", split="test")}
print("Lite size:", len(lite), "| Verified size:", len(verified))
print("clean instances found in Lite:", len(clean & lite))
both = sorted(clean & verified)
print("clean instances also in Verified:", len(both))
print("by repository:", dict(Counter(i.split("__")[0] + "/" + i.split("__")[1].rsplit("-", 1)[0] for i in both)))
open("clean_in_verified.txt", "w").write("\n".join(both) + "\n")
print("wrote clean_in_verified.txt")
