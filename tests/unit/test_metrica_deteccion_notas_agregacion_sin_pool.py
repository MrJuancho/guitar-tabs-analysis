"""Regresión del defecto real de OOM/corrección encontrado corriendo
`just detectar medibles <root_dir>` sobre las 288 grabaciones reales de
GuitarSet (research.md #16, FR-013, SC-002 de
`specs/006-deteccion-notas-guitarra-limpia/`): la primera implementación
de `agregar_conjunto` pooleaba las notas de referencia y estimadas de
TODAS las grabaciones no excluidas en dos listas únicas antes de
emparejar -- eso permite que una nota de una grabación se acredite
espuriamente contra una nota de OTRA grabación si sus instantes de inicio
caen dentro de la ventana de 50ms, y además construye una matriz
`mir_eval.transcription.match_notes` cuadrática en el tamaño del pool
(~61 GB medidos sobre 288 grabaciones reales).

Test 1 (`test_agregar_conjunto_nunca_acredita_una_nota_contra_otra_grabacion`):
el que más importa -- dos grabaciones sintéticas, cada una sin ningún
acierto real DENTRO de sí misma, pero con una nota de la grabación B que
cae dentro de tono/ventana de tolerancia de una nota de la grabación A --
correcto es 0 aciertos totales; el diseño pooled (roto) acredita 1.

Test 2 (`test_agregar_conjunto_agrega_por_suma_de_conteos_no_por_promedio`):
mismo patrón que `test_metrica_separacion_agregacion_equivalencia.py`
(Feature 002/004) -- confirma que "sumar conteos y dividir al final" es
exactamente la aritmética que `agregar_conjunto` aplica, con 3
grabaciones sintéticas de emparejamiento inequívoco (o matchea
completo, o no matchea nada) y una de ellas excluida.
"""

from __future__ import annotations

import mir_eval.util

from guitar_tabs_analysis.analytics.metrica_deteccion_notas import (
    ExclusionDeteccion,
    NotaEstimada,
    ResultadoDeteccionGrabacion,
    agregar_conjunto,
    evaluar_grabacion,
)
from guitar_tabs_analysis.ingestion.guitarset import NotaReferencia

# ---------------------------------------------------------------------
# Test 1 -- el que más importa: ninguna nota se acredita entre
# grabaciones distintas (FR-013, SC-002).
# ---------------------------------------------------------------------


def test_agregar_conjunto_nunca_acredita_una_nota_contra_otra_grabacion() -> None:
    # Grabación A: una referencia sola, sin ninguna estimada que la
    # acierte DENTRO de esta grabación (tono/inicio bien distintos).
    ref_a = NotaReferencia(tono_midi=60.0, inicio_s=1.000, fin_s=1.5)
    est_a = NotaEstimada(tono_midi=65.0, inicio_s=5.000, fin_s=5.5)

    # Grabación B: una referencia sola, tampoco acertada dentro de esta
    # grabación -- pero su nota ESTIMADA comparte tono e instante de
    # inicio (dentro de la ventana de 50ms/50 cents) con la REFERENCIA de
    # la grabación A de arriba. Sin relación temporal real entre A y B:
    # son dos clips independientes.
    ref_b = NotaReferencia(tono_midi=70.0, inicio_s=8.000, fin_s=8.5)
    est_b = NotaEstimada(tono_midi=60.0, inicio_s=1.010, fin_s=1.5)

    resultados = [
        ResultadoDeteccionGrabacion(
            grabacion_id="grab_a", notas_referencia=[ref_a], notas_estimadas=[est_a], exclusion=None
        ),
        ResultadoDeteccionGrabacion(
            grabacion_id="grab_b", notas_referencia=[ref_b], notas_estimadas=[est_b], exclusion=None
        ),
    ]

    global_, _mono, _poli = agregar_conjunto(resultados)

    # Si `agregar_conjunto` pooleara notas crudas de A y B, ref_a
    # emparejaría con est_b (mismo tono, inicio a 10ms de distancia) y
    # produciría 1 acierto espurio -- precisión/exhaustividad = 0.5, no
    # 0.0. La cifra correcta, por grabación, es 0 aciertos sobre 2
    # referencias y 2 estimadas. Esta es la primera aserción a propósito
    # (antes de tocar `verdaderos_positivos`, más abajo): ya alcanza sola
    # para reproducir el defecto contra el código pooled -- no depende de
    # que el campo nuevo exista.
    assert global_.precision == 0.0
    assert global_.exhaustividad == 0.0
    assert global_.num_notas_referencia == 2
    assert global_.num_notas_estimadas == 2

    # Lo correcto: emparejar CADA grabación por separado (nunca junto) y
    # sumar los aciertos ya resueltos -- ninguna de las dos grabaciones
    # tiene, dentro de sí misma, ningún acierto.
    global_a, _mono_a, _poli_a = evaluar_grabacion([ref_a], [est_a])
    global_b, _mono_b, _poli_b = evaluar_grabacion([ref_b], [est_b])
    aciertos_esperados_por_grabacion_separada = (
        global_a.verdaderos_positivos + global_b.verdaderos_positivos
    )
    assert aciertos_esperados_por_grabacion_separada == 0

    # El conteo total de verdaderos positivos coincide EXACTAMENTE con el
    # calculado por-grabación, nunca con el conteo mayor (1) que el
    # diseño pooled produciría.
    assert global_.verdaderos_positivos == aciertos_esperados_por_grabacion_separada
    assert global_.verdaderos_positivos == 0


# ---------------------------------------------------------------------
# Test 2 -- equivalencia de la agregación: sumar conteos y dividir al
# final es exactamente la aritmética que `agregar_conjunto` aplica.
# ---------------------------------------------------------------------


def test_agregar_conjunto_agrega_por_suma_de_conteos_no_por_promedio() -> None:
    # Grabación 1: dos referencias, dos estimadas -- ambas aciertan
    # exactamente (mismo tono/inicio que su referencia). TP=2, ref=2, est=2.
    ref1 = [
        NotaReferencia(tono_midi=60.0, inicio_s=0.0, fin_s=0.5),
        NotaReferencia(tono_midi=64.0, inicio_s=10.0, fin_s=10.5),
    ]
    est1 = [
        NotaEstimada(tono_midi=60.0, inicio_s=0.0, fin_s=0.5),
        NotaEstimada(tono_midi=64.0, inicio_s=10.0, fin_s=10.5),
    ]

    # Grabación 2: una referencia, tres estimadas -- ninguna acierta
    # (tonos deliberadamente muy separados, fuera de los 50 cents).
    # TP=0, ref=1, est=3.
    ref2 = [NotaReferencia(tono_midi=40.0, inicio_s=20.0, fin_s=20.5)]
    est2 = [
        NotaEstimada(tono_midi=80.0, inicio_s=20.0, fin_s=20.5),
        NotaEstimada(tono_midi=81.0, inicio_s=21.0, fin_s=21.5),
        NotaEstimada(tono_midi=82.0, inicio_s=22.0, fin_s=22.5),
    ]

    # Grabación 3: excluida -- no debe contarse en absoluto (sus notas
    # son `None`, mismo patrón que cualquier `ResultadoDeteccionGrabacion`
    # excluido, data-model.md).
    resultados = [
        ResultadoDeteccionGrabacion(
            grabacion_id="rec1", notas_referencia=ref1, notas_estimadas=est1, exclusion=None
        ),
        ResultadoDeteccionGrabacion(
            grabacion_id="rec2", notas_referencia=ref2, notas_estimadas=est2, exclusion=None
        ),
        ResultadoDeteccionGrabacion(
            grabacion_id="rec3_excluida",
            notas_referencia=None,
            notas_estimadas=None,
            exclusion=ExclusionDeteccion("rec3_excluida", "fallo simulado -- no debe contarse"),
        ),
    ]

    # Calculado a mano, SIN llamar a agregar_conjunto: TP=2+0=2,
    # num_ref=2+1=3, num_est=2+3=5 (rec3 no cuenta, está excluida).
    tp_esperado = 2
    num_ref_esperado = 3
    num_est_esperado = 5
    precision_esperada = tp_esperado / num_est_esperado
    exhaustividad_esperada = tp_esperado / num_ref_esperado
    balance_esperado = mir_eval.util.f_measure(precision_esperada, exhaustividad_esperada)

    global_, _mono, _poli = agregar_conjunto(resultados)

    assert global_.verdaderos_positivos == tp_esperado
    assert global_.num_notas_referencia == num_ref_esperado
    assert global_.num_notas_estimadas == num_est_esperado
    assert global_.precision == precision_esperada
    assert global_.exhaustividad == exhaustividad_esperada
    assert global_.balance_f1 == balance_esperado
