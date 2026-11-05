#!/bin/sh
# Close the loop on Exp PB: sender reads blocks (expTBread) and receiver may trip
# the censor on purpose (expTBsig); plain and cover acks, message censor. Resumable.
export PYTHONIOENCODING=utf-8
for ack in plain cover; do
  .venv/Scripts/python.exe -m src.covert_ack --name expTBread --ack $ack --censor_mode message --block_read --workers 6 --budget 1.5 &
  .venv/Scripts/python.exe -m src.covert_ack --name expTBsig --ack $ack --censor_mode message --block_signal --workers 6 --budget 1.5 &
  wait
done
echo TBDONE
