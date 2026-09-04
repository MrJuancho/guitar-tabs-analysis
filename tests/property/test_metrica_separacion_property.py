"""Property tests (Hypothesis) para `emparejar_tema()`/`agregar_conjunto()`
(T016, T023, T024 de `specs/002-metrica-separacion-guitarra/tasks.md`,
User Story 1/P1 y User Story 2/P2).

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

from guitar_tabs_analysis.analytics.metrica_separacion import (
    EntradaConjunto,
    agregar_conjunto,
    emparejar_tema,
)
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


_n_temas = st.integers(min_value=0, max_value=4)
_es_omitido = st.booleans()


@st.composite
def _conjunto_arbitrario(draw: DrawFn) -> list[EntradaConjunto]:
    """Genera una lista de `EntradaConjunto` -- cada tema con su propio
    `n_muestras`, 0-5 referencias y 0-5 estimaciones (senoidales u
    ocasionalmente silencio digital), y ocasionalmente marcado como
    perteneciente al directorio `omitted`."""
    n_temas = draw(_n_temas)
    entradas = []
    for indice_tema in range(n_temas):
        n_muestras = draw(_n_muestras)
        n_referencias = draw(_n_items)
        n_estimaciones = draw(_n_items)
        referencias = [
            referencia_sintetica(
                identificador_origen=f"T{indice_tema:02d}R{r:02d}",
                muestras=silencio(n_muestras)
                if draw(_es_silenciosa)
                else onda_senoidal(n_muestras, frecuencia_onda=draw(_frecuencia_onda)),
            )
            for r in range(n_referencias)
        ]
        estimaciones = [
            estimacion_sintetica(
                identificador=f"T{indice_tema:02d}E{e:02d}",
                muestras=silencio(n_muestras)
                if draw(_es_silenciosa)
                else onda_senoidal(n_muestras, frecuencia_onda=draw(_frecuencia_onda)),
            )
            for e in range(n_estimaciones)
        ]
        entradas.append(
            EntradaConjunto(
                tema_id=f"Track{indice_tema:02d}",
                referencias=referencias,
                estimaciones=estimaciones,
                es_directorio_omitido=draw(_es_omitido),
            )
        )
    return entradas


@given(entradas=_conjunto_arbitrario())
@settings(max_examples=150)
def test_invariantes_estructurales_de_agregar_conjunto(entradas: list[EntradaConjunto]) -> None:
    """data-model.md invariantes de `ResultadoAgregado`; SC-005."""
    resultado = agregar_conjunto(entradas)

    suma_distribucion = sum(resultado.distribucion_referencias_por_tema.values())
    assert suma_distribucion == resultado.num_temas_evaluados
    assert len(resultado.reportes_por_tema) == resultado.num_temas_evaluados
    assert len(resultado.exclusiones) + resultado.num_temas_evaluados == len(entradas)

    tema_ids_excluidos = {e.tema_id for e in resultado.exclusiones}
    tema_ids_evaluados = {r.tema_id for r in resultado.reportes_por_tema}
    assert tema_ids_excluidos.isdisjoint(tema_ids_evaluados)


@st.composite
def _tema_completamente_sin_emparejar(draw: DrawFn) -> EntradaConjunto:
    """Un tema garantizado a que NINGUNA de sus referencias quede
    emparejada -- cero estimaciones, así que todas caen en
    `sin_estimacion_disponible`. research.md #12: la garantía de SC-004
    solo es demostrable para este caso (el tema aporta *solo* copias del
    sentinel `-inf` al pool), no para un tema con *alguna* referencia sin
    pareja mezclada con otras bien emparejadas."""
    n_muestras = draw(_n_muestras)
    n_referencias = draw(st.integers(min_value=1, max_value=4))
    referencias = [
        referencia_sintetica(
            identificador_origen=f"Extra_R{r:02d}",
            muestras=onda_senoidal(n_muestras, frecuencia_onda=draw(_frecuencia_onda)),
        )
        for r in range(n_referencias)
    ]
    return EntradaConjunto(
        tema_id="TrackExtraTodoSinEmparejar",
        referencias=referencias,
        estimaciones=[],
        es_directorio_omitido=False,
    )


@given(entradas_base=_conjunto_arbitrario(), tema_extra=_tema_completamente_sin_emparejar())
@settings(max_examples=150)
def test_incluir_tema_completamente_sin_emparejar_nunca_mejora_la_mediana(
    entradas_base: list[EntradaConjunto], tema_extra: EntradaConjunto
) -> None:
    """spec.md AS US2.5, SC-004 -- acotado (research.md #12) a un tema
    donde ninguna referencia queda emparejada. No es una propiedad
    general sobre cualquier tema con alguna referencia sin pareja."""
    resultado_sin = agregar_conjunto(entradas_base)
    resultado_con = agregar_conjunto([*entradas_base, tema_extra])

    if resultado_sin.mediana is None:
        # "Sin datos" no es "peor valor" -- cualquier mediana con datos
        # reales es un resultado válido, no una mejora artificial.
        return
    assert resultado_con.mediana is not None
    assert resultado_con.mediana <= resultado_sin.mediana
