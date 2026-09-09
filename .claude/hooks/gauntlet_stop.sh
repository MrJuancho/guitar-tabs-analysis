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
#
# CASO 5 de la deuda "una compuerta que no examina nada y no lo dice"
# (docs/adr/0001-arquitectura-del-guantelete.md, sección 9): este script se
# invocaba con ruta relativa (`bash .claude/hooks/gauntlet_stop.sh` en
# settings.json), resuelta contra el directorio de trabajo del PROCESO que
# dispara el hook, no contra la raiz del proyecto -- si ese cwd no era
# exactamente la raiz, bash fallaba con "No such file or directory" (exit
# 127) ANTES de que una sola linea de este script corriera. Y como solo el
# codigo 2 bloquea el evento Stop (verificado contra
# https://code.claude.com/docs/en/hooks -- "exit code 2 is the only exit
# code that blocks... for most hook events"; cualquier otro codigo es un
# aviso NO bloqueante), ese 127 dejaba pasar el turno con un mensaje que
# aparecia al final de un reporte largo, sin bloquear nada -- exactamente
# la compuerta que existe para atrapar fallos silenciosos, fallando en
# silencio ella misma. Corregido en dos capas: `settings.json` ahora usa
# `${CLAUDE_PROJECT_DIR}` (variable oficial que Claude Code expone a los
# hooks con la raiz del proyecto) mas `|| exit 2` para que CUALQUIER fallo
# de la invocacion misma termine en el unico codigo que bloquea; y este
# script hace `cd "$CLAUDE_PROJECT_DIR"` explicito abajo para que
# `just gauntlet-fast` corra siempre contra la raiz real, sin importar
# desde donde lo haya invocado el proceso padre.
set -u

if [ -z "${CLAUDE_PROJECT_DIR:-}" ]; then
    echo "CLAUDE_PROJECT_DIR no esta definida -- no se puede verificar nada sin saber donde esta la raiz del proyecto. Bloqueado por seguridad (fail-closed)." >&2
    exit 2
fi

if ! cd "$CLAUDE_PROJECT_DIR"; then
    echo "No se pudo entrar a CLAUDE_PROJECT_DIR ($CLAUDE_PROJECT_DIR) -- bloqueado por seguridad (fail-closed)." >&2
    exit 2
fi

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
