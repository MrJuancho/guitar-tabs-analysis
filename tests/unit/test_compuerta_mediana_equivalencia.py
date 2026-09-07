"""Property test (T003 de `specs/005-compuerta-metrica/tasks.md`, User
Story 1): fija que `statistics.median` es seguro de usar para la mediana
de referencias *emparejadas* sin depender de la mediana de estadístico
de orden privada de la Feature 002
(`analytics.metrica_separacion._mediana_orden`) -- research.md #3.

La regla pesimista de `_mediana_orden` (resolver al valor más bajo de
los dos centrales cuando su promedio sería `NaN`) solo se activa cuando
el pool mezcla `+inf` y `-inf` en un pool de tamaño par. El pool de
*emparejadas* nunca contiene `-inf` (ese sentinela es exclusivo de
`sin_pareja`, Feature 002 FR-008) -- así que, sobre ese dominio
restringido, `statistics.median` y `_mediana_orden` son equivalentes por
construcción. Este archivo fija esa propiedad, y también la divergencia
real fuera del dominio, para probar que la verificación no es vacía.
"""

from __future__ import annotations

import math
import statistics

from hypothesis import given
from hypothesis import strategies as st

_pools_sin_menos_infinito = st.lists(
    st.floats(allow_nan=False, allow_infinity=False, min_value=-1000.0, max_value=1000.0)
    | st.just(float("inf")),
    min_size=1,
    max_size=12,
)


def _mediana_orden(pool: list[float]) -> float:
    """Copia local de la regla de `analytics.metrica_separacion._mediana_orden`
    (no se importa: este test fija la propiedad matemática, no crea una
    dependencia sobre una función privada de otro módulo)."""
    ordenado = sorted(pool)
    n = len(ordenado)
    if n % 2 == 1:
        return ordenado[n // 2]
    a, b = ordenado[n // 2 - 1], ordenado[n // 2]
    promedio = (a + b) / 2
    if math.isnan(promedio):
        return min(a, b)
    return promedio


@given(pool=_pools_sin_menos_infinito)
def test_statistics_median_coincide_con_mediana_de_orden_sin_menos_infinito(
    pool: list[float],
) -> None:
    assert statistics.median(pool) == _mediana_orden(pool)


def test_la_divergencia_es_real_fuera_del_dominio_restringido() -> None:
    """Evidencia de que la propiedad de arriba no es vacía: mezclar
    `+inf`/`-inf` sí hace que `statistics.median` diverja de
    `_mediana_orden` -- exactamente el caso que `_mediana_orden` existe
    para resolver, y exactamente el caso que el pool de *emparejadas*
    nunca puede producir."""
    pool = [float("inf"), float("-inf")]

    assert math.isnan(statistics.median(pool))
    assert _mediana_orden(pool) == float("-inf")
