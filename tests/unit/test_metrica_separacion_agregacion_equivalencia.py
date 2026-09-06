"""Regresión (T005 de `specs/004-medicion-linea-base/tasks.md`, indicación
explícita del usuario): la agregación en bloque (`agregar_conjunto`) y la
agregación incremental (`calcular_mediana_agregada`/
`calcular_distribucion_referencias` sobre una lista de `ReporteTema` ya
calculados y persistidos por separado, como hace la Feature 004) deben
producir **el mismo resultado exacto** -- no aproximado. La mediana
necesita el conjunto completo de valores para calcularse; "incremental"
aquí significa acumular cada `ReporteTema` a medida que se calcula y
aplicar las funciones de agregación una sola vez, al final, nunca un
estadístico corriente que actualice un valor aproximado tema a tema.

Ambos caminos se ejercitan sobre el mismo `list[EntradaConjunto]`, con
`referencias` siempre no vacías y `es_directorio_omitido=False` -- la
exclusión por `sin_guitarra_referencia`/`directorio_omitido` ya la prueba
la Feature 002 por separado (`test_metrica_separacion_integracion.py`);
no es lo que esta suite fija.
"""

from __future__ import annotations

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.strategies import DrawFn

from guitar_tabs_analysis.analytics.metrica_separacion import (
    EntradaConjunto,
    agregar_conjunto,
    calcular_distribucion_referencias,
    calcular_mediana_agregada,
    emparejar_tema,
)
from tests.fixtures.metrica_separacion_fixture import (
    estimacion_sintetica,
    onda_senoidal,
    referencia_sintetica,
)


def _reportes_incrementales(entradas: list[EntradaConjunto]) -> list:
    """Simula lo que la Feature 004 hace de verdad: calcular un
    `ReporteTema` a la vez y acumularlo -- nunca `agregar_conjunto` en
    bloque sobre la lista completa de `EntradaConjunto`."""
    return [
        emparejar_tema(entrada.tema_id, entrada.referencias, entrada.estimaciones)
        for entrada in entradas
    ]


def test_equivalencia_exacta_con_caso_concreto_mas_inf_y_menos_inf() -> None:
    """Caso concreto que ejercita el caso NaN de `_mediana_orden` (dos
    valores centrales +inf/-inf): un tema con una referencia emparejada
    consigo misma (`si_sdr` = +inf exacto, verificación de respuesta
    conocida) y un tema con una referencia sin ninguna estimación
    disponible (-inf por convención, FR-008 de la Feature 002)."""
    muestras = onda_senoidal(500)
    tema_mas_inf = EntradaConjunto(
        tema_id="TrackMasInf",
        referencias=[referencia_sintetica(identificador_origen="S01", muestras=muestras)],
        estimaciones=[estimacion_sintetica(identificador="S01", muestras=muestras)],
        es_directorio_omitido=False,
    )
    tema_menos_inf = EntradaConjunto(
        tema_id="TrackMenosInf",
        referencias=[referencia_sintetica(identificador_origen="S02", muestras=muestras)],
        estimaciones=[],
        es_directorio_omitido=False,
    )
    entradas = [tema_mas_inf, tema_menos_inf]

    resultado_bloque = agregar_conjunto(entradas)

    reportes = _reportes_incrementales(entradas)
    mediana_incremental = calcular_mediana_agregada(reportes)
    distribucion_incremental = calcular_distribucion_referencias(reportes)

    assert resultado_bloque.mediana == mediana_incremental
    assert resultado_bloque.mediana == float("-inf")  # caso NaN resuelto al valor bajo
    assert resultado_bloque.distribucion_referencias_por_tema == distribucion_incremental
    assert distribucion_incremental == {1: 2}


_frecuencia_onda = st.floats(
    min_value=10.0, max_value=2000.0, allow_nan=False, allow_infinity=False
)
_n_temas = st.integers(min_value=0, max_value=6)
_n_referencias = st.integers(min_value=1, max_value=5)
_n_estimaciones = st.integers(min_value=0, max_value=5)
_n_muestras = st.integers(min_value=50, max_value=500)
_es_silenciosa = st.integers(min_value=0, max_value=4).map(lambda n: n == 0)


@st.composite
def _conjunto_sin_exclusiones(draw: DrawFn) -> list[EntradaConjunto]:
    """Genera `list[EntradaConjunto]` con `referencias` siempre no vacías
    y `es_directorio_omitido=False` -- ningún tema de esta estrategia
    puede caer en `sin_guitarra_referencia` ni `directorio_omitido`, para
    que la comparación sea puramente sobre la aritmética de agregación,
    no sobre el filtrado de exclusiones (ya cubierto por la Feature 002)."""
    n_temas = draw(_n_temas)
    entradas = []
    for indice in range(n_temas):
        n_muestras = draw(_n_muestras)
        referencias = [
            referencia_sintetica(
                identificador_origen=f"T{indice:02d}R{r:02d}",
                muestras=onda_senoidal(n_muestras, frecuencia_onda=draw(_frecuencia_onda)),
            )
            for r in range(draw(_n_referencias))
        ]
        estimaciones = [
            estimacion_sintetica(
                identificador=f"T{indice:02d}E{e:02d}",
                muestras=np.zeros(n_muestras)
                if draw(_es_silenciosa)
                else onda_senoidal(n_muestras, frecuencia_onda=draw(_frecuencia_onda)),
            )
            for e in range(draw(_n_estimaciones))
        ]
        entradas.append(
            EntradaConjunto(
                tema_id=f"Track{indice:02d}",
                referencias=referencias,
                estimaciones=estimaciones,
                es_directorio_omitido=False,
            )
        )
    return entradas


@given(entradas=_conjunto_sin_exclusiones())
@settings(max_examples=200)
def test_equivalencia_exacta_bloque_vs_incremental(entradas: list[EntradaConjunto]) -> None:
    resultado_bloque = agregar_conjunto(entradas)

    reportes = _reportes_incrementales(entradas)
    mediana_incremental = calcular_mediana_agregada(reportes)
    distribucion_incremental = calcular_distribucion_referencias(reportes)

    assert resultado_bloque.mediana == mediana_incremental
    assert resultado_bloque.distribucion_referencias_por_tema == distribucion_incremental
