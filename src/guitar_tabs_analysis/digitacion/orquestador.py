"""Orquestación de la digitación con restricción de la mano (hito 3,
paquete nuevo -- importa de `ingestion` y `analytics` a la vez,
excluido a propósito del contrato `layers` de import-linter, mismo
criterio que `deteccion`/`medicion`, research.md #11 del hito 2): lee
la posición real de cada grabación (`ingestion.guitarset.
leer_grabacion_con_posicion_real`), calcula la digitación de coste
mínimo (`analytics.metrica_digitacion.asignar_secuencia`, User Story 2)
y mide la coincidencia contra la anotación real
(`evaluar_coincidencia`/`agregar_conjunto`, User Story 3), con
exclusión terminal por grabación ante un fallo de lectura -- nunca
aborta la corrida completa.

Reutiliza `deteccion.orquestador.construir_lista_grabaciones` tal cual
para cualquier partición medibles/reservado -- MUST NOT definir una
segunda función de partición (Principio VI, contracts/digitacion.md).

Ver `specs/007-digitacion-restriccion-mano/data-model.md` y
`specs/007-digitacion-restriccion-mano/contracts/digitacion.md` para
el contrato completo (T022, User Story 3).
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from guitar_tabs_analysis.analytics.metrica_digitacion import (
    MODELO_COSTE_POR_DEFECTO,
    ArtefactoDigitacion,
    Digitacion,
    ExclusionDigitacion,
    InstanteExcluido,
    ModeloCoste,
    NotaEntrada,
    Posicion,
    PosicionAsignada,
    ResultadoCoincidencia,
    ResultadoDigitacionGrabacion,
    agregar_conjunto,
    asignar_secuencia,
)
from guitar_tabs_analysis.deteccion.orquestador import construir_lista_grabaciones
from guitar_tabs_analysis.ingestion.guitarset import (
    GrabacionNoExisteError,
    NotaConPosicionReal,
    leer_grabacion_con_posicion_real,
)

__all__ = [
    "ArtefactoDigitacion",
    "construir_lista_grabaciones",
    "ejecutar_digitacion",
    "artefacto_a_dict",
]


# ---------------------------------------------------------------------
# ejecutar_digitacion (T022) -- contracts/digitacion.md.
# ---------------------------------------------------------------------


def ejecutar_digitacion(
    grabaciones: list[str],
    root_dir: Path,
    modelo: ModeloCoste = MODELO_COSTE_POR_DEFECTO,
) -> ArtefactoDigitacion:
    """Para cada `grabacion_id` de `grabaciones`, lee su posición real
    (`leer_grabacion_con_posicion_real`); si falla con
    `GrabacionNoExisteError`, registra la grabación como
    `ExclusionDigitacion` con el detalle del error real y continúa con
    la siguiente -- nunca aborta la corrida completa por un fallo
    individual (contracts/digitacion.md postcondición 1, mismo patrón
    que `ejecutar_deteccion` del hito 2).

    Si la lectura tiene éxito, calcula la digitación de coste mínimo
    sobre las notas proyectadas a `NotaEntrada` (sin la posición real,
    que solo se usa para medir después -- nunca para decidir qué
    posición asignar, FR-007) y mide la coincidencia contra las
    `NotaConPosicionReal` originales.

    Al completar todas las grabaciones, devuelve un único
    `ArtefactoDigitacion` con el modelo de coste aplicado, la lista de
    grabaciones, las exclusiones con su motivo, los resultados crudos
    por grabación, y el resultado de coincidencia agregado
    (`agregar_conjunto`) sobre las grabaciones no excluidas -- MUST NOT
    comparar ninguna cifra contra ningún umbral (FR-015,
    contracts/digitacion.md postcondición 3).

    Salida de progreso por grabación (mismo patrón que
    `ejecutar_deteccion`/`ejecutar_corrida`): `[i/N] grabacion_id  ok
    Xs  N posiciones` o `[i/N] grabacion_id  excluido: detalle`, y un
    aviso al entrar a la agregación."""
    resultados: list[ResultadoDigitacionGrabacion] = []
    total = len(grabaciones)
    ancho_indice = len(str(total))
    for indice, grabacion_id in enumerate(grabaciones, start=1):
        prefijo = f"[{indice:>{ancho_indice}}/{total}] {grabacion_id}"
        inicio = time.perf_counter()
        try:
            notas_con_posicion_real = leer_grabacion_con_posicion_real(grabacion_id, root_dir)
        except GrabacionNoExisteError as causa:
            exclusion = ExclusionDigitacion(grabacion_id, str(causa))
            resultados.append(
                ResultadoDigitacionGrabacion(
                    grabacion_id=grabacion_id,
                    digitacion=None,
                    notas_con_posicion_real=None,
                    exclusion=exclusion,
                )
            )
            print(f"{prefijo}  excluido: {exclusion.detalle}")
            continue

        notas_entrada: list[NotaEntrada] = [
            NotaEntrada(tono_midi=n.tono_midi, inicio_s=n.inicio_s, fin_s=n.fin_s)
            for n in notas_con_posicion_real
        ]
        digitacion = asignar_secuencia(notas_entrada, modelo)
        duracion = time.perf_counter() - inicio
        resultados.append(
            ResultadoDigitacionGrabacion(
                grabacion_id=grabacion_id,
                digitacion=digitacion,
                notas_con_posicion_real=notas_con_posicion_real,
                exclusion=None,
            )
        )
        print(f"{prefijo}  ok  {duracion:.1f}s  {len(digitacion.posiciones)} posiciones")

    print(f"agregando {total} grabaciones")
    exclusiones = [r.exclusion for r in resultados if r.exclusion is not None]
    resultado_coincidencia = agregar_conjunto(resultados)

    return ArtefactoDigitacion(
        modelo_coste=modelo,
        grabaciones=grabaciones,
        exclusiones_grabacion=exclusiones,
        resultados_por_grabacion=resultados,
        resultado_coincidencia=resultado_coincidencia,
    )


# ---------------------------------------------------------------------
# Serialización de ArtefactoDigitacion -- función pura, sin tocar disco
# (quien escribe el archivo final es `digitacion.cli`, T023). Mismo
# patrón exacto que `deteccion.orquestador.artefacto_a_dict`.
# ---------------------------------------------------------------------


def _modelo_coste_a_dict(modelo: ModeloCoste) -> dict[str, Any]:
    return {
        "midi_cuerda_abierta": modelo.midi_cuerda_abierta,
        "traste_minimo": modelo.traste_minimo,
        "traste_maximo": modelo.traste_maximo,
        "tolerancia_tono_cents": modelo.tolerancia_tono_cents,
        "limite_estiramiento_trastes": modelo.limite_estiramiento_trastes,
        "ventana_instante_s": modelo.ventana_instante_s,
        "peso_desplazamiento": modelo.peso_desplazamiento,
        "peso_cruce_cuerdas": modelo.peso_cruce_cuerdas,
    }


def _posicion_a_dict(posicion: Posicion) -> dict[str, Any]:
    return {"cuerda": posicion.cuerda, "traste": posicion.traste}


def _nota_entrada_a_dict(nota: NotaEntrada) -> dict[str, Any]:
    return {"tono_midi": nota.tono_midi, "inicio_s": nota.inicio_s, "fin_s": nota.fin_s}


def _posicion_asignada_a_dict(asignada: PosicionAsignada) -> dict[str, Any]:
    return {
        "nota": _nota_entrada_a_dict(asignada.nota),
        "posicion": _posicion_a_dict(asignada.posicion),
    }


def _instante_excluido_a_dict(excluido: InstanteExcluido) -> dict[str, Any]:
    return {
        "inicio_representativo_s": excluido.inicio_representativo_s,
        "motivo": excluido.motivo,
    }


def _digitacion_a_dict(digitacion: Digitacion) -> dict[str, Any]:
    return {
        "posiciones": [_posicion_asignada_a_dict(p) for p in digitacion.posiciones],
        "exclusiones": [_instante_excluido_a_dict(e) for e in digitacion.exclusiones],
        "coste_total": digitacion.coste_total,
    }


def _nota_con_posicion_real_a_dict(nota: NotaConPosicionReal) -> dict[str, Any]:
    return {
        "tono_midi": nota.tono_midi,
        "inicio_s": nota.inicio_s,
        "fin_s": nota.fin_s,
        "cuerda_real": nota.cuerda_real,
        "traste_real": nota.traste_real,
    }


def _exclusion_digitacion_a_dict(exclusion: ExclusionDigitacion) -> dict[str, Any]:
    return {"grabacion_id": exclusion.grabacion_id, "detalle": exclusion.detalle}


def _resultado_digitacion_grabacion_a_dict(
    resultado: ResultadoDigitacionGrabacion,
) -> dict[str, Any]:
    return {
        "grabacion_id": resultado.grabacion_id,
        "digitacion": _digitacion_a_dict(resultado.digitacion)
        if resultado.digitacion is not None
        else None,
        "notas_con_posicion_real": [
            _nota_con_posicion_real_a_dict(n) for n in resultado.notas_con_posicion_real
        ]
        if resultado.notas_con_posicion_real is not None
        else None,
        "exclusion": _exclusion_digitacion_a_dict(resultado.exclusion)
        if resultado.exclusion is not None
        else None,
    }


def _resultado_coincidencia_a_dict(resultado: ResultadoCoincidencia) -> dict[str, Any]:
    return {
        "fraccion_coincidencia": resultado.fraccion_coincidencia,
        "num_notas_medidas": resultado.num_notas_medidas,
        "num_notas_coincidentes": resultado.num_notas_coincidentes,
    }


def artefacto_a_dict(artefacto: ArtefactoDigitacion) -> dict[str, Any]:
    """`dict` JSON-compatible con todo lo que FR-016 exige: los
    parámetros del modelo de coste aplicados, la lista de grabaciones
    medidas, las exclusiones con su motivo, y la fracción de
    coincidencia con el número de notas que la componen."""
    return {
        "modelo_coste": _modelo_coste_a_dict(artefacto.modelo_coste),
        "grabaciones": artefacto.grabaciones,
        "exclusiones_grabacion": [
            _exclusion_digitacion_a_dict(e) for e in artefacto.exclusiones_grabacion
        ],
        "resultados_por_grabacion": [
            _resultado_digitacion_grabacion_a_dict(r) for r in artefacto.resultados_por_grabacion
        ],
        "resultado_coincidencia": _resultado_coincidencia_a_dict(artefacto.resultado_coincidencia),
    }
