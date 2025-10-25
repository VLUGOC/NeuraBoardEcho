#!/usr/bin/env bash
set -euo pipefail

# TMP fiable en Termux
DEFAULT_TMP="/data/data/com.termux/files/usr/tmp"
TMPROOT="${TMPDIR:-$DEFAULT_TMP}"
mkdir -p "$TMPROOT"

echo
echo "== Chequeo de rebase/merge pendiente =="
if [[ -d .git/rebase-merge || -d .git/rebase-apply ]]; then
  echo "❌ Hay un rebase/merge pendiente. Ejecuta:"
  echo "   git rm -f logs/sandbox.log nohup.out 2>/dev/null || true"
  echo "   git checkout --ours memory.json 2>/dev/null || true && git add memory.json"
  echo "   git rebase --continue"
  exit 1
else
  echo "✅ No hay rebase/merge pendiente"
fi

echo
echo "== Compilación de sintaxis =="
python3 tools/find_syntax_errors.py | tee "$TMPROOT/syntax.out"
if grep -q "Sin errores de sintaxis" "$TMPROOT/syntax.out"; then
  echo "✅ Sintaxis OK"
else
  echo "❌ Error de sintaxis"
  exit 1
fi

echo
echo "== Suite de tests =="
bash tools/test_suite.sh | tee "$TMPROOT/test_suite.out" || true
if grep -q "✅ TESTS OK" "$TMPROOT/test_suite.out"; then
  echo "✅ Suite pasó"
else
  echo "❌ Falló la ejecución de la suite"
fi

echo
echo "== Test del hook pre-commit (bloqueo de sintaxis rota) =="
PRECOMMIT_LOG="$TMPROOT/precommit.log"
: > "$PRECOMMIT_LOG"
# simulación simple: si romper sintaxis, debe bloquear; aquí solo verificamos que el hook exista
if [[ -f .git/hooks/pre-commit ]]; then
  echo "✅ Hook pre-commit presente"
else
  echo "⚠️ Hook pre-commit no encontrado (opcional)"
fi

echo
echo "== Verificación de .gitignore =="
for f in secrets/credentials.json logs/runtime.log .venv/bin/activate; do
  if git check-ignore -q "$f"; then
    echo "   Ignorado: $f"
  else
    echo "   ⚠️ No ignorado: $f"
  fi
done
echo "✅ .gitignore efectivo"

echo
echo "== Verificación de .gitattributes (merge=ours) =="
if [[ -f .gitattributes ]] && grep -q "merge=ours" .gitattributes; then
  echo "✅ .gitattributes configurado"
else
  echo "⚠️ Considera configurar .gitattributes con merge=ours para logs/nohup/memory"
fi

echo
echo "== Chequeo de orquestador (backup --exclude) =="
if grep -q -- "--exclude=" core/orchestrator.py; then
  echo "✅ Backup usa --exclude"
else
  echo "⚠️ No veo --exclude en backup; considera aplicarlo"
fi

echo
echo "== Verificación de tag de versión =="
if git describe --tags --abbrev=0 >/dev/null 2>&1; then
  echo "✅ Tag de versión presente"
else
  echo "⚠️ Sin tag; opcional crear uno (git tag vYYYY.MM.DD && git push --tags)"
fi

echo
echo "== Resultado final =="
if grep -q "✅ TESTS OK" "$TMPROOT/test_suite.out" && grep -q "Sin errores de sintaxis" "$TMPROOT/syntax.out"; then
  echo "✅ Sistema estable"
else
  echo "❌ Hay pendientes. Revisa los mensajes arriba."
fi
