#!/bin/sh
# Exp TB follow-ups 2: confused-sounding decoys and silent drop, block-reading sender.
export PYTHONIOENCODING=utf-8
for ack in plain cover; do
  .venv/Scripts/python.exe -m src.covert_ack --name expTBdecoy2 --ack $ack --censor_mode message --block_read --censor_variant decoy2 --workers 5 --budget 1.0 &
  .venv/Scripts/python.exe -m src.covert_ack --name expTBsilent --ack $ack --censor_mode message --block_read --censor_variant silent --workers 5 --budget 1.0 &
  wait
done
echo TB3DONE
