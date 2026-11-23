#!/usr/bin/env bash
cd "$(dirname "$0")/.."
export DOCKER_DEFAULT_PLATFORM=linux/amd64
missing=0
while read -r iid; do
  [ -z "$iid" ] && continue
  img="swebench/sweb.eval.x86_64.${iid/__/_1776_}:latest"
  if docker image inspect "$img" >/dev/null 2>&1; then
    echo "have    $iid"
  else
    echo "pulling $iid ..."
    if docker pull --platform linux/amd64 "$img" >/dev/null 2>&1; then echo "pulled  $iid"; else echo "FAILED  $iid"; missing=$((missing+1)); fi
  fi
done < new_gold_candidates.txt
echo "done; failed pulls: $missing"
docker system df | head -2
[ "$missing" -eq 0 ]
