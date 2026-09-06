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
import sys
from pathlib import Path

from guitar_tabs_analysis.separacion.demucs_separador import DemucsSeparador


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


def main(argv: list[str] | None = None) -> int:
    args = _construir_parser().parse_args(argv)
    separador = DemucsSeparador()
    print(f"TODO: ejecutar_corrida({args.modo!r}, {args.root_dir!r}, {separador!r}, ...)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
