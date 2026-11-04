#!/bin/sh
# Exp Z: reasoning + frontier senders, all 8 configs in parallel (reasoning games are slow). Resumable.
export PYTHONIOENCODING=utf-8
for c in dwZr_v8n_c4o dwZr_v9_c4o dwZf_v8n_c4o dwZf_v9_c4o dwZr_v8n_c41 dwZr_v9_c41 dwZf_v8n_c41 dwZf_v9_c41; do
  ( .venv/Scripts/python.exe -m src.run --config config/$c.yaml --workers 8 > data/Z_$c.log 2>&1; echo "$c done $(date)" ) &
done
wait
echo ZDONE
