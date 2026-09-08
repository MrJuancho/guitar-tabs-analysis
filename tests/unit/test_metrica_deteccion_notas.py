"""Tests unitarios de `evaluar_subconjunto()` (User Story 1,
`specs/006-deteccion-notas-guitarra-limpia/tasks.md`, T007/T008).

T007: los cinco Acceptance Scenarios de `spec.md` User Story 1, más el
caso de respuesta conocida (nota estimada = nota de referencia, pedido
explícito de la sesión de `/speckit-implement`).

T008: el denominador-cero de FR-008 (subconjunto vacío), en sus tres
combinaciones.

No prueba `clasificar_polifonia_en_instante`, `evaluar_grabacion` ni
`agregar_conjunto` -- son User Story 3 (T017 en adelante), fuera del
alcance de este slice.
"""

from __future__ import annotations

from guitar_tabs_analysis.analytics.metrica_deteccion_notas import (
    NotaEstimada,
    ResultadoSubconjunto,
    evaluar_subconjunto,
)
from guitar_tabs_analysis.ingestion.guitarset import NotaReferencia

# ---------------------------------------------------------------------
# T007 -- Acceptance Scenarios 1-5 de spec.md User Story 1.
# ---------------------------------------------------------------------


def test_as1_mismo_tono_e_inicio_dentro_de_ventana_acierta() -> None:
    referencia = NotaReferencia(tono_midi=60.0, inicio_s=1.0, fin_s=1.5)
    estimada = NotaEstimada(tono_midi=60.0, inicio_s=1.02, fin_s=1.6)

    resultado = evaluar_subconjunto([referencia], [estimada])

    assert resultado.precision == 1.0
    assert resultado.exhaustividad == 1.0
    assert resultado.balance_f1 == 1.0


def test_as2_tono_fuera_de_tolerancia_no_acierta() -> None:
    # 1.0 MIDI de diferencia == 100 cents (el doble de la tolerancia de
    # 50 cents, research.md #3) -- claramente fuera, sin importar que el
    # inicio esté muy cerca.
    referencia = NotaReferencia(tono_midi=60.0, inicio_s=1.0, fin_s=1.5)
    estimada = NotaEstimada(tono_midi=61.0, inicio_s=1.0, fin_s=1.5)

    resultado = evaluar_subconjunto([referencia], [estimada])

    assert resultado.precision == 0.0
    assert resultado.exhaustividad == 0.0
    assert resultado.balance_f1 == 0.0


def test_as3_inicio_fuera_de_ventana_no_acierta() -> None:
    referencia = NotaReferencia(tono_midi=60.0, inicio_s=1.0, fin_s=1.5)
    estimada = NotaEstimada(tono_midi=60.0, inicio_s=1.5, fin_s=2.0)

    resultado = evaluar_subconjunto([referencia], [estimada])

    assert resultado.precision == 0.0
    assert resultado.exhaustividad == 0.0
    assert resultado.balance_f1 == 0.0


def test_as4_duracion_distinta_no_participa_del_criterio() -> None:
    # Tono e inicio dentro de tolerancia; la duración difiere
    # sustancialmente (0.1s vs ~4s) -- FR-004: nunca participa.
    referencia = NotaReferencia(tono_midi=60.0, inicio_s=1.0, fin_s=1.1)
    estimada = NotaEstimada(tono_midi=60.0, inicio_s=1.01, fin_s=5.0)

    resultado = evaluar_subconjunto([referencia], [estimada])

    assert resultado.precision == 1.0
    assert resultado.exhaustividad == 1.0
    assert resultado.balance_f1 == 1.0


def test_as5_una_sola_estimada_no_acredita_dos_referencias_ambiguas() -> None:
    # Dos referencias suficientemente cerca entre sí como para que ambas
    # caigan dentro de tolerancia/ventana de la ÚNICA nota estimada --
    # solo una puede acreditarse (FR-005): exhaustividad = 1/2, nunca 1.0.
    referencia_a = NotaReferencia(tono_midi=60.0, inicio_s=1.00, fin_s=1.3)
    referencia_b = NotaReferencia(tono_midi=60.0, inicio_s=1.01, fin_s=1.3)
    estimada = NotaEstimada(tono_midi=60.0, inicio_s=1.005, fin_s=1.3)

    resultado = evaluar_subconjunto([referencia_a, referencia_b], [estimada])

    assert resultado.num_notas_referencia == 2
    assert resultado.num_notas_estimadas == 1
    assert resultado.precision == 1.0
    assert resultado.exhaustividad == 0.5


def test_as5_una_sola_referencia_no_se_acredita_dos_veces() -> None:
    # Simétrico al caso anterior: dos estimadas ambiguas contra una sola
    # referencia -- solo una puede acreditarse: precisión = 1/2, nunca 1.0.
    referencia = NotaReferencia(tono_midi=60.0, inicio_s=1.00, fin_s=1.3)
    estimada_a = NotaEstimada(tono_midi=60.0, inicio_s=1.00, fin_s=1.3)
    estimada_b = NotaEstimada(tono_midi=60.0, inicio_s=1.01, fin_s=1.3)

    resultado = evaluar_subconjunto([referencia], [estimada_a, estimada_b])

    assert resultado.num_notas_referencia == 1
    assert resultado.num_notas_estimadas == 2
    assert resultado.exhaustividad == 1.0
    assert resultado.precision == 0.5


def test_respuesta_conocida_estimada_igual_a_referencia_da_uno_exacto() -> None:
    """Caso de respuesta conocida (mismo criterio que SI-SDR del hito 1,
    pedido explícito de esta sesión): la MISMA lista de `NotaReferencia`,
    reconstruida como `NotaEstimada` con idéntico tono_midi/inicio_s,
    debe dar precisión/exhaustividad/balance EXACTAMENTE 1.0 -- cada
    nota se empareja consigo misma, sin tolerancia de por medio."""
    referencias = [
        NotaReferencia(tono_midi=60.0, inicio_s=0.0, fin_s=0.5),
        NotaReferencia(tono_midi=64.0, inicio_s=1.0, fin_s=1.3),
        NotaReferencia(tono_midi=67.0, inicio_s=2.0, fin_s=2.7),
    ]
    estimadas = [
        NotaEstimada(tono_midi=r.tono_midi, inicio_s=r.inicio_s, fin_s=r.fin_s) for r in referencias
    ]

    resultado = evaluar_subconjunto(referencias, estimadas)

    assert resultado.precision == 1.0
    assert resultado.exhaustividad == 1.0
    assert resultado.balance_f1 == 1.0
    assert resultado.num_notas_referencia == 3
    assert resultado.num_notas_estimadas == 3


# ---------------------------------------------------------------------
# T008 -- Subconjunto vacío (FR-008), las tres combinaciones.
# ---------------------------------------------------------------------


def test_subconjunto_vacio_ambas_listas_da_todo_none() -> None:
    resultado = evaluar_subconjunto([], [])

    assert resultado == ResultadoSubconjunto(
        precision=None,
        exhaustividad=None,
        balance_f1=None,
        num_notas_referencia=0,
        num_notas_estimadas=0,
    )


def test_subconjunto_vacio_solo_referencia_da_exhaustividad_none_precision_cero() -> None:
    estimada = NotaEstimada(tono_midi=60.0, inicio_s=1.0, fin_s=1.5)

    resultado = evaluar_subconjunto([], [estimada])

    assert resultado.exhaustividad is None
    assert resultado.precision == 0.0
    assert resultado.balance_f1 is None
    assert resultado.num_notas_referencia == 0
    assert resultado.num_notas_estimadas == 1


def test_subconjunto_vacio_solo_estimada_da_precision_none_exhaustividad_cero() -> None:
    referencia = NotaReferencia(tono_midi=60.0, inicio_s=1.0, fin_s=1.5)

    resultado = evaluar_subconjunto([referencia], [])

    assert resultado.precision is None
    assert resultado.exhaustividad == 0.0
    assert resultado.balance_f1 is None
    assert resultado.num_notas_referencia == 1
    assert resultado.num_notas_estimadas == 0
