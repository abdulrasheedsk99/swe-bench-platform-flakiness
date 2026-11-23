#!/usr/bin/env python3
"""Usage: python3 scripts/build_api_predictions.py PROVIDER

Reads trajectories_api/PROVIDER/preds.json, checks that every non-empty patch applies
cleanly (git apply --check inside the instance's own evaluation image), then writes
  predictions_api_PROVIDER.jsonl  (patches that apply; these are frozen and graded)
  api_status_PROVIDER.csv         (one row per planned instance, including failures)
Patches are never edited: they are copied byte for byte.
"""
import collections
import csv
import json
import os
import subprocess
import sys

GENERATORS = {
    "deepseek": "deepseek/deepseek-flash",
    "openai": "openai/gpt-6-luna",
    "gemini": "gemini/gemini-3.1-flash-lite",
    "anthropic": "anthropic/claude-haiku-5-5",
}


def image_for(iid):
    return "swebench/sweb.eval.x86_64." + iid.replace("__", "_1776_") + ":latest"


def apply_ok(iid, patch):
    cmd = ["docker", "run", "--rm", "-i", "--platform", "linux/amd64", image_for(iid),
           "bash", "-c", "cd /testbed && git apply --check -"]
    r = subprocess.run(cmd, input=patch.encode(), capture_output=True, timeout=300)
    note = r.stderr.decode(errors="replace").strip().replace("\n", " ")[:160] if r.returncode else ""
    return r.returncode == 0, note


def exit_status(prov, iid):
    path = "trajectories_api/%s/%s/%s.traj.json" % (prov, iid, iid)
    try:
        return json.load(open(path)).get("info", {}).get("exit_status")
    except Exception:
        return None


def main(prov):
    subset = [l.strip() for l in open("scripts/api_subset.txt") if l.strip()]
    preds_path = "trajectories_api/%s/preds.json" % prov
    preds = json.load(open(preds_path)) if os.path.exists(preds_path) else {}
    rows, keep = [], []
    for iid in subset:
        patch = (preds.get(iid) or {}).get("model_patch") or ""
        status = exit_status(prov, iid) or ("not run" if iid not in preds else "unknown")
        if not patch.strip():
            rows.append((prov, iid, status, 0, "no", "empty patch"))
            continue
        ok, note = apply_ok(iid, patch)
        rows.append((prov, iid, status, len(patch), "yes" if ok else "no", note))
        if ok:
            keep.append({"instance_id": iid, "model_name_or_path": "api-" + prov,
                         "generator": GENERATORS.get(prov, prov), "model_patch": patch})
    with open("api_status_%s.csv" % prov, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["provider", "instance_id", "exit_status", "patch_chars", "applies", "note"])
        w.writerows(rows)
    with open("predictions_api_%s.jsonl" % prov, "w") as f:
        for k in keep:
            f.write(json.dumps(k) + "\n")
    if not keep:
        os.remove("predictions_api_%s.jsonl" % prov)
    print("provider %s: %d planned | %d with a patch | %d apply cleanly (graded)" % (
        prov, len(subset), sum(1 for r in rows if r[3] > 0), len(keep)))
    print("exit statuses:", dict(collections.Counter(r[2] for r in rows)))
    for r in rows:
        print("  %-38s %-14s patch=%-6s applies=%s %s" % (r[1], r[2], r[3], r[4], r[5]))


if __name__ == "__main__":
    main(sys.argv[1])
