#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/NeuraBoardEco"
LOGDIR="$ROOT/logs"
REPORT="$LOGDIR/test_report.txt"
PYTHONPATH="$ROOT"
export PYTHONPATH

mkdir -p "$LOGDIR"
: > "$REPORT"

banner() { echo -e "\n===== $* =====" | tee -a "$REPORT"; }

status=0

banner "1) Compilación de módulos (syntax check)"
if ! python3 -m py_compile \
  "$ROOT"/core/*.py \
  "$ROOT"/core/integrations/*.py \
  "$ROOT"/eco_ant/*.py \
  "$ROOT"/sandbox/*.py 2>>"$REPORT"
then
  echo "[FAIL] Error de sintaxis en algún módulo" | tee -a "$REPORT"
  status=1
else
  echo "[OK] Sintaxis compilada sin errores" | tee -a "$REPORT"
fi

banner "2) Conteo previo de logs en memory.json"
BEFORE=$(python3 - <<'PY' 2>/dev/null
import json, os, sys
p=os.path.expanduser('~/NeuraBoardEco/memory.json')
try:
    with open(p,'r',encoding='utf-8') as f:
        data=json.load(f)
    print(len(data.get('logs',[])))
except Exception:
    print(0)
PY
)
echo "logs antes: $BEFORE" | tee -a "$REPORT"

banner "3) Ejecución del orchestrator (timeout 25s)"
if timeout 25s python3 "$ROOT/core/orchestrator.py" >>"$REPORT" 2>&1; then
  echo "[OK] Orchestrator terminó correctamente" | tee -a "$REPORT"
else
  echo "[FAIL] Orchestrator salió con error o timeout" | tee -a "$REPORT"
  status=1
fi

banner "4) Validación de memory.json (estructura y crecimiento de logs)"
AFTER=$(python3 - <<'PY' 2>/dev/null
import json, os, sys
p=os.path.expanduser('~/NeuraBoardEco/memory.json')
with open(p,'r',encoding='utf-8') as f:
    data=json.load(f)
assert isinstance(data, dict)
assert 'logs' in data
print(len(data['logs']))
PY
)
echo "logs después: $AFTER" | tee -a "$REPORT"

if [ "${AFTER:-0}" -ge "${BEFORE:-0}" ]; then
  echo "[OK] memory.json válido y logs crecieron o se mantuvieron" | tee -a "$REPORT"
else
  echo "[FAIL] El contador de logs no creció" | tee -a "$REPORT"
  status=1
fi

banner "5) Resumen"
if [ "$status" -eq 0 ]; then
  echo "✅ TESTS OK" | tee -a "$REPORT"
  if command -v termux-notification >/dev/null 2>&1; then
    termux-notification --title "NeuraBoard" --content "✅ Tests OK" --priority high
  fi
  exit 0
else
  echo "❌ TESTS FAIL" | tee -a "$REPORT"
  if command -v termux-notification >/dev/null 2>&1; then
    termux-notification --title "NeuraBoard" --content "❌ Tests FAIL (revisa logs/test_report.txt)" --priority high
  fi
  exit 1
fi
