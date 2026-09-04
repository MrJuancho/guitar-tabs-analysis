"""Métrica de separación de guitarra (capa `analytics`, importa de
`ingestion`, nunca al revés): dada la colección de pistas de guitarra
de referencia y una colección de estimaciones de un mismo tema,
`si_sdr()` calcula el SI-SDR (*Scale-Invariant Signal-to-Distortion
Ratio*) de un único par.

Este módulo, en su estado actual (T003, T005 de
`specs/002-metrica-separacion-guitarra/tasks.md`), cubre los tipos de
dominio, las excepciones, y `si_sdr()` -- el emparejamiento por tema
(`emparejar_tema`, T017) y la agregación sobre un conjunto
(`agregar_conjunto`, T025) llegan en sesiones futuras.

Ver `specs/002-metrica-separacion-guitarra/data-model.md` y
`specs/002-metrica-separacion-guitarra/contracts/metrica_separacion.md`
para el contrato completo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from guitar_tabs_analysis.ingestion.slakh2100 import PistaAudio, PistaGuitarra

# ---------------------------------------------------------------------
# Tipos de dominio (T003) -- todos inmutables: son el resultado de un
# cálculo, no construcción incremental (data-model.md).
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class Estimacion:
    """Una pista estimada por un separador (fuera de alcance de esta
    feature), con un identificador que el llamador le asigna para poder
    nombrarla en el reporte."""

    identificador: str
    audio: PistaAudio


MotivoSinPareja = Literal["sin_estimacion_disponible", "energia_nula"]


@dataclass(frozen=True)
class ReferenciaEmparejada:
    """Una referencia que quedó asociada a una estimación (FR-002)."""

    identificador_referencia: str
    identificador_estimacion: str
    si_sdr: float


@dataclass(frozen=True)
class ReferenciaSinPareja:
    """Una referencia del tema que no quedó asociada a ninguna
    estimación (FR-005), con el motivo explícito (FR-006/FR-003)."""

    identificador_referencia: str
    motivo: MotivoSinPareja


@dataclass(frozen=True)
class ReporteTema:
    """El resultado del cálculo sobre un tema individual (FR-004)."""

    tema_id: str
    num_referencias: int
    num_estimaciones_recibidas: int
    emparejadas: list[ReferenciaEmparejada] = field(default_factory=list)
    sin_pareja: list[ReferenciaSinPareja] = field(default_factory=list)


@dataclass(frozen=True)
class EntradaConjunto:
    """Un tema tal como lo aporta el llamador a la agregación sobre un
    conjunto (FR-007 en adelante), antes de aplicar las exclusiones."""

    tema_id: str
    referencias: list[PistaGuitarra]
    estimaciones: list[Estimacion]
    es_directorio_omitido: bool


MotivoExclusion = Literal["sin_guitarra_referencia", "directorio_omitido"]


@dataclass(frozen=True)
class Exclusion:
    """Un tema apartado del conjunto evaluado antes de agregar
    (FR-009/FR-010)."""

    tema_id: str
    motivo: MotivoExclusion


@dataclass(frozen=True)
class ResultadoAgregado:
    """El resultado de agregar la métrica sobre un conjunto de temas
    (FR-007 en adelante)."""

    mediana: float | None
    num_temas_evaluados: int
    distribucion_referencias_por_tema: dict[int, int]
    exclusiones: list[Exclusion] = field(default_factory=list)
    reportes_por_tema: list[ReporteTema] = field(default_factory=list)


# ---------------------------------------------------------------------
# Excepciones del contrato (T003) -- ver contracts/metrica_separacion.md.
# ---------------------------------------------------------------------


class EstimacionIncompatibleError(Exception):
    """Una referencia y una estimación candidata tienen distinta
    longitud (número de muestras) o distinta frecuencia de muestreo
    (research.md #7) -- no hay una comparación de SI-SDR bien definida
    entre ellas, así que no se recorta ni se remuestrea para forzarla."""

    def __init__(
        self, identificador_referencia: str, identificador_estimacion: str, motivo: str
    ) -> None:
        self.identificador_referencia = identificador_referencia
        self.identificador_estimacion = identificador_estimacion
        self.motivo = motivo
        super().__init__(
            f"La estimación '{identificador_estimacion}' es incompatible con la "
            f"referencia '{identificador_referencia}': {motivo}."
        )


class ReferenciaEnergiaNulaError(Exception):
    """La referencia tiene energía nula (silencio digital, research.md
    #4) -- el SI-SDR es matemáticamente indefinido (0/0) para ella,
    independientemente de la estimación candidata. `emparejar_tema()`
    (T017) nunca deja escapar esta excepción: comprueba la energía de
    cada referencia antes de llamar a `si_sdr()` sobre ella, y la
    reporta como `ReferenciaSinPareja(motivo="energia_nula")` en vez de
    propagar un fallo (FR-006). Solo la ve quien llama a `si_sdr()`
    directamente."""

    def __init__(self, identificador_referencia: str) -> None:
        self.identificador_referencia = identificador_referencia
        super().__init__(
            f"La referencia '{identificador_referencia}' tiene energía nula (silencio digital); "
            "el SI-SDR no está definido para ella."
        )
