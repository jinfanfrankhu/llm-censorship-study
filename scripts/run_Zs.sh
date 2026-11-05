#!/bin/sh
# Exp Z re-run for claude-sonnet-5.5 (effort low, max_tokens 2500). Resumable.
export PYTHONIOENCODING=utf-8
for c in dwZs_v8n_c4o dwZs_v9_c4o dwZs_v8n_c41 dwZs_v9_c41; do
  ( .venv/Scripts/python.exe -m src.run --config config/$c.yaml --workers 6 > data/Z_$c.log 2>&1; echo "$c done $(date)" ) &
done
wait
echo ZSDONE
