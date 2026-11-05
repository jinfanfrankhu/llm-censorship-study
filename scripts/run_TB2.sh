#!/bin/sh
# Exp TB follow-ups: censor designs against a block-reading sender (noise, decoy)
# and a calibrated sender (base rates + stricter rule). Resumable.
export PYTHONIOENCODING=utf-8
for ack in plain cover; do
  .venv/Scripts/python.exe -m src.covert_ack --name expTBnoise --ack $ack --censor_mode message --block_read --censor_variant noise --noise_rate 0.3 --workers 5 --budget 1.0 &
  .venv/Scripts/python.exe -m src.covert_ack --name expTBdecoy --ack $ack --censor_mode message --block_read --censor_variant decoy --workers 5 --budget 1.0 &
  .venv/Scripts/python.exe -m src.covert_ack --name expTBcal --ack $ack --censor_mode message --block_calib --workers 5 --budget 1.0 &
  wait
done
echo TB2DONE
