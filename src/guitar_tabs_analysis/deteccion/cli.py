"""CLI de `deteccion` (Fase 7, T032b de
`specs/006-deteccion-notas-guitarra-limpia/tasks.md`): único módulo de
esta feature que importa `transcripcion.basic_pitch_transcriptor` --
construye el `BasicPitchTranscriptor` real una sola vez, antes de invocar
`ejecutar_deteccion`. Mismo criterio que `medicion.cli` en el hito 1.

`--modo` es un argumento `required=True` sin `default=` (mismo criterio
que `medicion.cli`, FR-004 de Feature 004): omitirlo, o pasar un valor
fuera de las dos opciones, es un error de `argparse` (`SystemExit`,
código de salida distinto de 0) ANTES de construir ningún
`BasicPitchTranscriptor` ni tocar el disco -- acá el riesgo es más grave
todavía que en el hito 1: un default que apuntara a `"reservado"`
mediría el conjunto que el Principio VI de la constitución prohíbe tocar
durante el desarrollo.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Literal

from guitar_tabs_analysis.deteccion.orquestador import (
    ArtefactoDeteccion,
    artefacto_a_dict,
    construir_lista_grabaciones,
    ejecutar_deteccion,
)
from guitar_tabs_analysis.transcripcion.basic_pitch_transcriptor import BasicPitchTranscriptor
from guitar_tabs_analysis.transcripcion.transcriptor import Transcriptor


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m guitar_tabs_analysis.deteccion.cli",
        description=(
            "Detecta notas del hito 2: lee cada grabación de GuitarSet, transcribe "
            "con Basic Pitch, calcula precisión/exhaustividad/balance."
        ),
    )
    parser.add_argument(
        "--modo",
        choices=["medibles", "reservado"],
        required=True,
        help=(
            "medibles: 288 grabaciones (80% de GuitarSet), las únicas que se miden "
            "durante el desarrollo del hito 2. reservado: las 72 restantes (20%), "
            "solo para el cierre del hito 2 -- Principio VI de la constitución. "
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
    `medicion.cli.EscrituraIncompletaError` ya encontró en producción: no
    se confía en la ausencia de excepción como prueba de éxito, se relee
    lo que quedó en disco."""


def escribir_artefacto(ruta: Path, artefacto: ArtefactoDeteccion) -> None:
    """Escritura atómica del artefacto final -- mismo mecanismo exacto
    que `medicion.cli.escribir_artefacto`: archivo temporal en el mismo
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
    transcriptor: Transcriptor,
    ruta_artefacto: Path,
) -> int:
    """Núcleo testeable de `main()`, sin `argparse` ni
    `BasicPitchTranscriptor` -- recibe el `Transcriptor` ya construido,
    así los tests lo ejercitan con `TranscriptorFalso` sin invocar ningún
    subproceso."""
    grabaciones = construir_lista_grabaciones(modo, root_dir)
    artefacto = ejecutar_deteccion(grabaciones, root_dir, transcriptor)
    try:
        escribir_artefacto(ruta_artefacto, artefacto)
    except EscrituraIncompletaError as causa:
        print(str(causa), file=sys.stderr)
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _construir_parser().parse_args(argv)
    transcriptor = BasicPitchTranscriptor()
    ruta_artefacto = Path("mediciones") / f"deteccion_{args.modo}.json"
    return _ejecutar_y_escribir(args.modo, args.root_dir, transcriptor, ruta_artefacto)


if __name__ == "__main__":
    sys.exit(main())
