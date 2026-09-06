"""CLI de `medicion` (User Story 3, T027/T028 de
`specs/004-medicion-linea-base/tasks.md`): único módulo de esta capa que
importa `separacion.demucs_separador` -- construye el `Separador` real
una sola vez, antes de invocar `ejecutar_corrida`.

`--modo` es un argumento `required=True` sin `default=` (FR-004): omitirlo,
o pasar un valor fuera de las dos opciones, es un error de `argparse`
(`SystemExit`, código de salida distinto de 0) ANTES de construir ningún
`Separador` ni tocar el disco -- un valor por defecto aquí significa que
algún día alguien lanza una corrida de ~23 horas (`conjunto_completo`)
creyendo que lanzaba una de ~36 minutos (`submuestra_hito1`).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from guitar_tabs_analysis.medicion.orquestador import (
    ArtefactoMedicion,
    ModeloCambiadoError,
    ModoEjecucion,
    artefacto_a_dict,
    ejecutar_corrida,
)
from guitar_tabs_analysis.separacion.demucs_separador import DemucsSeparador
from guitar_tabs_analysis.separacion.separador import Separador


def _construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m guitar_tabs_analysis.medicion.cli",
        description="Mide el hito 1: lee cada tema, separa su guitarra, calcula SI-SDR.",
    )
    parser.add_argument(
        "--modo",
        choices=["submuestra_hito1", "conjunto_completo"],
        required=True,
        help=(
            "submuestra_hito1: 40 temas de validation/, semilla fija (~36 min). "
            "conjunto_completo: train/+validation/, sin muestreo (~23 h). "
            "Sin valor por defecto -- ver FR-004."
        ),
    )
    parser.add_argument(
        "--root-dir",
        type=Path,
        required=True,
        help="Raíz del dataset Slakh2100 (contiene train/, validation/, test/, omitted/).",
    )
    return parser


def escribir_artefacto(ruta: Path, artefacto: ArtefactoMedicion) -> None:
    """Escritura atómica del artefacto final -- mismo mecanismo que
    `orquestador.escribir_progreso_tema`/`escribir_manifiesto`
    (research.md #5): archivo temporal en el mismo directorio + `os.replace()`.
    Si el proceso se interrumpe entre escribir el temporal y renombrarlo,
    la ruta final nunca llega a existir -- nunca un artefacto truncado
    que parezca válido."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_name(ruta.name + ".tmp")
    temporal.write_text(json.dumps(artefacto_a_dict(artefacto)))
    os.replace(temporal, ruta)


def _ejecutar_y_escribir(
    modo: ModoEjecucion,
    root_dir: Path,
    separador: Separador,
    directorio_trabajo: Path,
    ruta_artefacto: Path,
) -> int:
    """Núcleo testeable de `main()`, sin `argparse` ni `DemucsSeparador`
    -- recibe el `Separador` ya construido, así los tests lo ejercitan
    con `SeparadorFalso` (Feature 003) sin tocar `torch`/`demucs`."""
    try:
        artefacto = ejecutar_corrida(modo, root_dir, separador, directorio_trabajo)
    except ModeloCambiadoError as causa:
        print(str(causa), file=sys.stderr)
        return 1
    escribir_artefacto(ruta_artefacto, artefacto)
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _construir_parser().parse_args(argv)
    separador = DemucsSeparador()
    directorio_trabajo = Path("data/silver/mediciones") / args.modo
    ruta_artefacto = Path("mediciones") / f"{args.modo}.json"
    return _ejecutar_y_escribir(
        args.modo, args.root_dir, separador, directorio_trabajo, ruta_artefacto
    )


if __name__ == "__main__":
    sys.exit(main())
