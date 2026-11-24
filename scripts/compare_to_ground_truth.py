#!/usr/bin/env python3
"""Compare SWE-bench evaluation reports with a ground-truth file.

Usage (from the repository root):
    python scripts/compare_to_ground_truth.py GROUND_TRUTH.json REPORT.json [REPORT.json ...]

GROUND_TRUTH.json maps instance_id -> "RESOLVED" or "UNRESOLVED". Each REPORT.json is
a report written by swebench.harness.run_evaluation. For every report the script
prints how many ground-truth instances were graded, how many disagree, and which.
Exit status is 0 when every report agrees on every instance, 1 otherwise.
"""
import json
import sys


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    truth = json.load(open(argv[1]))
    problems = 0
    for path in argv[2:]:
        report = json.load(open(path))
        resolved = set(report.get("resolved_ids", []))
        graded = set(report.get("completed_ids", []))
        not_graded = sorted(i for i in truth if i not in graded)
        disagree = sorted(i for i, v in truth.items()
                          if i in graded and (i in resolved) != (v == "RESOLVED"))
        print("%s: %d ground-truth instances, %d graded, %d disagreements, %d not graded"
              % (path, len(truth), len(truth) - len(not_graded), len(disagree), len(not_graded)))
        for i in disagree:
            print("  DISAGREES:", i, "(ground truth %s)" % truth[i])
        for i in not_graded:
            print("  NOT GRADED:", i)
        problems += len(disagree) + len(not_graded)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
