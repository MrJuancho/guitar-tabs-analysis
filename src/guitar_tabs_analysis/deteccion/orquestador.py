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

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import mirdata

from guitar_tabs_analysis.analytics.metrica_deteccion_notas import (
    TOLERANCIA_TONO_CENTS,
    VENTANA_INICIO_S,
    ExclusionDeteccion,
    NotaEstimada,
    ResultadoDeteccionGrabacion,
    ResultadoSubconjunto,
    agregar_conjunto,
)
from guitar_tabs_analysis.ingestion.guitarset import (
    GrabacionNoExisteError,
    NotaReferencia,
    leer_grabacion,
)
from guitar_tabs_analysis.transcripcion.transcriptor import (
    ModeloTranscripcionDeclarado,
    TranscripcionFallidaError,
    Transcriptor,
)

# ---------------------------------------------------------------------
# construir_lista_grabaciones (T028) -- contracts/deteccion.md,
# postcondición 1 de `deteccion.orquestador`, research.md #14.
# ---------------------------------------------------------------------

SEMILLA_RESERVA_HITO2 = 20260908
"""research.md #14 -- 72 de 360 grabaciones de GuitarSet (20%) reservadas
para el cierre del hito 2, Principio VI de la constitución v1.8.0."""

TAMANO_RESERVA_HITO2 = 72


def construir_lista_grabaciones(
    modo: Literal["medibles", "reservado"],
    root_dir: Path,
    *,
    tamano_reserva: int = TAMANO_RESERVA_HITO2,
    semilla_reserva: int = SEMILLA_RESERVA_HITO2,
) -> list[str]:
    """Deriva la partición medibles/reservado de GuitarSet EN VIVO de
    `semilla_reserva` en cada invocación -- MUST NOT leer ni escribir
    ningún archivo de manifiesto (research.md #14, corrección de
    T028/Fase 7: la decisión original preveía un manifiesto persistido en
    `tests/holdout/`, descartada a favor de esto -- un manifiesto
    cacheado en disco no reflejaría un cambio de `semilla_reserva` en el
    código, este cálculo sí).

    Enumera los identificadores de GuitarSet vía `dataset.track_ids`
    (`mirdata.core.Dataset`, verificado contra su código fuente real,
    instalado en este proyecto -- `mirdata/core.py` línea 466), los
    ordena (reproducibilidad, mismo criterio que
    `medicion.orquestador.construir_lista_temas`, cuyo orden de
    `mirdata`/`os.listdir` no tiene garantía propia de estabilidad), y
    calcula `random.Random(semilla_reserva).sample(todos, tamano_reserva)`
    una única vez: con `modo="reservado"` devuelve esa muestra (ordenada);
    con `modo="medibles"` devuelve el complemento exacto, en el mismo
    orden que `todos` -- ambos derivados del mismo cálculo, así que son
    complementarios por construcción (unión = `todos`, intersección
    vacía), nunca dos invocaciones de `random.Random` con parámetros
    distintos que podrían divergir.
    """
    dataset = mirdata.initialize("guitarset", data_home=str(root_dir))
    todos = sorted(dataset.track_ids)
    reservados = set(random.Random(semilla_reserva).sample(todos, tamano_reserva))
    if modo == "reservado":
        return sorted(reservados)
    if modo == "medibles":
        return [grabacion_id for grabacion_id in todos if grabacion_id not in reservados]


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


# ---------------------------------------------------------------------
# Serialización de ArtefactoDeteccion (T030) -- función pura, sin tocar
# disco (quien escribe el archivo final es `deteccion.cli`, Fase 7).
# Mismo patrón exacto que `medicion.orquestador.artefacto_a_dict`.
# ---------------------------------------------------------------------


def _nota_referencia_a_dict(nota: NotaReferencia) -> dict[str, Any]:
    return {"tono_midi": nota.tono_midi, "inicio_s": nota.inicio_s, "fin_s": nota.fin_s}


def _nota_estimada_a_dict(nota: NotaEstimada) -> dict[str, Any]:
    return {"tono_midi": nota.tono_midi, "inicio_s": nota.inicio_s, "fin_s": nota.fin_s}


def _exclusion_a_dict(exclusion: ExclusionDeteccion) -> dict[str, Any]:
    return {"grabacion_id": exclusion.grabacion_id, "detalle": exclusion.detalle}


def _resultado_subconjunto_a_dict(resultado: ResultadoSubconjunto) -> dict[str, Any]:
    return {
        "precision": resultado.precision,
        "exhaustividad": resultado.exhaustividad,
        "balance_f1": resultado.balance_f1,
        "num_notas_referencia": resultado.num_notas_referencia,
        "num_notas_estimadas": resultado.num_notas_estimadas,
    }


def _resultado_deteccion_grabacion_a_dict(resultado: ResultadoDeteccionGrabacion) -> dict[str, Any]:
    return {
        "grabacion_id": resultado.grabacion_id,
        "notas_referencia": (
            [_nota_referencia_a_dict(nota) for nota in resultado.notas_referencia]
            if resultado.notas_referencia is not None
            else None
        ),
        "notas_estimadas": (
            [_nota_estimada_a_dict(nota) for nota in resultado.notas_estimadas]
            if resultado.notas_estimadas is not None
            else None
        ),
        "exclusion": (
            _exclusion_a_dict(resultado.exclusion) if resultado.exclusion is not None else None
        ),
    }


def artefacto_a_dict(artefacto: ArtefactoDeteccion) -> dict[str, Any]:
    """`dict` JSON-compatible con todo lo que FR-011 exige: modelo
    declarado, tolerancia de tono y ventana de inicio aplicadas, la lista
    de grabaciones, las exclusiones con su motivo, los resultados crudos
    por grabación, y el desglose global/monofónico/polifónico de las tres
    cifras."""
    return {
        "modelo": {
            "nombre": artefacto.modelo.nombre,
            "variante": artefacto.modelo.variante,
            "firma": artefacto.modelo.firma,
            "backend": artefacto.modelo.backend,
            "licencia": artefacto.modelo.licencia,
        },
        "tolerancia_tono_cents": artefacto.tolerancia_tono_cents,
        "ventana_inicio_s": artefacto.ventana_inicio_s,
        "grabaciones": artefacto.grabaciones,
        "exclusiones": [_exclusion_a_dict(e) for e in artefacto.exclusiones],
        "resultados_por_grabacion": [
            _resultado_deteccion_grabacion_a_dict(r) for r in artefacto.resultados_por_grabacion
        ],
        "global": _resultado_subconjunto_a_dict(artefacto.global_),
        "monofonico": _resultado_subconjunto_a_dict(artefacto.monofonico),
        "polifonico": _resultado_subconjunto_a_dict(artefacto.polifonico),
    }
