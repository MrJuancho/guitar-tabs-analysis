#!/usr/bin/env bash
# Stop -- corre `just gauntlet-fast` (ruff + mypy --strict, acotado a
# archivos con cambios) antes de dar un turno por terminado.
#
# FALLA CERRADO -- decisión explícita. El principio "seguridad cierra,
# conveniencia abre" no clasifica este hook directamente: no es un control
# de PII como el bloqueo de holdout, pero tampoco es puramente "feedback
# rápido" como el ruff de PostToolUse (ese sí declarado conveniencia). Es
# la ÚLTIMA revisión antes de que termine el turno -- si `just` desaparece
# del entorno y esto fallara abierto, un turno entero podría cerrarse sin
# que mypy/ruff hayan corrido ni una vez, en silencio. Se optó por cerrado.
# Documentado en AGENTS.md para que se pueda revisar la decisión.
set -u

if ! command -v just >/dev/null 2>&1; then
    echo "No se pudo correr el guantelete: falta 'just' en el entorno." >&2
    echo "Instala 'just' o corre 'just doctor' manualmente antes de terminar el turno." >&2
    exit 2
fi

salida=$(just gauntlet-fast 2>&1)
codigo=$?

if [ "$codigo" -eq 0 ]; then
    exit 0
fi

echo "gauntlet-fast fallo antes de terminar el turno -- arregla esto antes de dar el cambio por terminado:" >&2
echo "$salida" >&2
exit 2
