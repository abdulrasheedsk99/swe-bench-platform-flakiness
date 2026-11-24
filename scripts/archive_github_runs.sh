#!/usr/bin/env bash
# Archive GitHub Actions evidence into the repository before it expires.
#
# GitHub keeps run logs and artifacts for 90 days by default, so the diagnostic runs
# from mid-September 2026 disappear in December. This script, run by the repository
# owner with an authenticated `gh`, saves for every workflow in .github/workflows:
#   - a TSV of every run (id, created, updated, conclusion, commit, title), which also
#     records the dispatch times needed to see how closely repetitions ran together;
# and, for the early and diagnostic workflows only (the later batches already commit
# their reports), the full log text and any artifacts of each run.
#
# Usage:   scripts/archive_github_runs.sh            (from the repository root)
# Output:  evidence/github-archive/
# It only reads from GitHub and writes new files (it removes only the empty error files it creates itself).
set -u
OUT="evidence/github-archive"
mkdir -p "$OUT/run-index"

ALL_WORKFLOWS=$(ls .github/workflows/*.yml | xargs -n1 basename)
FULL_ARCHIVE="check-cpu-evidence.yml check-dockerd.yml check-image-identity.yml check-local-build-arm64.yml check-manifest.yml diagnose-mismatch.yml tier-arm64-full.yml tier-arm64-test.yml tier-slim-test.yml tier-standard-full.yml tier-standard-test.yml swebench5-check.yml"

for wf in $ALL_WORKFLOWS; do
  idx="$OUT/run-index/${wf%.yml}.tsv"
  printf 'run_id\tcreated_at\tupdated_at\tconclusion\thead_sha\ttitle\n' > "$idx"
  gh run list --workflow "$wf" --limit 300 \
    --json databaseId,createdAt,updatedAt,conclusion,headSha,displayTitle \
    --jq '.[] | [.databaseId,.createdAt,.updatedAt,.conclusion,.headSha[0:7],.displayTitle] | @tsv' >> "$idx" \
    || echo "could not list runs for $wf" >&2
  echo "indexed $wf: $(($(wc -l < "$idx") - 1)) runs"
done

for wf in $FULL_ARCHIVE; do
  idx="$OUT/run-index/${wf%.yml}.tsv"
  [ -f "$idx" ] || continue
  tail -n +2 "$idx" | cut -f1 | while read -r id; do
    dir="$OUT/${wf%.yml}/$id"
    [ -d "$dir" ] && continue
    mkdir -p "$dir"
    gh run view "$id" --log > "$dir/run.log" 2> "$dir/run.log.err" || echo "no log for $wf run $id" >&2
    [ -s "$dir/run.log.err" ] || rm -f "$dir/run.log.err"
    gh run download "$id" -D "$dir/artifacts" 2>/dev/null || true
    echo "archived $wf run $id"
  done
done
echo "done: $(du -sh "$OUT" | cut -f1) in $OUT"
