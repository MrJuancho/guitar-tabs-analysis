"""Protocolo de transcripción de notas (capa `transcripcion`, importa de
`analytics`/`ingestion`, ninguna de las dos importa de vuelta): la interfaz
mínima que cualquier adaptador de un modelo de transcripción debe cumplir.

Este módulo NO importa `basic_pitch` -- solo depende de `NotaEstimada`
(`analytics.metrica_deteccion_notas`). El adaptador real que sí lo usa (por
subproceso, nunca importado directamente -- research.md #15 de
`specs/006-deteccion-notas-guitarra-limpia/`) vive en
`transcripcion.basic_pitch_transcriptor`. Esto es lo que permite construir y
probar `deteccion.orquestador` con un `Transcriptor` falso
(`tests/fixtures/transcriptor_fixture.py`), sin invocar ningún subproceso ni
cargar ningún modelo real.

Cubre T010(a) de `specs/006-deteccion-notas-guitarra-limpia/tasks.md`. Ver
data-model.md y contracts/deteccion.md para el contrato completo. Mismo
patrón exacto que `separacion.separador` (`Separador`/`ModeloDeclarado`/
`SeparacionFallidaError`) del hito 1.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from guitar_tabs_analysis.analytics.metrica_deteccion_notas import NotaEstimada


@dataclass(frozen=True)
class ModeloTranscripcionDeclarado:
    """El modelo de transcripción fijo usado, identificado de forma
    verificable (FR-011, data-model.md)."""

    nombre: str
    variante: str
    firma: str
    backend: str
    licencia: str


class Transcriptor(Protocol):
    """La interfaz mínima que `deteccion.orquestador` necesita -- no una
    clase concreta. `transcripcion.basic_pitch_transcriptor.BasicPitchTranscriptor`
    la implementa invocando Basic Pitch por subproceso; los tests inyectan un
    `TranscriptorFalso` (`tests/fixtures/transcriptor_fixture.py`) que la
    implementa sin invocar ningún proceso externo.

    `transcribir` recibe una **ruta de archivo**, no muestras cargadas en
    memoria (contracts/deteccion.md) -- a diferencia de
    `separacion.separador.Separador` del hito 1, porque
    `basic_pitch.inference.predict()` solo acepta ruta de archivo."""

    modelo_declarado: ModeloTranscripcionDeclarado

    def transcribir(self, ruta_audio: Path) -> list[NotaEstimada]: ...


class TranscripcionFallidaError(Exception):
    """Un fallo real del modelo o del framework de inferencia sobre
    `ruta_audio` (contracts/deteccion.md postcondición 2 de
    `Transcriptor.transcribir`) -- distinto del caso legítimo de
    `notas == []` (silencio total, spec.md US2 AS3). La causa original
    queda encadenada (`raise ... from causa`), nunca silenciada ni
    reformulada."""

    def __init__(self, ruta_audio: Path, causa: Exception) -> None:
        self.ruta_audio = ruta_audio
        super().__init__(
            f"La transcripción del archivo '{ruta_audio}' falló: {causa}. "
            "No es el caso legítimo de 'el modelo no detectó ninguna nota' "
            "(eso da una lista vacía, no una excepción) -- es un fallo real "
            "del modelo o del framework de inferencia."
        )
