#!/usr/bin/env bash
set -u
PY=.venv/Scripts/python.exe
W=10
for cfg in expN_folk_lenient expN_folk_moderate expN_folk_strict expO_ladder_v7 expO_ladder_v6; do
  echo "===== START $cfg (workers=$W) $(date) ====="
  $PY -m src.run --config config/$cfg.yaml --workers $W
  echo "===== END   $cfg $(date) ====="
done
echo "ALL PARALLEL DONE $(date)"
