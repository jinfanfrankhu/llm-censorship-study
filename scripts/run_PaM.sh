#!/bin/sh
# Reviewer checks: v9 paraphrases (dwPa) and cross-model pairs (dwM). Resumable.
export PYTHONIOENCODING=utf-8
for c in dwPa_v9p1_c4o dwPa_v9p2_c4o dwPa_v9p3_c4o dwM_v9_c4o dwM_v8n_c4o; do
  .venv/Scripts/python.exe -m src.run --config config/$c.yaml --workers 6 > data/PaM_$c.log 2>&1; echo "$c done $(date)"
done
echo PAMDONE
