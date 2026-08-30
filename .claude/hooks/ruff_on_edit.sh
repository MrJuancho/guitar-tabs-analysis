#!/usr/bin/env bash
# PostToolUse (Edit|Write) -- ruff sobre el archivo tocado. FALLA ABIERTO.
#
# Componente de conveniencia, no de seguridad: si falta `uv` en el entorno,
# no bloquea la edicion -- solo deja de dar feedback rapido. Un hallazgo
# real de ruff SI se reporta (exit 2), porque eso no es "la herramienta
# esta ausente", es "la herramienta corrio y encontro algo".
set -u

f=$(python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
    print((d.get("tool_input") or {}).get("file_path") or "")
except Exception:
    print("")
' 2>/dev/null)

case "$f" in
    *.py) ;;
    *) exit 0 ;;
esac

if ! command -v uv >/dev/null 2>&1; then
    exit 0
fi

salida=$(uv run ruff check "$f" 2>&1)
codigo=$?

if [ "$codigo" -eq 0 ]; then
    exit 0
fi

echo "$salida" >&2
exit 2
