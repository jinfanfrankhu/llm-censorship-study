#!/usr/bin/env bash
set -u
PY=.venv/Scripts/python.exe
for s in lenient moderate strict; do
  echo "===== START expN_folk_$s $(date) ====="
  $PY -m src.run --config config/expN_folk_$s.yaml
  echo "===== END   expN_folk_$s $(date) ====="
done
echo "ALL DONE $(date)"
