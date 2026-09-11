"""CLI de `digitacion` (T023 de
`specs/007-digitacion-restriccion-mano/tasks.md`): único punto de
entrada de proceso que arma la lista de grabaciones, corre
`ejecutar_digitacion` y escribe el artefacto final en disco -- mismo
patrón exacto que `deteccion.cli` del hito 2 (research.md #2 de esta
feature: sin ningún modelo/subproceso externo que construir, así que
`main()` no tiene el paso de "construir el transcriptor" que
`deteccion.cli` sí tiene).

`--modo` es un argumento `required=True` sin `default=` (mismo criterio
que `deteccion.cli`, FR-004 de Feature 004, Principio VI): omitirlo, o
pasar un valor fuera de las dos opciones, es un error de `argparse`
(`SystemExit`, código de salida distinto de 0) ANTES de tocar disco --
un default que apuntara a `"reservado"` mediría el conjunto que el
Principio VI de la constitución prohíbe tocar durante el desarrollo.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Literal

from guitar_tabs_analysis.digitacion.orquestador import (
    ArtefactoDigitacion,
    artefacto_a_dict,
    construir_lista_grabaciones,
    ejecutar_digitacion,
)
from guitar_tabs_analysis.ingestion.guitarset import (
    IndiceMirdataAusenteError,
    RaizGuitarSetInvalidaError,
    validar_indice_mirdata,
    validar_raiz_guitarset,
)


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m guitar_tabs_analysis.digitacion.cli",
        description=(
            "Digita el hito 3: lee la posición real de cada grabación de GuitarSet, "
            "calcula la digitación de coste mínimo y mide la coincidencia contra el uso real."
        ),
    )
    parser.add_argument(
        "--modo",
        choices=["medibles", "reservado"],
        required=True,
        help=(
            "medibles: 288 grabaciones (80% de GuitarSet), las únicas que se miden "
            "durante el desarrollo del hito 3. reservado: las 72 restantes (20%), "
            "solo para el cierre del hito 3 -- Principio VI de la constitución. "
            "Sin valor por defecto."
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
    """`os.replace()` no lanzó ninguna excepción, pero el artefacto final
    no quedó verificablemente en disco -- mismo modo de fallo que
    `deteccion.cli.EscrituraIncompletaError`/`medicion.cli.EscrituraIncompletaError`:
    no se confía en la ausencia de excepción como prueba de éxito, se
    relee lo que quedó en disco."""


def escribir_artefacto(ruta: Path, artefacto: ArtefactoDigitacion) -> None:
    """Escritura atómica del artefacto final -- mismo mecanismo exacto
    que `deteccion.cli.escribir_artefacto`: archivo temporal en el mismo
    directorio + `os.replace()`. Si el proceso se interrumpe entre
    escribir el temporal y renombrarlo, la ruta final nunca llega a
    existir -- nunca un artefacto truncado que parezca válido.

    Verifica el resultado releyendo la ruta final: nunca reporta éxito
    solo porque `os.replace()` no lanzó -- confirma que el archivo
    existe, es JSON interpretable, y que su lista de `grabaciones`
    coincide en longitud con la del artefacto que se acaba de calcular.
    """
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_name(ruta.name + ".tmp")
    temporal.write_text(json.dumps(artefacto_a_dict(artefacto)))
    os.replace(temporal, ruta)

    try:
        contenido = json.loads(ruta.read_text())
    except (FileNotFoundError, json.JSONDecodeError) as causa:
        raise EscrituraIncompletaError(
            f"'{ruta}' no quedó legible después de escribirlo -- {causa}."
        ) from causa
    if len(contenido.get("grabaciones", [])) != len(artefacto.grabaciones):
        raise EscrituraIncompletaError(
            f"'{ruta}' no coincide con el artefacto recién calculado: "
            f"{len(contenido.get('grabaciones', []))} grabaciones persistidas, "
            f"{len(artefacto.grabaciones)} esperadas."
        )


def _ejecutar_y_escribir(
    modo: Literal["medibles", "reservado"],
    root_dir: Path,
    ruta_artefacto: Path,
) -> int:
    """Núcleo testeable de `main()`, sin `argparse`.

    Precondiciones de arranque (FR-015/FR-016 del hito 2, research.md
    #19 de esa feature, mismo criterio reutilizado aquí -- no se
    reinventa la validación) MUST verificarse ANTES de
    `construir_lista_grabaciones`/`ejecutar_digitacion` -- nunca a mitad
    de una corrida."""
    try:
        validar_indice_mirdata()
        validar_raiz_guitarset(root_dir)
    except (IndiceMirdataAusenteError, RaizGuitarSetInvalidaError) as causa:
        print(str(causa), file=sys.stderr)
        return 1

    grabaciones = construir_lista_grabaciones(modo, root_dir)
    artefacto = ejecutar_digitacion(grabaciones, root_dir)
    try:
        escribir_artefacto(ruta_artefacto, artefacto)
    except EscrituraIncompletaError as causa:
        print(str(causa), file=sys.stderr)
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _construir_parser().parse_args(argv)
    ruta_artefacto = Path("mediciones") / f"digitacion_{args.modo}.json"
    return _ejecutar_y_escribir(args.modo, args.root_dir, ruta_artefacto)


if __name__ == "__main__":
    sys.exit(main())
