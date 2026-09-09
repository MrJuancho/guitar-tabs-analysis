"""Orquestación de la detección de notas del hito 2 (paquete nuevo,
importa de `ingestion`, `transcripcion` y `analytics` a la vez --
excluido a propósito del contrato `layers` de import-linter,
`pyproject.toml::[tool.importlinter]`, mismo criterio que `medicion` en
el hito 1, research.md #11 de `specs/006-deteccion-notas-guitarra-limpia/`):
dado un conjunto de identificadores de grabación, lee cada una
(`ingestion.guitarset.leer_grabacion`) y la transcribe (`Transcriptor`),
con exclusión terminal por grabación ante un fallo real (FR-012) -- nunca
aborta la corrida completa por un fallo individual.

Ver `specs/006-deteccion-notas-guitarra-limpia/data-model.md` y
`specs/006-deteccion-notas-guitarra-limpia/contracts/deteccion.md` para
el contrato completo (T023, User Story 3).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from guitar_tabs_analysis.analytics.metrica_deteccion_notas import (
    TOLERANCIA_TONO_CENTS,
    VENTANA_INICIO_S,
    ExclusionDeteccion,
    ResultadoDeteccionGrabacion,
    ResultadoSubconjunto,
    agregar_conjunto,
)
from guitar_tabs_analysis.ingestion.guitarset import GrabacionNoExisteError, leer_grabacion
from guitar_tabs_analysis.transcripcion.transcriptor import (
    ModeloTranscripcionDeclarado,
    TranscripcionFallidaError,
    Transcriptor,
)

# ---------------------------------------------------------------------
# ArtefactoDeteccion -- data-model.md. Vive aquí (no en `analytics`):
# nada por debajo de `deteccion` necesita referenciarlo en ninguna
# firma, así que no hay riesgo de ciclo de imports.
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ArtefactoDeteccion:
    """El artefacto final de una corrida completa sobre un conjunto de
    grabaciones (FR-011) -- mismo rol que `ArtefactoMedicion` del hito 1."""

    modelo: ModeloTranscripcionDeclarado
    tolerancia_tono_cents: float
    ventana_inicio_s: float
    grabaciones: list[str]
    exclusiones: list[ExclusionDeteccion]
    resultados_por_grabacion: list[ResultadoDeteccionGrabacion]
    global_: ResultadoSubconjunto
    monofonico: ResultadoSubconjunto
    polifonico: ResultadoSubconjunto


# ---------------------------------------------------------------------
# ejecutar_deteccion (T023) -- contracts/deteccion.md.
# ---------------------------------------------------------------------


def ejecutar_deteccion(
    grabaciones: list[str],
    root_dir: Path,
    transcriptor: Transcriptor,
) -> ArtefactoDeteccion:
    """Lee y transcribe cada grabación de `grabaciones` de a una
    (contracts/deteccion.md postcondición 1): si `leer_grabacion` levanta
    `GrabacionNoExisteError`, o `transcriptor.transcribir` levanta
    `TranscripcionFallidaError`, registra la grabación como
    `ExclusionDeteccion` con el detalle del error real y continúa con la
    siguiente -- nunca aborta la corrida completa por un fallo
    individual (FR-012).

    Al completar todas las grabaciones, devuelve un único
    `ArtefactoDeteccion` con el modelo declarado, la tolerancia y ventana
    fijas (`TOLERANCIA_TONO_CENTS`/`VENTANA_INICIO_S`), la lista de
    grabaciones, las exclusiones con su motivo, los resultados crudos por
    grabación, y las tres cifras (global/monofónico/polifónico)
    calculadas con `agregar_conjunto` sobre las grabaciones no excluidas
    -- MUST NOT comparar ninguna cifra contra ningún umbral (FR-009,
    postcondición 3)."""
    resultados: list[ResultadoDeteccionGrabacion] = []
    for grabacion_id in grabaciones:
        try:
            lectura = leer_grabacion(grabacion_id, root_dir)
        except GrabacionNoExisteError as causa:
            resultados.append(
                ResultadoDeteccionGrabacion(
                    grabacion_id=grabacion_id,
                    notas_referencia=None,
                    notas_estimadas=None,
                    exclusion=ExclusionDeteccion(grabacion_id, str(causa)),
                )
            )
            continue

        try:
            notas_estimadas = transcriptor.transcribir(lectura.ruta_audio)
        except TranscripcionFallidaError as causa:
            resultados.append(
                ResultadoDeteccionGrabacion(
                    grabacion_id=grabacion_id,
                    notas_referencia=None,
                    notas_estimadas=None,
                    exclusion=ExclusionDeteccion(grabacion_id, str(causa)),
                )
            )
            continue

        resultados.append(
            ResultadoDeteccionGrabacion(
                grabacion_id=grabacion_id,
                notas_referencia=lectura.notas_referencia,
                notas_estimadas=notas_estimadas,
                exclusion=None,
            )
        )

    exclusiones = [r.exclusion for r in resultados if r.exclusion is not None]
    global_, monofonico, polifonico = agregar_conjunto(resultados)

    return ArtefactoDeteccion(
        modelo=transcriptor.modelo_declarado,
        tolerancia_tono_cents=TOLERANCIA_TONO_CENTS,
        ventana_inicio_s=VENTANA_INICIO_S,
        grabaciones=grabaciones,
        exclusiones=exclusiones,
        resultados_por_grabacion=resultados,
        global_=global_,
        monofonico=monofonico,
        polifonico=polifonico,
    )
