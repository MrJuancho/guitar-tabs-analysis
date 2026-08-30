# justfile — la interfaz del guantelete.
#
# Los comandos viven aquí, no en la memoria de nadie. Cambiar una
# herramienta o su configuración no cambia la interfaz.
#
# NOTA para quien edite este archivo: la sintaxis {{recipe_arg}} de abajo
# es de `just`, no de Jinja/Copier -- este archivo se copia LITERAL (sin
# sufijo .jinja) precisamente para que Copier nunca intente renderizarla.
# El único valor que sí viene de Copier es guitar_tabs_analysis, sustituido por
# un `sed` en `_tasks` (ver copier.yml) justo después de generar el
# proyecto -- para cuando lees esto ya debería decir el nombre real del
# paquete, no el placeholder.

default:
    @just --list

# ---------------------------------------------------------------
# Guantelete escalonado
# ---------------------------------------------------------------

# Bucle interno — corre en cada edición vía hook. Objetivo: <5s en
# caliente. Se acota a los .py con cambios sin commitear (o a los que pasa
# el hook como argumento) para no pagar el costo de mypy --strict sobre
# todo src/ en cada edición -- medido en el proyecto de referencia
# (Covid19-Data-Analysis): ~12.6s en frío sobre todo src/, ~0.2s ya
# caliente y acotado a los archivos cambiados. NUNCA borres .mypy_cache/ en
# este camino.
gauntlet-fast *files:
    #!/usr/bin/env bash
    set -euo pipefail
    if [ -z "{{ files }}" ]; then
        targets=$(git diff --name-only --diff-filter=d HEAD -- \
            'src/guitar_tabs_analysis/**/*.py' 'tests/**/*.py' 2>/dev/null || true)
    else
        targets="{{ files }}"
    fi
    if [ -z "$targets" ]; then
        echo "Sin cambios .py que revisar."
        exit 0
    fi
    uv run ruff check $targets
    py_src=$(printf '%s\n' $targets | grep '^src/' | grep '\.py$' || true)
    if [ -n "$py_src" ]; then
        uv run mypy --strict $py_src
    fi

# Cierre de slice — antes de commit. Objetivo: < 2min
gauntlet: gauntlet-fast
    uv run ruff format --check src tests
    uv run lint-imports
    uv run pytest tests/unit tests/integration tests/property --cov=src --cov-fail-under=90

# Pre-merge / CI. Incluye retención y mutación del diff.
gauntlet-full: gauntlet
    uv run pytest tests/holdout
    just mutation-diff

# Auditoría completa — nocturno. Sin límite de tiempo.
audit: gauntlet-full
    uv run mutmut run
    uv run mutmut results

# ---------------------------------------------------------------
# Mutation testing
# ---------------------------------------------------------------

# just mutation quality.gates
mutation module:
    uv run mutmut run 'guitar_tabs_analysis.{{ module }}.*'
    uv run mutmut results

# Solo los módulos tocados en el diff contra main. Correr todos los
# mutantes del proyecto en cada PR es inviable (ver `just audit`, nocturno).
mutation-diff:
    #!/usr/bin/env bash
    set -euo pipefail
    # `origin/main` no existe en un proyecto recién generado (sin remoto
    # configurado todavía) -- `git diff origin/main...HEAD` con `set -e`
    # abortaría el recipe entero (exit 128, "bad revision") y dejaría
    # `gauntlet-full` inalcanzable hasta el primer push. Se cae a la rama
    # `main` local cuando el remoto no existe: si HEAD ya es `main` (caso
    # del primer commit), el diff resultante es honestamente vacío, no
    # fingido -- no hay módulos que puedan haber divergido todavía. Si
    # TAMPOCO existe una rama local `main`, no hay ninguna base contra la
    # cual comparar, y el recipe falla cerrado con un mensaje explícito en
    # vez de reportar "sin módulos" en silencio -- esa sería la misma forma
    # del fallo de `jq` que motivó ADR-0001 sección 7: una compuerta que no
    # puede verificar nada y lo disfraza de "nada que verificar".
    if git rev-parse --verify -q refs/remotes/origin/main >/dev/null; then
        base=origin/main
    elif git rev-parse --verify -q refs/heads/main >/dev/null; then
        base=main
        echo "AVISO: origin/main no existe (¿sin remoto configurado todavía?) -- usando 'main' local como base." >&2
    else
        echo "ERROR: no existe origin/main ni una rama 'main' local contra la cual comparar." >&2
        echo "  mutation-diff no tiene con qué acotar los módulos a mutar; no se asume 'sin cambios'." >&2
        echo "  Configura un remoto con 'main' publicado, o crea una rama local 'main', antes de correr gauntlet-full." >&2
        exit 1
    fi
    mods=$(git diff --name-only --diff-filter=d "$base"...HEAD -- 'src/guitar_tabs_analysis/**/*.py' \
           | sed 's|src/||; s|/|.|g; s|\.py$||; s|\.__init__$||' | sort -u)
    if [ -z "$mods" ]; then echo "Sin módulos modificados."; exit 0; fi
    for m in $mods; do
        # src/guitar_tabs_analysis/__init__.py (el paquete raíz) colapsa a
        # "guitar_tabs_analysis" sin puntos -- mutmut nombra sus mutantes igual
        # que los de CUALQUIER submódulo, así que no existe un patrón
        # fnmatch que lo acote sin matchear TODO el proyecto. Se detecta y
        # se omite en vez de correr "todo" en silencio disfrazado de
        # "acotado" (verificado contra el árbol real de mutmut en el
        # proyecto de referencia -- los __init__.py de subpaquetes no
        # tienen este problema, solo el de la raíz).
        if [ "$m" = "guitar_tabs_analysis" ]; then
            echo "AVISO: cambió src/guitar_tabs_analysis/__init__.py (paquete raíz)."
            echo "  No hay patrón que lo acote sin correr TODO el proyecto -- se omite."
            echo "  Revisa ese archivo a mano, o corre 'just audit' para la corrida completa."
            continue
        fi
        echo "→ $m"
        uv run mutmut run "$m.*" || true
    done
    echo
    echo "=== resumen (solo módulos de este diff) ==="
    for m in $mods; do
        [ "$m" = "guitar_tabs_analysis" ] && continue
        uv run mutmut results 2>&1 | grep -E "^\s*${m//./\\.}\." || true
    done

# ---------------------------------------------------------------
# Compuertas de calidad de datos (TODO: adaptar al dominio real)
# ---------------------------------------------------------------

# Evalúa GOLD_GATES sobre el artefacto de ejemplo. `quality/gates.py` en
# este template es un esqueleto FUNCIONAL con UN gate de ejemplo -- antes
# de usarlo en serio, reemplaza el gate de ejemplo por los del dominio real
# y actualiza esta ruta si el artefacto no vive en data/silver/.
gates:
    uv run python -m guitar_tabs_analysis.quality.gates

# ---------------------------------------------------------------
# Entorno
# ---------------------------------------------------------------

setup:
    uv sync
    @just doctor

# Verifica que las herramientas del guantelete existan. Un guantelete con
# una herramienta ausente falla abierto -- fue el hallazgo fundacional de
# este patrón (con `jq`, en el proyecto de referencia: ausente, y el hook
# que dependía de él habría dejado pasar cualquier edición sin avisar).
doctor:
    #!/usr/bin/env bash
    fallo=0
    for t in uv git python3 just; do
        command -v $t >/dev/null || { echo "FALTA: $t"; fallo=1; }
    done
    for m in ruff mypy pytest mutmut importlinter hypothesis; do
        uv run python -c "import ${m//-/_}" 2>/dev/null || { echo "FALTA (paquete Python): $m"; fallo=1; }
    done
    [ $fallo -eq 0 ] && echo "Guantelete completo." || exit 1

clean:
    rm -rf mutants/ .hypothesis/ .mutmut-cache .coverage htmlcov/

# ---------------------------------------------------------------
# Aislamiento de roles de verificación
# ---------------------------------------------------------------

# Crea un worktree aparte, en el commit actual (detached, no comparte rama
# con el árbol principal -- git no permite la misma rama en dos worktrees a
# la vez), para que `reviewer`/`data-auditor` trabajen sin interferir con
# `generator` ni entre sí. Ver AGENTS.md, "Aislamiento de roles" -- nace de
# un incidente real: dos roles de verificación corriendo en paralelo sobre
# el mismo árbol, uno cambiando de rama mientras el otro leía.
worktree-revision nombre:
    git worktree add --detach ".worktrees/{{ nombre }}" HEAD
    @echo "Worktree listo en .worktrees/{{ nombre }} (commit: $(git rev-parse --short HEAD))"

# Elimina el worktree de revisión cuando el rol termina. --force porque
# `uv sync`/`just doctor` dentro del worktree pueden dejar archivos sin
# trackear (uv.lock regenerado, .venv/) que `git worktree remove` sin
# forzar rechaza borrar -- es seguro forzarlo aquí porque estos worktrees
# son desechables por diseño: reviewer/data-auditor nunca escriben código
# fuente ahí (no tienen Edit/Write), así que no hay nada de valor que
# perder. Verificado: sin --force, `git worktree remove` falla en cuanto
# `uv sync` toca uv.lock dentro del worktree.
worktree-limpiar nombre:
    git worktree remove --force ".worktrees/{{ nombre }}"
