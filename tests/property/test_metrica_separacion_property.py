"""Property tests (Hypothesis) para `emparejar_tema()` (T016 de
`specs/002-metrica-separacion-guitarra/tasks.md`, User Story 1/P1).

La estrategia genera conjuntos arbitrarios de referencias y estimaciones
sintéticas -- senoidales con frecuencia muestreada de un rango real, y
ocasionalmente silencio digital exacto (para ejercitar tanto
"energia_nula" como "estimacion_silenciosa") -- en vez de una lista fija
de ejemplos a mano (AGENTS.md "Property tests: muestrea del dominio
real").
"""

from __future__ import annotations

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.strategies import DrawFn

from guitar_tabs_analysis.analytics.metrica_separacion import emparejar_tema
from tests.fixtures.metrica_separacion_fixture import (
    estimacion_sintetica,
    onda_senoidal,
    referencia_sintetica,
    silencio,
)

# Frecuencia estrictamente positiva -- una frecuencia de 0 Hz con fase 0
# generaría una onda constante en cero, un silencio ACCIDENTAL en vez del
# silencio deliberado que la estrategia ya modela por separado.
_frecuencia_onda = st.floats(
    min_value=10.0, max_value=2000.0, allow_nan=False, allow_infinity=False
)
_n_items = st.integers(min_value=0, max_value=5)
_n_muestras = st.integers(min_value=50, max_value=500)
# 1 de cada 5 pistas generadas es silencio digital exacto -- suficiente
# para que Hypothesis explore el caso sin dominar la mayoría de ejemplos.
_es_silenciosa = st.integers(min_value=0, max_value=4).map(lambda n: n == 0)


@st.composite
def _tema_arbitrario(
    draw: DrawFn,
) -> tuple[list[tuple[str, np.ndarray]], list[tuple[str, np.ndarray]]]:
    """Genera referencias y estimaciones independientes, compartiendo
    `n_muestras` (si no, cada par sería incompatible por construcción y
    `emparejar_tema` fallaría con `EstimacionIncompatibleError`, que no
    es lo que este property test ejercita)."""
    n_muestras = draw(_n_muestras)
    n_referencias = draw(_n_items)
    n_estimaciones = draw(_n_items)

    referencias = [
        (
            f"S{indice:02d}",
            silencio(n_muestras)
            if draw(_es_silenciosa)
            else onda_senoidal(n_muestras, frecuencia_onda=draw(_frecuencia_onda)),
        )
        for indice in range(n_referencias)
    ]
    estimaciones = [
        (
            f"E{indice:02d}",
            silencio(n_muestras)
            if draw(_es_silenciosa)
            else onda_senoidal(n_muestras, frecuencia_onda=draw(_frecuencia_onda)),
        )
        for indice in range(n_estimaciones)
    ]
    return referencias, estimaciones


@given(tema=_tema_arbitrario())
@settings(max_examples=200)
def test_invariantes_estructurales_de_emparejar_tema(
    tema: tuple[list[tuple[str, np.ndarray]], list[tuple[str, np.ndarray]]],
) -> None:
    """data-model.md invariantes de `ReporteTema`; SC-003, SC-009."""
    referencias_raw, estimaciones_raw = tema
    referencias = [
        referencia_sintetica(identificador_origen=identificador, muestras=muestras)
        for identificador, muestras in referencias_raw
    ]
    estimaciones = [
        estimacion_sintetica(identificador=identificador, muestras=muestras)
        for identificador, muestras in estimaciones_raw
    ]
    energia_por_estimacion = {
        identificador: float(np.dot(muestras, muestras))
        for identificador, muestras in estimaciones_raw
    }

    reporte = emparejar_tema("TrackProp", referencias, estimaciones)

    # Ninguna referencia se omite del reporte (FR-005, SC-002).
    assert len(reporte.emparejadas) + len(reporte.sin_pareja) == len(referencias)

    # Ninguna estimación se comparte entre dos referencias (FR-002, SC-003).
    identificadores_estimacion = [e.identificador_estimacion for e in reporte.emparejadas]
    assert len(identificadores_estimacion) == len(set(identificadores_estimacion))

    # Ninguna ReferenciaEmparejada tiene una estimación de energía nula
    # (SC-009) -- si la tuviera, debería estar en sin_pareja con motivo
    # "estimacion_silenciosa", no aquí.
    for emparejada in reporte.emparejadas:
        assert energia_por_estimacion[emparejada.identificador_estimacion] > 0.0
