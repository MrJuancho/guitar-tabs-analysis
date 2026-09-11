"""Tests unitarios de `digitacion.orquestador.artefacto_a_dict` (T022,
mismo patrón que `deteccion.orquestador.artefacto_a_dict`/T030-T031 del
hito 2): un `ArtefactoDigitacion` construido a mano, con todas las
piezas anidadas (posiciones, exclusiones de instante, notas con
posición real, exclusiones de grabación), para verificar la
serialización completa -- no solo el conteo de `grabaciones` que otros
tests (CLI, integración) ya cubren de punta a punta.
"""

from __future__ import annotations

import json

from guitar_tabs_analysis.analytics.metrica_digitacion import (
    ArtefactoDigitacion,
    Digitacion,
    ExclusionDigitacion,
    InstanteExcluido,
    ModeloCoste,
    Posicion,
    PosicionAsignada,
    ResultadoCoincidencia,
    ResultadoDigitacionGrabacion,
)
from guitar_tabs_analysis.digitacion.orquestador import artefacto_a_dict
from guitar_tabs_analysis.ingestion.guitarset import NotaConPosicionReal, NotaReferencia

_MODELO = ModeloCoste(
    midi_cuerda_abierta={"E": 40, "A": 45, "D": 50, "G": 55, "B": 59, "e": 64},
    traste_minimo=0,
    traste_maximo=19,
    tolerancia_tono_cents=50.0,
    limite_estiramiento_trastes=5,
    ventana_instante_s=0.03,
    peso_desplazamiento=1.0,
    peso_cruce_cuerdas=1.0,
)


def _artefacto_completo() -> ArtefactoDigitacion:
    n1 = NotaReferencia(tono_midi=47.0, inicio_s=1.0, fin_s=1.5)
    digitacion_g1 = Digitacion(
        posiciones=[PosicionAsignada(nota=n1, posicion=Posicion(cuerda="A", traste=2))],
        exclusiones=[
            InstanteExcluido(
                inicio_representativo_s=10.0, motivo="excede el límite de estiramiento"
            )
        ],
        coste_total=0.0,
    )
    reales_g1 = [
        NotaConPosicionReal(tono_midi=47.0, inicio_s=1.0, fin_s=1.5, cuerda_real="A", traste_real=2)
    ]
    resultado_g1 = ResultadoDigitacionGrabacion(
        grabacion_id="g1",
        digitacion=digitacion_g1,
        notas_con_posicion_real=reales_g1,
        exclusion=None,
    )
    resultado_g2 = ResultadoDigitacionGrabacion(
        grabacion_id="g2",
        digitacion=None,
        notas_con_posicion_real=None,
        exclusion=ExclusionDigitacion(grabacion_id="g2", detalle="no existe en el índice"),
    )
    return ArtefactoDigitacion(
        modelo_coste=_MODELO,
        grabaciones=["g1", "g2"],
        exclusiones_grabacion=[resultado_g2.exclusion] if resultado_g2.exclusion else [],
        resultados_por_grabacion=[resultado_g1, resultado_g2],
        resultado_coincidencia=ResultadoCoincidencia(
            fraccion_coincidencia=1.0, num_notas_medidas=1, num_notas_coincidentes=1
        ),
    )


def test_artefacto_a_dict_serializa_el_modelo_de_coste_completo() -> None:
    contenido = artefacto_a_dict(_artefacto_completo())

    assert contenido["modelo_coste"] == {
        "midi_cuerda_abierta": {"E": 40, "A": 45, "D": 50, "G": 55, "B": 59, "e": 64},
        "traste_minimo": 0,
        "traste_maximo": 19,
        "tolerancia_tono_cents": 50.0,
        "limite_estiramiento_trastes": 5,
        "ventana_instante_s": 0.03,
        "peso_desplazamiento": 1.0,
        "peso_cruce_cuerdas": 1.0,
    }


def test_artefacto_a_dict_serializa_posiciones_y_exclusiones_de_instante() -> None:
    contenido = artefacto_a_dict(_artefacto_completo())

    resultado_g1 = next(
        r for r in contenido["resultados_por_grabacion"] if r["grabacion_id"] == "g1"
    )
    assert resultado_g1["exclusion"] is None
    assert resultado_g1["digitacion"]["coste_total"] == 0.0
    assert resultado_g1["digitacion"]["posiciones"] == [
        {
            "nota": {"tono_midi": 47.0, "inicio_s": 1.0, "fin_s": 1.5},
            "posicion": {"cuerda": "A", "traste": 2},
        }
    ]
    assert resultado_g1["digitacion"]["exclusiones"] == [
        {"inicio_representativo_s": 10.0, "motivo": "excede el límite de estiramiento"}
    ]
    assert resultado_g1["notas_con_posicion_real"] == [
        {
            "tono_midi": 47.0,
            "inicio_s": 1.0,
            "fin_s": 1.5,
            "cuerda_real": "A",
            "traste_real": 2,
        }
    ]


def test_artefacto_a_dict_serializa_grabacion_excluida_sin_digitacion() -> None:
    contenido = artefacto_a_dict(_artefacto_completo())

    resultado_g2 = next(
        r for r in contenido["resultados_por_grabacion"] if r["grabacion_id"] == "g2"
    )
    assert resultado_g2["digitacion"] is None
    assert resultado_g2["notas_con_posicion_real"] is None
    assert resultado_g2["exclusion"] == {"grabacion_id": "g2", "detalle": "no existe en el índice"}
    assert contenido["exclusiones_grabacion"] == [
        {"grabacion_id": "g2", "detalle": "no existe en el índice"}
    ]


def test_artefacto_a_dict_serializa_resultado_coincidencia_y_grabaciones() -> None:
    contenido = artefacto_a_dict(_artefacto_completo())

    assert contenido["grabaciones"] == ["g1", "g2"]
    assert contenido["resultado_coincidencia"] == {
        "fraccion_coincidencia": 1.0,
        "num_notas_medidas": 1,
        "num_notas_coincidentes": 1,
    }


def test_artefacto_a_dict_hace_round_trip_completo_por_json() -> None:
    """`json.dumps`/`json.loads` no pierde ningún valor -- mismo patrón
    que T031 del hito 2."""
    original = artefacto_a_dict(_artefacto_completo())

    reconstruido = json.loads(json.dumps(original))

    assert reconstruido == original
