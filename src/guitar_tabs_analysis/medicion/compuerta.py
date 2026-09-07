"""Compuerta de la métrica (Feature 005): juzga un artefacto de medición
ya generado por `medicion.orquestador`/`medicion.cli` (Feature 004)
contra el presupuesto del Principio VII de la constitución (v1.5.0).

NO invoca ningún modelo, NO lee audio, NO recalcula ningún SI-SDR -- lee
el `dict` JSON del artefacto y compara valores que ya están ahí
(FR-001). Por eso este módulo solo importa `stdlib`: no importa
`medicion.orquestador` (sus funciones de deserialización son privadas,
pensadas para el round-trip interno del progreso por tema, no para
reuso externo -- research.md #1) ni `separacion`/`analytics`/`ingestion`
(research.md #1/#2 de `specs/005-compuerta-metrica/`).
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Principio VII de la constitución (v1.5.0): -8.0 dB sobre la mediana de
# referencias EMPAREJADAS, nunca sobre la mediana global (que es
# estructuralmente -inf con este modelo). Constante de código, nunca un
# argumento de `main` (FR-010) -- cambiarla requiere una enmienda de la
# constitución y una edición de código explícita.
PRESUPUESTO_SI_SDR_DB = -8.0


@dataclass(frozen=True)
class Veredicto:
    """El resultado de evaluar un artefacto contra el presupuesto
    (data-model.md). `aprobado` depende únicamente de
    `mediana_emparejadas` contra `presupuesto` -- el resto de los campos
    son contexto obligatorio (FR-003, FR-009), nunca condiciones del
    juicio."""

    aprobado: bool
    mediana_emparejadas: float
    presupuesto: float
    fraccion_sin_pareja: float
    total_emparejadas: int
    total_sin_pareja: int
    modelo_nombre: str
    modelo_variante: str
    modelo_firma: str
    modo: str
    semilla: int | None


class ArtefactoInvalidoError(Exception):
    """Rechazo por evidencia -- distinto de un rechazo por presupuesto no
    alcanzado, que nunca es una excepción (data-model.md). Cubre las
    tres condiciones de FR-004/FR-005/FR-006: ruta ausente, contenido no
    interpretable o sin la forma reconocible de un artefacto de
    medición, y evidencia insuficiente para calcular una mediana."""

    def __init__(self, motivo: str) -> None:
        self.motivo = motivo
        super().__init__(motivo)


def evaluar_artefacto(datos: dict[str, Any]) -> Veredicto:
    """Juzga un artefacto ya deserializado contra `PRESUPUESTO_SI_SDR_DB`
    (contracts/compuerta.md postcondiciones 3/4/5). Función pura: no
    toca disco, no importa nada fuera de `stdlib` (research.md #1).

    La mediana se calcula con `statistics.median` sobre el pool de
    `si_sdr` de las referencias *emparejadas* -- nunca incluye los
    sentinelas de `sin_pareja` (a diferencia de la `mediana` global que
    trae el propio artefacto, Principio VII de la constitución: el
    presupuesto se fija sobre la mediana de emparejadas, nunca sobre la
    global). Seguro de usar sin la regla pesimista de
    `analytics.metrica_separacion._mediana_orden`: ese pool nunca mezcla
    `+inf`/`-inf` (test_compuerta_mediana_equivalencia.py, research.md #3).
    """
    try:
        pool: list[float] = []
        total_sin_pareja = 0
        for reporte in datos["reportes"]:
            pool.extend(e["si_sdr"] for e in reporte["emparejadas"])
            total_sin_pareja += len(reporte["sin_pareja"])
        modelo = datos["modelo"]
        modelo_nombre = modelo["nombre"]
        modelo_variante = modelo["variante"]
        modelo_firma = modelo["firma"]
        modo = datos["modo"]
        semilla = datos["semilla"]
    except KeyError as causa:
        raise ArtefactoInvalidoError(
            f"El artefacto no tiene la forma reconocible de una medición: falta la clave {causa}."
        ) from causa

    if not pool:
        raise ArtefactoInvalidoError(
            "Sin evidencia suficiente para juzgar: ningún valor de SI-SDR emparejado "
            "en el artefacto (ni referencias, ni referencias sin pareja que puedan "
            "aportar una)."
        )

    mediana_emparejadas = statistics.median(pool)
    total_emparejadas = len(pool)
    return Veredicto(
        aprobado=mediana_emparejadas >= PRESUPUESTO_SI_SDR_DB,
        mediana_emparejadas=mediana_emparejadas,
        presupuesto=PRESUPUESTO_SI_SDR_DB,
        fraccion_sin_pareja=total_sin_pareja / (total_emparejadas + total_sin_pareja),
        total_emparejadas=total_emparejadas,
        total_sin_pareja=total_sin_pareja,
        modelo_nombre=modelo_nombre,
        modelo_variante=modelo_variante,
        modelo_firma=modelo_firma,
        modo=modo,
        semilla=semilla,
    )


def leer_artefacto(ruta: Path) -> dict[str, Any]:
    """Lee y deserializa un artefacto desde disco (contracts/compuerta.md).
    Único punto de esta feature que toca el sistema de archivos antes de
    `evaluar_artefacto` -- no valida la forma del artefacto, solo que la
    ruta exista y su contenido sea JSON interpretable (FR-004/FR-005)."""
    try:
        contenido = ruta.read_text()
    except FileNotFoundError as causa:
        raise ArtefactoInvalidoError(f"No existe el artefacto en '{ruta}'.") from causa

    try:
        resultado: dict[str, Any] = json.loads(contenido)
    except json.JSONDecodeError as causa:
        raise ArtefactoInvalidoError(
            f"El contenido de '{ruta}' no es JSON válido: {causa}."
        ) from causa
    return resultado


def _construir_parser() -> argparse.ArgumentParser:
    """`prog`/`description`/`help` de abajo son texto de ayuda de
    `argparse`, no comportamiento -- ningún test (ni debería) afirma su
    contenido exacto, así que sus mutaciones (T015, triage de mutación)
    sobreviven como equivalentes para el propósito de este proyecto:
    verificar la palabra exacta de un mensaje de ayuda sería una prueba
    frágil que no protege ninguna decisión real. Lo que sí es
    comportamiento -- `choices`, `required`, sin `default` -- está
    cubierto por `test_compuerta_cli.py` (`SystemExit` ante `--modo`
    ausente o inválido)."""
    parser = argparse.ArgumentParser(
        prog="python -m guitar_tabs_analysis.medicion.compuerta",  # pragma: no mutate
        description=(
            "Juzga un artefacto de medición ya generado (Feature 004) contra "  # pragma: no mutate
            "el presupuesto del Principio VII de la constitución -- nunca "  # pragma: no mutate
            "ejecuta una medición ni invoca ningún modelo."  # pragma: no mutate
        ),
    )
    parser.add_argument(
        "--modo",
        choices=["submuestra_hito1", "conjunto_completo"],
        required=True,
        help=(
            "Cuál de los dos artefactos de la Feature 004 evaluar "  # pragma: no mutate
            "(mediciones/<modo>.json). Sin valor por defecto -- FR-008."  # pragma: no mutate
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _construir_parser().parse_args(argv)
    ruta = Path("mediciones") / f"{args.modo}.json"
    try:
        datos = leer_artefacto(ruta)
        veredicto = evaluar_artefacto(datos)
    except ArtefactoInvalidoError as causa:
        print(str(causa), file=sys.stderr)
        return 2

    total_referencias = veredicto.total_emparejadas + veredicto.total_sin_pareja
    print(
        f"{'APROBADO' if veredicto.aprobado else 'RECHAZADO'} -- "
        f"mediana de emparejadas: {veredicto.mediana_emparejadas:.2f} dB "
        f"(presupuesto: {veredicto.presupuesto:.2f} dB); "
        f"fracción sin pareja: {veredicto.fraccion_sin_pareja:.3f} "
        f"({veredicto.total_sin_pareja}/{total_referencias}); "
        f"modelo: {veredicto.modelo_nombre} {veredicto.modelo_variante} "
        f"(firma {veredicto.modelo_firma}); modo: {veredicto.modo}; "
        f"semilla: {veredicto.semilla}"
    )
    return 0 if veredicto.aprobado else 1


if __name__ == "__main__":
    sys.exit(main())
