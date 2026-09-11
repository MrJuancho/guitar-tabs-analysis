"""Property test (Hypothesis) del invariante permanente de partición
mono/poli de `evaluar_grabacion` (FR-014, research.md #17, SC-007):
`verdaderos_positivos` de monofónico + polifónico == global, para
cualquier conjunto de notas de UNA grabación -- guarda permanente contra
reintroducir un emparejamiento independiente por subconjunto (research.md
#9, superado por #17). Referencias/estimadas ya sumaban exacto antes del
arreglo; este test cubre el conteo que sí se rompía.

La estrategia genera notas de referencia y estimadas con tono/inicio/
duración arbitrarios dentro de un rango que produce con frecuencia
acordes (2+ referencias con el mismo o similar inicio) y estimadas cuyo
inicio cae cerca -- pero no exactamente encima -- del de la referencia
que empareja, el escenario donde el defecto original se manifestaba
(AGENTS.md, "Property tests: muestrea del dominio real")."""

from __future__ import annotations

from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.strategies import DrawFn

from guitar_tabs_analysis.analytics.metrica_deteccion_notas import (
    NotaEstimada,
    evaluar_grabacion,
)
from guitar_tabs_analysis.ingestion.guitarset import NotaReferencia

_tono_midi = st.floats(min_value=40.0, max_value=80.0, allow_nan=False, allow_infinity=False)
_inicio_s = st.floats(min_value=0.0, max_value=5.0, allow_nan=False, allow_infinity=False)
_duracion_s = st.floats(min_value=0.01, max_value=1.5, allow_nan=False, allow_infinity=False)


@st.composite
def _nota_referencia_arbitraria(draw: DrawFn) -> NotaReferencia:
    inicio = draw(_inicio_s)
    duracion = draw(_duracion_s)
    return NotaReferencia(tono_midi=draw(_tono_midi), inicio_s=inicio, fin_s=inicio + duracion)


@st.composite
def _nota_estimada_arbitraria(draw: DrawFn) -> NotaEstimada:
    inicio = draw(_inicio_s)
    duracion = draw(_duracion_s)
    return NotaEstimada(tono_midi=draw(_tono_midi), inicio_s=inicio, fin_s=inicio + duracion)


_notas_referencia = st.lists(_nota_referencia_arbitraria(), min_size=0, max_size=10)
_notas_estimadas = st.lists(_nota_estimada_arbitraria(), min_size=0, max_size=10)


@given(notas_referencia=_notas_referencia, notas_estimadas=_notas_estimadas)
@settings(max_examples=300)
def test_verdaderos_positivos_de_mono_y_poli_siempre_suman_el_global(
    notas_referencia: list[NotaReferencia], notas_estimadas: list[NotaEstimada]
) -> None:
    global_, mono, poli = evaluar_grabacion(notas_referencia, notas_estimadas)

    assert mono.verdaderos_positivos + poli.verdaderos_positivos == global_.verdaderos_positivos
    assert mono.num_notas_referencia + poli.num_notas_referencia == global_.num_notas_referencia
    assert mono.num_notas_estimadas + poli.num_notas_estimadas == global_.num_notas_estimadas
