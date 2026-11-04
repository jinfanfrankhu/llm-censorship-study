#!/bin/sh
export PYTHONIOENCODING=utf-8
I=dw01,dw03,dw04,dw06,dw07,dw08,dw10,dw11,dw12,dw13,dw17,dw21
for c in both censor sender; do
  echo "== $c"; .venv/Scripts/python.exe -m src.arms_race --name arA --items $I --rounds 4 --cond $c --workers 6 --budget 3.0 2>&1 | grep -v "^$"
done
