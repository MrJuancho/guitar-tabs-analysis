"""CLI de la barrida del peso de altura de traste (Feature 008, T008 de
`specs/008-preferencia-posiciones-bajas/tasks.md`): único punto de
entrada de proceso que arma la lista de las 288 grabaciones medibles,
corre `ejecutar_barrida_peso_altura` sobre el conjunto de valores
candidatos ya declarado, y escribe la curva completa en disco -- mismo
patrón exacto que `digitacion/cli.py`.

Dos diferencias deliberadas frente a `digitacion/cli.py`:

- **Sin `--modo`**: esta CLI siempre mide sobre `"medibles"` -- la
  barrida del peso nunca corre sobre las 72 reservadas (Principio VI),
  así que no existe ningún argumento que pudiera apuntar ahí por error.
- **Sin ningún argumento para los valores candidatos**: el conjunto
  (`VALORES_CANDIDATOS_ALTURA_TRASTE`, research.md #3/#5 de la Feature
  008) es una constante nombrada de este módulo, declarada ANTES de
  correr cualquier medición -- un flag de línea de comandos permitiría
  "ajustar el rango después de ver la curva" (FR-007 de la Feature 008),
  el mismo vicio que Principio VII ya prohíbe para presupuestos.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from guitar_tabs_analysis.analytics.metrica_digitacion import ResultadoBarrida
from guitar_tabs_analysis.digitacion.orquestador import (
    construir_lista_grabaciones,
    ejecutar_barrida_peso_altura,
    resultado_barrida_a_dict,
)
from guitar_tabs_analysis.ingestion.guitarset import (
    IndiceMirdataAusenteError,
    RaizGuitarSetInvalidaError,
    validar_indice_mirdata,
    validar_raiz_guitarset,
)

VALORES_CANDIDATOS_ALTURA_TRASTE: tuple[float, ...] = (
    0.0,
    0.01,
    0.03,
    0.1,
    0.3,
    1.0,
    3.0,
    10.0,
    30.0,
    100.0,
)
"""Escala logarítmica declarada en research.md #3 de la Feature 008,
elegida contra la magnitud real medida del coste actual (traste medio
asignado `6.08`, coste actual por nota `≈7.77`) -- cubre tanto "no
cambia nada" (`0.01`) como "domina por completo" (`100.0`). Fijo en
código, nunca un argumento de línea de comandos (research.md #5)."""


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m guitar_tabs_analysis.digitacion.cli_barrido",
        description=(
            "Barre el peso de altura de traste del modelo de coste de digitación "
            "sobre las 288 grabaciones medibles de GuitarSet, con el conjunto de "
            "valores candidatos ya declarado en código, y mide fraccion_coincidencia "
            "para cada uno."
        ),
    )
    parser.add_argument(
        "--root-dir",
        type=Path,
        required=True,
        help="Raíz de una distribución de GuitarSet ya presente en disco.",
    )
    return parser


class EscrituraIncompletaError(Exception):
    """`os.replace()` no lanzó ninguna excepción, pero el resultado de
    la barrida no quedó verificablemente en disco -- mismo modo de
    fallo que `digitacion.cli.EscrituraIncompletaError`: no se confía
    en la ausencia de excepción como prueba de éxito, se relee lo que
    quedó en disco."""


def escribir_resultado_barrida(ruta: Path, resultado: ResultadoBarrida) -> None:
    """Escritura atómica de la curva completa -- mismo mecanismo exacto
    que `digitacion.cli.escribir_artefacto`: archivo temporal en el
    mismo directorio + `os.replace()`. Verifica el resultado releyendo
    la ruta final: confirma que el archivo existe, es JSON
    interpretable, y que su lista de `puntos` coincide en longitud con
    la del resultado que se acaba de calcular."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_name(ruta.name + ".tmp")
    temporal.write_text(json.dumps(resultado_barrida_a_dict(resultado)))
    os.replace(temporal, ruta)

    try:
        contenido = json.loads(ruta.read_text())
    except (FileNotFoundError, json.JSONDecodeError) as causa:
        raise EscrituraIncompletaError(
            f"'{ruta}' no quedó legible después de escribirlo -- {causa}."
        ) from causa
    if len(contenido.get("puntos", [])) != len(resultado.puntos):
        raise EscrituraIncompletaError(
            f"'{ruta}' no coincide con el resultado recién calculado: "
            f"{len(contenido.get('puntos', []))} puntos persistidos, "
            f"{len(resultado.puntos)} esperados."
        )


def _ejecutar_y_escribir(root_dir: Path, ruta_artefacto: Path) -> int:
    """Núcleo testeable de `main()`, sin `argparse`.

    Precondiciones de arranque (mismo criterio que `digitacion.cli`)
    MUST verificarse ANTES de `construir_lista_grabaciones`/
    `ejecutar_barrida_peso_altura` -- nunca a mitad de una corrida."""
    try:
        validar_indice_mirdata()
        validar_raiz_guitarset(root_dir)
    except (IndiceMirdataAusenteError, RaizGuitarSetInvalidaError) as causa:
        print(str(causa), file=sys.stderr)
        return 1

    grabaciones = construir_lista_grabaciones("medibles", root_dir)
    resultado = ejecutar_barrida_peso_altura(
        list(VALORES_CANDIDATOS_ALTURA_TRASTE), grabaciones, root_dir
    )
    try:
        escribir_resultado_barrida(ruta_artefacto, resultado)
    except EscrituraIncompletaError as causa:
        print(str(causa), file=sys.stderr)
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _construir_parser().parse_args(argv)
    ruta_artefacto = Path("mediciones") / "barrido_altura_traste.json"
    return _ejecutar_y_escribir(args.root_dir, ruta_artefacto)


if __name__ == "__main__":
    sys.exit(main())
