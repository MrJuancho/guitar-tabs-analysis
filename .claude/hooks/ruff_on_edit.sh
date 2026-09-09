#!/usr/bin/env bash
# PostToolUse (Edit|Write) -- ruff sobre el archivo tocado. FALLA ABIERTO.
#
# Componente de conveniencia, no de seguridad: si falta `uv` en el entorno,
# no bloquea la edicion -- solo deja de dar feedback rapido. Un hallazgo
# real de ruff SI se reporta (exit 2), porque eso no es "la herramienta
# esta ausente", es "la herramienta corrio y encontro algo".
#
# Nota sobre el caso 5 de la deuda "una compuerta que no examina nada y no
# lo dice" (docs/adr/0001-arquitectura-del-guantelete.md, seccion 9): este
# script comparte con gauntlet_stop.sh y block_holdout.py el mismo bug de
# ruta relativa en `settings.json` (ya corregido con `${CLAUDE_PROJECT_DIR}`),
# pero a proposito NO lleva el `|| exit 2` que se agrego a esos dos. Un
# hook PostToolUse no puede bloquear bajo ninguna circunstancia -- la
# herramienta que dispara el hook ya corrio (verificado contra
# https://code.claude.com/docs/en/hooks: "Since the tool already ran, exit
# code 2 cannot prevent it") -- asi que forzar el codigo 2 aqui no
# cambiaria ningun comportamiento observable, solo agregaria ruido. Lo
# unico que SI vale la pena corregir aqui es que `uv run ruff` corra desde
# la raiz real del proyecto (ver `cd` abajo), para que de verdad encuentre
# `pyproject.toml` sin importar desde donde el proceso padre invoco el hook.
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

# `cd` a la raiz real del proyecto antes de invocar `uv` -- sin esto, `uv
# run ruff check` resuelve pyproject.toml/el venv contra el cwd del
# proceso que disparo el hook, no contra el proyecto real (el mismo bug de
# fondo que gauntlet_stop.sh, aplicado aqui a `uv` en vez de a `just`).
# Fail-open explicito si no se puede: este hook es de conveniencia, no de
# verificacion -- sin `CLAUDE_PROJECT_DIR` o sin poder entrar, simplemente
# deja de dar feedback, no bloquea nada (no podria, ver nota de arriba).
if [ -z "${CLAUDE_PROJECT_DIR:-}" ] || ! cd "$CLAUDE_PROJECT_DIR"; then
    exit 0
fi

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
