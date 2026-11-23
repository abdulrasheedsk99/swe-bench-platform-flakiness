#!/usr/bin/env python3
"""Usage: python3 scripts/api_ground_truth.py PROVIDER

Reads the three local grading reports for PROVIDER and writes
  ground_truth_api_PROVIDER.json  (instances with the same verdict in all three passes)
  excluded_api_PROVIDER.json      (instances with an error or a verdict that varied)
"""
import glob
import json
import sys


def main(prov):
    pred_ids = [json.loads(l)["instance_id"] for l in open("predictions_api_%s.jsonl" % prov) if l.strip()]
    reps = []
    for i in (1, 2, 3):
        files = glob.glob("*.api_%s_local_rep%d.json" % (prov, i))
        if len(files) != 1:
            sys.exit("expected exactly one report for local rep%d, found %s" % (i, files))
        reps.append(json.load(open(files[0])))
    gt, excluded = {}, {}
    for iid in pred_ids:
        verdicts = []
        for r in reps:
            if iid in r.get("resolved_ids", []):
                verdicts.append("RESOLVED")
            elif iid in r.get("unresolved_ids", []):
                verdicts.append("UNRESOLVED")
            else:
                verdicts.append("ERROR")
        if len(set(verdicts)) == 1 and verdicts[0] != "ERROR":
            gt[iid] = verdicts[0]
        else:
            excluded[iid] = verdicts
    json.dump(gt, open("ground_truth_api_%s.json" % prov, "w"), indent=2, sort_keys=True)
    json.dump(excluded, open("excluded_api_%s.json" % prov, "w"), indent=2, sort_keys=True)
    n_res = sum(1 for v in gt.values() if v == "RESOLVED")
    print("%s: %d graded | %d RESOLVED | %d UNRESOLVED | %d excluded (error or unstable)" % (
        prov, len(pred_ids), n_res, len(gt) - n_res, len(excluded)))
    for iid, v in excluded.items():
        print("  EXCLUDED", iid, v)


if __name__ == "__main__":
    main(sys.argv[1])
