#!/bin/sh
# Arms race, second seed (run_index 3-5). Sequential arms; resumable.
export PYTHONIOENCODING=utf-8
I=dw01,dw03,dw04,dw06,dw07,dw08,dw10,dw11,dw12,dw13,dw17,dw21
for c in both censor sender; do
  echo "== $c"; .venv/Scripts/python.exe -m src.arms_race --name arB --items $I --rounds 4 --cond $c --run_offset 3 --workers 6 --budget 1.5 2>&1 | grep -v "^$"
done
echo ARBDONE
