#!/bin/sh
# Exp U: new-item replication. Waits for the v3 gap check to exit (rate limits).
export PYTHONIOENCODING=utf-8
while powershell -NoProfile -Command "if (Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { \$_.CommandLine -like '*gap_check*' }) { exit 0 } else { exit 1 }"; do sleep 60; done
for c in dwU_v9_c4o dwU_v8n_c4o; do
  echo "== $c"; .venv/Scripts/python.exe -m src.run --config config/$c.yaml --workers 6 2>&1 | grep -v "it/s\|s/it" | tail -3
done
echo UDONE
