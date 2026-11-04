#!/bin/sh
# Exp S gpt-4o-mini cells to 6 runs/item (resumable; adds run_index 3-5). Waits for arB.
export PYTHONIOENCODING=utf-8
until grep -q ARBDONE data/arB.log 2>/dev/null; do sleep 60; done
for c in dwS_v9_c4o dwS_v8n_c4o; do
  echo "== $c"; .venv/Scripts/python.exe -m src.run --config config/$c.yaml --workers 6 2>&1 | grep -v "it/s\|s/it" | tail -3
done
echo S6DONE
