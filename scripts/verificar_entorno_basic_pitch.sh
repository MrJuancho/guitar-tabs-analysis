#!/usr/bin/env bash
# Verifica el entorno secundario de inferencia de Basic Pitch (Feature 006,
# research.md #15/#18 de specs/006-deteccion-notas-guitarra-limpia/) --
# extraído de `just doctor` en un script parametrizado por ruta para poder
# probarlo con un directorio sintético (tests/unit/test_verificar_entorno_basic_pitch.py)
# sin depender de -- ni fabricar en cada corrida -- el `.venv` real, que
# instala basic-pitch/tflite-runtime y solo existe cuando alguien corrió
# `uv sync` dentro de `envs/basic_pitch_py310/` (nunca en CI a propósito).
#
# Uso: verificar_entorno_basic_pitch.sh <ruta_entorno>
#
# Códigos de salida (tres, no dos -- "ausente" y "roto" son casos
# distinguibles y NO deben confundirse con el mismo código):
#   0 -- el entorno existe y se verificó completo, sin problemas.
#   1 -- problema real: el directorio del entorno no existe (research.md
#        #15 lo declara versionado -- pyproject.toml/uv.lock/
#        transcribir_subproceso.py -- su ausencia es un repositorio roto,
#        no una omisión esperada), o existe pero algo dentro está mal
#        (intérprete no ejecutable pese a existir el directorio del
#        entorno, `import basic_pitch` falla, o el lock está
#        desincronizado).
#   2 -- `.venv` no existe todavía (nadie corrió `uv sync` ahí) -- estado
#        ESPERADO en CI (research.md #18: ese entorno solo hace falta para
#        `just detectar` y los tests `modelo_real`, que CI ya excluye;
#        crearlo ahí instalaría basic-pitch/tflite-runtime sin que nada los
#        use). Se reporta de forma visible -- nunca en silencio, mismo
#        criterio que el marcador `modelo_real` (`tests/conftest.py`) --
#        pero no es un fallo: quien invoca este script decide si un
#        código 2 debe contar como `fallo` (CI: no) o no (mismo criterio
#        localmente, research.md #18 -- ver esa sección para el argumento
#        completo de por qué la condición es sobre el estado del `.venv`,
#        no sobre CI-vs-local).
set -u

ruta="${1:?uso: verificar_entorno_basic_pitch.sh <ruta_entorno>}"

if [ ! -d "$ruta" ]; then
    echo "FALTA: $ruta no existe -- ver research.md #15 de specs/006-deteccion-notas-guitarra-limpia/."
    exit 1
fi

if [ ! -x "$ruta/.venv/bin/python" ]; then
    echo "=================================================================="
    echo "OMITIDO: $ruta/.venv no existe -- entorno de inferencia real"
    echo "(Basic Pitch/tflite) SIN VERIFICAR. Es el estado esperado en CI"
    echo "(research.md #18): ese entorno solo hace falta para 'just"
    echo "detectar' y los tests marcados modelo_real, que CI ya excluye --"
    echo "crearlo ahí instalaría basic-pitch/tflite-runtime en cada corrida"
    echo "sin que nada los use."
    echo "Para verificarlo de verdad: 'cd $ruta && uv sync'."
    echo "=================================================================="
    exit 2
fi

# Mismo orden que el resto de `just doctor` (research.md, "un chequeo de
# estado va antes de cualquier comando que pueda repararlo"): sin `uv run`
# antes de ningún check -- intérprete (ya confirmado ejecutable arriba),
# import, y lock al final, en ese orden.
"$ruta/.venv/bin/python" -c "import basic_pitch" >/dev/null 2>&1 \
    || {
        echo "FALTA: basic_pitch no importa en $ruta/.venv -- correr 'uv sync' dentro de ese directorio."
        exit 1
    }

(cd "$ruta" && uv lock --check) >/dev/null 2>&1 \
    || {
        echo "FALTA: $ruta/uv.lock desincronizado con su pyproject.toml -- correr 'uv lock' dentro de ese directorio."
        exit 1
    }

echo "Entorno de inferencia real ($ruta) verificado."
exit 0
