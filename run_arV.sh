#!/bin/sh
# Arms race from the DEFAULT prompt (v8n), sender learns only: do senders discover
# dogwhistles from block/deliver feedback? Two seeds, 6 rounds. Resumable.
export PYTHONIOENCODING=utf-8
I=dw01,dw03,dw04,dw06,dw07,dw08,dw10,dw11,dw12,dw13,dw17,dw21
echo "== seed1 $(date)"; .venv/Scripts/python.exe -m src.arms_race --name arV8a --items $I --rounds 6 --cond sender --prompt v8n --workers 6 --budget 3.0 2>&1 | grep -v "^$"
echo "== seed2 $(date)"; .venv/Scripts/python.exe -m src.arms_race --name arV8b --items $I --rounds 6 --cond sender --prompt v8n --run_offset 3 --workers 6 --budget 3.0 2>&1 | grep -v "^$"
echo ARVDONE
