"""Fixture de prueba para `transcripcion.transcriptor`: un `Transcriptor`
falso que implementa el protocolo sin invocar ningún subproceso ni cargar
ningún modelo real -- mismo patrón que `SeparadorFalso`
(`tests/fixtures/separador_fixture.py`, hito 1).
"""

from __future__ import annotations

from pathlib import Path

from guitar_tabs_analysis.analytics.metrica_deteccion_notas import NotaEstimada
from guitar_tabs_analysis.transcripcion.transcriptor import ModeloTranscripcionDeclarado

MODELO_FALSO = ModeloTranscripcionDeclarado(
    nombre="ModeloFalso",
    variante="v0-prueba",
    firma="dummy0000",
    backend="ninguno",
    licencia="ninguna -- solo para tests",
)


class TranscriptorFalso:
    """Implementa el protocolo `Transcriptor` (data-model.md) de forma
    completamente configurable, para ejercitar `deteccion.orquestador` sin
    ningún costo de subproceso ni de cómputo real.

    Por defecto, `transcribir()` devuelve `[]` (silencio total, camino
    legítimo de la interfaz -- spec.md US2 AS3). Si `notas` se pasa, las
    devuelve tal cual. Si `excepcion` no es `None`, la levanta en vez de
    devolver nada -- para ejercitar el camino de exclusión terminal del
    orquestador (FR-012).
    """

    def __init__(
        self,
        *,
        notas: list[NotaEstimada] | None = None,
        modelo_declarado: ModeloTranscripcionDeclarado = MODELO_FALSO,
        excepcion: Exception | None = None,
    ) -> None:
        self.modelo_declarado = modelo_declarado
        self._notas = notas
        self._excepcion = excepcion
        self.llamadas = 0
        self.ultima_ruta_audio: Path | None = None

    def transcribir(self, ruta_audio: Path) -> list[NotaEstimada]:
        self.llamadas += 1
        self.ultima_ruta_audio = ruta_audio
        if self._excepcion is not None:
            raise self._excepcion
        if self._notas is not None:
            return self._notas
        return []
